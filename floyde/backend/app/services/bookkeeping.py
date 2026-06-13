"""Open-source bookkeeping sync.

Pushes successful payments into Frappe Books or Akaunting as sales entries.
Provider is selected by `FLOYDE_BOOKKEEPING_PROVIDER`. Default "none" records
an idempotency marker locally so the rest of the system behaves identically
whether or not a ledger is connected.

The HTTP calls here are intentionally thin adapters — real field mappings
(accounts, tax, party) belong in a follow-up once a target ledger is chosen.
"""

from __future__ import annotations

import logging

import httpx
from sqlmodel import Session

from app.config import settings
from app.models import Payment

log = logging.getLogger("floyde.bookkeeping")


def record_payment(session: Session, payment: Payment) -> Payment:
    """Idempotently sync a succeeded payment to the configured ledger."""
    if payment.bookkeeping_ref:  # already synced
        return payment

    provider = settings.bookkeeping_provider
    try:
        if provider == "frappe":
            ref = _sync_frappe(payment)
        elif provider == "akaunting":
            ref = _sync_akaunting(payment)
        else:
            ref = f"local:{payment.id}"
    except httpx.HTTPError as exc:  # never block the sale on ledger downtime
        log.warning("Bookkeeping sync failed for payment %s: %s", payment.id, exc)
        return payment

    payment.bookkeeping_ref = ref
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def _amount_dollars(payment: Payment) -> float:
    return round(payment.amount_cents / 100, 2)


def _sync_frappe(payment: Payment) -> str:
    """Create a Payment Entry in Frappe Books / ERPNext."""
    base = (settings.bookkeeping_base_url or "").rstrip("/")
    resp = httpx.post(
        f"{base}/api/resource/Payment Entry",
        headers={"Authorization": f"token {settings.bookkeeping_api_key}"},
        json={
            "payment_type": "Receive",
            "paid_amount": _amount_dollars(payment),
            "received_amount": _amount_dollars(payment),
            "reference_no": payment.stripe_payment_intent_id,
            "remarks": f"Floyde {payment.type} for booking {payment.booking_id}",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return f"frappe:{resp.json().get('data', {}).get('name', payment.id)}"


def _sync_akaunting(payment: Payment) -> str:
    """Create a revenue transaction in Akaunting."""
    base = (settings.bookkeeping_base_url or "").rstrip("/")
    resp = httpx.post(
        f"{base}/api/transactions",
        headers={"Authorization": f"Bearer {settings.bookkeeping_api_key}"},
        json={
            "type": "income",
            "amount": _amount_dollars(payment),
            "currency_code": payment.currency.upper(),
            "reference": payment.stripe_payment_intent_id,
            "description": f"Floyde {payment.type} (booking {payment.booking_id})",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return f"akaunting:{resp.json().get('data', {}).get('id', payment.id)}"

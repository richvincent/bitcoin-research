"""Stripe payment intents — with a zero-config stub mode.

When no Stripe key is set (`FLOYDE_STRIPE_SECRET_KEY`), this returns
deterministic fake intents so the booking/POS flow is fully exercisable in
dev and CI without network or credentials. Bookkeeping sync is triggered on
success regardless of mode.
"""

from __future__ import annotations

import uuid

from sqlmodel import Session

from app.config import settings
from app.models import Payment, PaymentStatus, PaymentType
from app.services import bookkeeping


def _create_stripe_intent(amount_cents: int, currency: str) -> tuple[str, str]:
    """Return (payment_intent_id, client_secret). Real Stripe call."""
    import stripe

    stripe.api_key = settings.stripe_secret_key
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        automatic_payment_methods={"enabled": True},
    )
    return intent.id, intent.client_secret


def create_intent(amount_cents: int, currency: str = "usd") -> tuple[str, str | None, bool]:
    """Create a payment intent (real or stub).

    Returns (intent_id, client_secret, succeeded). In stub mode the charge is
    considered immediately succeeded; with real Stripe it starts pending and
    is confirmed later via the webhook. Shared by POS and marketplace.
    """
    if amount_cents <= 0:
        raise ValueError("amount_cents must be positive")
    if settings.stripe_enabled:
        intent_id, client_secret = _create_stripe_intent(amount_cents, currency)
        return intent_id, client_secret, False
    intent_id = f"pi_stub_{uuid.uuid4().hex[:24]}"
    return intent_id, f"{intent_id}_secret_stub", True


def create_payment(
    session: Session,
    *,
    shop_id: int,
    amount_cents: int,
    booking_id: int | None = None,
    payment_type: PaymentType = PaymentType.DEPOSIT,
    currency: str = "usd",
) -> tuple[Payment, str | None]:
    """Create a Payment row + provider intent. Returns (payment, client_secret).

    In stub mode the payment is marked SUCCEEDED immediately so downstream
    flows (confirmation, bookkeeping) can be tested end to end.
    """
    intent_id, client_secret, succeeded = create_intent(amount_cents, currency)
    status = PaymentStatus.SUCCEEDED if succeeded else PaymentStatus.PENDING

    payment = Payment(
        booking_id=booking_id,
        shop_id=shop_id,
        amount_cents=amount_cents,
        currency=currency,
        type=payment_type,
        status=status,
        stripe_payment_intent_id=intent_id,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)

    if payment.status is PaymentStatus.SUCCEEDED:
        bookkeeping.record_payment(session, payment)

    return payment, client_secret


def mark_succeeded(session: Session, payment: Payment) -> Payment:
    """Promote a pending payment to succeeded (e.g. from a Stripe webhook)."""
    if payment.status is PaymentStatus.SUCCEEDED:
        return payment
    payment.status = PaymentStatus.SUCCEEDED
    session.add(payment)
    session.commit()
    session.refresh(payment)
    bookkeeping.record_payment(session, payment)
    return payment

"""POS & payments — checkout, deposits, Stripe webhook."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.config import settings
from app.models import Payment, PaymentStatus
from app.schemas.schemas import PaymentCreate, PaymentOut
from app.services import payments

router = APIRouter(prefix="/pos", tags=["pos"])


@router.post("/charge", status_code=status.HTTP_201_CREATED)
def charge(body: PaymentCreate, _: CurrentUser, session: SessionDep) -> dict:
    """Create a payment intent. Returns the payment plus a client_secret the
    frontend uses to confirm with Stripe.js. In stub mode it auto-succeeds."""
    try:
        payment, client_secret = payments.create_payment(
            session,
            shop_id=body.shop_id,
            amount_cents=body.amount_cents,
            booking_id=body.booking_id,
            payment_type=body.type,
            currency=body.currency,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return {
        "payment": PaymentOut.model_validate(payment).model_dump(),
        "client_secret": client_secret,
    }


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    _: CurrentUser, session: SessionDep, shop_id: int | None = None
) -> list[Payment]:
    stmt = select(Payment)
    if shop_id is not None:
        stmt = stmt.where(Payment.shop_id == shop_id)
    return list(session.exec(stmt.order_by(Payment.created_at.desc())).all())


@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, session: SessionDep) -> dict:
    """Handle Stripe events. Verifies signature when a webhook secret is set."""
    payload = await request.body()
    event_type = None

    if settings.stripe_webhook_secret:
        import stripe

        sig = request.headers.get("stripe-signature", "")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig, settings.stripe_webhook_secret
            )
        except Exception as exc:  # signature / parse failure
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook") from exc
        event_type = event["type"]
        intent_id = event["data"]["object"].get("id")
    else:
        import json

        body = json.loads(payload or b"{}")
        event_type = body.get("type")
        intent_id = body.get("data", {}).get("object", {}).get("id")

    if event_type == "payment_intent.succeeded" and intent_id:
        payment = session.exec(
            select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
        ).first()
        if payment and payment.status != PaymentStatus.SUCCEEDED:
            payments.mark_succeeded(session, payment)

    return {"received": True}

"""Marketplace helpers: slugging, rating aggregation, and order checkout."""

from __future__ import annotations

import re

from sqlmodel import Session, func, select

from app.config import settings
from app.models import (
    MarketplaceOrder,
    Offering,
    OrderItem,
    OrderStatus,
    Provider,
    Review,
)
from app.services import payments

_slug_re = re.compile(r"[^a-z0-9]+")


class OrderError(ValueError):
    """Raised for invalid order requests (unknown/unpriced offerings, etc.)."""


def place_order(
    session: Session,
    *,
    provider_id: int,
    buyer_id: int,
    lines: list[tuple[int, int]],  # (offering_id, quantity)
    buyer_shop_id: int | None = None,
    notes: str = "",
) -> MarketplaceOrder:
    """Validate lines, compute commission, create the order, and capture
    payment (stub auto-succeeds). Every offering must belong to the provider
    and have a price."""
    provider = session.get(Provider, provider_id)
    if provider is None or not provider.is_active:
        raise OrderError("Provider not found")

    items: list[OrderItem] = []
    subtotal = 0
    for offering_id, qty in lines:
        if qty < 1:
            raise OrderError("Quantity must be at least 1")
        offering = session.get(Offering, offering_id)
        if offering is None or offering.provider_id != provider_id:
            raise OrderError(f"Offering {offering_id} not found for this provider")
        if offering.price_cents is None:
            raise OrderError(f"'{offering.title}' is contact-for-pricing only")
        line_total = offering.price_cents * qty
        subtotal += line_total
        items.append(
            OrderItem(
                offering_id=offering.id,
                title=offering.title,
                unit_price_cents=offering.price_cents,
                quantity=qty,
                line_total_cents=line_total,
            )
        )

    rate = settings.marketplace_commission_rate
    commission = round(subtotal * rate)

    order = MarketplaceOrder(
        provider_id=provider_id,
        buyer_id=buyer_id,
        buyer_shop_id=buyer_shop_id,
        subtotal_cents=subtotal,
        commission_rate=rate,
        commission_cents=commission,
        provider_payout_cents=subtotal - commission,
        notes=notes,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    for it in items:
        it.order_id = order.id
        session.add(it)
    session.commit()

    # Capture payment (stub auto-succeeds; real Stripe stays pending until webhook).
    intent_id, _secret, succeeded = payments.create_intent(subtotal, order.currency)
    order.stripe_payment_intent_id = intent_id
    if succeeded:
        order.status = OrderStatus.PAID
    session.add(order)
    session.commit()
    session.refresh(order)
    return order



def slugify(name: str) -> str:
    return _slug_re.sub("-", name.lower()).strip("-")


def unique_slug(session: Session, name: str) -> str:
    base = slugify(name) or "provider"
    slug = base
    i = 2
    while session.exec(select(Provider).where(Provider.slug == slug)).first():
        slug = f"{base}-{i}"
        i += 1
    return slug


def recompute_rating(session: Session, provider: Provider) -> Provider:
    """Refresh a provider's cached average rating + review count."""
    avg, count = session.exec(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.provider_id == provider.id
        )
    ).one()
    provider.rating = round(float(avg), 2) if avg is not None else 0.0
    provider.review_count = int(count or 0)
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider

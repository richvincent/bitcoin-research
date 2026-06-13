"""Marketplace lite: provider directory, offerings, and ratings/reviews.

Phase 2 scope — discovery and reputation only. Transactions and commissions
are a later phase. Any authenticated user can list a provider (and becomes its
owner); only the owner can edit it or add offerings. Anyone (except the owner)
can leave one review per provider.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    MarketplaceOrder,
    Offering,
    OrderItem,
    OrderStatus,
    Provider,
    ProviderCategory,
    Review,
    User,
)
from app.schemas.schemas import (
    OfferingCreate,
    OfferingOut,
    OrderCreate,
    OrderItemOut,
    OrderOut,
    ProviderCreate,
    ProviderDetail,
    ProviderOut,
    ReviewCreate,
    ReviewOut,
)
from app.services import marketplace

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/categories", response_model=list[str])
def list_categories() -> list[str]:
    return [c.value for c in ProviderCategory]


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(
    session: SessionDep,
    category: ProviderCategory | None = None,
    q: str | None = None,
    sort: str = "rating",
) -> list[Provider]:
    """Public directory. Filter by category, free-text search, sort by
    `rating` (default) or `newest`."""
    stmt = select(Provider).where(Provider.is_active == True)  # noqa: E712
    if category is not None:
        stmt = stmt.where(Provider.category == category)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Provider.name).like(like))
    rows = list(session.exec(stmt).all())
    if sort == "newest":
        rows.sort(key=lambda p: p.id or 0, reverse=True)
    else:  # rating, then review volume as a tiebreaker
        rows.sort(key=lambda p: (p.rating, p.review_count), reverse=True)
    return rows


@router.post("/providers", response_model=ProviderOut, status_code=status.HTTP_201_CREATED)
def create_provider(
    body: ProviderCreate, user: CurrentUser, session: SessionDep
) -> Provider:
    provider = Provider(
        **body.model_dump(),
        slug=marketplace.unique_slug(session, body.name),
        created_by=user.id,
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.get("/providers/{provider_id}", response_model=ProviderDetail)
def get_provider(provider_id: int, session: SessionDep) -> ProviderDetail:
    provider = session.get(Provider, provider_id)
    if provider is None or not provider.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")
    offerings = session.exec(
        select(Offering).where(
            Offering.provider_id == provider_id,
            Offering.is_active == True,  # noqa: E712
        )
    ).all()
    reviews = session.exec(
        select(Review).where(Review.provider_id == provider_id)
    ).all()
    review_out = []
    for r in sorted(reviews, key=lambda x: x.created_at, reverse=True):
        author = session.get(User, r.author_id)
        review_out.append(
            ReviewOut(
                **r.model_dump(),
                author_name=(author.full_name or "Member") if author else "Member",
            )
        )
    return ProviderDetail(
        **ProviderOut.model_validate(provider).model_dump(),
        offerings=[OfferingOut.model_validate(o) for o in offerings],
        reviews=review_out,
    )


@router.post(
    "/providers/{provider_id}/offerings",
    response_model=OfferingOut,
    status_code=status.HTTP_201_CREATED,
)
def add_offering(
    provider_id: int,
    body: OfferingCreate,
    user: CurrentUser,
    session: SessionDep,
) -> Offering:
    provider = _owned_provider(session, provider_id, user)
    offering = Offering(provider_id=provider.id, **body.model_dump())
    session.add(offering)
    session.commit()
    session.refresh(offering)
    return offering


@router.post(
    "/providers/{provider_id}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def add_review(
    provider_id: int,
    body: ReviewCreate,
    user: CurrentUser,
    session: SessionDep,
) -> ReviewOut:
    provider = session.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")
    if provider.created_by == user.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You can't review your own listing"
        )

    # One review per author per provider — update in place if it exists.
    existing = session.exec(
        select(Review).where(
            Review.provider_id == provider_id, Review.author_id == user.id
        )
    ).first()
    if existing:
        existing.rating = body.rating
        existing.title = body.title
        existing.body = body.body
        review = existing
    else:
        review = Review(provider_id=provider_id, author_id=user.id, **body.model_dump())
    session.add(review)
    session.commit()
    session.refresh(review)

    # Snapshot the response before recompute_rating's commit expires `review`.
    out = ReviewOut(**review.model_dump(), author_name=user.full_name or "Member")
    marketplace.recompute_rating(session, provider)
    return out


def _owned_provider(session: SessionDep, provider_id: int, user: User) -> Provider:
    provider = session.get(Provider, provider_id)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider not found")
    if provider.created_by != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your listing")
    return provider


# ── Orders / transactions ─────────────────────────────────────────────
def _order_out(session: SessionDep, order: MarketplaceOrder) -> OrderOut:
    provider = session.get(Provider, order.provider_id)
    buyer = session.get(User, order.buyer_id)
    items = session.exec(
        select(OrderItem).where(OrderItem.order_id == order.id)
    ).all()
    return OrderOut(
        **order.model_dump(),
        provider_name=provider.name if provider else "",
        buyer_name=(buyer.full_name or buyer.email) if buyer else "",
        items=[OrderItemOut.model_validate(i) for i in items],
    )


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    body: OrderCreate, user: CurrentUser, session: SessionDep
) -> OrderOut:
    try:
        order = marketplace.place_order(
            session,
            provider_id=body.provider_id,
            buyer_id=user.id,
            lines=[(i.offering_id, i.quantity) for i in body.items],
            buyer_shop_id=body.buyer_shop_id,
            notes=body.notes,
        )
    except marketplace.OrderError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _order_out(session, order)


@router.get("/orders", response_model=list[OrderOut])
def list_orders(
    user: CurrentUser, session: SessionDep, role: str = "buyer"
) -> list[OrderOut]:
    """`role=buyer` (default) returns the user's purchases; `role=seller`
    returns orders placed against providers they own."""
    if role == "seller":
        owned = session.exec(
            select(Provider.id).where(Provider.created_by == user.id)
        ).all()
        if not owned:
            return []
        stmt = select(MarketplaceOrder).where(
            MarketplaceOrder.provider_id.in_(owned)  # type: ignore[attr-defined]
        )
    else:
        stmt = select(MarketplaceOrder).where(MarketplaceOrder.buyer_id == user.id)
    orders = session.exec(stmt.order_by(MarketplaceOrder.created_at.desc())).all()
    return [_order_out(session, o) for o in orders]


def _accessible_order(
    session: SessionDep, order_id: int, user: User
) -> MarketplaceOrder:
    order = session.get(MarketplaceOrder, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    provider = session.get(Provider, order.provider_id)
    is_seller = provider is not None and provider.created_by == user.id
    if order.buyer_id != user.id and not is_seller and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your order")
    return order


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: CurrentUser, session: SessionDep) -> OrderOut:
    return _order_out(session, _accessible_order(session, order_id, user))


@router.post("/orders/{order_id}/fulfill", response_model=OrderOut)
def fulfill_order(order_id: int, user: CurrentUser, session: SessionDep) -> OrderOut:
    """Seller marks a paid order fulfilled."""
    order = session.get(MarketplaceOrder, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    _owned_provider(session, order.provider_id, user)  # seller-only
    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Only paid orders can be fulfilled (status: {order.status})",
        )
    order.status = OrderStatus.FULFILLED
    session.add(order)
    session.commit()
    session.refresh(order)
    return _order_out(session, order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, user: CurrentUser, session: SessionDep) -> OrderOut:
    """Buyer or seller cancels an order that hasn't been fulfilled."""
    order = _accessible_order(session, order_id, user)
    if order.status == OrderStatus.FULFILLED:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Fulfilled orders can't be cancelled"
        )
    order.status = OrderStatus.CANCELLED
    session.add(order)
    session.commit()
    session.refresh(order)
    return _order_out(session, order)

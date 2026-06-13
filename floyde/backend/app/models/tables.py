"""Table models.

Money is stored in integer cents to avoid float rounding. List/dict fields
(style tags, photo URLs, specialties) are stored as JSON columns — fine for
the MVP; revisit as relations if we need to query inside them.
"""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

import uuid

from app.models.enums import (
    BookingSource,
    BookingStatus,
    ConciergeStatus,
    OrderStatus,
    PaymentStatus,
    PaymentType,
    ProviderCategory,
    UserRole,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str = ""
    role: UserRole = Field(default=UserRole.CLIENT, index=True)
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)

    barber: "Barber" = Relationship(back_populates="user")
    client_profile: "ClientProfile" = Relationship(back_populates="user")


class Shop(SQLModel, table=True):
    __tablename__ = "shops"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(index=True, unique=True)
    owner_id: int | None = Field(default=None, foreign_key="users.id")
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = "America/Detroit"
    created_at: datetime = Field(default_factory=_utcnow)

    barbers: list["Barber"] = Relationship(back_populates="shop")
    services: list["Service"] = Relationship(back_populates="shop")
    products: list["Product"] = Relationship(back_populates="shop")


class Barber(SQLModel, table=True):
    __tablename__ = "barbers"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    shop_id: int = Field(foreign_key="shops.id", index=True)
    display_name: str
    bio: str = ""
    # e.g. ["fade", "beard", "scissor", "afro", "lineup"]
    specialties: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    rating: float = 5.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)

    user: User = Relationship(back_populates="barber")
    shop: Shop = Relationship(back_populates="barbers")
    bookings: list["Booking"] = Relationship(back_populates="barber")


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: int | None = Field(default=None, primary_key=True)
    shop_id: int = Field(foreign_key="shops.id", index=True)
    name: str
    description: str = ""
    duration_minutes: int = 30
    price_cents: int = 0
    # tags help match a service to a client's preferred styles
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_active: bool = True

    shop: Shop = Relationship(back_populates="services")


class ClientProfile(SQLModel, table=True):
    """Persistent style profile — the differentiator. Travels with the client
    across shops and powers smart matching + concierge context."""

    __tablename__ = "client_profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    phone: str = ""
    # Free-form, agent-readable: ["skin fade", "textured top", "low maintenance"]
    preferred_styles: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    # Nuances a barber should know: cowlicks, sensitivities, guard numbers, etc.
    style_notes: str = ""
    nuances: dict = Field(default_factory=dict, sa_column=Column(JSON))
    photo_urls: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    preferred_products: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    loyalty_points: int = 0
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    user: User = Relationship(back_populates="client_profile")


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    barber_id: int = Field(foreign_key="barbers.id", index=True)
    shop_id: int = Field(foreign_key="shops.id", index=True)
    service_id: int = Field(foreign_key="services.id")
    start_time: datetime = Field(index=True)
    end_time: datetime
    status: BookingStatus = Field(default=BookingStatus.PENDING, index=True)
    source: BookingSource = Field(default=BookingSource.ONLINE)
    deposit_cents: int = 0
    notes: str = ""
    # captured at booking time for analytics / explainability
    match_score: float | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    barber: Barber = Relationship(back_populates="bookings")
    payments: list["Payment"] = Relationship(back_populates="booking")


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: int | None = Field(default=None, primary_key=True)
    booking_id: int | None = Field(default=None, foreign_key="bookings.id", index=True)
    shop_id: int = Field(foreign_key="shops.id", index=True)
    amount_cents: int
    currency: str = "usd"
    type: PaymentType = Field(default=PaymentType.DEPOSIT)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)
    stripe_payment_intent_id: str | None = None
    # set once synced to Frappe/Akaunting, for idempotency
    bookkeeping_ref: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    booking: Booking | None = Relationship(back_populates="payments")


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    shop_id: int = Field(foreign_key="shops.id", index=True)
    name: str
    brand: str = ""
    sku: str = ""
    quantity: int = 0
    reorder_threshold: int = 3
    cost_cents: int = 0
    price_cents: int = 0
    amazon_asin: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    shop: Shop = Relationship(back_populates="products")


# ── Marketplace (Phase 2 "lite": directory + ratings, no transactions yet) ──
class Provider(SQLModel, table=True):
    """A marketplace vendor — supplies, insurance, marketing, etc."""

    __tablename__ = "providers"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(index=True, unique=True)
    category: ProviderCategory = Field(default=ProviderCategory.OTHER, index=True)
    description: str = ""
    website: str = ""
    logo_url: str = ""
    contact_email: str = ""
    location: str = ""
    created_by: int | None = Field(default=None, foreign_key="users.id")
    is_active: bool = True
    # Cached aggregates, recomputed on each new review.
    rating: float = 0.0
    review_count: int = 0
    created_at: datetime = Field(default_factory=_utcnow)

    offerings: list["Offering"] = Relationship(back_populates="provider")
    reviews: list["Review"] = Relationship(back_populates="provider")


class Offering(SQLModel, table=True):
    """A listing under a provider (a product, plan, or service)."""

    __tablename__ = "offerings"

    id: int | None = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="providers.id", index=True)
    title: str
    description: str = ""
    price_cents: int | None = None  # None = "contact for pricing"
    unit: str = ""  # e.g. "per month", "each", "per case"
    is_active: bool = True
    created_at: datetime = Field(default_factory=_utcnow)

    provider: Provider = Relationship(back_populates="offerings")


class MarketplaceOrder(SQLModel, table=True):
    """A purchase from a provider. Money split: the buyer pays the subtotal,
    the platform keeps a commission, and the provider is owed the remainder."""

    __tablename__ = "marketplace_orders"

    id: int | None = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="providers.id", index=True)
    buyer_id: int = Field(foreign_key="users.id", index=True)
    buyer_shop_id: int | None = Field(default=None, foreign_key="shops.id")
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True)
    subtotal_cents: int = 0
    commission_rate: float = 0.0
    commission_cents: int = 0
    provider_payout_cents: int = 0
    currency: str = "usd"
    stripe_payment_intent_id: str | None = None
    notes: str = ""
    created_at: datetime = Field(default_factory=_utcnow)

    items: list["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """A line on an order. Title/price are snapshotted so history is stable
    even if the offering later changes."""

    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="marketplace_orders.id", index=True)
    offering_id: int = Field(foreign_key="offerings.id")
    title: str = ""
    unit_price_cents: int = 0
    quantity: int = 1
    line_total_cents: int = 0

    order: MarketplaceOrder = Relationship(back_populates="items")


class Review(SQLModel, table=True):
    """A 1–5 star rating + note for a provider. One per author per provider."""

    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="providers.id", index=True)
    author_id: int = Field(foreign_key="users.id", index=True)
    rating: int  # 1..5
    title: str = ""
    body: str = ""
    created_at: datetime = Field(default_factory=_utcnow)

    provider: Provider = Relationship(back_populates="reviews")


def _concierge_ref() -> str:
    return f"ccg_{uuid.uuid4().hex[:16]}"


class ConciergeRequest(SQLModel, table=True):
    """A premium live-voice (Ruby) callback request from a client."""

    __tablename__ = "concierge_requests"

    id: int | None = Field(default=None, primary_key=True)
    request_id: str = Field(default_factory=_concierge_ref, index=True, unique=True)
    client_id: int = Field(foreign_key="users.id", index=True)
    shop_id: int | None = Field(default=None, foreign_key="shops.id", index=True)
    phone: str = ""
    topic: str = ""
    status: ConciergeStatus = Field(default=ConciergeStatus.QUEUED, index=True)
    notes: str = ""
    # Telephony: set once a "call now" bridge is placed.
    call_sid: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

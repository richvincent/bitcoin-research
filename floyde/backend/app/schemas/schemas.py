"""Request/response schemas (the API contract).

Kept separate from table models so the wire format can evolve independently
and never leaks columns like ``hashed_password``.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import (
    BookingSource,
    BookingStatus,
    PaymentStatus,
    PaymentType,
    ProviderCategory,
    UserRole,
)


# ── Auth ──────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
    role: UserRole = UserRole.CLIENT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


# ── Shops / barbers / services ────────────────────────────────────────
class ShopCreate(BaseModel):
    name: str
    slug: str
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    timezone: str = "America/Detroit"


class ShopOut(ShopCreate):
    id: int
    model_config = {"from_attributes": True}


class BarberCreate(BaseModel):
    user_id: int
    shop_id: int
    display_name: str
    bio: str = ""
    specialties: list[str] = []


class BarberOut(BaseModel):
    id: int
    shop_id: int
    display_name: str
    bio: str
    specialties: list[str]
    rating: float
    is_active: bool
    model_config = {"from_attributes": True}


class ServiceCreate(BaseModel):
    shop_id: int
    name: str
    description: str = ""
    duration_minutes: int = 30
    price_cents: int = 0
    tags: list[str] = []


class ServiceOut(ServiceCreate):
    id: int
    is_active: bool = True
    model_config = {"from_attributes": True}


# ── Client profiles ───────────────────────────────────────────────────
class ClientProfileUpsert(BaseModel):
    phone: str = ""
    preferred_styles: list[str] = []
    style_notes: str = ""
    nuances: dict = {}
    photo_urls: list[str] = []
    preferred_products: list[str] = []


class ClientProfileOut(ClientProfileUpsert):
    id: int
    user_id: int
    loyalty_points: int
    model_config = {"from_attributes": True}


# ── Matching ──────────────────────────────────────────────────────────
class BarberMatch(BaseModel):
    barber: BarberOut
    shop: ShopOut
    score: float = Field(description="0..1 composite fit score")
    distance_km: float | None = None
    next_available: datetime | None = None
    reasons: list[str] = []


# ── Bookings ──────────────────────────────────────────────────────────
class BookingCreate(BaseModel):
    barber_id: int
    service_id: int
    start_time: datetime
    source: BookingSource = BookingSource.ONLINE
    notes: str = ""


class BookingOut(BaseModel):
    id: int
    client_id: int
    barber_id: int
    shop_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    source: BookingSource
    deposit_cents: int
    match_score: float | None
    notes: str
    model_config = {"from_attributes": True}


class StaffBookingCreate(BaseModel):
    """A barber/owner booking on behalf of a client (e.g. a walk-in)."""

    client_email: EmailStr
    barber_id: int
    service_id: int
    start_time: datetime
    source: BookingSource = BookingSource.WALK_IN
    notes: str = ""


class ManagedBooking(BaseModel):
    """Enriched booking row for the staff schedule (names resolved)."""

    id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    source: BookingSource
    deposit_cents: int
    price_cents: int
    match_score: float | None
    notes: str
    client_name: str
    client_email: str
    barber_id: int
    barber_name: str
    service_name: str


# ── Payments / POS ────────────────────────────────────────────────────
class PaymentCreate(BaseModel):
    booking_id: int | None = None
    shop_id: int
    amount_cents: int
    type: PaymentType = PaymentType.DEPOSIT
    currency: str = "usd"


class PaymentOut(BaseModel):
    id: int
    booking_id: int | None
    shop_id: int
    amount_cents: int
    currency: str
    type: PaymentType
    status: PaymentStatus
    stripe_payment_intent_id: str | None
    model_config = {"from_attributes": True}


# ── Inventory ─────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    shop_id: int
    name: str
    brand: str = ""
    sku: str = ""
    quantity: int = 0
    reorder_threshold: int = 3
    cost_cents: int = 0
    price_cents: int = 0
    amazon_asin: str | None = None


class ProductOut(ProductCreate):
    id: int
    model_config = {"from_attributes": True}


class AmazonRec(BaseModel):
    asin: str
    title: str
    brand: str = ""
    price: str = ""
    rating: float | None = None
    review_count: int | None = None
    url: str = ""
    image_url: str = ""


# ── Marketplace ───────────────────────────────────────────────────────
class OfferingCreate(BaseModel):
    title: str
    description: str = ""
    price_cents: int | None = None
    unit: str = ""


class OfferingOut(OfferingCreate):
    id: int
    provider_id: int
    is_active: bool = True
    model_config = {"from_attributes": True}


class ProviderCreate(BaseModel):
    name: str
    category: ProviderCategory = ProviderCategory.OTHER
    description: str = ""
    website: str = ""
    logo_url: str = ""
    contact_email: str = ""
    location: str = ""


class ProviderOut(BaseModel):
    id: int
    name: str
    slug: str
    category: ProviderCategory
    description: str
    website: str
    logo_url: str
    contact_email: str
    location: str
    rating: float
    review_count: int
    is_active: bool
    created_by: int | None = None
    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str = ""
    body: str = ""


class ReviewOut(BaseModel):
    id: int
    provider_id: int
    author_id: int
    author_name: str = ""
    rating: int
    title: str
    body: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ProviderDetail(ProviderOut):
    offerings: list[OfferingOut] = []
    reviews: list[ReviewOut] = []

"""Domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "client"
    BARBER = "barber"
    OWNER = "owner"
    ADMIN = "admin"


class BookingStatus(StrEnum):
    PENDING = "pending"          # created, awaiting deposit/confirmation
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingSource(StrEnum):
    ONLINE = "online"            # booked via the booking page/PWA
    WALK_IN = "walk_in"          # added at the chair
    FLEX = "flex"                # on-demand "Flex Cut Now" matching


class PaymentType(StrEnum):
    DEPOSIT = "deposit"
    FINAL = "final"
    PRODUCT = "product"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class ProviderCategory(StrEnum):
    SUPPLIES = "supplies"
    EQUIPMENT = "equipment"
    INSURANCE = "insurance"
    MARKETING = "marketing"
    EDUCATION = "education"
    FINANCE = "finance"
    SOFTWARE = "software"
    OTHER = "other"

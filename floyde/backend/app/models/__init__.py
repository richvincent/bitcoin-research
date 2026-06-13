"""SQLModel table definitions for Floyde.

Importing this package registers every table on ``SQLModel.metadata``.
"""

from app.models.enums import (
    BookingSource,
    BookingStatus,
    PaymentStatus,
    PaymentType,
    ProviderCategory,
    UserRole,
)
from app.models.tables import (
    Barber,
    Booking,
    ClientProfile,
    Offering,
    Payment,
    Product,
    Provider,
    Review,
    Service,
    Shop,
    User,
)

__all__ = [
    "BookingSource",
    "BookingStatus",
    "PaymentStatus",
    "PaymentType",
    "ProviderCategory",
    "UserRole",
    "Barber",
    "Booking",
    "ClientProfile",
    "Offering",
    "Payment",
    "Product",
    "Provider",
    "Review",
    "Service",
    "Shop",
    "User",
]

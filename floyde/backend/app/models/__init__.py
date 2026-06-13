"""SQLModel table definitions for Floyde.

Importing this package registers every table on ``SQLModel.metadata``.
"""

from app.models.enums import (
    BookingSource,
    BookingStatus,
    PaymentStatus,
    PaymentType,
    UserRole,
)
from app.models.tables import (
    Barber,
    Booking,
    ClientProfile,
    Payment,
    Product,
    Service,
    Shop,
    User,
)

__all__ = [
    "BookingSource",
    "BookingStatus",
    "PaymentStatus",
    "PaymentType",
    "UserRole",
    "Barber",
    "Booking",
    "ClientProfile",
    "Payment",
    "Product",
    "Service",
    "Shop",
    "User",
]

"""Reports & analytics — staff-only shop rollups."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, require_roles
from app.models import User, UserRole
from app.schemas.schemas import ShopReport
from app.services import reports

router = APIRouter(prefix="/reports", tags=["reports"])

_STAFF = (UserRole.OWNER, UserRole.BARBER)


@router.get("/summary", response_model=ShopReport)
def summary(
    shop_id: int,
    session: SessionDep,
    days: int = Query(default=30, ge=1, le=365),
    _: User = Depends(require_roles(*_STAFF)),
) -> ShopReport:
    """Bookings, POS revenue, barber leaderboard, and supply spend for a shop
    over the trailing `days` window."""
    return ShopReport(**reports.shop_summary(session, shop_id, days))

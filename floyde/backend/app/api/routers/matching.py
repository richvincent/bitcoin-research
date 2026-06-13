"""Smart matching endpoints powering "Flex Cut Now"."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas.schemas import BarberMatch
from app.services import matching

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/barbers", response_model=list[BarberMatch])
def match_barbers(
    user: CurrentUser,
    session: SessionDep,
    service_id: int | None = None,
    lat: float | None = None,
    lng: float | None = None,
    shop_id: int | None = None,
    limit: int = 10,
) -> list[BarberMatch]:
    """Rank barbers for the current client by style fit, proximity,
    rating, and availability."""
    return matching.find_matches(
        session,
        client_user_id=user.id,
        service_id=service_id,
        client_lat=lat,
        client_lng=lng,
        shop_id=shop_id,
        limit=limit,
    )

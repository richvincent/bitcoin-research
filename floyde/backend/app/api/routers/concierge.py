"""Premium concierge (Ruby) requests."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.services import concierge

router = APIRouter(prefix="/concierge", tags=["concierge"])


class ConciergeRequest(BaseModel):
    phone: str
    topic: str = "booking assistance"


@router.post("/call")
def request_call(body: ConciergeRequest, user: CurrentUser) -> dict:
    """Queue a premium live-voice callback (top tiers)."""
    return concierge.initiate_call(
        client_user_id=user.id, phone=body.phone, topic=body.topic
    )

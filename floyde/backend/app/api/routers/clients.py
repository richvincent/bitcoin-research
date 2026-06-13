"""Client CRM — persistent style profiles (the differentiator)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import ClientProfile
from app.schemas.schemas import ClientProfileOut, ClientProfileUpsert

router = APIRouter(prefix="/clients", tags=["clients"])


def _get_or_create(session, user_id: int) -> ClientProfile:
    profile = session.exec(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    ).first()
    if profile is None:
        profile = ClientProfile(user_id=user_id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.get("/me/profile", response_model=ClientProfileOut)
def get_my_profile(user: CurrentUser, session: SessionDep) -> ClientProfile:
    return _get_or_create(session, user.id)


@router.put("/me/profile", response_model=ClientProfileOut)
def upsert_my_profile(
    body: ClientProfileUpsert, user: CurrentUser, session: SessionDep
) -> ClientProfile:
    profile = _get_or_create(session, user.id)
    for field, value in body.model_dump().items():
        setattr(profile, field, value)
    profile.updated_at = datetime.now(UTC)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/{user_id}/profile", response_model=ClientProfileOut)
def get_client_profile(
    user_id: int, _: CurrentUser, session: SessionDep
) -> ClientProfile:
    """Barber/agent view of a client's profile (e.g. before a flex cut)."""
    profile = session.exec(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    ).first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No profile for that client")
    return profile

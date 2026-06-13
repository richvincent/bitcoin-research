"""Premium concierge (Ruby) requests — client raises, staff fulfills."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models import ConciergeRequest, ConciergeStatus, User, UserRole
from app.schemas.schemas import ConciergeCallRequest, ConciergeRequestOut
from app.services import concierge

router = APIRouter(prefix="/concierge", tags=["concierge"])

_STAFF = (UserRole.OWNER, UserRole.BARBER)


def _to_out(session: SessionDep, req: ConciergeRequest) -> ConciergeRequestOut:
    client = session.get(User, req.client_id)
    return ConciergeRequestOut(
        **req.model_dump(),
        client_name=(client.full_name or client.email) if client else "",
    )


@router.post("/call", response_model=ConciergeRequestOut, status_code=status.HTTP_201_CREATED)
def request_call(
    body: ConciergeCallRequest, user: CurrentUser, session: SessionDep
) -> ConciergeRequestOut:
    """Queue a premium live-voice callback (top tiers)."""
    req = ConciergeRequest(
        client_id=user.id,
        shop_id=body.shop_id,
        phone=body.phone,
        topic=body.topic,
    )
    session.add(req)
    session.commit()
    session.refresh(req)

    concierge.notify_desk(req)  # fire-and-forget; never blocks the request
    return _to_out(session, req)


@router.get("/requests", response_model=list[ConciergeRequestOut])
def list_requests(
    user: CurrentUser, session: SessionDep, shop_id: int | None = None
) -> list[ConciergeRequestOut]:
    """Clients see their own requests; staff/admin see the desk queue."""
    stmt = select(ConciergeRequest)
    if user.role == UserRole.CLIENT:
        stmt = stmt.where(ConciergeRequest.client_id == user.id)
    elif shop_id is not None:
        stmt = stmt.where(ConciergeRequest.shop_id == shop_id)
    rows = session.exec(stmt.order_by(ConciergeRequest.created_at.desc())).all()
    return [_to_out(session, r) for r in rows]


@router.post("/requests/{request_id}/status", response_model=ConciergeRequestOut)
def update_status(
    request_id: int,
    new_status: ConciergeStatus,
    session: SessionDep,
    _: User = Depends(require_roles(*_STAFF)),
) -> ConciergeRequestOut:
    """Concierge desk advances a request (in_progress / completed / cancelled)."""
    req = session.get(ConciergeRequest, request_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    req.status = new_status
    session.add(req)
    session.commit()
    session.refresh(req)
    return _to_out(session, req)

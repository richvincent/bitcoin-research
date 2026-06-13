"""Service catalog (haircuts, beard trims, etc.)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import SessionDep, require_roles
from app.models import Service, Shop, User, UserRole
from app.schemas.schemas import ServiceCreate, ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    body: ServiceCreate,
    session: SessionDep,
    _: User = Depends(require_roles(UserRole.OWNER, UserRole.ADMIN)),
) -> Service:
    if session.get(Shop, body.shop_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shop not found")
    service = Service(**body.model_dump())
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@router.get("", response_model=list[ServiceOut])
def list_services(session: SessionDep, shop_id: int | None = None) -> list[Service]:
    stmt = select(Service).where(Service.is_active == True)  # noqa: E712
    if shop_id is not None:
        stmt = stmt.where(Service.shop_id == shop_id)
    return list(session.exec(stmt).all())

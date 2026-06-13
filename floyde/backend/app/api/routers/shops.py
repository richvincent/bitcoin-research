"""Shops and barbers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models import Barber, Shop, User, UserRole
from app.schemas.schemas import BarberCreate, BarberOut, ShopCreate, ShopOut

router = APIRouter(prefix="/shops", tags=["shops"])


@router.post("", response_model=ShopOut, status_code=status.HTTP_201_CREATED)
def create_shop(
    body: ShopCreate,
    session: SessionDep,
    user: User = Depends(require_roles(UserRole.OWNER, UserRole.ADMIN)),
) -> Shop:
    if session.exec(select(Shop).where(Shop.slug == body.slug)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Shop slug already in use")
    shop = Shop(owner_id=user.id, **body.model_dump())
    session.add(shop)
    session.commit()
    session.refresh(shop)
    return shop


@router.get("", response_model=list[ShopOut])
def list_shops(session: SessionDep) -> list[Shop]:
    return list(session.exec(select(Shop)).all())


@router.get("/{shop_id}", response_model=ShopOut)
def get_shop(shop_id: int, session: SessionDep) -> Shop:
    shop = session.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shop not found")
    return shop


@router.post("/barbers", response_model=BarberOut, status_code=status.HTTP_201_CREATED)
def add_barber(
    body: BarberCreate,
    session: SessionDep,
    _: User = Depends(require_roles(UserRole.OWNER, UserRole.ADMIN)),
) -> Barber:
    if session.get(Shop, body.shop_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shop not found")
    barber = Barber(**body.model_dump())
    session.add(barber)
    session.commit()
    session.refresh(barber)
    return barber


@router.get("/{shop_id}/barbers", response_model=list[BarberOut])
def list_barbers(shop_id: int, session: SessionDep) -> list[Barber]:
    return list(
        session.exec(
            select(Barber).where(
                Barber.shop_id == shop_id, Barber.is_active == True  # noqa: E712
            )
        ).all()
    )

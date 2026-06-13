"""Inventory + Amazon product intelligence."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models import Product, Shop, User, UserRole
from app.schemas.schemas import AmazonRec, ProductCreate, ProductOut
from app.services import amazon

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def add_product(
    body: ProductCreate,
    session: SessionDep,
    _: User = Depends(require_roles(UserRole.OWNER, UserRole.BARBER)),
) -> Product:
    if session.get(Shop, body.shop_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shop not found")
    product = Product(**body.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("/products", response_model=list[ProductOut])
def list_products(
    _: CurrentUser, session: SessionDep, shop_id: int | None = None
) -> list[Product]:
    stmt = select(Product)
    if shop_id is not None:
        stmt = stmt.where(Product.shop_id == shop_id)
    return list(session.exec(stmt).all())


@router.get("/low-stock", response_model=list[ProductOut])
def low_stock(_: CurrentUser, session: SessionDep, shop_id: int) -> list[Product]:
    products = session.exec(select(Product).where(Product.shop_id == shop_id)).all()
    return [p for p in products if p.quantity <= p.reorder_threshold]


@router.get("/recommendations", response_model=list[AmazonRec])
def recommendations(_: CurrentUser, q: str, limit: int = 5) -> list[AmazonRec]:
    """Amazon product recommendations for a search query."""
    return amazon.get_recommendations(q, limit=limit)


@router.get("/reorder-suggestions", response_model=list[AmazonRec])
def reorder_suggestions(
    _: CurrentUser, session: SessionDep, shop_id: int
) -> list[AmazonRec]:
    """Amazon restock suggestions for everything below its reorder threshold."""
    products = session.exec(select(Product).where(Product.shop_id == shop_id)).all()
    low = [p.name for p in products if p.quantity <= p.reorder_threshold]
    return amazon.reorder_suggestions(low)

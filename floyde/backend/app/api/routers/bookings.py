"""Scheduling & booking: availability, create, confirm, cancel, walk-ins."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Booking,
    BookingStatus,
    PaymentType,
    Service,
    UserRole,
)
from app.schemas.schemas import BookingCreate, BookingOut
from app.services import payments, scheduling

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/availability", response_model=list[datetime])
def availability(
    barber_id: int,
    service_id: int,
    session: SessionDep,
    _: CurrentUser,
    count: int = 8,
) -> list[datetime]:
    """Return up to `count` upcoming open start times for a barber+service."""
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service not found")
    slots: list[datetime] = []
    after: datetime | None = None
    for _i in range(count):
        nxt = scheduling.next_available(
            session, barber_id, service.duration_minutes, after=after
        )
        if nxt is None:
            break
        slots.append(nxt)
        # advance past this slot to find the following one
        after = nxt + timedelta(minutes=service.duration_minutes)
    return slots


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    body: BookingCreate, user: CurrentUser, session: SessionDep
) -> BookingOut:
    try:
        booking = scheduling.create_booking(
            session,
            client_id=user.id,
            barber_id=body.barber_id,
            service_id=body.service_id,
            start_time=body.start_time,
            source=body.source,
            notes=body.notes,
        )
    except scheduling.SchedulingError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    # Create the deposit intent (stub-mode auto-succeeds + confirms).
    if booking.deposit_cents > 0:
        payment, _secret = payments.create_payment(
            session,
            shop_id=booking.shop_id,
            amount_cents=booking.deposit_cents,
            booking_id=booking.id,
            payment_type=PaymentType.DEPOSIT,
        )
        if payment.status.value == "succeeded":
            booking.status = BookingStatus.CONFIRMED
            session.add(booking)
            session.commit()
            session.refresh(booking)

    return BookingOut.model_validate(booking)


@router.get("", response_model=list[BookingOut])
def list_bookings(user: CurrentUser, session: SessionDep) -> list[Booking]:
    """Clients see their own bookings; barbers/owners see their shop's."""
    if user.role == UserRole.CLIENT:
        stmt = select(Booking).where(Booking.client_id == user.id)
    else:
        stmt = select(Booking)
    return list(session.exec(stmt.order_by(Booking.start_time)).all())


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, user: CurrentUser, session: SessionDep) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if user.role == UserRole.CLIENT and booking.client_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your booking")
    return booking


@router.post("/{booking_id}/confirm", response_model=BookingOut)
def confirm_booking(booking_id: int, _: CurrentUser, session: SessionDep) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    booking.status = BookingStatus.CONFIRMED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, user: CurrentUser, session: SessionDep) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if user.role == UserRole.CLIENT and booking.client_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your booking")
    booking.status = BookingStatus.CANCELLED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking

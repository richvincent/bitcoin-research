"""Scheduling & booking: availability, create, confirm, cancel, walk-ins."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models import (
    Barber,
    Booking,
    BookingStatus,
    PaymentType,
    Service,
    User,
    UserRole,
)
from app.schemas.schemas import (
    BookingCreate,
    BookingOut,
    ManagedBooking,
    StaffBookingCreate,
)
from app.services import payments, scheduling

_STAFF = (UserRole.OWNER, UserRole.BARBER)

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


# NOTE: literal paths must be declared before the dynamic /{booking_id} route.
@router.get("/manage", response_model=list[ManagedBooking])
def manage_schedule(
    session: SessionDep,
    shop_id: int | None = None,
    _: User = Depends(require_roles(*_STAFF)),
) -> list[ManagedBooking]:
    """Enriched schedule for staff: booking rows with names resolved."""
    stmt = select(Booking)
    if shop_id is not None:
        stmt = stmt.where(Booking.shop_id == shop_id)
    rows: list[ManagedBooking] = []
    for b in session.exec(stmt.order_by(Booking.start_time)).all():
        client = session.get(User, b.client_id)
        barber = session.get(Barber, b.barber_id)
        service = session.get(Service, b.service_id)
        rows.append(
            ManagedBooking(
                id=b.id,
                start_time=b.start_time,
                end_time=b.end_time,
                status=b.status,
                source=b.source,
                deposit_cents=b.deposit_cents,
                price_cents=service.price_cents if service else 0,
                match_score=b.match_score,
                notes=b.notes,
                client_name=(client.full_name or client.email) if client else "—",
                client_email=client.email if client else "",
                barber_id=b.barber_id,
                barber_name=barber.display_name if barber else "—",
                service_name=service.name if service else "—",
            )
        )
    return rows


@router.post(
    "/staff", response_model=BookingOut, status_code=status.HTTP_201_CREATED
)
def staff_booking(
    body: StaffBookingCreate,
    session: SessionDep,
    _: User = Depends(require_roles(*_STAFF)),
) -> BookingOut:
    """Book on behalf of an existing client (walk-ins, phone bookings)."""
    client = session.exec(select(User).where(User.email == body.client_email)).first()
    if client is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"No client account for {body.client_email}. Ask them to sign up first.",
        )
    try:
        booking = scheduling.create_booking(
            session,
            client_id=client.id,
            barber_id=body.barber_id,
            service_id=body.service_id,
            start_time=body.start_time,
            source=body.source,
            notes=body.notes,
        )
    except scheduling.SchedulingError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return BookingOut.model_validate(booking)


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


@router.post("/{booking_id}/complete", response_model=BookingOut)
def complete_booking(
    booking_id: int,
    session: SessionDep,
    _: User = Depends(require_roles(*_STAFF)),
) -> Booking:
    """Mark a booking completed (after the chair). Staff only."""
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    booking.status = BookingStatus.COMPLETED
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

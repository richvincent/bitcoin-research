"""Availability + booking creation logic.

Shared by the REST API and the MCP server so humans and agents create
bookings through identical rules (no double-booking, deposit calc, etc.).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models import (
    Barber,
    Booking,
    BookingSource,
    BookingStatus,
    Service,
)

# Simple uniform business hours for the MVP. A real shop-hours model
# (per-barber, per-weekday, breaks, time off) is a Phase 2 item.
OPEN_HOUR = 9
CLOSE_HOUR = 19

# Fraction of service price taken as a deposit for online/flex bookings.
DEPOSIT_RATE = 0.20

_ACTIVE = (BookingStatus.PENDING, BookingStatus.CONFIRMED)


class SchedulingError(ValueError):
    """Raised for invalid scheduling requests (conflicts, bad input)."""


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _overlaps(session: Session, barber_id: int, start: datetime, end: datetime) -> bool:
    rows = session.exec(
        select(Booking).where(
            Booking.barber_id == barber_id,
            Booking.status.in_(_ACTIVE),  # type: ignore[attr-defined]
        )
    ).all()
    for b in rows:
        if _aware(b.start_time) < end and start < _aware(b.end_time):
            return True
    return False


def is_slot_available(
    session: Session, barber_id: int, start: datetime, duration_minutes: int
) -> bool:
    start = _aware(start)
    end = start + timedelta(minutes=duration_minutes)
    if not (OPEN_HOUR <= start.hour < CLOSE_HOUR):
        return False
    return not _overlaps(session, barber_id, start, end)


def next_available(
    session: Session,
    barber_id: int,
    duration_minutes: int,
    *,
    after: datetime | None = None,
    horizon_days: int = 7,
    step_minutes: int = 15,
) -> datetime | None:
    """Return the next bookable start time for a barber, or None."""
    cursor = _aware(after or datetime.now(UTC))
    # round up to the next step boundary
    minute = (cursor.minute // step_minutes + 1) * step_minutes
    cursor = cursor.replace(second=0, microsecond=0, minute=0) + timedelta(
        minutes=minute
    )
    limit = cursor + timedelta(days=horizon_days)
    while cursor < limit:
        if cursor.hour < OPEN_HOUR:
            cursor = cursor.replace(hour=OPEN_HOUR, minute=0)
        if cursor.hour >= CLOSE_HOUR:
            cursor = (cursor + timedelta(days=1)).replace(hour=OPEN_HOUR, minute=0)
            continue
        if is_slot_available(session, barber_id, cursor, duration_minutes):
            return cursor
        cursor += timedelta(minutes=step_minutes)
    return None


def create_booking(
    session: Session,
    *,
    client_id: int,
    barber_id: int,
    service_id: int,
    start_time: datetime,
    source: BookingSource = BookingSource.ONLINE,
    notes: str = "",
    match_score: float | None = None,
) -> Booking:
    barber = session.get(Barber, barber_id)
    if barber is None or not barber.is_active:
        raise SchedulingError("Barber not found or inactive")
    service = session.get(Service, service_id)
    if service is None or service.shop_id != barber.shop_id:
        raise SchedulingError("Service not found for this barber's shop")

    start = _aware(start_time)
    end = start + timedelta(minutes=service.duration_minutes)

    # Walk-ins skip the business-hours/conflict gate (added at the chair).
    if source is not BookingSource.WALK_IN:
        if not (OPEN_HOUR <= start.hour < CLOSE_HOUR):
            raise SchedulingError("Requested time is outside business hours")
        if _overlaps(session, barber_id, start, end):
            raise SchedulingError("That time slot is no longer available")

    deposit = (
        int(service.price_cents * DEPOSIT_RATE)
        if source in (BookingSource.ONLINE, BookingSource.FLEX)
        else 0
    )

    booking = Booking(
        client_id=client_id,
        barber_id=barber_id,
        shop_id=barber.shop_id,
        service_id=service_id,
        start_time=start,
        end_time=end,
        status=BookingStatus.PENDING,
        source=source,
        deposit_cents=deposit,
        notes=notes,
        match_score=match_score,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking

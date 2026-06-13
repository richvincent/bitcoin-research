"""Analytics: roll up a shop's bookings, POS revenue, and supply spend.

Pure read-only aggregation over existing tables — no new state. Times stored
by the app are UTC-aware; SQLite can hand them back naive, so we normalize.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models import (
    Barber,
    Booking,
    BookingStatus,
    MarketplaceOrder,
    OrderStatus,
    Payment,
    PaymentStatus,
)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def shop_summary(session: Session, shop_id: int, days: int = 30) -> dict:
    now = datetime.now(UTC)
    since = now - timedelta(days=days)

    # ── Payments / revenue ──
    payments = session.exec(
        select(Payment).where(Payment.shop_id == shop_id)
    ).all()
    revenue_by_type: dict[str, int] = defaultdict(int)
    revenue_by_day: dict[str, int] = defaultdict(int)
    revenue_cents = 0
    payments_count = 0
    for p in payments:
        if p.status is not PaymentStatus.SUCCEEDED:
            continue
        created = _aware(p.created_at)
        if created < since:
            continue
        revenue_cents += p.amount_cents
        payments_count += 1
        revenue_by_type[p.type.value] += p.amount_cents
        revenue_by_day[created.date().isoformat()] += p.amount_cents

    # Continuous day series (fill gaps with zero) for charting.
    series = []
    for i in range(days):
        day = (since + timedelta(days=i + 1)).date().isoformat()
        series.append({"date": day, "cents": revenue_by_day.get(day, 0)})

    # ── Bookings ──
    bookings = session.exec(
        select(Booking).where(Booking.shop_id == shop_id)
    ).all()
    in_range = [b for b in bookings if _aware(b.start_time) >= since]
    counts: dict[str, int] = defaultdict(int)
    for b in in_range:
        counts[b.status.value] += 1
    upcoming = sum(
        1
        for b in bookings
        if b.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)
        and _aware(b.start_time) >= now
    )

    # ── Barber leaderboard (completed bookings in range) ──
    completed_by_barber: dict[int, int] = defaultdict(int)
    for b in in_range:
        if b.status is BookingStatus.COMPLETED:
            completed_by_barber[b.barber_id] += 1
    leaderboard = []
    for barber_id, n in completed_by_barber.items():
        barber = session.get(Barber, barber_id)
        leaderboard.append(
            {
                "barber_id": barber_id,
                "name": barber.display_name if barber else "—",
                "completed": n,
            }
        )
    leaderboard.sort(key=lambda r: r["completed"], reverse=True)

    # ── Marketplace supply spend (orders bought for this shop) ──
    orders = session.exec(
        select(MarketplaceOrder).where(MarketplaceOrder.buyer_shop_id == shop_id)
    ).all()
    supply_spend = sum(
        o.subtotal_cents
        for o in orders
        if o.status != OrderStatus.CANCELLED and _aware(o.created_at) >= since
    )

    completed = counts.get(BookingStatus.COMPLETED.value, 0)
    cancelled = counts.get(BookingStatus.CANCELLED.value, 0)
    no_show = counts.get(BookingStatus.NO_SHOW.value, 0)
    finished = completed + no_show
    no_show_rate = round(no_show / finished, 3) if finished else 0.0

    return {
        "shop_id": shop_id,
        "range_days": days,
        "revenue_cents": revenue_cents,
        "payments_count": payments_count,
        "revenue_by_type": dict(revenue_by_type),
        "revenue_by_day": series,
        "bookings_total": len(in_range),
        "bookings_completed": completed,
        "bookings_cancelled": cancelled,
        "bookings_no_show": no_show,
        "bookings_upcoming": upcoming,
        "no_show_rate": no_show_rate,
        "barber_leaderboard": leaderboard,
        "supply_spend_cents": supply_spend,
        "net_cents": revenue_cents - supply_spend,
    }

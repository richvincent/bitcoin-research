"""Smart matching — the "Flex Cut" brain.

Scores barbers for a client by combining:
  • style fit  — overlap between the client's preferred styles and the
                 barber's specialties / requested service tags
  • proximity  — haversine distance if coordinates are available
  • rating     — barber's rolling rating
  • availability — how soon the barber can take the client

Pure, dependency-light, and explainable (every match carries `reasons`),
so both the API and MCP agents can show *why* a barber was suggested.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Barber, ClientProfile, Service, Shop, User
from app.schemas.schemas import BarberMatch, BarberOut, ShopOut
from app.services import scheduling

# Weights for the composite score (must sum to 1.0).
W_STYLE = 0.40
W_DISTANCE = 0.25
W_RATING = 0.15
W_AVAILABILITY = 0.20

_EARTH_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2) -> float | None:
    if None in (lat1, lon1, lat2, lon2):
        return None
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return _EARTH_KM * 2 * math.asin(math.sqrt(a))


def _style_fit(client_styles: list[str], barber_specialties: list[str],
               service_tags: list[str]) -> tuple[float, list[str]]:
    if not client_styles:
        return 0.5, []  # neutral when we know nothing about the client yet
    wanted = {s.lower() for s in client_styles}
    have = {s.lower() for s in barber_specialties} | {t.lower() for t in service_tags}
    if not have:
        return 0.4, []
    matched = wanted & have
    score = len(matched) / len(wanted)
    reasons = [f"matches your preferred style '{m}'" for m in sorted(matched)]
    return score, reasons


def _distance_score(km: float | None) -> tuple[float, list[str]]:
    if km is None:
        return 0.5, []
    # 0 km -> 1.0, decaying to ~0 by 25 km
    score = max(0.0, 1.0 - km / 25.0)
    reasons = [f"{km:.1f} km away"] if km <= 25 else []
    return score, reasons


def _availability_score(minutes_until: float | None) -> tuple[float, list[str]]:
    if minutes_until is None:
        return 0.0, ["no availability in the next week"]
    if minutes_until <= 30:
        return 1.0, ["available right now"]
    # decay over a 48-hour window
    score = max(0.1, 1.0 - minutes_until / (48 * 60))
    hrs = minutes_until / 60
    label = f"next opening in ~{hrs:.0f}h" if hrs >= 1 else "opening within the hour"
    return score, [label]


def find_matches(
    session: Session,
    *,
    client_user_id: int | None,
    service_id: int | None = None,
    client_lat: float | None = None,
    client_lng: float | None = None,
    shop_id: int | None = None,
    limit: int = 10,
) -> list[BarberMatch]:
    profile: ClientProfile | None = None
    if client_user_id is not None:
        profile = session.exec(
            select(ClientProfile).where(ClientProfile.user_id == client_user_id)
        ).first()
    client_styles = profile.preferred_styles if profile else []

    service = session.get(Service, service_id) if service_id else None
    service_tags = service.tags if service else []
    duration = service.duration_minutes if service else 30

    stmt = select(Barber).where(Barber.is_active == True)  # noqa: E712
    if shop_id is not None:
        stmt = stmt.where(Barber.shop_id == shop_id)
    if service is not None:
        stmt = stmt.where(Barber.shop_id == service.shop_id)
    barbers = session.exec(stmt).all()

    now = datetime.now(UTC)
    results: list[BarberMatch] = []
    for barber in barbers:
        shop = session.get(Shop, barber.shop_id)
        if shop is None:
            continue

        style_s, style_r = _style_fit(client_styles, barber.specialties, service_tags)

        km = haversine_km(client_lat, client_lng, shop.latitude, shop.longitude)
        dist_s, dist_r = _distance_score(km)

        rating_s = min(barber.rating / 5.0, 1.0)

        nxt = scheduling.next_available(session, barber.id, duration, after=now)
        mins = (nxt - now).total_seconds() / 60 if nxt else None
        avail_s, avail_r = _availability_score(mins)

        score = (
            W_STYLE * style_s
            + W_DISTANCE * dist_s
            + W_RATING * rating_s
            + W_AVAILABILITY * avail_s
        )
        reasons = style_r + dist_r + avail_r
        if barber.rating >= 4.8:
            reasons.append(f"top-rated ({barber.rating:.1f}★)")

        results.append(
            BarberMatch(
                barber=BarberOut.model_validate(barber),
                shop=ShopOut.model_validate(shop),
                score=round(score, 4),
                distance_km=round(km, 2) if km is not None else None,
                next_available=nxt,
                reasons=reasons,
            )
        )

    results.sort(key=lambda m: m.score, reverse=True)
    return results[:limit]

"""Floyde MCP server — exposes the platform to AI agents.

Runs over stdio so it can be wired into Claude Desktop, OpenClaw, or any
MCP-capable agent. Every tool calls the same ``app.services`` layer the REST
API uses, so agents and humans share identical business logic.

Run:  python -m mcp_server.server

These tools act on behalf of a client identified by email. In production,
agent auth/scoping should be enforced (A2A identity) before exposing booking
or payment mutations; for the MVP we keep it simple and explicit.
"""

from __future__ import annotations

from datetime import datetime

from mcp.server.fastmcp import FastMCP
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models import ClientProfile, Service, User, UserRole
from app.services import amazon, concierge, matching, scheduling

mcp = FastMCP("floyde")


def _resolve_client(session: Session, client_email: str) -> User:
    user = session.exec(select(User).where(User.email == client_email)).first()
    if user is None:
        raise ValueError(f"No user with email {client_email!r}")
    return user


@mcp.tool()
def list_services(shop_id: int | None = None) -> list[dict]:
    """List bookable services (haircuts, beard trims). Optionally filter by shop."""
    with Session(engine) as session:
        stmt = select(Service).where(Service.is_active == True)  # noqa: E712
        if shop_id is not None:
            stmt = stmt.where(Service.shop_id == shop_id)
        return [
            {
                "id": s.id, "shop_id": s.shop_id, "name": s.name,
                "duration_minutes": s.duration_minutes,
                "price_usd": round(s.price_cents / 100, 2), "tags": s.tags,
            }
            for s in session.exec(stmt).all()
        ]


@mcp.tool()
def get_client_profile(client_email: str) -> dict:
    """Fetch a client's persistent style profile (preferred styles, nuances,
    products) — the context a barber or agent needs before a cut."""
    with Session(engine) as session:
        user = _resolve_client(session, client_email)
        profile = session.exec(
            select(ClientProfile).where(ClientProfile.user_id == user.id)
        ).first()
        if profile is None:
            return {"client_email": client_email, "profile": None}
        return {
            "client_email": client_email,
            "full_name": user.full_name,
            "preferred_styles": profile.preferred_styles,
            "style_notes": profile.style_notes,
            "nuances": profile.nuances,
            "preferred_products": profile.preferred_products,
            "loyalty_points": profile.loyalty_points,
        }


@mcp.tool()
def find_available_barbers(
    client_email: str,
    service_id: int | None = None,
    lat: float | None = None,
    lng: float | None = None,
    shop_id: int | None = None,
    limit: int = 5,
) -> list[dict]:
    """Rank barbers for a client by style fit, proximity, rating, and how soon
    they're available. Powers the 'Flex Cut Now' experience."""
    with Session(engine) as session:
        user = _resolve_client(session, client_email)
        matches = matching.find_matches(
            session,
            client_user_id=user.id,
            service_id=service_id,
            client_lat=lat,
            client_lng=lng,
            shop_id=shop_id,
            limit=limit,
        )
        return [
            {
                "barber_id": m.barber.id,
                "barber": m.barber.display_name,
                "shop": m.shop.name,
                "score": m.score,
                "distance_km": m.distance_km,
                "next_available": (
                    m.next_available.isoformat() if m.next_available else None
                ),
                "reasons": m.reasons,
            }
            for m in matches
        ]


@mcp.tool()
def book_with_profile(
    client_email: str,
    barber_id: int,
    service_id: int,
    start_time: str,
    notes: str = "",
) -> dict:
    """Book an appointment for a client. `start_time` is ISO-8601
    (e.g. '2026-06-15T14:30:00'). Uses the client's saved profile context."""
    with Session(engine) as session:
        user = _resolve_client(session, client_email)
        try:
            start = datetime.fromisoformat(start_time)
        except ValueError as exc:
            raise ValueError(f"start_time must be ISO-8601: {exc}") from exc
        try:
            booking = scheduling.create_booking(
                session,
                client_id=user.id,
                barber_id=barber_id,
                service_id=service_id,
                start_time=start,
                source="flex",  # type: ignore[arg-type]
                notes=notes,
            )
        except scheduling.SchedulingError as exc:
            return {"ok": False, "error": str(exc)}
        return {
            "ok": True,
            "booking_id": booking.id,
            "status": booking.status,
            "start_time": booking.start_time.isoformat(),
            "deposit_usd": round(booking.deposit_cents / 100, 2),
        }


@mcp.tool()
def get_amazon_recs(query: str, limit: int = 5) -> list[dict]:
    """Get ranked Amazon product recommendations for barbershop supplies or
    retail (clippers, pomades, sanitation, etc.)."""
    return [r.model_dump() for r in amazon.get_recommendations(query, limit=limit)]


@mcp.tool()
def initiate_concierge_call(client_email: str, phone: str, topic: str) -> dict:
    """Queue a premium live-voice concierge (Ruby) callback for a client."""
    with Session(engine) as session:
        user = _resolve_client(session, client_email)
        return concierge.initiate_call(
            client_user_id=user.id, phone=phone, topic=topic
        )


def main() -> None:
    init_db()
    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()

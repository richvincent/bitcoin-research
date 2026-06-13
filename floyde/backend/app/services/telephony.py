"""Telephony (Twilio) — outbound voice for the concierge desk.

Places a click-to-call that dials the client and bridges them to the human
concierge desk. Follows Floyde's stub-first rule: with no Twilio credentials
it returns a simulated call SID (no network), so the flow is fully demoable.
"""

from __future__ import annotations

import logging
import uuid
from xml.sax.saxutils import escape

import httpx

from app.config import settings

log = logging.getLogger("floyde.telephony")


def _build_twiml(connect_to: str | None) -> str:
    """TwiML the client hears: a brief greeting, then a bridge to the desk."""
    greeting = "Connecting you to your Floyde concierge. One moment."
    parts = [f"<Say>{escape(greeting)}</Say>"]
    if connect_to:
        parts.append(f"<Dial>{escape(connect_to)}</Dial>")
    return f"<Response>{''.join(parts)}</Response>"


def place_call(to: str, connect_to: str | None = None) -> dict:
    """Dial `to` and (optionally) bridge to `connect_to`.

    Returns {sid, status, stub}. Never raises on a provider/network error —
    callers treat a failed dial as a soft failure and keep the request queued.
    """
    if not to:
        raise ValueError("A destination phone number is required")

    if not settings.twilio_enabled:
        sid = f"CA_stub_{uuid.uuid4().hex[:24]}"
        log.info("Telephony stub: pretend-dialing %s (sid %s)", to, sid)
        return {"sid": sid, "status": "queued", "stub": True}

    desk = connect_to or settings.concierge_desk_number
    try:
        resp = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Calls.json",
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            data={
                "To": to,
                "From": settings.twilio_from_number,
                "Twiml": _build_twiml(desk),
            },
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        return {
            "sid": body.get("sid", ""),
            "status": body.get("status", "queued"),
            "stub": False,
        }
    except httpx.HTTPError as exc:
        log.warning("Twilio call to %s failed: %s", to, exc)
        return {"sid": "", "status": "failed", "stub": False}

"""Premium concierge (Ruby) — live human voice for top tiers.

For the MVP this records a concierge request and (optionally) pings a
webhook that a human concierge desk subscribes to. AI voice for lower tiers
is a later phase.
"""

from __future__ import annotations

import logging
import uuid

import httpx

from app.config import settings

log = logging.getLogger("floyde.concierge")


def initiate_call(*, client_user_id: int, phone: str, topic: str) -> dict:
    """Queue a concierge callback. Returns a request descriptor."""
    request_id = f"ccg_{uuid.uuid4().hex[:16]}"
    payload = {
        "request_id": request_id,
        "client_user_id": client_user_id,
        "phone": phone,
        "topic": topic,
        "status": "queued",
    }
    if settings.concierge_webhook_url:
        try:
            httpx.post(settings.concierge_webhook_url, json=payload, timeout=5)
        except httpx.HTTPError as exc:
            log.warning("Concierge webhook failed (%s); request still queued", exc)
    else:
        log.info("Concierge request %s queued (stub mode): %s", request_id, topic)
    return payload

"""Premium concierge (Ruby) — live human voice for top tiers.

Requests are persisted (see ConciergeRequest); this module handles the
outbound notification to the human concierge desk. When no webhook is
configured it logs, so the flow works end to end without external setup.
AI voice for lower tiers is a later phase.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.models import ConciergeRequest

log = logging.getLogger("floyde.concierge")


def notify_desk(request: ConciergeRequest) -> bool:
    """Ping the concierge desk webhook for a queued request.

    Returns True if delivered (or stubbed/logged), False on webhook failure.
    Never raises — a desk outage must not break the client's request.
    """
    payload = {
        "request_id": request.request_id,
        "client_id": request.client_id,
        "phone": request.phone,
        "topic": request.topic,
        "status": request.status,
    }
    if not settings.concierge_webhook_url:
        log.info("Concierge %s queued (stub mode): %s", request.request_id, request.topic)
        return True
    try:
        httpx.post(settings.concierge_webhook_url, json=payload, timeout=5)
        return True
    except httpx.HTTPError as exc:
        log.warning("Concierge webhook failed for %s: %s", request.request_id, exc)
        return False

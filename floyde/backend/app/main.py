"""Floyde API entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routers import (
    auth,
    bookings,
    clients,
    concierge,
    inventory,
    marketplace,
    matching,
    pos,
    reports,
    services,
    shops,
)
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Floyde API",
    version=__version__,
    summary="Agent-native barbershop super tool",
    lifespan=lifespan,
)

# Permissive CORS in dev so the PWA / tools can call from anywhere.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth, shops, services, clients, matching, bookings, pos, inventory,
    concierge, marketplace, reports,
):
    app.include_router(r.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "env": settings.env,
        "integrations": {
            "stripe": "live" if settings.stripe_enabled else "stub",
            "amazon": "live" if settings.amazon_enabled else "catalog",
            "bookkeeping": settings.bookkeeping_provider,
            "telephony": "live" if settings.twilio_enabled else "stub",
        },
    }

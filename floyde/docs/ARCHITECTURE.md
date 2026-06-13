# Floyde Architecture

This document describes the Phase 1 MVP backend and how it maps to the
product blueprint.

## Principles

1. **Agent-native / headless-first.** Every capability is a service function
   exposed twice: as a REST endpoint and as an MCP tool. Humans and AI agents
   share identical business logic.
2. **Self-host first.** Zero-config dev (SQLite + stubbed integrations);
   one `docker compose up` for the Postgres stack.
3. **Privacy-first.** No third-party calls are required to run. Stripe,
   Amazon, and bookkeeping all degrade to safe local/stub behavior when not
   configured.
4. **Explainable matching.** Every barber match carries human-readable
   `reasons`, so the UI and concierge can justify a recommendation.

## Layers

```
            ┌──────────────────────────────────────────────┐
 Agents ───▶│  MCP server (mcp_server/server.py)            │
            │     find_available_barbers, book_with_profile │
            └──────────────────┬───────────────────────────┘
                               │  (same calls)
 Humans ───▶  REST API (app/api/routers/*)                  │
                               │
                               ▼
                 Service layer (app/services/*)
        matching · scheduling · payments · amazon ·
        bookkeeping · concierge
                               │
                               ▼
                 Data (app/models, SQLModel → Postgres/SQLite)
```

### Service layer (`app/services`)

| Module | Responsibility | External dep | Stub/fallback |
|---|---|---|---|
| `scheduling` | availability, conflict-free booking, deposits | — | — |
| `matching` | style-fit + distance + rating + availability scoring | — | neutral score when no profile |
| `payments` | Stripe PaymentIntents | Stripe | fake intents auto-succeed |
| `bookkeeping` | sync sales to Frappe/Akaunting | HTTP | local idempotency marker |
| `amazon` | product recommendations | PA-API | curated offline catalog |
| `concierge` | premium Ruby live-voice callbacks | webhook | logs request |

### Data model

`User` (role: client/barber/owner/admin) · `Shop` · `Barber` · `Service` ·
`ClientProfile` (persistent style profile) · `Booking` · `Payment` ·
`Product`. Money is integer cents. Style/photo/nuance lists are JSON columns.

## Matching algorithm

Composite score in `app/services/matching.py`:

```
score = 0.40 * style_fit      # client.preferred_styles ∩ (barber.specialties ∪ service.tags)
      + 0.25 * proximity      # haversine, decays to ~0 by 25 km
      + 0.15 * rating         # barber.rating / 5
      + 0.20 * availability    # sooner is better; "now" = 1.0
```

Weights are constants today; Phase 3 can learn them per-market.

## Booking & payment flow

1. `POST /bookings` → `scheduling.create_booking` (validates hours, prevents
   overlap, computes a 20% deposit for online/flex).
2. If a deposit is due → `payments.create_payment` makes a Stripe intent
   (or a stub that auto-succeeds), which triggers `bookkeeping.record_payment`.
3. On success the booking flips to `confirmed`. Real Stripe confirmations
   arrive via `POST /pos/webhook/stripe`.

## What's deliberately deferred

- **Migrations:** MVP uses `SQLModel.metadata.create_all`. Add Alembic before
  the first production schema change.
- **Shop hours model:** uniform 9–19 today; per-barber/weekday/breaks next.
- **Frontend:** Next.js PWA (chosen) — not in this build.
- **Marketplace transactions, OpenClaw/A2A orchestration, AI voice, one-click
  installer:** Phase 2/3 per the blueprint.
- **AuthN for MCP tools:** they trust `client_email`; add A2A identity before
  remote exposure.

## Repo layout

```
floyde/
  backend/
    app/
      api/routers/   REST endpoints
      core/          security (JWT, hashing)
      models/        SQLModel tables + enums
      schemas/       Pydantic request/response contracts
      services/      business logic (shared by API + MCP)
      config.py  database.py  main.py  seed.py
    mcp_server/      MCP server (imports app.services)
    tests/           pytest suite
    Dockerfile  requirements.txt
  docs/ARCHITECTURE.md
  docker-compose.yml  .env.example
```

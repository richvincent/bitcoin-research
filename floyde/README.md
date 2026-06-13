# Floyde

> An agent-native, self-hostable super tool for barbershops.
> Named in homage to Floyd the barber of Mayberry.

Floyde combines operations, on-demand premium booking, intelligent product
sourcing, marketing, open-source bookkeeping, and a multi-sided marketplace
into one minimal, privacy-first platform. It is **headless-first**: every
capability is exposed as a clean REST API *and* as MCP tools so AI agents can
operate the platform alongside humans.

This repository currently contains the **Phase 1 MVP backend core**.

## What's in this build

| Capability | Status | Module |
|---|---|---|
| Auth & roles (JWT) | ✅ | `app/api/routers/auth.py`, `app/core/security.py` |
| Shops & barbers | ✅ | `app/api/routers/shops.py` |
| Services catalog | ✅ | `app/api/routers/services.py` |
| Scheduling & booking (online, walk-in, flex) | ✅ | `app/api/routers/bookings.py` |
| Smart matching (style-fit score) | ✅ | `app/services/matching.py` |
| Client CRM + style profiles | ✅ | `app/api/routers/clients.py` |
| POS & payments (Stripe, stubbable) | ✅ | `app/api/routers/pos.py`, `app/services/payments.py` |
| Inventory + Amazon product recs | ✅ | `app/api/routers/inventory.py`, `app/services/amazon.py` |
| Bookkeeping sync (Frappe/Akaunting adapter) | ✅ (adapter stub) | `app/services/bookkeeping.py` |
| MCP server (agent tools) | ✅ | `mcp_server/server.py` |

Not yet built (later phases): Next.js PWA frontend, marketplace transactions,
Ruby concierge live-voice integration, OpenClaw/A2A orchestration, one-click
self-host installer.

## Quick start (local, SQLite)

```bash
cd floyde/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env          # tweak as needed
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

A demo seed (one shop, two barbers, services, a client with a style profile)
is available:

```bash
python -m app.seed
```

## Quick start (Docker, Postgres)

```bash
cd floyde
cp .env.example .env
docker compose up --build
```

API → http://localhost:8000 · MCP server → stdio (see below).

## Running the MCP server

The MCP server exposes Floyde to AI agents (Claude Desktop, OpenClaw, etc.):

```bash
cd floyde/backend
python -m mcp_server.server          # stdio transport
```

Tools exposed: `find_available_barbers`, `book_with_profile`,
`get_client_profile`, `list_services`, `get_amazon_recs`,
`initiate_concierge_call`.

See [`mcp_server/README.md`](mcp_server/README.md) for client config.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The short version:

```
Agents / Humans
      │
  REST API  ──────────  MCP server  (same service layer)
      │                      │
      └──────── app/services ┘   (matching, payments, amazon, bookkeeping)
                  │
            SQLModel / Postgres
```

The API routers and the MCP tools both call the same `app/services` layer, so
agents and humans always go through identical business logic.

## Tests

```bash
cd floyde/backend
pytest
```

## License

TBD (self-host friendly — likely AGPL or Apache-2.0).

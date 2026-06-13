# Floyde — working notes for Claude

Agent-native, self-hostable barbershop super tool. Named after Floyd the
barber (Mayberry). This is the **Phase 1 MVP backend**.

## Stack
- **Backend:** Python 3.12, FastAPI, SQLModel (SQLAlchemy + Pydantic v2).
- **DB:** SQLite by default (zero-config dev), Postgres via docker-compose.
- **MCP:** `mcp` (FastMCP) server in `backend/mcp_server/`.
- **Frontend (future):** Next.js (React) — not built yet.

## Golden rule
Business logic lives in `app/services/*`. REST routers (`app/api/routers/*`)
and MCP tools (`mcp_server/server.py`) are thin adapters that BOTH call the
service layer. When adding a capability, write the service function first,
then expose it through both surfaces.

## Conventions
- Money is **integer cents**. Never floats for money.
- Times are timezone-aware UTC; `scheduling._aware()` normalizes naive input.
- External integrations must degrade to a stub when unconfigured (see how
  `payments`, `amazon`, `bookkeeping` check `settings.*_enabled`). Keep the
  app fully runnable with zero credentials.
- Settings come from `app/config.py` (env prefix `FLOYDE_`). Add new config
  there with a dev-safe default.
- New tables: define in `app/models/tables.py`, export in `app/models/__init__.py`.
  No Alembic yet — `create_all` on startup. Add Alembic before prod schema changes.

## Commands
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload     # API at :8000/docs
python -m app.seed                # demo data (logins: password123)
python -m mcp_server.server       # MCP stdio server
pytest                            # tests
```

## Run from repo root via Docker
```bash
cd floyde && docker compose up --build
```

## Where things are
- Auth/JWT: `app/core/security.py`, `app/api/deps.py`
- Matching brain: `app/services/matching.py`
- Booking rules: `app/services/scheduling.py`
- Payments (Stripe + stub): `app/services/payments.py`
- Architecture detail: `docs/ARCHITECTURE.md`

## Not yet built (don't assume these exist)
Frontend, marketplace transactions, marketing automation, OpenClaw/A2A
orchestration, AI voice, Alembic migrations, per-barber shop hours.

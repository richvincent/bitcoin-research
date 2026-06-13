# Floyde MCP server

> The implementation lives at `floyde/backend/mcp_server/server.py` (it needs
> the backend `app` package on its path). This folder is a pointer + docs.

Floyde is headless-first: everything humans can do via the REST API, agents
can do via these MCP tools — both go through the same `app.services` layer.

## Tools

| Tool | Purpose |
|---|---|
| `list_services` | List bookable services, optionally by shop |
| `get_client_profile` | Fetch a client's persistent style profile |
| `find_available_barbers` | Rank barbers by style fit, distance, rating, availability |
| `book_with_profile` | Create a booking on behalf of a client |
| `get_amazon_recs` | Ranked Amazon product recommendations |
| `initiate_concierge_call` | Queue a premium Ruby live-voice callback |

## Run

```bash
cd floyde/backend
pip install -r requirements.txt
python -m mcp_server.server     # stdio
```

## Claude Desktop config

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "floyde": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/floyde/backend"
    }
  }
}
```

## Example agent flow

1. `get_client_profile(client_email="client@floyde.app")` → learns preferred
   styles + nuances.
2. `find_available_barbers(client_email=..., service_id=1, lat=42.33, lng=-83.04)`
   → ranked matches with reasons.
3. `book_with_profile(client_email=..., barber_id=1, service_id=1,
   start_time="2026-06-15T14:30:00")` → confirmed booking + deposit.

## Notes / TODO

- Auth: these tools currently trust the `client_email` argument. Before
  exposing externally, enforce A2A identity / scoped tokens so an agent can
  only act for its authenticated principal.
- Transport: stdio today; add HTTP/SSE transport for remote agents in Phase 2.

# AGENTS

This file guides automated agents working on this repository.

## Project Summary

- Python MCP server that exposes Serper Google Search APIs as MCP tools.
- Uses stdio MCP transport and aiohttp to call Serper endpoints.

## Key Files

- `README.md` usage and setup instructions.
- `src/serper_mcp_server/server.py` tool registry and request dispatch.
- `src/serper_mcp_server/core.py` HTTP client and endpoint routing.
- `src/serper_mcp_server/schemas.py` Pydantic request models and schemas.
- `src/serper_mcp_server/enums.py` tool names and enums.
- `src/serper_mcp_server/__init__.py` entrypoint wiring.
- `pyproject.toml` dependencies and packaging metadata.

## Configuration

- `SERPER_API_KEY` (required): API key for Serper.
- `AIOHTTP_TIMEOUT` (optional): total request timeout in seconds, default `15`.
- `.env` is loaded via `python-dotenv` in `server.py`.

## Run Locally

- `python -m serper_mcp_server`
- `serper-mcp-server`
- `uvx serper-mcp-server` (if installed via uvx)

## Adding or Modifying Tools

1. Add enum entry in `src/serper_mcp_server/enums.py`.
2. Add or update request schema in `src/serper_mcp_server/schemas.py`.
3. Wire schema in `google_request_map` in `src/serper_mcp_server/server.py`.
4. If the endpoint path does not match the tool suffix, adjust `core.google()`
   or add a new call function in `src/serper_mcp_server/core.py`.

## Testing

- No automated tests are configured in this repository.

# Architecture

## Summary

This service runs as a single Cloud Run app that exposes:
- REST API via Connexion (`/v1/...`)
- MCP tools via FastMCP (`/mcp`)

API Gateway sits in front for authentication and rate limiting. The app is stateless and stores
state in Firestore (metadata) and GCS (artifacts).

Runtime flow:

`Client -> API Gateway -> Cloud Run -> Connexion/MCP -> Services -> Repositories -> GCP`

## Code layout

```
src/api/
  app.py                  # ASGI app; mounts REST + MCP
  specification.yaml      # OpenAPI contract
  controllers/            # REST handlers
  mcp_tools/              # MCP tool definitions
  services/               # Business logic
  repositories/           # Firestore/GCS adapters + in-memory adapters
  interfaces/             # Port interfaces
  models/dtos/            # Pydantic DTOs
  middleware/             # Error handling
  shared/                 # Utilities
```

## Request paths

### REST API
- `GET /v1/generators`
- `POST /v1/generators`
- `GET /v1/generators/{generatorId}`
- `DELETE /v1/generators/{generatorId}`

### MCP
- `POST /mcp` (JSON-RPC)

## Data flow

1. Connexion or FastMCP validates input.
2. `GeneratorService` executes business logic.
3. Repositories hit Firestore/GCS (or in-memory adapters in dev/tests).
4. Responses are serialized and sensitive fields are pruned.

## Local mode

Use in-memory adapters to avoid GCP during local dev/tests:

```
USE_IN_MEMORY_ADAPTERS=true
```

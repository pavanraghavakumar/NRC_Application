# NRC backend API

The backend is a Python 3.13 / FastAPI service implementing the `/api/v1` contract in the authoritative root documentation. It is deliberately schema-driven: business tables and analytic views are supplied by the database workstream, while the API owns request validation, authentication context, authorization, optimistic concurrency, workflow commands, RFC 9457 errors, correlation IDs, rate limiting, and audit writes.

## Run

```cmd
set NRC_DATABASE_PATH=data\nrc_spa.db
set NRC_DEV_AUTH=true
python -m uvicorn nrc_api.main:app --host 127.0.0.1 --port 8000
```

Production must set `NRC_DEV_AUTH=false` and configure a trusted ICAM/Entra identity proxy using `NRC_TRUSTED_PROXY_SECRET`. The proxy supplies verified `X-NRC-User-*` and `X-NRC-Roles` headers. The API rejects direct untrusted identity headers. `NRC_OIDC_ISSUER`, `NRC_OIDC_CLIENT_ID`, and `NRC_OIDC_REDIRECT_URI` populate the authorization redirect; token exchange remains at the deployment identity proxy so unverified JWTs never reach application code.

## Database contract

The API expects SQLite 3.45+, the documented singular prefixed table names, canonical UUID text keys, UTC timestamp text, and integer `row_version`. Every connection enables foreign keys, WAL, a five-second busy timeout, and in-memory temporary storage. Writes use `BEGIN IMMEDIATE`. Business SQL is confined to `nrc_api.repository.Repository`.

After the database branch is composed, its package is authoritative: create or upgrade a database with `python -m database.migrate <db-path>`, verify it with `python -m database.verify <db-path>`, and delegate the narrow connection adapter in `nrc_api.db` to `database.Database`. Identifier creation must use `database.draw_identifier`, and `database.ConcurrencyConflict` must map to the API's `409 CONCURRENCY_CONFLICT` problem response. The API contains no parallel migration mechanism.

## Development identity

Only when `NRC_DEV_AUTH=true`, requests may send `X-Dev-User-Id`, `X-Dev-Name`, `X-Dev-Email`, and comma-separated `X-Dev-Roles`. Defaults represent an EDO user. Startup fails if development authentication is enabled outside the `development` environment.

## Decisions used for documented gaps

The clarification round received no answer, so implementation uses the specification's recommended defaults: configurable approval queues with one-stage chains supported; restricted CBJ/APPR and Agencywide creation for both Performance Indicators and Enterprise Risks; owners may delete their own Draft records; federal fiscal years begin October 1; notification delivery uses an outbox with in-app, e-mail, and Teams adapters. Provider credentials and environment topology are deployment configuration and are never committed.

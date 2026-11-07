from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import Body, FastAPI, Header, Request, Response
from fastapi.responses import RedirectResponse

from .auth import Principal, principal_from_request
from .catalog import RELATIONSHIPS, RESOURCES, WORKFLOW_TYPES
from .config import Settings
from .db import Database
from .errors import ApiError, api_error_handler
from .repository import Repository, utc_now


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    db = Database(settings.database_path)
    repo = Repository(db)
    app = FastAPI(title="NRC Strategic Planning and Performance Management API", version="1.0.0", openapi_version="3.1.0")
    app.state.settings, app.state.db, app.state.repo = settings, db, repo
    app.add_exception_handler(ApiError, api_error_handler)
    buckets: dict[str, deque[float]] = defaultdict(deque)

    @app.on_event("startup")
    def startup() -> None:
        db.check_version()
        if settings.environment != "development" and settings.dev_auth_enabled:
            raise RuntimeError("Development authentication must be disabled outside development.")

    @app.middleware("http")
    async def request_controls(request: Request, call_next):
        correlation = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        try: uuid.UUID(correlation)
        except ValueError: correlation = str(uuid.uuid4())
        request.state.correlation_id = correlation
        key = request.client.host if request.client else "unknown"
        now, bucket = time.monotonic(), buckets[key]
        while bucket and bucket[0] <= now - 60: bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            response = await api_error_handler(request, ApiError(429, "RATE_LIMITED", "The request rate limit was exceeded."))
            response.headers["Retry-After"] = "60"
            response.headers["X-Correlation-Id"] = correlation
            return response
        bucket.append(now)
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def principal(request: Request) -> Principal:
        return principal_from_request(request, settings)

    @app.get("/api/v1/auth/login")
    def login() -> Response:
        if not settings.oidc_issuer or not settings.oidc_client_id or not settings.oidc_redirect_uri:
            raise ApiError(503, "OIDC_NOT_CONFIGURED", "ICAM/Entra OIDC is not configured.")
        query = urlencode({"client_id": settings.oidc_client_id, "response_type": "code", "redirect_uri": settings.oidc_redirect_uri, "scope": "openid profile email", "state": str(uuid.uuid4()), "nonce": str(uuid.uuid4())})
        return RedirectResponse(f"{settings.oidc_issuer.rstrip('/')}/authorize?{query}")

    @app.get("/api/v1/auth/callback")
    def callback() -> None:
        raise ApiError(501, "OIDC_PROXY_REQUIRED", "The deployment identity proxy must exchange and verify the authorization code.")

    @app.post("/api/v1/auth/refresh")
    def refresh(request: Request) -> dict[str, Any]:
        p = principal(request)
        return {"user_id": p.id, "refreshed": True}

    @app.post("/api/v1/auth/logout", status_code=204)
    def logout() -> None: return None

    @app.get("/api/v1/me")
    def me(request: Request) -> dict[str, Any]:
        p = principal(request)
        return {"id": p.id, "domain_name": p.email, "full_name": p.full_name, "internal_email_address": p.email, "title": None, "business_unit": None, "manager": None, "teams": [], "roles": [{"name": x} for x in sorted(p.roles)], "is_edo_user": p.is_edo, "is_submitter": p.is_submitter, "is_view_only": p.roles == {"SPA View Only User"}}

    @app.get("/api/v1/me/roles")
    def my_roles(request: Request): return [{"name": x} for x in sorted(principal(request).roles)]

    @app.get("/api/v1/me/teams")
    def my_teams(request: Request): return [{"id": x} for x in principal(request).team_ids]

    @app.get("/api/v1/me/permissions")
    def permissions(request: Request):
        p = principal(request)
        depth = "organization" if p.is_edo else "user" if p.is_submitter else "none"
        return {r.entity: {op: ("organization" if op == "read" else depth) for op in ("create", "read", "write", "delete", "append", "append_to", "assign", "share")} for r in RESOURCES.values()}

    @app.get("/api/v1/admin/health")
    def health(): return {"status": "ok", "time": utc_now()}

    @app.get("/api/v1/admin/ready")
    def ready():
        with db.read() as conn: conn.execute("SELECT 1").fetchone()
        return {"status": "ready"}

    @app.get("/api/v1/metadata/entities")
    def metadata_entities(request: Request):
        principal(request)
        return [{"name": r.entity, "resource": r.slug, "table": r.table, "primary_field": r.title_field, "label": r.entity.replace("_", " ").title()} for r in RESOURCES.values()]

    @app.get("/api/v1/metadata/entities/{entity}")
    def metadata_entity(entity: str, request: Request):
        principal(request)
        resource = next((r for r in RESOURCES.values() if r.entity == entity or r.slug == entity), None)
        if not resource: raise ApiError(404, "NOT_FOUND", "Unknown metadata entity.")
        with db.read() as conn:
            if not db.table_exists(conn, resource.table): return {"name": resource.entity, "attributes": []}
            attrs = [{"name": row["name"], "type": row["type"], "required": bool(row["notnull"]), "primary_key": bool(row["pk"])} for row in conn.execute(f'PRAGMA table_info("{resource.table}")')]
        return {"name": resource.entity, "label": resource.entity.replace("_", " ").title(), "primary_field": resource.title_field, "attributes": attrs}

    @app.get("/api/v1/metadata/{kind:path}")
    def metadata_generic(kind: str, request: Request):
        principal(request)
        return {"kind": kind, "items": []}

    @app.post("/api/v1/workflow/{command}")
    def bulk_workflow(command: str, request: Request, payload: dict[str, Any] = Body(...), idempotency_key: str | None = Header(None, alias="Idempotency-Key")):
        p = principal(request)
        if not idempotency_key: raise ApiError(400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required for bulk commands.")
        ids = payload.get("ids", [])
        if not isinstance(ids, list) or not ids or len(ids) > 500: raise ApiError(400, "VALIDATION_FAILED", "ids must contain between 1 and 500 record ids.")
        slug = WORKFLOW_TYPES.get(payload.get("record_type", ""))
        if not slug: raise ApiError(400, "VALIDATION_FAILED", "Unknown workflow record_type.")
        results = []
        for record_id in ids:
            try:
                item = _transition(slug, record_id, command, p, request.state.correlation_id, payload.get("comments"))
                results.append({"id": record_id, "code": item.get(RESOURCES[slug].title_field), "status": "ok", "new_status_reason": item.get("status_reason")})
            except ApiError as exc:
                results.append({"id": record_id, "status": "error", "error": {"code": exc.code, "message": exc.detail}})
        failed = sum(x["status"] == "error" for x in results)
        body = {"requested": len(ids), "succeeded": len(ids) - failed, "failed": failed, "results": results, "correlation_id": request.state.correlation_id}
        if failed: raise ApiError(422, "BULK_PARTIAL_FAILURE", json.dumps(body))
        return body

    def _transition(slug: str, record_id: str, command: str, p: Principal, correlation_id: str, comments: str | None = None):
        resource = RESOURCES[slug]
        item = repo.get(resource, record_id, p)
        current = item.get("status_reason")
        target = {"submit": "pending_approval", "approve": "finalized", "return": "revision", "propose-discontinue": current, "discontinue": "discontinued", "deny-discontinue": "finalized"}.get(command)
        if target is None: raise ApiError(404, "NOT_FOUND", "Unknown workflow command.")
        if command == "submit" and current not in {"draft", "revision"}: raise ApiError(409, "INVALID_STATE", "Only Draft or Revision records may be submitted.")
        if command in {"approve", "return"} and current != "pending_approval": raise ApiError(409, "INVALID_STATE", "Only Pending approval records may be approved or returned.")
        if command in {"discontinue", "deny-discontinue"} and not p.is_edo: raise ApiError(403, "FORBIDDEN", "EDO User role is required.")
        update: dict[str, Any] = {"status_reason": target}
        if "state" in item: update["state"] = "inactive" if target in {"finalized", "discontinued"} else "active"
        if comments is not None and "comments" in item: update["comments"] = comments
        if command == "propose-discontinue":
            key = "indicator_status" if slug == "performance-indicators" else "risk_status"
            update[key] = "pending_discontinue"
        if command == "discontinue":
            key = "indicator_status" if slug == "performance-indicators" else "risk_status"
            update[key] = "discontinued"
        return repo.update(resource, record_id, update, p, str(item.get("row_version")) if "row_version" in item else None, correlation_id)

    @app.post("/api/v1/{resource}/{record_id}/{command}")
    def record_command(resource: str, record_id: str, command: str, request: Request, payload: dict[str, Any] | None = Body(None)):
        if resource not in RESOURCES or command not in {"submit", "approve", "return", "activate", "deactivate", "assign"}: raise ApiError(404, "NOT_FOUND", "Unknown command endpoint.")
        p = principal(request)
        if command in {"submit", "approve", "return"}: return _transition(resource, record_id, command, p, request.state.correlation_id, (payload or {}).get("comments"))
        item = repo.get(RESOURCES[resource], record_id, p)
        update = {"state": "active" if command == "activate" else "inactive"} if command != "assign" else (payload or {})
        return repo.update(RESOURCES[resource], record_id, update, p, str(item.get("row_version")) if "row_version" in item else None, request.state.correlation_id)

    @app.get("/api/v1/analytics/{page:path}")
    def analytics(page: str, request: Request):
        principal(request)
        view = "analytics_" + page.replace("/", "_").replace("-", "_")
        with db.read() as conn:
            if not db.table_exists(conn, view): raise ApiError(503, "ANALYTICS_NOT_READY", f"Analytics view {view} is not installed.")
            return {"items": [dict(x) for x in conn.execute(f'SELECT * FROM "{view}" LIMIT 1000')]}

    @app.get("/api/v1/{resource}")
    def list_resource(resource: str, request: Request):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        return repo.list(RESOURCES[resource], principal(request), dict(request.query_params))

    @app.post("/api/v1/{resource}", status_code=201)
    def create_resource(resource: str, request: Request, payload: dict[str, Any] = Body(...)):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        return repo.create(RESOURCES[resource], payload, principal(request), request.state.correlation_id)

    @app.get("/api/v1/{resource}/{record_id}")
    def get_resource(resource: str, record_id: str, request: Request):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        return repo.get(RESOURCES[resource], record_id, principal(request))

    @app.patch("/api/v1/{resource}/{record_id}")
    def patch_resource(resource: str, record_id: str, request: Request, payload: dict[str, Any] = Body(...), if_match: str | None = Header(None, alias="If-Match")):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        return repo.update(RESOURCES[resource], record_id, payload, principal(request), if_match, request.state.correlation_id)

    @app.delete("/api/v1/{resource}/{record_id}", status_code=204)
    def delete_resource(resource: str, record_id: str, request: Request):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        repo.delete(RESOURCES[resource], record_id, principal(request), request.state.correlation_id)

    return app


app = create_app()


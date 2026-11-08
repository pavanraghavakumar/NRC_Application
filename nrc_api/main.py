from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import Body, FastAPI, Header, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse

from database import migrate

from .auth import Principal, principal_from_request
from .catalog import RELATIONSHIPS, RESOURCES, WORKFLOW_TYPES
from .config import Settings
from .db import Database
from .errors import ApiError, api_error_handler
from .repository import Repository, utc_now
from .services import JOBS, OPTION_SETS, RelationshipService, RuntimeStore, csv_response, parse_csv, require_edo, safe_attachment_path


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    db = Database(settings.database_path)
    repo = Repository(db)
    relationships, runtime = RelationshipService(db), RuntimeStore()
    app = FastAPI(title="NRC Strategic Planning and Performance Management API", version="1.0.0", openapi_version="3.1.0")
    app.state.settings, app.state.db, app.state.repo = settings, db, repo
    app.add_exception_handler(ApiError, api_error_handler)
    buckets: dict[str, deque[float]] = defaultdict(deque)

    @app.on_event("startup")
    def startup() -> None:
        db.check_version()
        if settings.auto_migrate:
            migrate(settings.database_path)
        if settings.dev_auth_enabled:
            dev_user_id = "00000000-0000-4000-8000-000000000001"
            dev_bu_id = "00000000-0000-4000-8000-000000000002"
            with db.write() as connection:
                if db.table_exists(connection, "core_business_unit") and db.table_exists(connection, "core_app_user"):
                    connection.execute(
                        "INSERT OR IGNORE INTO core_business_unit(id,name,is_root) VALUES(?,?,1)",
                        (dev_bu_id, "Development"),
                    )
                    connection.execute(
                        "INSERT OR IGNORE INTO core_app_user(id,domain_name,full_name,internal_email_address,business_unit_id) VALUES(?,?,?,?,?)",
                        (dev_user_id, "dev@nrc.gov", "Development User", "dev@nrc.gov", dev_bu_id),
                    )
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

    # Declared before generic resource routes so attachment filenames are not
    # interpreted as relationship names by Starlette's ordered router.
    @app.get("/api/v1/attachments/{attachment_id}/{filename}")
    def download_attachment_early(attachment_id: str, filename: str, request: Request):
        principal(request); path = safe_attachment_path(settings.attachment_directory, attachment_id, filename)
        if not path.is_file(): raise ApiError(404, "NOT_FOUND", "Attachment not found.")
        return FileResponse(path, filename=filename)

    @app.delete("/api/v1/attachments/{attachment_id}/{filename}", status_code=204)
    def delete_attachment(attachment_id: str, filename: str, request: Request):
        principal(request); path = safe_attachment_path(settings.attachment_directory, attachment_id, filename)
        if not path.is_file(): raise ApiError(404, "NOT_FOUND", "Attachment not found.")
        path.unlink(); path.parent.rmdir()

    # These fixed/specialized routes must precede the generic
    # /{resource}/{id}/{relationship} route.
    @app.get("/api/v1/analytics/{page}/export")
    def export_analytics_early(page: str, request: Request, format: str = "csv"):
        principal(request)
        if format != "csv": raise ApiError(400, "UNSUPPORTED_FORMAT", "Only CSV analytics export is available from the API tier.")
        view = "analytics_" + page.replace("-", "_")
        with db.read() as conn:
            if not db.table_exists(conn, view): raise ApiError(503, "ANALYTICS_NOT_READY", f"Analytics view {view} is not installed.")
            fieldnames = [column[1] for column in conn.execute(f'PRAGMA table_info("{view}")')]
            rows = [dict(x) for x in conn.execute(f'SELECT * FROM "{view}" LIMIT 10000')]
        return PlainTextResponse(csv_response(rows, fieldnames), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{page}.csv"'})

    @app.get("/api/v1/analytics/query/suggestions")
    def query_suggestions_early(request: Request):
        principal(request)
        return {"items": ["How many enterprise risks are active?", "Show performance indicator trends by quarter.", "Which accomplishments support Goal 1?"]}

    @app.post("/api/v1/analytics/query")
    def analytics_query_early(request: Request, payload: dict[str, Any] = Body(...)):
        principal(request); question = str(payload.get("question", "")).strip()
        if not question or len(question) > 500: raise ApiError(400, "VALIDATION_FAILED", "question must contain 1 to 500 characters.")
        return {"question": question, "answer": "Natural-language analytics requires the configured analytics provider.", "data": [], "visual": {"type": "table", "columns": []}, "provider_status": "not_configured"}

    @app.get("/api/v1/performance-indicators/{record_id}/prefill")
    def pi_prefill_early(record_id: str, request: Request, previous_pi_id: str):
        p = principal(request); repo.get(RESOURCES["performance-indicators"], record_id, p)
        source = repo.get(RESOURCES["performance-indicators"], previous_pi_id, p)
        excluded = {"id", "indicator_code", "status_reason", "state", "row_version", "created_on", "created_by_id", "modified_on", "modified_by_id"}
        return {k: v for k, v in source.items() if k not in excluded}

    @app.get("/api/v1/performance-indicators/{record_id}/revision-chain")
    def revision_chain_early(record_id: str, request: Request):
        return {"items": [repo.get(RESOURCES["performance-indicators"], record_id, principal(request))]}

    @app.get("/api/v1/metadata/entities")
    def metadata_entities(request: Request):
        principal(request)
        return [{"name": r.entity, "resource": r.slug, "table": r.table, "primary_field": r.title_field, "label": r.entity.replace("_", " ").title(), "plural_label": r.slug.replace("-", " ").title()} for r in RESOURCES.values()]

    @app.get("/api/v1/metadata/entities/{entity}")
    def metadata_entity(entity: str, request: Request):
        principal(request)
        resource = next((r for r in RESOURCES.values() if r.entity == entity or r.slug == entity), None)
        if not resource: raise ApiError(404, "NOT_FOUND", "Unknown metadata entity.")
        with db.read() as conn:
            if not db.table_exists(conn, resource.table): return {"name": resource.entity, "attributes": []}
            attrs = [{"name": row["name"], "type": row["type"], "required": bool(row["notnull"]), "primary_key": bool(row["pk"])} for row in conn.execute(f'PRAGMA table_info("{resource.table}")')]
        return {"name": resource.entity, "label": resource.entity.replace("_", " ").title(), "primary_field": resource.title_field, "attributes": attrs}

    @app.get("/api/v1/metadata/entities/{entity}/views")
    def metadata_views(entity: str, request: Request):
        principal(request)
        if entity not in RESOURCES and entity not in {r.entity for r in RESOURCES.values()}: raise ApiError(404, "NOT_FOUND", "Unknown metadata entity.")
        return {"items": [{"name": "active", "label": "Active", "filter": {"state": "active"}, "sort": ["modified_on:desc"]}, {"name": "my-records", "label": "My Records", "filter": {"owner": "me"}, "sort": ["modified_on:desc"]}]}

    @app.get("/api/v1/metadata/entities/{entity}/views/{view}")
    def metadata_view(entity: str, view: str, request: Request):
        views = metadata_views(entity, request)["items"]
        result = next((x for x in views if x["name"] == view), None)
        if not result: raise ApiError(404, "NOT_FOUND", "Unknown view.")
        return result

    @app.get("/api/v1/metadata/entities/{entity}/forms")
    def metadata_forms(entity: str, request: Request):
        detail = metadata_entity(entity, request)
        return {"items": [{"name": "main", "label": detail["label"], "tabs": [{"label": "General", "sections": [{"label": "General", "controls": [{"attribute": x["name"]} for x in detail["attributes"] if x["name"] not in {"id", "row_version"}]}]}]}]}

    @app.get("/api/v1/metadata/option-sets")
    def option_sets(request: Request): principal(request); return {"items": [{"name": k, "options": [{"value": x, "label": x.replace("_", " ").title()} for x in v]} for k, v in OPTION_SETS.items()]}

    @app.get("/api/v1/metadata/option-sets/{name}")
    def option_set(name: str, request: Request):
        principal(request)
        if name not in OPTION_SETS: raise ApiError(404, "NOT_FOUND", "Unknown option set.")
        return {"name": name, "options": [{"value": x, "label": x.replace("_", " ").title()} for x in OPTION_SETS[name]]}

    @app.get("/api/v1/metadata/navigation")
    def navigation(request: Request):
        p = principal(request)
        groups = [{"label": "Strategic Planning", "items": [{"resource": x, "label": RESOURCES[x].entity.replace("_", " ").title()} for x in ("goals", "objectives", "strategies")]}, {"label": "Performance Management", "items": [{"resource": x, "label": RESOURCES[x].entity.replace("_", " ").title()} for x in ("performance-indicators", "enterprise-risks", "accomplishments", "priorities")]}, {"label": "Evidence Building", "items": [{"resource": x, "label": RESOURCES[x].entity.replace("_", " ").title()} for x in ("priority-questions", "evaluations", "research-activities")]}]
        if p.is_edo: groups.append({"label": "Administration", "items": [{"resource": x, "label": RESOURCES[x].entity.replace("_", " ").title()} for x in ("users", "teams", "settings", "view-definitions", "form-definitions")]})
        return {"groups": groups}

    @app.get("/api/v1/metadata/business-rules/{entity}")
    def business_rules(entity: str, request: Request):
        principal(request)
        return {"entity": entity, "rules": [{"when": {"status_reason": {"not_in": ["draft", "revision"]}}, "effects": [{"type": "lock", "target": "*"}]}, {"when": {"report_level": "cbj_appr"}, "effects": [{"type": "require_role", "role": "EDO User"}]}]}

    @app.get("/api/v1/metadata/commands/{entity}")
    def commands(entity: str, request: Request):
        p = principal(request); resource = RESOURCES.get(entity)
        if not resource: raise ApiError(404, "NOT_FOUND", "Unknown entity.")
        values = ["create", "export"] + (["submit", "assign"] if resource.workflow and p.is_submitter else []) + (["approve", "return", "deactivate"] if resource.workflow and p.is_edo else [])
        return {"items": [{"name": x, "label": x.replace("-", " ").title(), "confirmation": x in {"approve", "return", "deactivate"}} for x in values]}

    @app.get("/api/v1/metadata/{kind:path}")
    def metadata_generic(kind: str, request: Request):
        principal(request)
        return {"kind": kind, "items": []}

    @app.post("/api/v1/workflow/{command}")
    def bulk_workflow(command: str, request: Request, payload: dict[str, Any] = Body(...), idempotency_key: str | None = Header(None, alias="Idempotency-Key")):
        p = principal(request)
        if not idempotency_key: raise ApiError(400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required for bulk commands.")
        replay = runtime.replay(idempotency_key, payload)
        if replay is not None: return replay
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
        runtime.remember(idempotency_key, payload, body)
        return body

    @app.get("/api/v1/{resource}/{record_id}/audit")
    def record_audit(resource: str, record_id: str, request: Request):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        return {"items": repo.audit(RESOURCES[resource], record_id, principal(request))}

    @app.get("/api/v1/{resource}/{record_id}/timeline")
    def timeline(resource: str, record_id: str, request: Request):
        items = repo.audit(RESOURCES[resource], record_id, principal(request))
        return {"items": [{"type": "field_change", "timestamp": x.get("changed_on"), "data": x} for x in items]}

    @app.get("/api/v1/{resource}/{record_id}/workflow")
    def workflow_detail(resource: str, record_id: str, request: Request):
        p = principal(request); item = repo.get(RESOURCES[resource], record_id, p); current = item.get("status_reason")
        available = {"draft": ["submit"], "revision": ["submit"], "pending_approval": ["approve", "return"]}.get(current, [])
        return {"status": current, "available_transitions": available if p.is_submitter else [], "chain": []}

    @app.get("/api/v1/{resource}/{record_id}/{relationship}")
    def relationship_list(resource: str, record_id: str, relationship: str, request: Request):
        if resource not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Unknown resource.")
        repo.get(RESOURCES[resource], record_id, principal(request))
        return relationships.list(RESOURCES[resource], record_id, relationship)

    @app.post("/api/v1/{resource}/{record_id}/{relationship}")
    def relationship_add(resource: str, record_id: str, relationship: str, request: Request, payload: dict[str, Any] = Body(...)):
        if relationship in {"submit", "approve", "return", "activate", "deactivate", "assign"}: return record_command(resource, record_id, relationship, request, payload)
        p = principal(request); repo.get(RESOURCES[resource], record_id, p)
        if not p.is_submitter: raise ApiError(403, "FORBIDDEN", "Write privilege is required.")
        return relationships.add(RESOURCES[resource], record_id, relationship, payload.get("ids", []))

    @app.delete("/api/v1/{resource}/{record_id}/{relationship}/{related_id}", status_code=204)
    def relationship_remove(resource: str, record_id: str, relationship: str, related_id: str, request: Request):
        p = principal(request); repo.get(RESOURCES[resource], record_id, p)
        if not p.is_submitter: raise ApiError(403, "FORBIDDEN", "Write privilege is required.")
        relationships.remove(RESOURCES[resource], record_id, relationship, related_id)

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

    @app.get("/api/v1/analytics/refresh-status")
    def refresh_status(request: Request): principal(request); return {"mode": "live", "last_refresh": utc_now(), "next_refresh": None}

    @app.get("/api/v1/analytics/query/suggestions")
    def query_suggestions(request: Request):
        principal(request); return {"items": ["How many enterprise risks are active?", "Show performance indicator trends by quarter.", "Which accomplishments support Goal 1?"]}

    @app.post("/api/v1/analytics/query")
    def analytics_query(request: Request, payload: dict[str, Any] = Body(...)):
        principal(request); question = str(payload.get("question", "")).strip()
        if not question or len(question) > 500: raise ApiError(400, "VALIDATION_FAILED", "question must contain 1 to 500 characters.")
        return {"question": question, "answer": "Natural-language analytics requires the configured analytics provider.", "data": [], "visual": {"type": "table", "columns": []}, "provider_status": "not_configured"}

    @app.get("/api/v1/analytics/{page:path}/export")
    def export_analytics(page: str, request: Request, format: str = "csv"):
        principal(request)
        if format != "csv": raise ApiError(400, "UNSUPPORTED_FORMAT", "Only CSV analytics export is available from the API tier.")
        view = "analytics_" + page.replace("/", "_").replace("-", "_")
        with db.read() as conn:
            if not db.table_exists(conn, view): raise ApiError(503, "ANALYTICS_NOT_READY", f"Analytics view {view} is not installed.")
            rows = [dict(x) for x in conn.execute(f'SELECT * FROM "{view}" LIMIT 10000')]
        return PlainTextResponse(csv_response(rows), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{page.replace("/", "-")}.csv"'})

    @app.get("/api/v1/analytics/{page:path}")
    def analytics(page: str, request: Request):
        principal(request)
        view = "analytics_" + page.replace("/", "_").replace("-", "_")
        with db.read() as conn:
            if db.table_exists(conn, view):
                items = [dict(x) for x in conn.execute(f'SELECT * FROM "{view}" LIMIT 1000')]
            else:
                # Dashboard routes remain useful against a newly migrated, empty
                # database. Counts are computed from the operational tables and
                # are never substituted with mocked browser data.
                items = []
            counts = {}
            for label, table in (
                ("performance_indicators", "perf_performance_indicator"),
                ("enterprise_risks", "perf_enterprise_risk"),
                ("priorities", "perf_priority"),
                ("accomplishments", "perf_accomplishment"),
                ("positive_change_management", "perf_positive_change_management"),
            ):
                if db.table_exists(conn, table):
                    counts[label] = conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            return {"page": page, "generated_at": utc_now(), "filters": dict(request.query_params), "items": items, "summary": {"total": len(items), **counts}, "visuals": [], **counts}

    @app.get("/api/v1/{resource}/export")
    def export_resource(resource: str, request: Request, format: str = "csv"):
        if format != "csv": raise ApiError(400, "UNSUPPORTED_FORMAT", "Only CSV export is available from the API tier.")
        result = repo.list(RESOURCES[resource], principal(request), {**dict(request.query_params), "page_size": 200})
        return PlainTextResponse(csv_response(result["items"]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{resource}.csv"'})

    @app.post("/api/v1/import/validate")
    async def validate_import(request: Request, entity: str):
        require_edo(principal(request)); content = await request.body()
        if len(content) > 32 * 1024 * 1024: raise ApiError(413, "IMPORT_TOO_LARGE", "Import files may not exceed 32 MB.")
        rows = parse_csv(content); resource = RESOURCES.get(entity)
        if not resource: raise ApiError(400, "VALIDATION_FAILED", "Unknown import entity.")
        with db.read() as conn: columns = set(db.columns(conn, resource.table))
        errors = [{"row": index + 2, "fields": sorted(set(row) - columns)} for index, row in enumerate(rows) if set(row) - columns]
        return {"valid": not errors, "row_count": len(rows), "errors": errors}

    @app.post("/api/v1/import/jobs", status_code=201)
    async def execute_import(request: Request, entity: str):
        p = principal(request); require_edo(p); content = await request.body()
        if len(content) > 32 * 1024 * 1024: raise ApiError(413, "IMPORT_TOO_LARGE", "Import files may not exceed 32 MB.")
        rows, resource = parse_csv(content), RESOURCES.get(entity)
        if not resource: raise ApiError(400, "VALIDATION_FAILED", "Unknown import entity.")
        imported, errors = 0, []
        for index, row in enumerate(rows, 2):
            try: repo.create(resource, {k: v for k, v in row.items() if v != ""}, p, request.state.correlation_id); imported += 1
            except ApiError as exc: errors.append({"row": index, "code": exc.code, "message": exc.detail})
        return {"id": str(uuid.uuid4()), "status": "completed_with_errors" if errors else "completed", "total_rows": len(rows), "imported_rows": imported, "failed_rows": len(errors), "errors": errors}

    @app.get("/api/v1/performance-indicators/{record_id}/revision-chain")
    def revision_chain(record_id: str, request: Request):
        p = principal(request); item = repo.get(RESOURCES["performance-indicators"], record_id, p)
        with db.read() as conn:
            cols = db.columns(conn, "perf_performance_indicator")
            key = next((x for x in ("previous_pi_id", "previous_performance_indicator_id", "revised_from_id") if x in cols), None)
            if not key: return {"items": [item]}
            chain, seen = [item], {record_id}
            while chain[-1].get(key) and chain[-1][key] not in seen:
                seen.add(chain[-1][key]); row = conn.execute('SELECT * FROM perf_performance_indicator WHERE id=?', (chain[-1][key],)).fetchone()
                if not row: break
                chain.append(dict(row))
        return {"items": chain}

    @app.get("/api/v1/performance-indicators/{record_id}/prefill")
    def pi_prefill(record_id: str, request: Request, previous_pi_id: str):
        principal(request); source = repo.get(RESOURCES["performance-indicators"], previous_pi_id, principal(request))
        excluded = {"id", "indicator_code", "status_reason", "state", "row_version", "created_on", "created_by_id", "modified_on", "modified_by_id"}
        return {k: v for k, v in source.items() if k not in excluded}

    @app.get("/api/v1/risk-updates/previous-quarter")
    def risk_previous_quarter(request: Request, enterprise_risk_id: str, fiscal_year_id: str, quarter: str):
        principal(request)
        if "risk-updates" not in RESOURCES: raise ApiError(404, "NOT_FOUND", "Risk updates are unavailable.")
        with db.read() as conn:
            table = RESOURCES["risk-updates"].table
            if not db.table_exists(conn, table): raise ApiError(503, "SCHEMA_NOT_READY", f"Database table {table} is not installed.")
            cols = db.columns(conn, table); required = {"enterprise_risk_id", "fiscal_year_id", "quarter"}
            if not required <= cols: raise ApiError(503, "SCHEMA_NOT_READY", "Risk update period columns are not installed.")
            order = ["q1", "q2", "q3", "q4"]
            if quarter.lower() not in order or quarter.lower() == "q1": return {"item": None}
            previous = order[order.index(quarter.lower()) - 1]
            row = conn.execute(f'SELECT * FROM "{table}" WHERE enterprise_risk_id=? AND fiscal_year_id=? AND lower(quarter)=? ORDER BY modified_on DESC LIMIT 1', (enterprise_risk_id, fiscal_year_id, previous)).fetchone()
            return {"item": dict(row) if row else None}

    @app.post("/api/v1/attachments", status_code=201)
    async def upload_attachment(request: Request, filename: str):
        principal(request); content = await request.body()
        if len(content) > 32 * 1024 * 1024: raise ApiError(413, "ATTACHMENT_TOO_LARGE", "Attachments may not exceed 32 MB.")
        attachment_id = str(uuid.uuid4()); path = safe_attachment_path(settings.attachment_directory, attachment_id, filename)
        path.parent.mkdir(parents=True, exist_ok=False); path.write_bytes(content)
        return {"id": attachment_id, "filename": filename, "size": len(content), "content_type": request.headers.get("content-type", "application/octet-stream")}

    @app.get("/api/v1/notifications")
    def notifications(request: Request):
        p = principal(request); return {"items": [x for x in runtime.notifications.values() if x["user_id"] == p.id]}

    @app.post("/api/v1/notifications/{notification_id}/read")
    def read_notification(notification_id: str, request: Request):
        p = principal(request); item = runtime.notifications.get(notification_id)
        if not item or item["user_id"] != p.id: raise ApiError(404, "NOT_FOUND", "Notification not found.")
        item["read_on"] = utc_now(); return item

    @app.get("/api/v1/notifications/preferences")
    def get_preferences(request: Request):
        p = principal(request); return runtime.preferences.setdefault(p.id, {"in_app": True, "email": True, "teams": True})

    @app.put("/api/v1/notifications/preferences")
    def put_preferences(request: Request, payload: dict[str, bool] = Body(...)):
        p = principal(request)
        if set(payload) != {"in_app", "email", "teams"} or not all(isinstance(x, bool) for x in payload.values()): raise ApiError(400, "VALIDATION_FAILED", "All notification channel preferences are required booleans.")
        runtime.preferences[p.id] = payload; return payload

    @app.post("/api/v1/tasks/{task_id}/complete")
    def complete_task(task_id: str, request: Request):
        p = principal(request); item = repo.get(RESOURCES["tasks"], task_id, p)
        return repo.update(RESOURCES["tasks"], task_id, {"state": "completed", "completed_on": utc_now()}, p, str(item.get("row_version")) if "row_version" in item else None, request.state.correlation_id)

    @app.get("/api/v1/admin/jobs")
    def job_status(request: Request): require_edo(principal(request)); return {"items": list(runtime.jobs.values())}

    @app.post("/api/v1/admin/jobs/{job}/run")
    def run_job(job: str, request: Request):
        require_edo(principal(request))
        if job not in JOBS: raise ApiError(404, "NOT_FOUND", "Unknown background job.")
        runtime.jobs[job].update(status="succeeded", last_run=utc_now(), last_error=None); return runtime.jobs[job]

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

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        root = settings.static_directory.resolve()
        candidate = (root / full_path).resolve()
        if root in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        index = root / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise ApiError(404, "NOT_FOUND", "The requested page was not found.")

    return app


app = create_app()

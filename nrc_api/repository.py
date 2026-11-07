from __future__ import annotations

import json
import math
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from .auth import Principal
from .catalog import Resource
from .db import Database
from .errors import ApiError


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class Repository:
    def __init__(self, db: Database):
        self.db = db

    def _require_table(self, conn: sqlite3.Connection, resource: Resource) -> dict[str, sqlite3.Row]:
        if not self.db.table_exists(conn, resource.table):
            raise ApiError(503, "SCHEMA_NOT_READY", f"Database table {resource.table} is not installed.")
        return self.db.columns(conn, resource.table)

    @staticmethod
    def _visible_sql(columns: dict[str, sqlite3.Row], principal: Principal, operation: str) -> tuple[str, list[Any]]:
        if principal.is_edo:
            return "1=1", []
        if "owner_user_id" in columns and "owner_team_id" in columns:
            placeholders = ",".join("?" for _ in principal.team_ids) or "NULL"
            return f"(owner_user_id=? OR owner_team_id IN ({placeholders}))", [principal.id, *principal.team_ids]
        # Public/reference rows without ownership columns are readable by authenticated users.
        return ("1=1", []) if operation == "read" and "owner_user_id" not in columns else ("0=1", [])

    def list(self, resource: Resource, principal: Principal, query: dict[str, Any]) -> dict[str, Any]:
        page = max(1, int(query.get("page", 1)))
        size = min(200, max(1, int(query.get("page_size", 50))))
        with self.db.read() as conn:
            columns = self._require_table(conn, resource)
            visibility, params = self._visible_sql(columns, principal, "read")
            clauses = [visibility]
            applied: dict[str, Any] = {}
            for key, value in query.items():
                if key.startswith("filter[") and key.endswith("]"):
                    name = key[7:-1]
                    if name not in columns:
                        raise ApiError(400, "VALIDATION_FAILED", f"Unknown filter field: {name}")
                    values = [v for v in str(value).split(",") if v]
                    clauses.append(f'"{name}" IN ({",".join("?" for _ in values)})')
                    params.extend(values)
                    applied[name] = values
            if query.get("q"):
                searchable = [x for x in (resource.title_field, "title", "description", "name") if x in columns]
                if searchable:
                    clauses.append("(" + " OR ".join(f'"{c}" LIKE ? ESCAPE \'\\\'' for c in searchable) + ")")
                    escaped = str(query["q"]).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                    params.extend([f"%{escaped}%"] * len(searchable))
            order = "modified_on DESC" if "modified_on" in columns else f'"{resource.title_field}" COLLATE NOCASE'
            if query.get("sort"):
                parts = []
                for item in str(query["sort"]).split(","):
                    field, _, direction = item.partition(":")
                    if field not in columns or direction.lower() not in {"asc", "desc", ""}:
                        raise ApiError(400, "VALIDATION_FAILED", "Invalid sort expression.")
                    parts.append(f'"{field}" {direction or "asc"}')
                order = ",".join(parts)
            where = " AND ".join(clauses)
            total = conn.execute(f'SELECT count(*) FROM "{resource.table}" WHERE {where}', params).fetchone()[0]
            requested = [x for x in str(query.get("fields", "")).split(",") if x]
            if requested and any(x not in columns for x in requested):
                raise ApiError(400, "VALIDATION_FAILED", "One or more selected fields do not exist.")
            select = ",".join(f'"{x}"' for x in requested) if requested else "*"
            rows = conn.execute(f'SELECT {select} FROM "{resource.table}" WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?', (*params, size, (page - 1) * size)).fetchall()
            return {"items": [dict(x) for x in rows], "page": {"number": page, "size": size, "total_items": total, "total_pages": math.ceil(total / size)}, "applied_view": query.get("view"), "applied_filters": applied}

    def get(self, resource: Resource, record_id: str, principal: Principal) -> dict[str, Any]:
        with self.db.read() as conn:
            columns = self._require_table(conn, resource)
            visibility, params = self._visible_sql(columns, principal, "read")
            row = conn.execute(f'SELECT * FROM "{resource.table}" WHERE id=? AND {visibility}', (record_id, *params)).fetchone()
            if not row:
                raise ApiError(404, "NOT_FOUND", "The record does not exist or is not visible.")
            return dict(row)

    def create(self, resource: Resource, payload: dict[str, Any], principal: Principal, correlation_id: str) -> dict[str, Any]:
        if not principal.is_submitter and not principal.is_edo:
            raise ApiError(403, "FORBIDDEN", "Create privilege is required.")
        if resource.restricted_creation and not principal.is_edo and (payload.get("report_level") == "cbj_appr" or payload.get("agency_wide_support_level") == "agency"):
            raise ApiError(403, "INSUFFICIENT_PRIVILEGE_FOR_FIELD_VALUE", "You do not have the necessary privileges to create this record with this field value.")
        with self.db.write() as conn:
            columns = self._require_table(conn, resource)
            unknown = set(payload) - set(columns)
            if unknown:
                raise ApiError(400, "VALIDATION_FAILED", "Unknown fields were supplied.", [{"field": x, "code": "UNKNOWN_FIELD", "message": "Field is not part of this resource."} for x in sorted(unknown)])
            data = dict(payload)
            data.setdefault("id", str(uuid.uuid4()))
            if "owner_user_id" in columns and "owner_team_id" in columns:
                data.setdefault("owner_user_id", principal.id)
            if "created_by_id" in columns: data.setdefault("created_by_id", principal.id)
            if "modified_by_id" in columns: data.setdefault("modified_by_id", principal.id)
            if "created_on" in columns: data.setdefault("created_on", utc_now())
            if "modified_on" in columns: data.setdefault("modified_on", utc_now())
            if "row_version" in columns: data.setdefault("row_version", 1)
            names = list(data)
            conn.execute(f'INSERT INTO "{resource.table}" ({",".join(f"\"{x}\"" for x in names)}) VALUES ({",".join("?" for _ in names)})', [data[x] for x in names])
            self._audit(conn, resource.table, data["id"], "insert", None, data, principal.id, correlation_id)
            return dict(conn.execute(f'SELECT * FROM "{resource.table}" WHERE id=?', (data["id"],)).fetchone())

    def update(self, resource: Resource, record_id: str, payload: dict[str, Any], principal: Principal, if_match: str | None, correlation_id: str) -> dict[str, Any]:
        with self.db.write() as conn:
            columns = self._require_table(conn, resource)
            old = conn.execute(f'SELECT * FROM "{resource.table}" WHERE id=?', (record_id,)).fetchone()
            if not old:
                raise ApiError(404, "NOT_FOUND", "The record does not exist or is not visible.")
            old_dict = dict(old)
            visibility, visibility_params = self._visible_sql(columns, principal, "write")
            visible = conn.execute(f'SELECT 1 FROM "{resource.table}" WHERE id=? AND {visibility}', (record_id, *visibility_params)).fetchone()
            if not visible: raise ApiError(404, "NOT_FOUND", "The record does not exist or is not visible.")
            if not principal.is_edo and old_dict.get("status_reason") not in {None, "draft", "revision"}:
                raise ApiError(403, "RECORD_LOCKED", "The record is locked outside Draft or Revision.")
            if "row_version" in columns:
                if if_match is None:
                    raise ApiError(428, "PRECONDITION_REQUIRED", "If-Match is required for updates.")
                try: expected = int(if_match.strip('"'))
                except ValueError as exc: raise ApiError(400, "VALIDATION_FAILED", "If-Match must contain a row version.") from exc
                if expected != old_dict["row_version"]:
                    raise ApiError(409, "CONCURRENCY_CONFLICT", "The record was modified by another request.")
            unknown = set(payload) - set(columns) - {"id", "row_version", "created_on", "created_by_id"}
            if unknown:
                raise ApiError(400, "VALIDATION_FAILED", "Unknown or immutable fields were supplied.")
            data = {k: v for k, v in payload.items() if k in columns and k not in {"id", "row_version", "created_on", "created_by_id"}}
            if "modified_on" in columns: data["modified_on"] = utc_now()
            if "modified_by_id" in columns: data["modified_by_id"] = principal.id
            if "row_version" in columns: data["row_version"] = old_dict["row_version"] + 1
            if not data: return old_dict
            conn.execute(f'UPDATE "{resource.table}" SET {",".join(f"\"{k}\"=?" for k in data)} WHERE id=?', (*data.values(), record_id))
            new = dict(conn.execute(f'SELECT * FROM "{resource.table}" WHERE id=?', (record_id,)).fetchone())
            self._audit(conn, resource.table, record_id, "update", old_dict, new, principal.id, correlation_id)
            return new

    def delete(self, resource: Resource, record_id: str, principal: Principal, correlation_id: str) -> None:
        with self.db.write() as conn:
            columns = self._require_table(conn, resource)
            row = conn.execute(f'SELECT * FROM "{resource.table}" WHERE id=?', (record_id,)).fetchone()
            if not row: raise ApiError(404, "NOT_FOUND", "The record does not exist or is not visible.")
            item = dict(row)
            visibility, visibility_params = self._visible_sql(columns, principal, "delete")
            if not conn.execute(f'SELECT 1 FROM "{resource.table}" WHERE id=? AND {visibility}', (record_id, *visibility_params)).fetchone():
                raise ApiError(404, "NOT_FOUND", "The record does not exist or is not visible.")
            if not principal.is_edo and (item.get("status_reason") != "draft" or item.get("owner_user_id") != principal.id):
                raise ApiError(403, "RECORD_LOCKED", "Only an owner may delete their Draft record.")
            conn.execute(f'DELETE FROM "{resource.table}" WHERE id=?', (record_id,))
            self._audit(conn, resource.table, record_id, "delete", item, None, principal.id, correlation_id)

    @staticmethod
    def _audit(conn: sqlite3.Connection, table: str, record_id: str, operation: str, old: Any, new: Any, user_id: str, correlation_id: str) -> None:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='wf_field_audit'").fetchone()
        if not exists: return
        cols = {x["name"] for x in conn.execute('PRAGMA table_info("wf_field_audit")')}
        if {"table_name", "record_id", "column_name", "old_value", "new_value", "operation", "changed_by_id", "changed_on", "correlation_id"} <= cols:
            before, after = old or {}, new or {}
            for field in sorted(set(before) | set(after)):
                if before.get(field) != after.get(field):
                    conn.execute("INSERT INTO wf_field_audit(table_name,record_id,column_name,old_value,new_value,operation,changed_by_id,changed_on,correlation_id) VALUES(?,?,?,?,?,?,?,?,?)", (table, record_id, field, json.dumps(before.get(field)), json.dumps(after.get(field)), operation, user_id, utc_now(), correlation_id))

    def audit(self, resource: Resource, record_id: str, principal: Principal) -> list[dict[str, Any]]:
        self.get(resource, record_id, principal)
        with self.db.read() as conn:
            if not self.db.table_exists(conn, "wf_field_audit"): return []
            return [dict(x) for x in conn.execute("SELECT * FROM wf_field_audit WHERE table_name=? AND record_id=? ORDER BY changed_on DESC", (resource.table, record_id))]

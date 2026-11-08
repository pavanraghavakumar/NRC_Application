from __future__ import annotations

import csv
import hashlib
import io
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .auth import Principal
from .catalog import RELATIONSHIPS, RESOURCES, Resource
from .db import Database
from .errors import ApiError
from .repository import utc_now


OPTION_SETS = {
    "record_state": ["active", "inactive"],
    "workflow_status": ["draft", "pending_approval", "revision", "finalized", "discontinued"],
    "quarter": ["q1", "q2", "q3", "q4"],
    "report_level": ["cbj_appr", "business_product_line"],
    "notification_channel": ["in_app", "email", "teams"],
    "risk_rating": ["low", "medium", "high", "critical"],
    "indicator_type": ["output", "outcome", "contextual"],
    "indicator_status": ["under_development", "active", "discontinued", "cancelled_closed", "versioned_revised"],
    "data_type": ["number", "percentage", "currency", "date", "text"],
    "measure_type": ["cumulative", "non_cumulative"],
    "frequency": ["monthly", "quarterly", "semiannual", "annual"],
    "likelihood": ["rare", "unlikely", "possible", "likely", "almost_certain"],
    "consequence": ["insignificant", "minor", "moderate", "major", "severe"],
    "risk_status": ["under_development", "active", "pending_discontinue", "discontinued"],
    "publish_status": ["internal", "public"],
    "approval_stage": ["draft", "review", "final"],
    "task_state": ["open", "completed", "cancelled"],
}

JOBS = ("create_submission_tasks", "create_approval_tasks", "create_rejection_tasks", "dispatch_notifications", "close_completed_tasks", "recompute_rollups", "refresh_analytics", "maintain_database")


class RuntimeStore:
    """Fallback state used only when optional workflow tables are absent."""

    def __init__(self) -> None:
        self.idempotency: dict[str, tuple[str, Any]] = {}
        self.notifications: dict[str, dict[str, Any]] = {}
        self.preferences: dict[str, dict[str, bool]] = {}
        self.jobs = {name: {"name": name, "status": "idle", "last_run": None, "last_error": None} for name in JOBS}

    def replay(self, key: str, payload: Any) -> Any | None:
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        existing = self.idempotency.get(key)
        if existing and existing[0] != fingerprint:
            raise ApiError(409, "IDEMPOTENCY_CONFLICT", "The idempotency key was already used with another request.")
        return existing[1] if existing else None

    def remember(self, key: str, payload: Any, response: Any) -> None:
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        self.idempotency[key] = (fingerprint, response)


class RelationshipService:
    def __init__(self, db: Database): self.db = db

    def _resolve(self, conn: sqlite3.Connection, resource: Resource, relationship: str) -> tuple[str, str, str]:
        target = RELATIONSHIPS.get(relationship, relationship.replace("-", "_").removesuffix("s"))
        source_token, target_token = resource.table.removeprefix("perf_").removeprefix("plan_").removeprefix("evidence_").removeprefix("ref_").removeprefix("core_"), target
        candidates = [x[0] for x in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in candidates:
            cols = self.db.columns(conn, table)
            source_fk, target_fk = f"{source_token}_id", f"{target_token}_id"
            if source_fk in cols and target_fk in cols:
                return table, source_fk, target_fk
        raise ApiError(404, "RELATIONSHIP_NOT_FOUND", "The relationship is not installed in this schema.")

    def list(self, resource: Resource, record_id: str, relationship: str) -> dict[str, Any]:
        with self.db.read() as conn:
            table, source_fk, target_fk = self._resolve(conn, resource, relationship)
            rows = conn.execute(f'SELECT "{target_fk}" AS id FROM "{table}" WHERE "{source_fk}"=?', (record_id,)).fetchall()
            return {"items": [dict(x) for x in rows]}

    def add(self, resource: Resource, record_id: str, relationship: str, ids: list[str]) -> dict[str, Any]:
        if not ids or len(ids) > 500: raise ApiError(400, "VALIDATION_FAILED", "ids must contain between 1 and 500 identifiers.")
        with self.db.write() as conn:
            table, source_fk, target_fk = self._resolve(conn, resource, relationship)
            cols = self.db.columns(conn, table)
            for related_id in dict.fromkeys(ids):
                data = {source_fk: record_id, target_fk: related_id}
                if "id" in cols: data["id"] = str(uuid.uuid4())
                names = list(data)
                conn.execute(f'INSERT OR IGNORE INTO "{table}" ({",".join(f"\"{x}\"" for x in names)}) VALUES ({",".join("?" for _ in names)})', list(data.values()))
        return self.list(resource, record_id, relationship)

    def remove(self, resource: Resource, record_id: str, relationship: str, related_id: str) -> None:
        with self.db.write() as conn:
            table, source_fk, target_fk = self._resolve(conn, resource, relationship)
            cursor = conn.execute(f'DELETE FROM "{table}" WHERE "{source_fk}"=? AND "{target_fk}"=?', (record_id, related_id))
            if not cursor.rowcount: raise ApiError(404, "NOT_FOUND", "The relationship does not exist.")


def csv_response(rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> str:
    if not rows and not fieldnames: return ""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames or list(rows[0]), extrasaction="ignore")
    writer.writeheader(); writer.writerows(rows)
    return output.getvalue()


def parse_csv(content: bytes, *, max_rows: int = 10000) -> list[dict[str, str]]:
    try: text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc: raise ApiError(400, "INVALID_FILE", "CSV files must use UTF-8 encoding.") from exc
    rows = list(csv.DictReader(io.StringIO(text)))
    if len(rows) > max_rows: raise ApiError(413, "IMPORT_TOO_LARGE", f"Imports may contain at most {max_rows} rows.")
    return rows


def safe_attachment_path(root: Path, attachment_id: str, filename: str) -> Path:
    try: uuid.UUID(attachment_id)
    except ValueError as exc: raise ApiError(400, "VALIDATION_FAILED", "Attachment id must be a UUID.") from exc
    clean = Path(filename).name
    if clean != filename or not clean: raise ApiError(400, "INVALID_FILENAME", "The filename is invalid.")
    root = root.resolve(); path = (root / attachment_id / clean).resolve()
    if root not in path.parents: raise ApiError(400, "INVALID_FILENAME", "The filename is invalid.")
    return path


def require_edo(principal: Principal) -> None:
    if not principal.is_edo: raise ApiError(403, "FORBIDDEN", "EDO User role is required.")

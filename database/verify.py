"""Database-level verification used in CI, deployment readiness, and migration reconciliation."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .connection import configure_connection


@dataclass(frozen=True)
class Finding:
    check: str
    detail: str


def verify(path: str | Path) -> list[Finding]:
    connection = sqlite3.connect(path)
    configure_connection(connection)
    findings: list[Finding] = []
    try:
        for row in connection.execute("PRAGMA integrity_check"):
            if row[0] != "ok": findings.append(Finding("integrity_check", row[0]))
        for row in connection.execute("PRAGMA foreign_key_check"):
            findings.append(Finding("foreign_key_check", repr(tuple(row))))
        required = {"core_app_user","plan_goal","perf_performance_indicator","perf_pi_result_period","perf_risk_update","wf_submission","wf_field_audit","analytics_fact_pi_result"}
        actual = {r[0] for r in connection.execute("SELECT name FROM sqlite_schema WHERE type IN ('table','view')")}
        for missing in sorted(required-actual): findings.append(Finding("schema", f"missing {missing}"))
        expected_junctions = 61
        present_junctions = len([n for n in actual if n in __import__('database.migrations.001_initial', fromlist=['JUNCTIONS']).JUNCTIONS])
        if present_junctions != expected_junctions: findings.append(Finding("junction_count", f"expected {expected_junctions}, got {present_junctions}"))
        fk_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        if fk_enabled != 1: findings.append(Finding("connection", "foreign_keys is off"))
        return findings
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("database")
    args = parser.parse_args()
    errors = verify(args.database)
    for error in errors: print(f"{error.check}: {error.detail}")
    raise SystemExit(bool(errors))

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nrc_api.config import Settings
from nrc_api.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    database = tmp_path / "test.db"
    conn = sqlite3.connect(database)
    conn.executescript("""
    CREATE TABLE plan_goal (
      id TEXT PRIMARY KEY, goal TEXT NOT NULL, goal_text TEXT,
      state TEXT NOT NULL DEFAULT 'active', status_reason TEXT NOT NULL DEFAULT 'active',
      owner_user_id TEXT, owner_team_id TEXT, created_on TEXT, created_by_id TEXT,
      modified_on TEXT, modified_by_id TEXT, row_version INTEGER NOT NULL DEFAULT 1
    ) STRICT;
    CREATE TABLE perf_performance_indicator (
      id TEXT PRIMARY KEY, indicator_code TEXT NOT NULL UNIQUE, indicator_title TEXT NOT NULL,
      report_level TEXT NOT NULL, agency_wide_support_level TEXT NOT NULL,
      state TEXT NOT NULL DEFAULT 'active', status_reason TEXT NOT NULL DEFAULT 'draft',
      indicator_status TEXT DEFAULT 'under_development', comments TEXT,
      owner_user_id TEXT, owner_team_id TEXT, created_on TEXT, created_by_id TEXT,
      modified_on TEXT, modified_by_id TEXT, row_version INTEGER NOT NULL DEFAULT 1
    ) STRICT;
    CREATE TABLE ref_office (id TEXT PRIMARY KEY, office TEXT NOT NULL, state TEXT DEFAULT 'active', row_version INTEGER NOT NULL DEFAULT 1) STRICT;
    CREATE TABLE perf_performance_indicator_office (id TEXT PRIMARY KEY, performance_indicator_id TEXT NOT NULL, office_id TEXT NOT NULL, UNIQUE(performance_indicator_id, office_id)) STRICT;
    CREATE TABLE wf_field_audit (id INTEGER PRIMARY KEY, table_name TEXT, record_id TEXT, column_name TEXT, old_value TEXT, new_value TEXT, operation TEXT, changed_by_id TEXT, changed_on TEXT, correlation_id TEXT) STRICT;
    CREATE VIEW analytics_strategic_planning_home AS SELECT id, goal, goal_text FROM plan_goal;
    """)
    conn.close()
    settings = Settings(database, "development", True, None, None, None, None, 1000, tmp_path / "files")
    with TestClient(create_app(settings)) as test_client:
        yield test_client

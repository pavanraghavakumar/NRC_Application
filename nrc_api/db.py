from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .errors import ApiError


class Database:
    def __init__(self, path: Path):
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=5, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA temp_store = MEMORY")
        return conn

    def check_version(self) -> None:
        if sqlite3.sqlite_version_info < (3, 45, 0):
            raise RuntimeError(f"SQLite 3.45+ required; found {sqlite3.sqlite_version}")

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.execute("PRAGMA optimize")
            conn.close()

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            message = str(exc)
            if message.startswith("HIERARCHY_MISMATCH"):
                raise ApiError(400, "HIERARCHY_MISMATCH", message.partition(":")[2].strip()) from exc
            if "UNIQUE" in message:
                raise ApiError(409, "DUPLICATE_CODE", "A record with the same unique value already exists.") from exc
            raise ApiError(400, "VALIDATION_FAILED", "The database rejected the supplied values.") from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA optimize")
            conn.close()

    @staticmethod
    def columns(conn: sqlite3.Connection, table: str) -> dict[str, sqlite3.Row]:
        return {row["name"]: row for row in conn.execute(f'PRAGMA table_info("{table}")')}

    @staticmethod
    def table_exists(conn: sqlite3.Connection, table: str) -> bool:
        return conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (table,)).fetchone() is not None


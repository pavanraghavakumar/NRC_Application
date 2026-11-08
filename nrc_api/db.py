from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from database import ConcurrencyConflict, Database as SQLiteDatabase, draw_identifier

from .errors import ApiError


class Database(SQLiteDatabase):
    """API-facing adapter over the production SQLite package.

    The persistence package owns connection policy and transaction semantics;
    this adapter only translates database failures into the public problem model
    and retains the schema-inspection helpers used by the repository layer.
    """

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.path,
            timeout=5,
            isolation_level=None,
            check_same_thread=False,
        )
        from database.connection import configure_connection

        configure_connection(connection)
        return connection

    def check_version(self) -> None:
        if sqlite3.sqlite_version_info < (3, 45, 0):
            raise RuntimeError(f"SQLite 3.45+ required; found {sqlite3.sqlite_version}")

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        try:
            with super().write() as connection:
                yield connection
        except ConcurrencyConflict as exc:
            raise ApiError(409, "CONCURRENCY_CONFLICT", "The record was modified by another request.") from exc
        except sqlite3.IntegrityError as exc:
            message = str(exc)
            if message.startswith("HIERARCHY_MISMATCH"):
                raise ApiError(400, "HIERARCHY_MISMATCH", message.partition(":")[2].strip()) from exc
            if "UNIQUE" in message:
                raise ApiError(409, "DUPLICATE_CODE", "A record with the same unique value already exists.") from exc
            raise ApiError(400, "VALIDATION_FAILED", "The database rejected the supplied values.") from exc

    @staticmethod
    def columns(connection: sqlite3.Connection, table: str) -> dict[str, sqlite3.Row]:
        return {row["name"]: row for row in connection.execute(f'PRAGMA table_info("{table}")')}

    @staticmethod
    def table_exists(connection: sqlite3.Connection, table: str) -> bool:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?",
            (table,),
        ).fetchone() is not None


__all__ = ["ConcurrencyConflict", "Database", "draw_identifier"]

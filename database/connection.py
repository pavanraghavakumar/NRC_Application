"""Connection and transaction primitives shared by the API and maintenance jobs."""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from typing import Iterator, Mapping, Any


MINIMUM_SQLITE = (3, 45, 0)


class ConcurrencyConflict(RuntimeError):
    """Raised when an optimistic update loses a row-version race."""


def configure_connection(connection: sqlite3.Connection) -> None:
    if sqlite3.sqlite_version_info < MINIMUM_SQLITE:
        raise RuntimeError("NRC SPA requires SQLite 3.45 or later")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA temp_store = MEMORY")


class Database:
    """Opens configured SQLite connections and short, immediate write transactions."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        configure_connection(connection)
        return connection

    @contextlib.contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.execute("PRAGMA optimize")
            connection.close()

    @contextlib.contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA optimize")
            connection.close()

    def optimistic_update(
        self, table: str, record_id: str, expected_version: int, values: Mapping[str, Any]
    ) -> int:
        if not table.replace("_", "").isalnum() or not values:
            raise ValueError("invalid optimistic update")
        columns = list(values)
        if any(not column.replace("_", "").isalnum() for column in columns):
            raise ValueError("invalid column name")
        assignments = ", ".join(f'"{column}" = ?' for column in columns)
        sql = (
            f'UPDATE "{table}" SET {assignments}, row_version = row_version + 1, '
            "modified_on = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE id = ? AND row_version = ? RETURNING row_version"
        )
        with self.write() as connection:
            row = connection.execute(sql, [values[c] for c in columns] + [record_id, expected_version]).fetchone()
            if row is None:
                raise ConcurrencyConflict(f"stale {table}:{record_id}")
            return int(row[0])


def draw_identifier(connection: sqlite3.Connection, scope_key: str) -> int:
    """Atomically draw the next scoped identifier inside the caller's transaction."""
    row = connection.execute(
        """INSERT INTO core_id_counter(scope_key, next_value) VALUES (?, 1)
           ON CONFLICT(scope_key) DO UPDATE SET next_value = next_value + 1
           RETURNING next_value""",
        (scope_key,),
    ).fetchone()
    return int(row[0])

"""Small deterministic migration runner; intentionally dependency-free."""

from __future__ import annotations

import argparse
import importlib
import pkgutil
import sqlite3
from pathlib import Path

from .connection import configure_connection


def _migrations():
    package = importlib.import_module("database.migrations")
    for module in sorted(m.name for m in pkgutil.iter_modules(package.__path__) if m.name[:3].isdigit()):
        yield module, importlib.import_module(f"database.migrations.{module}")


def migrate(path: str | Path) -> list[str]:
    connection = sqlite3.connect(path, timeout=5, isolation_level=None)
    configure_connection(connection)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS core_schema_migration(version TEXT PRIMARY KEY, applied_on TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))) STRICT"
    )
    applied: list[str] = []
    try:
        for version, module in _migrations():
            if connection.execute("SELECT 1 FROM core_schema_migration WHERE version=?", (version,)).fetchone():
                continue
            connection.execute("BEGIN IMMEDIATE")
            try:
                module.upgrade(connection)
                connection.execute("INSERT INTO core_schema_migration(version) VALUES (?)", (version,))
                connection.commit()
                applied.append(version)
            except BaseException:
                connection.rollback()
                raise
        return applied
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("database")
    args = parser.parse_args()
    print("\n".join(migrate(args.database)))

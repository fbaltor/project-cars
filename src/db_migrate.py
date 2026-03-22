"""Database migration runner wrapping yoyo-migrations.

Run via: python -m src.db_migrate
Or:      mise run db:migrate
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from yoyo import get_backend, read_migrations

MIGRATIONS_DIR = Path(__file__).parent.parent / "db" / "migrations"


def _normalize_url(url: str) -> str:
    """Ensure the URL uses postgresql+psycopg:// for psycopg3."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def apply_migrations(database_url: str | None = None) -> int:
    """Apply all pending migrations. Returns count of applied migrations."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(2)

    url = _normalize_url(url)
    backend = get_backend(url)
    migrations = read_migrations(str(MIGRATIONS_DIR))

    with backend.lock():
        to_apply = backend.to_apply(migrations)
        if not to_apply:
            print("No pending migrations.")
            return 0
        backend.apply_migrations(to_apply)
        count = len(to_apply)
        print(f"Applied {count} migration(s).")
        return count


def rollback_migrations(database_url: str | None = None) -> int:
    """Roll back the most recently applied batch. Returns count rolled back."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(2)

    url = _normalize_url(url)
    backend = get_backend(url)
    migrations = read_migrations(str(MIGRATIONS_DIR))

    with backend.lock():
        to_rollback = backend.to_rollback(migrations)
        if not to_rollback:
            print("No migrations to roll back.")
            return 0
        backend.rollback_migrations(to_rollback)
        count = len(to_rollback)
        print(f"Rolled back {count} migration(s).")
        return count


if __name__ == "__main__":
    apply_migrations()

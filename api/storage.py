"""SQLite persistence for the single-user Quorum demo."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DATABASE = Path(os.getenv("QUORUM_DB", Path(__file__).resolve().parents[1] / "var" / "quorum.sqlite"))

def connection() -> sqlite3.Connection:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(DATABASE)
    database.row_factory = sqlite3.Row
    database.executescript("""
      CREATE TABLE IF NOT EXISTS saved_places (
        id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, address TEXT NOT NULL,
        latitude REAL, longitude REAL, radius_meters INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
      CREATE TABLE IF NOT EXISTS monitor_state (
        place_id INTEGER NOT NULL, item_id TEXT NOT NULL, status TEXT NOT NULL,
        PRIMARY KEY (place_id, item_id)
      );
      CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY, place_id INTEGER NOT NULL, item_id TEXT NOT NULL,
        status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (place_id, item_id, status)
      );
    """)
    return database

def reset() -> None:
    if DATABASE.exists():
        DATABASE.unlink()

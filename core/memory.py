from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


class SessionMemory:
    """SQLite-backed session memory for per-run context windows."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", "./memory.db")
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    agent_type TEXT,
                    context_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS run_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    agent_type TEXT,
                    input_summary TEXT,
                    output_summary TEXT,
                    timestamp TEXT
                )
            """)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_session(self, session_id: str, agent_type: str, context: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, agent_type, context_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET context_json=excluded.context_json, updated_at=excluded.updated_at
                """,
                (session_id, agent_type, json.dumps(context), now, now),
            )

    def get_session(self, session_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT context_json FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        if row:
            return json.loads(row["context_json"])
        return None

    def log_run(
        self,
        session_id: str,
        agent_type: str,
        input_summary: str,
        output_summary: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO run_log (session_id, agent_type, input_summary, output_summary, timestamp) VALUES (?,?,?,?,?)",
                (session_id, agent_type, input_summary, output_summary, now),
            )

    def get_run_history(self, agent_type: str | None = None, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            if agent_type:
                rows = conn.execute(
                    "SELECT * FROM run_log WHERE agent_type=? ORDER BY timestamp DESC LIMIT ?",
                    (agent_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM run_log ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]

    def prune_old_runs(self, keep: int = 1000) -> int:
        """Delete run_log rows beyond the most recent `keep` entries. Returns rows deleted."""
        with self._conn() as conn:
            deleted = conn.execute(
                """
                DELETE FROM run_log WHERE id NOT IN (
                    SELECT id FROM run_log ORDER BY timestamp DESC LIMIT ?
                )
                """,
                (keep,),
            ).rowcount
        return deleted

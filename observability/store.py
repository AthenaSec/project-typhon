"""SQLite persistence for red-team runs and findings.

One row per run in `runs`, one row per attack result in `findings`. This is
the durable record the compliance mapper and report generator read from —
not an operational log (see cli.py for that). Writes happen inline from
redteam_engine/runner.py as each attack finishes; there's no separate
collector process.
"""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from redteam_engine.schemas import Attack, Judgment

DB_PATH = Path(__file__).parent / "redteam.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    target_url TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(id),
    category TEXT NOT NULL,
    attack_id TEXT NOT NULL,
    attack_name TEXT NOT NULL,
    attack_prompt TEXT NOT NULL,
    attack_goal TEXT NOT NULL,
    response TEXT NOT NULL,
    vulnerable INTEGER NOT NULL,
    rationale TEXT NOT NULL,
    engine TEXT NOT NULL DEFAULT 'single_turn',
    trace TEXT,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)


def start_run(target_url: str) -> str:
    run_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO runs (id, target_url, started_at) VALUES (?, ?, ?)",
            (run_id, target_url, _now()),
        )
    return run_id


def finish_run(run_id: str) -> None:
    with _connect() as conn:
        conn.execute("UPDATE runs SET finished_at = ? WHERE id = ?", (_now(), run_id))


def save_finding(
    run_id: str,
    category: str,
    attack: Attack,
    response: str,
    judgment: Judgment,
    trace: dict | None = None,
    engine: str = "single_turn",
) -> None:
    """Persist one attack's result. `trace` holds engine-specific evidence —
    for the pyrit engine, the multi-turn conversation (`{"turns": [...]}`);
    always None for single_turn."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO findings (
                run_id, category, attack_id, attack_name, attack_prompt,
                attack_goal, response, vulnerable, rationale, engine, trace, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                category,
                attack.id,
                attack.name,
                attack.prompt,
                attack.goal,
                response,
                int(judgment.vulnerable),
                judgment.rationale,
                engine,
                json.dumps(trace) if trace is not None else None,
                _now(),
            ),
        )


def list_runs() -> list[dict]:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM runs ORDER BY started_at DESC").fetchall()
        return [dict(row) for row in rows]


def get_run(run_id: str) -> dict:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else {}


def get_findings(run_id: str | None = None) -> list[dict]:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        if run_id:
            rows = conn.execute("SELECT * FROM findings WHERE run_id = ?", (run_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM findings").fetchall()
        return [dict(row) for row in rows]

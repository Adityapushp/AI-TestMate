
"""SQLite repository for AI-TestMate results."""

import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# Vercel's application directory is read-only.
# Use its temporary writable directory when deployed.
if os.getenv("VERCEL") == "1":
    DB_PATH = Path("/tmp/ai-testmate/testmate.db")
else:
    DB_PATH = Path(__file__).resolve().parents[1] / "testmate.db"

# Ensure the database directory exists.
DB_PATH.parent.mkdir(parents=True, exist_ok=True)



class ResultRepository:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.execute("PRAGMA busy_timeout = 10000")
        return con

    def initialize(self):
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    failed INTEGER NOT NULL
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS case_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    case_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    score REAL NOT NULL,
                    details TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                )
            """)

    def save_run(self, results: list[dict]) -> int:
        passed = sum(1 for item in results if item["passed"])

        with self.connect() as con:
            cur = con.execute(
                """
                INSERT INTO runs(created_at, total, passed, failed)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    len(results),
                    passed,
                    len(results) - passed,
                ),
            )

            run_id = cur.lastrowid

            con.executemany(
                """
                INSERT INTO case_results(
                    run_id, case_id, question, answer,
                    passed, score, details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        r["case_id"],
                        r["question"],
                        r["answer"],
                        int(r["passed"]),
                        r["score"],
                        json.dumps(r),
                    )
                    for r in results
                ],
            )

            return int(run_id)

    def list_runs(self, limit: int = 20) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT id, created_at, total, passed, failed
                FROM runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            dict(
                id=r[0],
                created_at=r[1],
                total=r[2],
                passed=r[3],
                failed=r[4],
            )
            for r in rows
        ]

    def get_run(self, run_id: int) -> dict | None:
        with self.connect() as con:
            run = con.execute(
                """
                SELECT id, created_at, total, passed, failed
                FROM runs WHERE id = ?
                """,
                (run_id,),
            ).fetchone()

            if not run:
                return None

            rows = con.execute(
                """
                SELECT details FROM case_results
                WHERE run_id = ?
                ORDER BY id
                """,
                (run_id,),
            ).fetchall()

        return {
            "id": run[0],
            "created_at": run[1],
            "total": run[2],
            "passed": run[3],
            "failed": run[4],
            "results": [json.loads(r[0]) for r in rows],
        }

    def previous_run(self, run_id: int) -> dict | None:
        with self.connect() as con:
            row = con.execute(
                """
                SELECT id FROM runs
                WHERE id < ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()

        return self.get_run(row[0]) if row else None

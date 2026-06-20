"""SQLite-backed detection log for Navi Drone."""

import sqlite3
import time
from contextlib import contextmanager

DB_PATH = "navi_drone_log.db"


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                name TEXT NOT NULL,
                similarity REAL,
                det_score REAL
            )
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_detection(name, similarity, det_score):
    with _conn() as c:
        c.execute(
            "INSERT INTO detections (ts, name, similarity, det_score) VALUES (?, ?, ?, ?)",
            (time.time(), name, similarity, det_score),
        )


def recent_logs(limit=100):
    with _conn() as c:
        rows = c.execute(
            "SELECT ts, name, similarity, det_score FROM detections ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"ts": r[0], "name": r[1], "similarity": r[2], "det_score": r[3]}
        for r in rows
    ]


def stats():
    with _conn() as c:
        rows = c.execute("""
            SELECT name, COUNT(*) as count, MAX(ts) as last_seen
            FROM detections GROUP BY name ORDER BY count DESC
        """).fetchall()
        total = c.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
    return {
        "total_detections": total,
        "by_person": [
            {"name": r[0], "count": r[1], "last_seen": r[2]} for r in rows
        ],
    }

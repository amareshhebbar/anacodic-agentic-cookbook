from __future__ import annotations

import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS trials (
    trial_id TEXT PRIMARY KEY,
    timestamp REAL,
    query_id TEXT,
    query_text TEXT,
    provider TEXT,
    trial_num INTEGER,
    paper_count INTEGER,
    latency_ms INTEGER,
    wall_time_ms INTEGER,
    keyword_precision REAL,
    papers_meeting_min_evidence INTEGER,
    avg_rcs_score REAL,
    avg_citation_count REAL,
    keywords_found TEXT,
    keywords_missing TEXT,
    error TEXT
)
"""


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def insert_trial(conn: sqlite3.Connection, r: dict) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO trials
        (trial_id, timestamp, query_id, query_text, provider, trial_num,
         paper_count, latency_ms, wall_time_ms, keyword_precision,
         papers_meeting_min_evidence, avg_rcs_score, avg_citation_count,
         keywords_found, keywords_missing, error)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            r["trial_id"],
            r["timestamp"],
            r.get("query_id", ""),
            r.get("query", ""),
            r["provider"],
            r["trial_num"],
            r.get("paper_count", 0),
            r.get("latency_ms", 0),
            r.get("wall_time_ms", 0),
            r.get("keyword_precision", 0.0),
            r.get("papers_meeting_min_evidence", 0),
            r.get("avg_rcs_score", 0.0),
            r.get("avg_citation_count", 0.0),
            json.dumps(r.get("keywords_found", [])),
            json.dumps(r.get("keywords_missing", [])),
            r.get("error"),
        ),
    )
    conn.commit()


def load_all_trials(path: str) -> list[dict]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM trials").fetchall()
    conn.close()
    return [dict(r) for r in rows]
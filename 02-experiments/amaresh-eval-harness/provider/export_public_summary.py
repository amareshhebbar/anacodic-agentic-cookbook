"""Make a run's results safe to publish.

run_single_benchmark.py writes results/single_<id>.json with the retrieved
corpus TEXT ("context", "retrieved_chunks") and the generated answers in it.
The corpus is licensed journal text and must never reach this public repo,
so raw single_*.json files are gitignored. This script writes a copy with
those text fields removed -- scores, counts, timings and chunk IDs only --
as results/summary_<id>.json, which is safe to commit.

    python export_public_summary.py results/single_L01.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TEXT_FIELDS = ("context", "answer", "retrieved_chunks")


def export(raw_path: Path) -> Path:
    data = json.loads(raw_path.read_text())
    for trial in data.get("results", []):
        for field in TEXT_FIELDS:
            trial.pop(field, None)
    out = raw_path.with_name(raw_path.name.replace("single_", "summary_", 1))
    out.write_text(json.dumps(data, indent=2))
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"wrote {export(Path(arg))}")

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")  # repo root

from groq import Groq

from local_queries import LOCAL_BENCHMARK_QUERIES
from local_retrieval import load_corpus
from local_pipeline import run_local_trial
from storage import init_db, insert_trial, load_all_trials
from graph_store import build_graph, add_comparison_edges, write_graphml
from charts import (
    chart_precision_by_provider,
    chart_paper_count_variance,
    chart_latency_by_provider,
)

RESULTS_DIR = Path(__file__).parent / "results"
CHARTS_DIR = RESULTS_DIR / "charts"

DEFAULT_GROQ_MODELS = {
    "groq_llama": "llama-3.1-8b-instant",
    "groq_qwen": "openai/gpt-oss-120b",
}


def list_available_groq_models() -> list[str]:
    client = Groq()
    resp = client.models.list()
    return sorted(m.id for m in resp.data)


def validate_models(models: dict[str, str]) -> None:
    try:
        available = list_available_groq_models()
    except Exception as exc:
        print(f"WARNING: could not fetch model list from Groq ({exc}); skipping validation.")
        return

    bad = {label: mid for label, mid in models.items() if mid not in available}
    if bad:
        print("ERROR: the following model IDs are not available on your Groq account:")
        for label, mid in bad.items():
            print(f"  {label} -> {mid}")
        print()
        print("Models your Groq API key can actually use right now:")
        for m in available:
            print(f"  {m}")
        print()
        print("Fix: rerun with --groq-llama-model and/or --groq-qwen-model set to one")
        print("of the IDs listed above, e.g.:")
        print("  python run_local_pilot.py ... --groq-llama-model <id> --groq-qwen-model <id>")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-meta", default=str(Path(__file__).resolve().parents[1] / "corpus" / "chunk_meta.jsonl"))
    parser.add_argument("--embeddings", default=str(Path(__file__).resolve().parents[1] / "corpus" / "embeddings.npy"))
    parser.add_argument("--query-ids", nargs="+", default=["L01", "L02", "L03"])
    parser.add_argument("--providers", nargs="+", default=["groq_llama", "groq_qwen"])
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--groq-llama-model", default=DEFAULT_GROQ_MODELS["groq_llama"])
    parser.add_argument("--groq-qwen-model", default=DEFAULT_GROQ_MODELS["groq_qwen"])
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="print the models available on your Groq account and exit",
    )
    args = parser.parse_args()

    if args.list_models:
        for m in list_available_groq_models():
            print(m)
        return

    groq_models = {
        "groq_llama": args.groq_llama_model,
        "groq_qwen": args.groq_qwen_model,
    }
    needed = {p: groq_models[p] for p in args.providers if p in groq_models}
    validate_models(needed)

    RESULTS_DIR.mkdir(exist_ok=True)
    CHARTS_DIR.mkdir(exist_ok=True)
    db_path = str(RESULTS_DIR / "results.db")

    meta, embeddings = load_corpus(args.chunk_meta, args.embeddings)

    cases = [c for c in LOCAL_BENCHMARK_QUERIES if c["id"] in args.query_ids]
    missing = set(args.query_ids) - {c["id"] for c in cases}
    if missing:
        raise ValueError(f"unknown query ids: {missing}")

    conn = init_db(db_path)
    total = len(cases) * len(args.providers) * args.trials
    done = 0
    for case in cases:
        for provider in args.providers:
            model = groq_models[provider]
            for trial in range(1, args.trials + 1):
                r = run_local_trial(
                    query_id=case["id"],
                    query=case["query"],
                    required_keywords=case["required_keywords"],
                    meta=meta,
                    embeddings=embeddings,
                    groq_model=model,
                    provider_label=provider,
                    trial_num=trial,
                    top_k=args.top_k,
                )
                insert_trial(conn, r)
                done += 1
                print(
                    f"[{done}/{total}] {case['id']} / {provider} / trial {trial} "
                    f"-> papers={r['paper_count']} kw={r['keyword_precision']} "
                    f"latency={r['latency_ms']}ms err={r['error']}"
                )
    conn.close()

    all_rows = load_all_trials(db_path)
    G = build_graph(all_rows)
    add_comparison_edges(G, all_rows)
    graph_path = RESULTS_DIR / "comparison.graphml"
    write_graphml(G, str(graph_path))

    chart_precision_by_provider(all_rows, str(CHARTS_DIR / "precision_by_provider.png"))
    chart_paper_count_variance(all_rows, str(CHARTS_DIR / "paper_count_variance.png"))
    chart_latency_by_provider(all_rows, str(CHARTS_DIR / "latency_by_provider.png"))

    print()
    print(f"Ran {len(cases) * len(args.providers) * args.trials} trials, {len(all_rows)} total in DB.")
    print(f"DB:     {db_path}")
    print(f"Graph:  {graph_path}")
    print(f"Charts: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
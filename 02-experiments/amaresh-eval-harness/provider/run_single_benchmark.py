from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from local_queries import LOCAL_BENCHMARK_QUERIES
from local_retrieval import load_corpus
from local_pipeline import run_local_trial
from ollama_embed import embed_texts
from charts import chart_single_query_deep_comparison

RESULTS_DIR = Path(__file__).parent / "results"
CHARTS_DIR = RESULTS_DIR / "charts"


def resolve_query(args):
    if args.query_id:
        cases = [c for c in LOCAL_BENCHMARK_QUERIES if c["id"] == args.query_id]
        if not cases:
            raise ValueError(f"unknown query id: {args.query_id}")
        return cases[0]["id"], cases[0]["query"], cases[0]["required_keywords"]
    if not args.query:
        raise ValueError("pass --query-id or --query")
    return "custom", args.query, args.required_keywords


def pairwise_similarity_matrix(answers: list[str]):
    non_empty = [a if a.strip() else "EMPTY_ANSWER" for a in answers]
    vecs = embed_texts(non_empty)
    return vecs @ vecs.T


def faithfulness_scores(answers: list[str], contexts: list[str]) -> list[float]:
    safe_answers = [a if a.strip() else "EMPTY_ANSWER" for a in answers]
    safe_contexts = [c if c.strip() else "EMPTY_CONTEXT" for c in contexts]
    n = len(safe_answers)
    combined = safe_answers + safe_contexts
    vecs = embed_texts(combined)
    answer_vecs = vecs[:n]
    context_vecs = vecs[n:]
    return [float(answer_vecs[i] @ context_vecs[i]) for i in range(n)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-meta", default="data/chunk_meta.jsonl")
    parser.add_argument("--embeddings", default="data/embeddings_ollama.npy")
    parser.add_argument("--query-id")
    parser.add_argument("--query")
    parser.add_argument("--required-keywords", nargs="*", default=[])
    parser.add_argument("--groq-model", required=True)
    parser.add_argument("--trials", type=int, default=10)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--out-prefix", default=None)
    args = parser.parse_args()

    qid, query, required_keywords = resolve_query(args)
    meta, embeddings = load_corpus(args.chunk_meta, args.embeddings)
    print(f"corpus loaded: {len(meta)} chunks checked per trial, top_k={args.top_k} retrieved each time")
    print()

    results = []
    for trial in range(1, args.trials + 1):
        r = run_local_trial(
            query_id=qid,
            query=query,
            required_keywords=required_keywords,
            meta=meta,
            embeddings=embeddings,
            groq_model=args.groq_model,
            provider_label=args.groq_model,
            trial_num=trial,
            top_k=args.top_k,
        )
        results.append(r)
        print(
            f"[{trial}/{args.trials}] kw={r['keyword_precision']} "
            f"latency={r['latency_ms']}ms err={r['error']}"
        )

    answers = [r["answer"] for r in results]
    contexts = [r.get("context", "") for r in results]
    sim_matrix = pairwise_similarity_matrix(answers)
    n = sim_matrix.shape[0]
    off_diag = [float(sim_matrix[i, j]) for i in range(n) for j in range(n) if i != j]
    confidence_score = sum(off_diag) / len(off_diag) if off_diag else 0.0

    ground_scores = faithfulness_scores(answers, contexts)
    for r, g in zip(results, ground_scores):
        r["groundedness"] = round(g, 4)
        print(f"trial {r['trial_num']}: groundedness={g:.4f} keyword_precision={r['keyword_precision']}")

    precisions = [r["keyword_precision"] for r in results]
    precision_mean = sum(precisions) / len(precisions)
    precision_std = (sum((p - precision_mean) ** 2 for p in precisions) / len(precisions)) ** 0.5

    ground_mean = sum(ground_scores) / len(ground_scores)
    ground_std = (sum((g - ground_mean) ** 2 for g in ground_scores) / len(ground_scores)) ** 0.5

    RESULTS_DIR.mkdir(exist_ok=True)
    CHARTS_DIR.mkdir(exist_ok=True)
    prefix = args.out_prefix or qid

    json_path = RESULTS_DIR / f"single_{prefix}.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "query_id": qid,
                "query": query,
                "provider": args.groq_model,
                "trials": args.trials,
                "corpus_size_checked": len(meta),
                "top_k_retrieved_per_trial": args.top_k,
                "chunk_meta_path": args.chunk_meta,
                "embeddings_path": args.embeddings,
                "keyword_precision_mean": round(precision_mean, 3),
                "keyword_precision_std": round(precision_std, 3),
                "groundedness_mean": round(ground_mean, 4),
                "groundedness_std": round(ground_std, 4),
                "confidence_score": round(confidence_score, 3),
                "results": results,
                "similarity_matrix": sim_matrix.tolist(),
            },
            f,
            indent=2,
        )

    chart_path = CHARTS_DIR / f"single_{prefix}_deep.png"
    chart_single_query_deep_comparison(
        precisions=precisions,
        faithfulness_scores=ground_scores,
        sim_matrix=sim_matrix,
        confidence_score=confidence_score,
        query_id=qid,
        provider=args.groq_model,
        out_path=str(chart_path),
    )

    print()
    print(f"keyword_precision: mean={precision_mean:.3f} std={precision_std:.3f}")
    print(f"groundedness:      mean={ground_mean:.4f} std={ground_std:.4f}")
    print(f"confidence_score (avg pairwise answer similarity): {confidence_score:.3f}")
    print(f"JSON:  {json_path}")
    print(f"Chart: {chart_path}")


if __name__ == "__main__":
    main()

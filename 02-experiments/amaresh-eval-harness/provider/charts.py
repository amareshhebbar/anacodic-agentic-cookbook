from __future__ import annotations

from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def chart_precision_by_provider(rows: list[dict], out_path: str) -> None:
    by_provider = defaultdict(list)
    for r in rows:
        by_provider[r["provider"]].append(r["keyword_precision"] or 0.0)

    providers = sorted(by_provider)
    means = [sum(by_provider[p]) / len(by_provider[p]) for p in providers]
    stds = [
        (sum((x - m) ** 2 for x in by_provider[p]) / len(by_provider[p])) ** 0.5
        for p, m in zip(providers, means)
    ]

    plt.figure(figsize=(6, 4))
    plt.bar(providers, means, yerr=stds, capsize=5)
    plt.ylabel("keyword precision")
    plt.title("Keyword precision by provider (mean +/- stdev across trials)")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def chart_keyword_gap_by_query(rows: list[dict], out_path: str) -> None:
    by_query_provider = defaultdict(list)
    for r in rows:
        key = (r.get("query_id", "unknown"), r["provider"])
        by_query_provider[key].append(r["keyword_precision"] or 0.0)

    query_ids = sorted({r.get("query_id", "unknown") for r in rows})
    providers = sorted({r["provider"] for r in rows})

    means = {}
    stds = {}
    for qid in query_ids:
        for p in providers:
            vals = by_query_provider.get((qid, p), [])
            if vals:
                m = sum(vals) / len(vals)
                s = (sum((x - m) ** 2 for x in vals) / len(vals)) ** 0.5
            else:
                m, s = 0.0, 0.0
            means[(qid, p)] = m
            stds[(qid, p)] = s

    n_providers = len(providers)
    bar_width = 0.8 / max(n_providers, 1)
    x = list(range(len(query_ids)))

    plt.figure(figsize=(9, 5))
    plt.axhline(1.0, color="green", linestyle="--", linewidth=1.5, label="Ideal (ground truth)")

    for i, p in enumerate(providers):
        offsets = [xi + (i - (n_providers - 1) / 2) * bar_width for xi in x]
        heights = [means[(qid, p)] for qid in query_ids]
        errs = [stds[(qid, p)] for qid in query_ids]
        plt.bar(offsets, heights, width=bar_width, yerr=errs, capsize=4, label=p)

    plt.xticks(x, query_ids)
    plt.ylim(0, 1.15)
    plt.ylabel("keyword precision (1.0 = matches ideal answer)")
    plt.title("Gap between AI answer and ideal answer, per query and provider")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def chart_paper_count_variance(rows: list[dict], out_path: str) -> None:
    by_query = defaultdict(list)
    for r in rows:
        by_query[r["query_id"]].append(r["paper_count"] or 0)

    queries = sorted(by_query)
    plt.figure(figsize=(8, 4))
    plt.boxplot([by_query[q] for q in queries], tick_labels=queries)
    plt.ylabel("paper_count")
    plt.title("Paper count spread across trials, per query")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def chart_single_query_consistency(
    precisions: list[float],
    sim_matrix,
    confidence_score: float,
    query_id: str,
    provider: str,
    out_path: str,
) -> None:
    n = len(precisions)
    mean_p = sum(precisions) / n if n else 0.0
    trials = list(range(1, n + 1))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(trials, precisions, color="#4C72B0")
    axes[0].axhline(mean_p, color="black", linestyle="--", linewidth=1, label=f"mean={mean_p:.2f}")
    axes[0].axhline(1.0, color="green", linestyle=":", linewidth=1, label="ideal")
    axes[0].set_xticks(trials)
    axes[0].set_xlabel("trial")
    axes[0].set_ylabel("keyword precision")
    axes[0].set_ylim(0, 1.15)
    axes[0].set_title(f"{query_id} / {provider}\nkeyword precision per trial")
    axes[0].legend()

    idx = list(range(n))
    im = axes[1].imshow(sim_matrix, vmin=0, vmax=1, cmap="viridis")
    axes[1].set_xticks(idx)
    axes[1].set_yticks(idx)
    axes[1].set_xticklabels([str(t) for t in trials])
    axes[1].set_yticklabels([str(t) for t in trials])
    axes[1].set_xlabel("trial")
    axes[1].set_ylabel("trial")
    axes[1].set_title(f"answer-to-answer similarity\nconfidence score = {confidence_score:.3f}")
    fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def chart_single_query_deep_comparison(
    precisions: list[float],
    faithfulness_scores: list[float],
    sim_matrix,
    confidence_score: float,
    query_id: str,
    provider: str,
    out_path: str,
) -> None:
    n = len(precisions)
    mean_p = sum(precisions) / n if n else 0.0
    mean_f = sum(faithfulness_scores) / n if n else 0.0
    trials = list(range(1, n + 1))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))

    axes[0].bar(trials, precisions, color="#4C72B0")
    axes[0].axhline(mean_p, color="black", linestyle="--", linewidth=1, label=f"mean={mean_p:.2f}")
    axes[0].axhline(1.0, color="green", linestyle=":", linewidth=1, label="ideal")
    axes[0].set_xticks(trials)
    axes[0].set_xlabel("trial")
    axes[0].set_ylabel("keyword precision")
    axes[0].set_ylim(0, 1.15)
    axes[0].set_title("keyword precision per trial")
    axes[0].legend()

    axes[1].plot(trials, faithfulness_scores, marker="o", color="#DD8452")
    axes[1].axhline(mean_f, color="black", linestyle="--", linewidth=1, label=f"mean={mean_f:.3f}")
    axes[1].set_xticks(trials)
    axes[1].set_xlabel("trial")
    axes[1].set_ylabel("answer-to-evidence similarity")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("groundedness score per trial\n(answer vs retrieved evidence)")
    axes[1].legend()

    idx = list(range(n))
    im = axes[2].imshow(sim_matrix, vmin=0, vmax=1, cmap="viridis")
    axes[2].set_xticks(idx)
    axes[2].set_yticks(idx)
    axes[2].set_xticklabels([str(t) for t in trials])
    axes[2].set_yticklabels([str(t) for t in trials])
    axes[2].set_xlabel("trial")
    axes[2].set_ylabel("trial")
    axes[2].set_title(f"answer-to-answer similarity\nconfidence = {confidence_score:.3f}")
    fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04)

    fig.suptitle(f"{query_id} / {provider} — deep comparison across {n} trials")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def chart_latency_by_provider(rows: list[dict], out_path: str) -> None:
    by_provider = defaultdict(list)
    for r in rows:
        by_provider[r["provider"]].append(r["latency_ms"] or 0)

    providers = sorted(by_provider)
    plt.figure(figsize=(6, 4))
    plt.boxplot([by_provider[p] for p in providers], tick_labels=providers)
    plt.ylabel("latency_ms")
    plt.title("Retrieval latency by provider")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
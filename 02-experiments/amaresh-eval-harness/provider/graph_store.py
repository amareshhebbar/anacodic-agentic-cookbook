from __future__ import annotations

from collections import defaultdict

import networkx as nx


def build_graph(rows: list[dict]) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    for r in rows:
        qnode = f"query:{r.get('query_id', 'unknown')}"
        pnode = f"provider:{r['provider']}"
        tnode = f"trial:{r['trial_id']}"

        G.add_node(qnode, type="query", label=r.get("query_id", "unknown"))
        G.add_node(pnode, type="provider", label=r["provider"])
        G.add_node(
            tnode,
            type="trial",
            paper_count=r.get("paper_count", 0) or 0,
            keyword_precision=r.get("keyword_precision", 0.0) or 0.0,
            latency_ms=r.get("latency_ms", 0) or 0,
            trial_num=r.get("trial_num", 0),
            error=str(r.get("error") or ""),
        )

        G.add_edge(qnode, tnode, relation="tested_in")
        G.add_edge(tnode, pnode, relation="ran_on")

    return G


def add_comparison_edges(G: nx.MultiDiGraph, rows: list[dict]) -> None:
    by_query_provider = defaultdict(list)
    for r in rows:
        key = (r.get("query_id", "unknown"), r["provider"])
        by_query_provider[key].append(r.get("keyword_precision", 0.0) or 0.0)

    by_query = defaultdict(dict)
    for (qid, provider), vals in by_query_provider.items():
        by_query[qid][provider] = sum(vals) / len(vals)

    for qid, provider_scores in by_query.items():
        providers = sorted(provider_scores)
        for i in range(len(providers)):
            for j in range(i + 1, len(providers)):
                a, b = providers[i], providers[j]
                diff = provider_scores[a] - provider_scores[b]
                winner = a if diff > 0 else (b if diff < 0 else "tie")
                G.add_edge(
                    f"provider:{a}",
                    f"provider:{b}",
                    relation="compared_on",
                    query_id=qid,
                    metric="keyword_precision",
                    score_a=provider_scores[a],
                    score_b=provider_scores[b],
                    diff=diff,
                    winner=winner,
                )


def write_graphml(G: nx.MultiDiGraph, path: str) -> None:
    nx.write_graphml(G, path)
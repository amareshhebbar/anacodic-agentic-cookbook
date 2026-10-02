from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ollama_embed import embed_query as ollama_embed_query


def load_corpus(chunk_meta_path: str | Path, embeddings_path: str | Path):
    meta = []
    with open(chunk_meta_path) as f:
        for line in f:
            line = line.strip()
            if line:
                meta.append(json.loads(line))
    embeddings = np.load(embeddings_path)
    if embeddings.shape[0] != len(meta):
        raise ValueError(
            f"embeddings rows ({embeddings.shape[0]}) != chunk_meta rows ({len(meta)})"
        )
    return meta, embeddings


def search(
    query: str,
    meta: list[dict],
    embeddings: np.ndarray,
    top_k: int = 8,
) -> list[dict]:
    qvec = ollama_embed_query(query)
    sims = embeddings @ qvec
    top_idx = np.argsort(-sims)[:top_k]
    results = []
    for i in top_idx:
        c = meta[i]
        results.append(
            {
                "chunk_id": c["chunk_id"],
                "paper_slug": c["paper_slug"],
                "section_path": c.get("section_path", ""),
                "text": c.get("text", ""),
                "score": float(sims[i]),
                "chunk_type": c.get("chunk_type", ""),
            }
        )
    return results
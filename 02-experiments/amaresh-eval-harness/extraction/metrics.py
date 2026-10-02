from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

DOI_RE = re.compile(r'10\.\d{4,9}/[^\s"<>]+')
SUSPICIOUS_GLYPH_RE = re.compile(r'[\u00de\u00df\u00dd\u00a4\u00a7\u00b6\ufffd]| Y (?=\d)')
EMPTY_CHUNK_MIN_CHARS = 20
NEAR_DUP_COSINE = 0.995


def load_chunks(chunk_meta_path: str | Path) -> list[dict]:
    chunks = []
    with open(chunk_meta_path) as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def group_by_paper(chunks: list[dict]) -> dict[str, list[dict]]:
    papers = defaultdict(list)
    for c in chunks:
        papers[c["paper_slug"]].append(c)
    return papers


def check_page_coverage(papers: dict[str, list[dict]]) -> dict:
    gaps = {}
    for slug, chunks in papers.items():
        pages = sorted(set(p for c in chunks for p in c.get("pages", [])))
        if not pages:
            continue
        expected = set(range(pages[0], pages[-1] + 1))
        missing = sorted(expected - set(pages))
        if missing:
            gaps[slug] = {"pages_present": pages, "pages_missing": missing}
    return {
        "papers_checked": len(papers),
        "papers_with_gaps": len(gaps),
        "detail": gaps,
    }


def check_empty_chunks(chunks: list[dict]) -> dict:
    empty = [c for c in chunks if len(c.get("text", "").strip()) < EMPTY_CHUNK_MIN_CHARS]
    return {
        "total_chunks": len(chunks),
        "empty_chunks": len(empty),
        "empty_ratio": round(len(empty) / len(chunks), 4) if chunks else 0.0,
        "examples": [
            {"chunk_id": c["chunk_id"], "text": c["text"][:50]} for c in empty[:10]
        ],
    }


def check_context_injection(chunks: list[dict]) -> dict:
    bad = [c for c in chunks if len(c.get("embed_text", "")) < len(c.get("text", ""))]
    return {
        "total_chunks": len(chunks),
        "chunks_with_shrunk_embed_text": len(bad),
        "examples": [c["chunk_id"] for c in bad[:10]],
    }


def extract_dois(papers: dict[str, list[dict]]) -> dict[str, list[str]]:
    doi_map = {}
    for slug, chunks in papers.items():
        found = set()
        for c in chunks:
            for m in DOI_RE.findall(c.get("text", "")):
                found.add(m.rstrip(".,);"))
        doi_map[slug] = sorted(found)
    return doi_map


def check_suspicious_glyphs(chunks: list[dict]) -> dict:
    total_hits = 0
    examples = []
    for c in chunks:
        matches = SUSPICIOUS_GLYPH_RE.findall(c.get("text", ""))
        if matches:
            total_hits += len(matches)
            if len(examples) < 15:
                m = SUSPICIOUS_GLYPH_RE.search(c["text"])
                snippet = c["text"][max(0, m.start() - 30):m.start() + 30]
                examples.append({"chunk_id": c["chunk_id"], "snippet": snippet})
    return {"total_hits": total_hits, "examples": examples}


def check_table_structure(chunks: list[dict]) -> dict:
    tables = [c for c in chunks if c.get("is_table")]
    missing_md = [c for c in tables if not c.get("table_md", "").strip()]
    missing_cells = [c for c in tables if not c.get("table_cells")]
    missing_otsl = [c for c in tables if not c.get("table_otsl", "").strip()]

    cells_status = defaultdict(int)
    for c in tables:
        cells_status[c.get("table_cells_status", "missing")] += 1

    row_count_mismatches = []
    for c in tables:
        td = c.get("table_data", {})
        n_rows_data = len(td.get("rows", []))
        n_rows_field = c.get("table_n_data_rows")
        if n_rows_field is not None and n_rows_data and abs(n_rows_data - n_rows_field) > 1:
            row_count_mismatches.append(c["chunk_id"])

    return {
        "total_table_chunks": len(tables),
        "missing_table_md": len(missing_md),
        "missing_table_cells": len(missing_cells),
        "missing_table_otsl": len(missing_otsl),
        "table_cells_status": dict(cells_status),
        "row_count_mismatches": len(row_count_mismatches),
        "row_count_mismatch_examples": row_count_mismatches[:10],
        "examples_missing_structure": [
            {"chunk_id": c["chunk_id"], "text": c["text"][:150]} for c in missing_md[:5]
        ],
    }


def check_duplicate_chunks(papers: dict[str, list[dict]], prefix_len: int = 300) -> dict:
    seen = {}
    dup_pairs = []
    for chunks in papers.values():
        for c in chunks:
            key = c["text"].strip()[:prefix_len]
            if key and key in seen:
                dup_pairs.append((seen[key], c["chunk_id"]))
            else:
                seen[key] = c["chunk_id"]
    return {"duplicate_pairs": len(dup_pairs), "examples": dup_pairs[:10]}


def check_section_distribution(chunks: list[dict]) -> dict:
    sections = defaultdict(int)
    for c in chunks:
        sections[c.get("section_path", "")[:60]] += 1
    ranked = sorted(sections.items(), key=lambda x: -x[1])
    empty_sections = sum(n for s, n in sections.items() if not s.strip())
    return {
        "unique_sections": len(sections),
        "empty_section_path_chunks": empty_sections,
        "top_sections": ranked[:15],
    }


def embedding_health(embeddings: np.ndarray) -> dict:
    norms = np.linalg.norm(embeddings, axis=1)
    return {
        "shape": list(embeddings.shape),
        "nan_count": int(np.isnan(embeddings).sum()),
        "zero_norm_vectors": int((norms < 1e-6).sum()),
        "norm_mean": float(norms.mean()),
        "norm_std": float(norms.std()),
    }


def embedding_semantic_locality(
    embeddings: np.ndarray, chunks: list[dict], seed: int = 0, samples: int = 500
) -> dict:
    papers = group_by_paper(chunks)
    idx_by_slug = defaultdict(list)
    for i, c in enumerate(chunks):
        idx_by_slug[c["paper_slug"]].append(i)

    rng = np.random.default_rng(seed)
    within = []
    for slug, idxs in idx_by_slug.items():
        if len(idxs) < 2:
            continue
        for _ in range(min(20, len(idxs))):
            i, j = rng.choice(idxs, 2, replace=False)
            within.append(float(embeddings[i] @ embeddings[j]))

    all_idx = np.arange(len(chunks))
    across = []
    attempts = 0
    while len(across) < samples and attempts < samples * 10:
        i, j = rng.choice(all_idx, 2, replace=False)
        attempts += 1
        if chunks[i]["paper_slug"] != chunks[j]["paper_slug"]:
            across.append(float(embeddings[i] @ embeddings[j]))

    within_arr = np.array(within) if within else np.array([0.0])
    across_arr = np.array(across) if across else np.array([0.0])
    return {
        "within_paper_cosine_mean": float(within_arr.mean()),
        "across_paper_cosine_mean": float(across_arr.mean()),
        "separation": float(within_arr.mean() - across_arr.mean()),
    }


def embedding_near_duplicates(
    embeddings: np.ndarray, chunks: list[dict], threshold: float = NEAR_DUP_COSINE
) -> dict:
    idx_by_slug = defaultdict(list)
    for i, c in enumerate(chunks):
        idx_by_slug[c["paper_slug"]].append(i)

    pairs = []
    for slug, idxs in idx_by_slug.items():
        sub = embeddings[idxs]
        sims = sub @ sub.T
        n = len(idxs)
        for a in range(n):
            for b in range(a + 1, n):
                if sims[a, b] > threshold:
                    pairs.append(
                        {
                            "paper_slug": slug,
                            "chunk_a": chunks[idxs[a]]["chunk_id"],
                            "chunk_b": chunks[idxs[b]]["chunk_id"],
                            "cosine": float(sims[a, b]),
                        }
                    )
    return {"near_duplicate_pairs": len(pairs), "examples": pairs[:10]}


def run_structural_and_embedding_checks(
    chunk_meta_path: str | Path, embeddings_path: str | Path
) -> dict:
    chunks = load_chunks(chunk_meta_path)
    papers = group_by_paper(chunks)
    embeddings = np.load(embeddings_path)

    return {
        "n_papers": len(papers),
        "n_chunks": len(chunks),
        "page_coverage": check_page_coverage(papers),
        "empty_chunks": check_empty_chunks(chunks),
        "context_injection": check_context_injection(chunks),
        "dois_by_paper": extract_dois(papers),
        "suspicious_glyphs": check_suspicious_glyphs(chunks),
        "table_structure": check_table_structure(chunks),
        "duplicate_chunks": check_duplicate_chunks(papers),
        "section_distribution": check_section_distribution(chunks),
        "embedding_health": embedding_health(embeddings),
        "embedding_semantic_locality": embedding_semantic_locality(embeddings, chunks),
        "embedding_near_duplicates": embedding_near_duplicates(embeddings, chunks),
    }
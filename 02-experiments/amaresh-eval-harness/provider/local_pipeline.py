from __future__ import annotations

import re
import time
import uuid

from groq import Groq

from local_retrieval import search

MAX_ANSWER_TOKENS = 500
MAX_RETRIES = 4

SYNTHESIS_PROMPT = """You are a plastic surgery evidence assistant. Answer the clinical \
question using ONLY the evidence excerpts below. Cite which excerpt(s) support each claim.

Question: {query}

Evidence:
{context}

Give a concise, cited answer."""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] ({c['paper_slug']}) {c['text'][:800]}")
    return "\n\n".join(parts)


def run_local_trial(
    query_id: str,
    query: str,
    required_keywords: list[str],
    meta: list[dict],
    embeddings,
    groq_model: str,
    provider_label: str,
    trial_num: int,
    top_k: int = 8,
) -> dict:
    groq_client = Groq()

    t0 = time.monotonic()
    error = None
    answer = ""
    retrieved = []
    try:
        retrieved = search(query, meta, embeddings, top_k=top_k)
        context = build_context(retrieved)
        prompt = SYNTHESIS_PROMPT.format(query=query, context=context)
        for attempt in range(MAX_RETRIES):
            try:
                resp = groq_client.chat.completions.create(
                    model=groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=MAX_ANSWER_TOKENS,
                )
                answer = resp.choices[0].message.content or ""
                break
            except Exception as exc:
                msg = str(exc)
                is_rate_limit = "rate_limit_exceeded" in msg or "429" in msg
                if is_rate_limit and attempt < MAX_RETRIES - 1:
                    wait_match = re.search(r"try again in ([\d.]+)s", msg)
                    wait_s = float(wait_match.group(1)) if wait_match else 20.0
                    time.sleep(min(wait_s, 60.0) + 1.0)
                    continue
                raise
    except Exception as exc:
        error = str(exc)

    latency_ms = int((time.monotonic() - t0) * 1000)

    all_text = (answer + " " + " ".join(c["text"] for c in retrieved)).lower()
    keywords_found = [kw for kw in required_keywords if kw.lower() in all_text]
    keyword_precision = (
        len(keywords_found) / len(required_keywords) if required_keywords else 0.0
    )

    return {
        "trial_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "query_id": query_id,
        "query": query,
        "provider": provider_label,
        "trial_num": trial_num,
        "paper_count": len(set(c["paper_slug"] for c in retrieved)),
        "latency_ms": latency_ms,
        "wall_time_ms": latency_ms,
        "keyword_precision": round(keyword_precision, 3),
        "keywords_found": keywords_found,
        "keywords_missing": [kw for kw in required_keywords if kw not in keywords_found],
        "papers_meeting_min_evidence": len(retrieved),
        "avg_rcs_score": 0.0,
        "avg_citation_count": 0.0,
        "answer": answer,
        "retrieved_chunk_ids": [c["chunk_id"] for c in retrieved],
        "context": " ".join(c["text"] for c in retrieved),
        "corpus_size_checked": len(meta),
        "top_k": top_k,
        "retrieved_chunks": [
            {
                "chunk_id": c["chunk_id"],
                "paper_slug": c["paper_slug"],
                "section_path": c.get("section_path", ""),
                "chunk_type": c.get("chunk_type", ""),
                "similarity_score": round(c["score"], 4),
                "text_preview": c["text"][:300],
            }
            for c in retrieved
        ],
        "error": error,
    }

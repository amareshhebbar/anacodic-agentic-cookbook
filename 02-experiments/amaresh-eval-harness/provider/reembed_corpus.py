from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ollama_embed import embed_texts, EMBED_MODEL


def load_chunks(path: str) -> list[dict]:
    meta = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                meta.append(json.loads(line))
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-meta", default="data/chunk_meta.jsonl")
    parser.add_argument("--out", default="data/embeddings_ollama.npy")
    parser.add_argument("--model", default=EMBED_MODEL)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    meta = load_chunks(args.chunk_meta)
    texts = [c.get("embed_text") or c.get("text", "") for c in meta]

    all_vecs = []
    for i in range(0, len(texts), args.batch_size):
        batch = texts[i : i + args.batch_size]
        vecs = embed_texts(batch, model=args.model)
        all_vecs.append(vecs)
        print(f"embedded {min(i + args.batch_size, len(texts))}/{len(texts)}")

    result = np.vstack(all_vecs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out, result)
    print(f"wrote {args.out}  shape={result.shape}")


if __name__ == "__main__":
    main()
from __future__ import annotations

import numpy as np
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"


def embed_texts(texts: list[str], model: str = EMBED_MODEL, base_url: str = OLLAMA_BASE_URL) -> np.ndarray:
    resp = requests.post(
        f"{base_url}/api/embed",
        json={"model": model, "input": texts},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    vecs = np.array(data["embeddings"], dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def embed_query(query: str, model: str = EMBED_MODEL, base_url: str = OLLAMA_BASE_URL) -> np.ndarray:
    return embed_texts([query], model=model, base_url=base_url)[0]
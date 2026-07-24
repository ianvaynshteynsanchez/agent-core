"""Embeddings with a local-first strategy.

Ollama (all-minilm, 384 dims) matches the Pinecone index and has no quota.
Falls back to Cohere if Ollama isn't running.
"""
import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "all-minilm")
_backend = None


def _ollama_up():
    try:
        return requests.get(f"{OLLAMA_URL}/api/version", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def backend():
    global _backend
    if _backend is None:
        _backend = "ollama" if _ollama_up() else "cohere"
        print(f"[embeddings] using {_backend}")
    return _backend


def _ollama_embed(text):
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": OLLAMA_MODEL, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def _cohere():
    import cohere
    from app.config import COHERE_API_KEY
    return cohere.Client(COHERE_API_KEY)


def embed_documents(texts):
    if backend() == "ollama":
        return [_ollama_embed(t) for t in texts]
    from app.config import EMBED_MODEL
    return _cohere().embed(texts=texts, model=EMBED_MODEL,
                           input_type="search_document").embeddings


def embed_query(text):
    if backend() == "ollama":
        return _ollama_embed(text)
    from app.config import EMBED_MODEL
    return _cohere().embed(texts=[text], model=EMBED_MODEL,
                           input_type="search_query").embeddings[0]

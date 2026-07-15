from app.clients.embeddings import embed_query
from app.clients.vectorstore import query
from app.config import DEFAULT_NAMESPACE


def retrieve(question, top_k=5, namespace=DEFAULT_NAMESPACE):
    vec = embed_query(question)
    res = query(vec, top_k=top_k, namespace=namespace)
    return [
        {
            "score": m.score,
            "source": m.metadata.get("source"),
            "text": m.metadata.get("text", ""),
        }
        for m in res.matches
    ]


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "What are the eligibility requirements?"
    for hit in retrieve(q):
        print(f"\n[{hit['score']:.3f}] {hit['source']}")
        print(hit["text"][:300], "...")

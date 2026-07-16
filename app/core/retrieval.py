from app.clients.embeddings import embed_query
from app.clients.vectorstore import index
from app.clients.rerank import rerank
from app.config import DEFAULT_NAMESPACE


def retrieve(question, top_k=5, namespace=DEFAULT_NAMESPACE, source=None,
             candidates=50, use_rerank=True):
    vec = embed_query(question)
    kwargs = {
        "vector": vec,
        "top_k": candidates if use_rerank else top_k,
        "namespace": namespace,
        "include_metadata": True,
    }
    if source:
        kwargs["filter"] = {"source": {"$eq": source}}
    res = index.query(**kwargs)

    hits = [
        {
            "score": m.score,
            "source": m.metadata.get("source"),
            "text": m.metadata.get("text", ""),
        }
        for m in res.matches
    ]
    if not use_rerank or not hits:
        return hits[:top_k]

    ranked = rerank(question, [h["text"] for h in hits], top_n=top_k)
    out = []
    for idx, rel in ranked:
        hit = dict(hits[idx])
        hit["vector_score"] = hit.pop("score")
        hit["score"] = rel
        out.append(hit)
    return out


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    source = None
    use_rerank = True
    if args and args[0] == "--no-rerank":
        use_rerank = False
        args = args[1:]
    if args and args[0] == "--source":
        source = args[1]
        args = args[2:]
    q = " ".join(args) or "What are the eligibility requirements?"

    for hit in retrieve(q, source=source, use_rerank=use_rerank):
        v = hit.get("vector_score")
        tag = f"[rerank {hit['score']:.3f} | vec {v:.3f}]" if v else f"[{hit['score']:.3f}]"
        print(f"\n{tag} {hit['source']}")
        print(hit["text"][:300], "...")

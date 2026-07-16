import cohere
from app.config import COHERE_API_KEY

client = cohere.Client(COHERE_API_KEY)
RERANK_MODEL = "rerank-english-v3.0"


def rerank(query, docs, top_n=5):
    """docs = list of strings. Returns [(index, relevance_score), ...]."""
    if not docs:
        return []
    res = client.rerank(
        model=RERANK_MODEL,
        query=query,
        documents=docs,
        top_n=min(top_n, len(docs)),
    )
    return [(r.index, r.relevance_score) for r in res.results]

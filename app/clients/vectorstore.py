from pinecone import Pinecone
from app.config import PINECONE_API_KEY, PINECONE_INDEX, DEFAULT_NAMESPACE

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def upsert(vectors, namespace=DEFAULT_NAMESPACE):
    """vectors = list of (id, embedding, metadata) tuples."""
    index.upsert(vectors=vectors, namespace=namespace)


def query(embedding, top_k=5, namespace=DEFAULT_NAMESPACE):
    """Return the top_k most similar chunks."""
    return index.query(
        vector=embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )

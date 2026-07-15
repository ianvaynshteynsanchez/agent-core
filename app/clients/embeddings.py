import cohere
from app.config import COHERE_API_KEY, EMBED_MODEL

client = cohere.Client(COHERE_API_KEY)


def embed_documents(texts):
    """Embed chunks that will be stored in the vector DB."""
    resp = client.embed(
        texts=texts,
        model=EMBED_MODEL,
        input_type="search_document",
    )
    return resp.embeddings


def embed_query(text):
    """Embed a user question for searching."""
    resp = client.embed(
        texts=[text],
        model=EMBED_MODEL,
        input_type="search_query",
    )
    return resp.embeddings[0]

import sys
sys.path.insert(0, ".")

from app.clients.embeddings import embed_query
from app.clients.vectorstore import index
from app.clients.llm import generate


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except Exception as e:
        print(f"FAIL  {name}: {e}")


check("Cohere embeddings", lambda: embed_query("hello world"))
check("Pinecone index", lambda: index.describe_index_stats())
check("Groq LLM", lambda: generate("Say the word: ok"))

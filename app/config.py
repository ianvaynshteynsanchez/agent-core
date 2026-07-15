import os
from dotenv import load_dotenv

load_dotenv()

# --- API keys (from .env, never hardcoded) ---
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Model + index settings ---
EMBED_MODEL = os.getenv("EMBED_MODEL", "embed-english-light-v3.0")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "agent-core")

# --- The config-seam value that keeps clients isolated later ---
DEFAULT_NAMESPACE = os.getenv("DEFAULT_NAMESPACE", "default")

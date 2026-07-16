import os
import time
import unicodedata
from pypdf import PdfReader
from app.clients.embeddings import embed_documents
from app.clients.vectorstore import upsert
from app.config import DEFAULT_NAMESPACE

DATA_DIR = "data"
CHUNK_SIZE = 450
OVERLAP = 80
BATCH = 48
PAUSE = 20


def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    return text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')


def read_file(path):
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        raw = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
    return normalize(raw)


def chunk_text(text):
    text = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks


def embed_with_retry(batch, tries=5):
    for attempt in range(tries):
        try:
            return embed_documents(batch)
        except Exception as e:
            if "429" not in str(e) and "rate limit" not in str(e).lower():
                raise
            wait = 30 * (attempt + 1)
            print(f"  rate limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("still rate limited after retries")


def ingest(namespace=DEFAULT_NAMESPACE):
    total = 0
    for name in sorted(os.listdir(DATA_DIR)):
        if not name.endswith((".pdf", ".txt")):
            continue
        path = os.path.join(DATA_DIR, name)
        chunks = chunk_text(read_file(path))
        print(f"{name}: {len(chunks)} chunks")

        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            vectors = embed_with_retry(batch)
            records = [
                (
                    f"{name}-{i + j}",
                    vec,
                    {"source": name, "chunk": i + j, "text": batch[j]},
                )
                for j, vec in enumerate(vectors)
            ]
            upsert(records, namespace=namespace)
            total += len(records)
            print(f"  {total} chunks done")
            time.sleep(PAUSE)

    print(f"Done. {total} chunks upserted to namespace '{namespace}'.")


if __name__ == "__main__":
    ingest()

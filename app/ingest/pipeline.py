import os
from pypdf import PdfReader
from app.clients.embeddings import embed_documents
from app.clients.vectorstore import upsert
from app.config import DEFAULT_NAMESPACE

DATA_DIR = "data"
CHUNK_SIZE = 1000
OVERLAP = 150
BATCH = 90


def read_file(path):
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk_text(text):
    text = " ".join(text.split())
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks


def ingest(namespace=DEFAULT_NAMESPACE):
    total = 0
    for name in sorted(os.listdir(DATA_DIR)):
        if not name.endswith((".pdf", ".txt")):
            continue
        path = os.path.join(DATA_DIR, name)
        text = read_file(path)
        chunks = chunk_text(text)
        print(f"{name}: {len(chunks)} chunks")

        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            vectors = embed_documents(batch)
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

    print(f"Done. {total} chunks upserted to namespace '{namespace}'.")


if __name__ == "__main__":
    ingest()

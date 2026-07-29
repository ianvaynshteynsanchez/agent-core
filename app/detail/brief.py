"""Answer standard NOFO questions against full announcement text, with sources.

This is where the retrieval stack earns its keep: chunk the announcement,
embed it into a per-opportunity namespace, then retrieve + rerank for each
question so answers are grounded and citable rather than inferred from a stub.
"""
import json
from datetime import datetime, timezone

from app.clients.embeddings import embed_documents
from app.clients.llm import client
from app.clients.vectorstore import index
from app.config import LLM_MODEL
from app.core.retrieval import retrieve
from app.db.store import connect
from app.detail.fetch import fetch_full_text
from app.ingest.pipeline import chunk_text

QUESTIONS = [
    ("eligibility", "What organizations are eligible to apply? Are small businesses eligible? Any restrictions on foreign organizations?"),
    ("budget", "What is the award budget limit or ceiling? What is the maximum project period?"),
    ("deadlines", "In the Key Dates section, what are the application due dates for new applications? Give only the application due date(s), not review dates, council dates, or earliest start dates."),
    ("scope", "What kinds of projects does this fund? What is explicitly out of scope or non-responsive?"),
]

ANSWER_PROMPT = """Answer the question using ONLY the excerpts below from a
federal funding announcement. Be specific and concise - quote figures and dates
exactly. If the excerpts do not contain the answer, say "Not stated in retrieved
sections." Do not infer or guess.

QUESTION: {q}

EXCERPTS:
{ctx}

Answer in 1-3 sentences."""


def namespace_for(opp_id):
    return f"nofo-{opp_id.replace(':', '-')}"


def index_announcement(opp_id, text, batch=48):
    ns = namespace_for(opp_id)
    chunks = chunk_text(text)
    print(f"  indexing {len(chunks)} chunks -> {ns}")
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        vecs = embed_documents(part)
        index.upsert(
            vectors=[(f"{opp_id}-{i+j}", v, {"text": part[j], "source": opp_id})
                     for j, v in enumerate(vecs)],
            namespace=ns,
        )
    return len(chunks)


def answer(question, ns, top_k=5):
    hits = retrieve(question, top_k=top_k, namespace=ns)
    if not hits:
        return "Not stated in retrieved sections.", []
    ctx = "\n\n---\n\n".join(h["text"] for h in hits)
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": ANSWER_PROMPT.format(q=question, ctx=ctx)}],
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip(), hits


def build_brief(opp_id, native_id, reindex=False):
    text, url, status = fetch_full_text(native_id)
    if status != "ok":
        print(f"  {native_id}: {status}")
        return None

    ns = namespace_for(opp_id)
    stats = index.describe_index_stats()
    existing = (stats.namespaces or {}).get(ns)
    if reindex or not existing:
        index_announcement(opp_id, text)

    brief = {"native_id": native_id, "url": url, "answers": {}}
    for key, q in QUESTIONS:
        a, hits = answer(q, ns)
        brief["answers"][key] = {"question": q, "answer": a,
                                 "top_score": hits[0]["score"] if hits else None}
        print(f"  {key:12} {a[:100]}")
    return brief


if __name__ == "__main__":
    conn = connect()
    rows = conn.execute(
        "SELECT o.id, o.native_id, o.title FROM opportunity o "
        "JOIN assessment a ON a.opportunity_id = o.id WHERE a.verdict='pursue'"
    ).fetchall()

    for r in rows:
        print(f"\n{r['native_id']}  {r['title'][:50]}")
        build_brief(r["id"], r["native_id"])
    conn.close()

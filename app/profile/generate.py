import glob
import os
from datetime import datetime, timezone

from app.clients.llm import client
from app.config import LLM_MODEL
from app.db.store import connect

SOURCE_DIR = "data/awards"

PROMPT = """You are building a capability profile for a company that will be used
to judge whether federal funding opportunities are a good fit for them.

Below are public source documents about the company: patents, technology pages,
and other material.

Write a capability profile in markdown with EXACTLY these sections:

## What they build
Concrete technical description. Mechanism, materials, form factors. Be specific.

## What they do NOT do
The most important section. Adjacent capabilities they lack or explicitly avoid.
Infer these from what the sources emphasize and omit. If they reformulate existing
drugs, they do not discover new ones. Be concrete about the boundary.

## Fit criteria
Bullet list. What must a solicitation want for this company to be a real fit?
Frame around capability and modality, not disease area.

## Anti-fit signals
Bullet list. What makes a solicitation look relevant but actually be wrong?
These are the "adjacent but not a good fit" traps.

## Vocabulary
Three sub-lists:
- Internal terms (how the company describes itself)
- Agency terms (how a funding agency would describe the same thing)
- Trap terms (words that match superficially but indicate different technology)

## Open questions
Things you could not determine from the sources that a human should confirm.

Rules:
- Ground every claim in the sources. Do not invent products or partnerships.
- If something is unclear, put it in Open questions rather than guessing.
- Be blunt and specific. Vague profiles produce vague judgments.

SOURCE DOCUMENTS:
{sources}
"""


def load_sources():
    parts = []
    for path in sorted(glob.glob(os.path.join(SOURCE_DIR, "*"))):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            parts.append(f"--- {os.path.basename(path)} ---\n{f.read()}")
    return "\n\n".join(parts)


def generate(save=True, note="v1 from public sources"):
    sources = load_sources()
    if not sources.strip():
        raise SystemExit(f"No source files in {SOURCE_DIR}")

    print(f"sending {len(sources)} chars from {SOURCE_DIR}...")
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": PROMPT.format(sources=sources)}],
        temperature=0.2,
    )
    content = resp.choices[0].message.content
    print(f"tokens: {resp.usage.total_tokens}")

    if save:
        conn = connect()
        row = conn.execute("SELECT MAX(version) v FROM profile").fetchone()
        version = (row["v"] or 0) + 1
        conn.execute(
            "INSERT INTO profile (version, client, content, created_at, note) VALUES (?,?,?,?,?)",
            (version, CLIENT, content, datetime.now(timezone.utc).isoformat(), note),
        )
        conn.commit()
        conn.close()

        os.makedirs("profiles", exist_ok=True)
        out = f"profiles/v{version}.md"
        with open(out, "w") as f:
            f.write(content)
        print(f"saved profile v{version} -> {out}")

    return content


if __name__ == "__main__":
    print(generate())

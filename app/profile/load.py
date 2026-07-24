"""Load the active client profile and derive search config from it.

A profile is a markdown file with a Vocabulary section. The agency terms
become search keywords, the trap terms become exclusions. One document
defines a client.
"""
import os
import re

from app.db.store import connect

CLIENT = os.getenv("CLIENT", "hera")


def active(conn=None):
    """Return (version, markdown) for the current client's newest profile."""
    own = conn is None
    conn = conn or connect()
    row = conn.execute(
        "SELECT version, content FROM profile ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if own:
        conn.close()
    if not row:
        raise SystemExit("No profile found.")
    return row["version"], row["content"]


def _section(md, heading):
    """Pull the body of a '## Heading' section."""
    m = re.search(rf"^##\s*{heading}.*?$(.*?)(?=^##\s|\Z)", md,
                  re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def _terms(block, label):
    """Extract backtick-quoted or bullet terms under a **Label** line."""
    m = re.search(rf"\*\*{label}\*\*.*?$(.*?)(?=\*\*|\Z)", block,
                  re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    chunk = m.group(1)
    terms = re.findall(r"`([^`]+)`", chunk)
    if not terms:
        terms = [t.strip(" -*·\n") for t in re.split(r"[·\n]", chunk)]
    return [t.strip() for t in terms if t.strip() and len(t.strip()) > 2]


def search_keywords(md=None):
    """Broad nets for the API. Falls back to agency terms if none defined."""
    md = md or active()[1]
    vocab = _section(md, "Vocabulary")
    # Search both tiers: broad nets for volume, specific terms for precision.
    seen, terms = set(), []
    for label in ("Search terms", "Agency terms"):
        for t in _terms(vocab, label):
            k = t.strip().strip('"').lower()
            if k and k not in seen:
                seen.add(k)
                terms.append(t)
    out = []
    for t in terms:
        t = t.strip().strip('"')
        out.append(f'"{t}"' if " " in t else t)
    return out


def relevance_terms(md=None):
    """Everything the client's world is described with, broad and specific.
    Short acronyms are kept but matched on word boundaries elsewhere."""
    md = md or active()[1]
    vocab = _section(md, "Vocabulary")
    seen, out = set(), []
    for label in ("Search terms", "Agency terms", "Internal terms"):
        for t in _terms(vocab, label):
            t = t.strip().lower()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def trap_terms(md=None):
    md = md or active()[1]
    return [t.lower() for t in _terms(_section(md, "Vocabulary"), "Trap terms")]


if __name__ == "__main__":
    v, md = active()
    print(f"profile v{v} ({CLIENT})\n")
    print(f"search keywords ({len(search_keywords(md))}):")
    for k in search_keywords(md):
        print(f"  {k}")
    print(f"\nrelevance terms: {len(relevance_terms(md))}")
    print(f"trap terms: {len(trap_terms(md))}")

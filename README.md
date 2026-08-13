# agent-core

An automated agent that reads federal funding announcements and reasons about
whether they fit a specific research program — and, more usefully, explains why
most of them don't.

Tracking tools tell you what exists. This tells you what to ignore, with a
reason you can audit.

![dashboard](docs/dashboard.png)

---

## What it does

A single day's run against a real capability profile:

| Stage | Count |
|---|---|
| Opportunities tracked | 526 |
| Passed the structured relevance gate | 14 |
| Assessed by the reasoning layer | 10 |
| Judged worth pursuing | 1 |

512 opportunities were ruled out before a single token was spent. Of the 10 that
reached the reasoning layer, 9 were rejected — each with a written rationale
citing the specific mismatch. The remaining 4 are forecasted announcements:
tracked, but not yet assessable.

The rejections are the product. An example, verbatim from a stored assessment:

> The funding opportunity focuses on natural products, such as botanicals,
> dietary supplements, and probiotics, which does not align with [the
> organization's] capability of developing a drug delivery platform for existing
> approved drugs. [...] The specific match on 'clinical trial' is a trap, as
> [the organization] is a platform licensor, not a sponsor running trials.

That announcement matched on keywords. A tracker would have surfaced it. The
agent identified the match as misleading and said why.

---

## How it works

```
poll      →  query grants.gov, SBIR.gov, and the NIH Guide on a keyword set
fetch     →  pull full solicitation text for anything missing a description
shortlist →  structured filter: relevance, deadline viability, agency scope
              (no tokens — 526 → 14 happens here)
assess    →  LLM reasons each survivor against a capability profile, producing
              a verdict, confidence, rationale, and cited evidence
briefs    →  for pursue-worthy items, extract eligibility, budget, deadlines,
              and scope from the announcement text, with source links
dashboard →  static HTML, rebuilt each run
```

Runs unattended once a day via `launchd`. A DNS preflight handles the case where
the machine wakes from sleep before the network is up — without it, one wake-time
run spent 39 minutes in retry backoff against an unresolvable host.

### Design decisions worth naming

**One markdown document defines a client.** The capability profile is a
versioned, human-editable markdown file with a `## Vocabulary` section. Search
keywords, relevance terms, and trap terms are all parsed from it. Onboarding a
new subject means writing a document, not changing code.

**Trap terms are the differentiator.** A profile declares terms that *look* like
matches but aren't — `clinical trial`, for an organization that licenses a
platform rather than sponsoring trials. This is what lets the agent overrule a
keyword hit with a stated reason instead of surfacing it.

**Assessments are keyed to a profile version.** Editing the profile and bumping
the version triggers re-assessment; assessments from superseded versions are
pruned automatically. Every verdict is traceable to the exact profile text that
produced it.

**Verdicts are three-way.** `pursue`, `maybe`, and `skip`. A `maybe` means a
specific unresolved question exists, and the rationale names it — for example,
whether a required nonprofit partnership can be arranged.

**Forecasted opportunities are tracked before they are assessable.** When an
announcement transitions from forecasted to posted, the transition is recorded
and any stale assessment invalidated. Being early is the point.

**Structured filtering happens before the model.** 97% of the corpus is removed
by deterministic rules. The expensive layer only sees what survived.

---

## Evaluation

11 hand-labeled cases, currently ~10/11 agreement with the reasoner.

The honest caveat: at n=11, one case is nine percentage points, and there is no
meaningful confidence interval to quote. The number is not the claim. The claim
is that a held-out labeled set exists, that every verdict stores its rationale
and cited evidence for audit, and that disagreements are inspected individually
rather than averaged away. Expanding the set is in progress.

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.14 |
| State | SQLite |
| Embeddings | Ollama (`all-minilm`, 384-dim), local |
| Vector store | Pinecone |
| Reasoning | Groq (`llama-3.3-70b-versatile`) |
| Scheduling | `launchd` (macOS) |
| Output | static HTML |

Embeddings run locally because the hosted provider's free tier is rate-limited;
the provider is swappable at the embedding boundary. The Pinecone index is
384-dimensional, so any replacement must match that dimensionality or the index
must be rebuilt.

---

## Setup

```bash
git clone <repo>
cd agent-core
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Copy the environment template and fill in your own keys:

```bash
cp .env.example .env
```

```
GROQ_API_KEY=          # console.groq.com
PINECONE_API_KEY=      # app.pinecone.io
PINECONE_INDEX=        # must be a 384-dimensional index
LLM_MODEL=llama-3.3-70b-versatile
DB_PATH=agent.db
DASHBOARD_OUT=dashboard.html
CLIENT=hera
```

Ollama must be running locally with the embedding model pulled:

```bash
ollama pull all-minilm
```

Initialize the database:

```bash
python -m app.db.store
```

Load a capability profile (see `profiles/` for the expected structure), then run
the pipeline:

```bash
python -m app.pipeline
```

Or use the wrapper, which sets the database and output paths together:

```bash
./run.sh              # default subject
./run.sh <subject>    # uses agent-<subject>.db and dashboard-<subject>.html
```

---

## Repository layout

```
app/
  pipeline.py        orchestration; each stage isolated, timed, and fail-safe
  sources/           grants.gov, SBIR.gov, NIH Guide clients
  profile/
    load.py          parses vocabulary and terms out of the profile markdown
    generate.py      profile authoring
  reason/
    filter.py        structured shortlist (no tokens)
  detail/
    fetch.py         full announcement retrieval
    brief.py         eligibility / budget / deadline / scope extraction
    cache.py         brief caching
  db/
    schema.sql       full schema; builds a working database from scratch
    store.py         connection and initialization
  dashboard/
    build.py         static HTML generation
scripts/             one-shot anchored patch scripts, kept as a change record
profiles/            versioned capability profiles, as markdown
```

---

## Status and limitations

- One capability profile per database. Multiple subjects are supported by
  separate database files rather than by tenancy within a single one.
- Deadline extraction from announcement tables is imperfect. Extracted deadlines
  are flagged for verification against the source rather than silently trusted.
- Vocabulary is hand-written per subject. The system does not expand or suggest
  terms, so a term nobody thinks to write does not exist to the system.
- The evaluation set is small (see above).
- Non-federal funders — private foundations, disease-specific organizations —
  are not currently polled.

---

## Scope

Built as an independent project. All inputs are publicly available: federal
funding announcements and a hand-written capability profile describing publicly
known capabilities. No proprietary or internal material from any organization is
used or stored.

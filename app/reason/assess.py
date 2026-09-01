import json
from datetime import date, datetime, timezone

from app.clients.llm import client
from app.config import LLM_MODEL
from app.db.store import connect

import os
ASSESS_TEMP = float(os.getenv("ASSESS_TEMP", "0.1"))

PROMPT = """You are a grant strategist deciding whether a company should spend
time pursuing a funding opportunity. Be skeptical. Most opportunities are NOT a
good fit, and recommending a bad one wastes the company's scarce proposal effort.

COMPANY CAPABILITY PROFILE:
{profile}

FUNDING OPPORTUNITY:
Title: {title}
Agency: {agency}
Status: {status}
Due: {due_date} ({days_left} days away)
Description:
{description}

Decide: is this worth pursuing? Respond with ONLY a JSON object, no other text:
{{
  "verdict": "pursue" | "maybe" | "skip",
  "confidence": 0.0-1.0,
  "rationale": "2-4 sentences. Reason from the profile's fit criteria and anti-fit
                signals. Name the SPECIFIC match or mismatch. If it looks relevant
                but is a trap, say why.",
  "matched_on": ["short phrases from the opportunity that support a fit"],
  "concerns": ["specific reasons this might be wrong or borderline"]
}}

Judge on capability and modality, not disease area alone. A perfect disease-area
match with the wrong modality is a SKIP. Reward matches on the problem the agency
wants solved, not on surface keywords.

CHOOSING THE VERDICT - this matters:
- "pursue": the capability match is clear AND no disqualifying barrier.
- "skip": definite mismatch in modality/capability, OR an explicit exclusion
  or eligibility rule that rules the applicant out. Eligibility includes whether
  the applicant's institutional role and career stage permit holding this
  mechanism at all - a mechanism the applicant cannot hold is a skip regardless
  of how well the science fits.
- "maybe": use whenever the answer depends on something you cannot determine
  from the text. Typical cases: capability fits but eligibility is unclear
  (prior-award requirements, prime vs partner rules); the solicitation is
  vague; or it fits one part of the profile and conflicts with another.

Do NOT force a borderline case to pursue or skip. If you find yourself
writing "may not align" or "it is crucial to ensure" or "would need to
confirm", that is a maybe, not a confident verdict. An honest maybe is more
useful than a confident guess - a human resolves it in one minute.

Set "confidence" as confidence in the VERDICT itself. For a maybe, put the
specific unresolved question first in "concerns"."""


def current_profile(conn):
    from app.profile.load import CLIENT
    row = conn.execute(
        "SELECT version, content FROM profile WHERE client=? "
        "ORDER BY version DESC LIMIT 1", (CLIENT,)
    ).fetchone()
    if not row:
        raise SystemExit("No profile. Run app.profile.generate first.")
    return row["version"], row["content"]


def days_until(due):
    if not due:
        return None
    try:
        return (date.fromisoformat(due) - date.today()).days
    except ValueError:
        return None


def assess_one(conn, opp, profile_version, profile_text):
    days_left = days_until(opp["due_date"])
    prompt = PROMPT.format(
        profile=profile_text,
        title=opp["title"],
        agency=opp["agency"],
        status=opp["status"],
        due_date=opp["due_date"] or "unknown",
        days_left=days_left if days_left is not None else "unknown",
        description=(opp["description"] or "")[:6000],
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=ASSESS_TEMP,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content
    data = json.loads(raw)

    conn.execute(
        """INSERT OR REPLACE INTO assessment
           (opportunity_id, profile_version, verdict, confidence, rationale,
            evidence, days_to_due, model, tokens_used, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            opp["id"], profile_version,
            data.get("verdict"), data.get("confidence"),
            data.get("rationale"),
            json.dumps({"matched_on": data.get("matched_on"),
                        "concerns": data.get("concerns")}),
            days_left, LLM_MODEL, resp.usage.total_tokens,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return data, resp.usage.total_tokens


def run(limit=10):
    conn = connect()
    pv, ptext = current_profile(conn)
    print(f"using profile v{pv}\n")

    from app.reason.filter import shortlist
    opps = [r for r in shortlist(verbose=False)
            if r.get("description")][:limit]

    if not opps:
        raise SystemExit("No opportunities with descriptions. Fetch details first.")

    total_tokens = 0
    for opp in opps:
        data, toks = assess_one(conn, dict(opp), pv, ptext)
        total_tokens += toks
        v = data.get("verdict", "?").upper()
        print(f"[{v:6}] {data.get('confidence', 0):.2f}  {opp['title'][:55]}")
        print(f"         {data.get('rationale', '')}\n")

    conn.commit()
    conn.close()
    print(f"assessed {len(opps)} | {total_tokens} tokens")


if __name__ == "__main__":
    run()

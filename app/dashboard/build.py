import html
import json
from datetime import date, datetime

from app.db.store import connect
from app.reason.filter import shortlist

OUT = "dashboard.html"


def _esc(s):
    return html.escape(html.unescape(str(s or "")))


def _days(due):
    if not due:
        return None
    try:
        return (date.fromisoformat(due) - date.today()).days
    except ValueError:
        return None


def gather():
    conn = connect()
    ids = {r["id"] for r in shortlist(verbose=False)}

    pv = conn.execute("SELECT MAX(version) v FROM profile").fetchone()["v"]
    assessed = conn.execute(
        """SELECT a.verdict, a.confidence, a.rationale, a.evidence, a.days_to_due,
                  o.id, o.native_id, o.title, o.agency, o.due_date, o.url, o.status
           FROM assessment a JOIN opportunity o ON a.opportunity_id = o.id
           WHERE a.profile_version = ?""",
        (pv,),
    ).fetchall()

    watching = conn.execute(
        """SELECT id, title, agency, due_date, open_date, url
           FROM opportunity
           WHERE status='forecasted' AND id IN ({})""".format(
            ",".join("?" * len(ids)) or "''"
        ),
        list(ids),
    ).fetchall()
    just_opened = conn.execute(
        """SELECT id, title, agency, due_date, url, became_posted,
                  julianday('now') - julianday(became_posted) AS days_ago
           FROM opportunity
           WHERE became_posted IS NOT NULL
             AND julianday('now') - julianday(became_posted) <= 7
           ORDER BY became_posted DESC"""
    ).fetchall()
    conn.close()

    pursue = [dict(r) for r in assessed if r["verdict"] == "pursue"]
    maybe = [dict(r) for r in assessed if r["verdict"] == "maybe"]
    skip = [dict(r) for r in assessed if r["verdict"] == "skip"]
    # Pursue: most confident first. Skip: same.
    for grp in (pursue, skip):
        grp.sort(key=lambda x: (-(x["confidence"] or 0)))
    # Maybe is a triage queue: best fit at the top, weakest at the bottom.
    # Low verdict-confidence on a maybe means "closer to a real candidate",
    # so we surface those first and let clear near-misses sink.
    maybe.sort(key=lambda x: (x["confidence"] or 0))
    return pursue, maybe, skip, [dict(r) for r in watching], [dict(r) for r in just_opened]


def brief_block(opp_id):
    """Render the cached detail brief for an opportunity, if any."""
    from app.db.store import connect
    import json as _json
    conn = connect()
    row = conn.execute(
        "SELECT status, answers, url FROM brief WHERE opportunity_id=?", (opp_id,)
    ).fetchone()
    conn.close()
    if not row:
        return ""

    if row["status"] != "ok":
        return ('<div class="brief pending">Full announcement not yet published '
                '\u2014 flagged early, before its synopsis exists.</div>')

    answers = _json.loads(row["answers"]) if row["answers"] else {}
    labels = {"eligibility": "Eligibility", "budget": "Budget & period",
              "deadlines": "Deadlines", "scope": "Scope"}
    rows = ""
    for key in ("eligibility", "budget", "deadlines", "scope"):
        a = answers.get(key)
        if a:
            note = (" <span class='verify'>\u26a0 verify against source</span>"
                    if key == "deadlines" else "")
            rows += (f"<div class='brief-row'><span class='bl'>{labels[key]}{note}</span>"
                     f"<span class='bv'>{_esc(a.get('answer',''))}</span></div>")
    src = (f"<a href='{_esc(row['url'] or '#')}' target='_blank' "
           f"class='brief-src'>full announcement \u2197</a>")
    return (f"<details class='brief'><summary>What you'd need to know to apply</summary>"
            f"{rows}{src}</details>")


def card(a, dim=False):
    ev = {}
    try:
        ev = json.loads(a.get("evidence") or "{}")
    except Exception:
        pass
    matched = ev.get("matched_on") or []
    concerns = ev.get("concerns") or []
    days = a.get("days_to_due")
    urgency = ""
    if days is not None:
        urgency = "urgent" if days < 21 else "normal"
    deadline = f"{days}d" if days is not None else "no date"

    matched_html = "".join(f"<li>{_esc(m)}</li>" for m in matched)
    concerns_html = "".join(f"<li>{_esc(c)}</li>" for c in concerns)
    conf = a.get("confidence") or 0

    return f"""
    <article class="card {'dim' if dim else ''}">
      <header>
        <span class="verdict v-{_esc(a['verdict'])}">{_esc(a['verdict'])}</span>
        <span class="deadline {urgency}">{deadline}</span>
        <span class="conf">{conf:.0%} confidence</span>
      </header>
      <h3><a href="{_esc(a.get('url') or '#')}" target="_blank">{_esc(a['title'])}</a></h3>
      <p class="agency"><span class="nid">{_esc(a.get('native_id'))}</span>{_esc(a.get('agency'))}</p>
      <p class="rationale">{_esc(a['rationale'])}</p>
      <div class="evidence">
        {'<div class="matched"><h4>Matched on</h4><ul>' + matched_html + '</ul></div>' if matched else ''}
        {'<div class="concerns"><h4>Concerns</h4><ul>' + concerns_html + '</ul></div>' if concerns else ''}
      </div>
      {brief_block(a.get('id',''))}
    </article>"""


def watch_card(w):
    d = _days(w.get("open_date"))
    when = f"opens in {d}d" if d and d > 0 else "forecasted"
    return f"""
    <article class="card watch">
      <header><span class="verdict v-watch">watching</span>
      <span class="deadline">{when}</span></header>
      <h3><a href="{_esc(w.get('url') or '#')}" target="_blank">{_esc(w['title'])}</a></h3>
      <p class="agency">{_esc(w.get('agency'))} — not yet assessable, no synopsis published</p>
    </article>"""


def build():
    pursue, maybe, skip, watching, just_opened = gather()
    stamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    def section(title, items, sub, collapsed=False, watch=False):
        if not items:
            return ""
        cards = "".join(watch_card(i) if watch else card(i, dim=collapsed) for i in items)
        openattr = "" if collapsed else " open"
        summary = (f"<summary><h2>{title} <span class='count'>{len(items)}</span>"
                   f"<span class='chev'>\u203a</span></h2><p class='sub'>{sub}</p></summary>")
        return f"<details class='lane'{openattr}>{summary}{cards}</details>"

    def opened_banner(items):
        if not items:
            return ""
        rows = ""
        for o in items:
            days = o.get("days_ago")
            ago = "today" if days is not None and days < 1 else f"{int(days)}d ago"
            due = o.get("due_date") or "check announcement"
            rows += (f"<li><a href=\"{_esc(o.get('url') or '#')}\" target=\"_blank\">"
                     f"{_esc(o['title'])}</a>"
                     f"<span class='meta'>opened {ago} \u00b7 due {_esc(due)} \u00b7 "
                     f"{_esc(o.get('agency'))}</span></li>")
        return (f"<section class='opened'><h2>\u26a1 Just opened "
                f"<span class='count'>{len(items)}</span></h2>"
                f"<p class='sub'>Opportunities you were watching are now open for "
                f"application. These were flagged before their synopsis existed.</p>"
                f"<ul>{rows}</ul></section>")

    body = (
        opened_banner(just_opened)
        + section("Pursue", pursue, "Worth the proposal effort. Reasoning below.")
        + section("Ruled out", skip, "Read in full, then rejected \u2014 each with the reason. This is the work you don\'t have to redo.")
        + section("Maybe", maybe, "Borderline \u2014 read the concerns.")
        + section("Watching", watching, "Forecasted and relevant. Flagged early, before the synopsis is out.", watch=True)
    )

    doc = TEMPLATE.replace("{{BODY}}", body).replace("{{STAMP}}", stamp) \
        .replace("{{NP}}", str(len(pursue))).replace("{{NW}}", str(len(watching))) \
        .replace("{{NS}}", str(len(skip))) \
        .replace("{{NR}}", str(len(pursue) + len(maybe) + len(skip)))
    with open(OUT, "w") as f:
        f.write(doc)
    print(f"wrote {OUT}: {len(pursue)} pursue, {len(maybe)} maybe, {len(watching)} watching, {len(skip)} skip")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Opportunity Brief — Hera Health</title>
<style>
:root{
  --bg:#0f1216; --panel:#161b22; --line:#232a33; --ink:#e6edf3;
  --dim:#8b949e; --go:#3fb950; --warn:#d29922; --stop:#6e7681;
  --accent:#58a6ff; --serif:Georgia,'Times New Roman',serif;
  --mono:ui-monospace,'SF Mono',Menlo,monospace;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:820px;margin:0 auto;padding:48px 24px 96px}
header.top{border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:40px}
header.top h1{font-family:var(--serif);font-weight:600;font-size:32px;margin:0 0 6px;letter-spacing:-.01em}
header.top .meta{color:var(--dim);font-family:var(--mono);font-size:12px}
.summary{display:flex;gap:28px;margin-top:20px}
.summary .stat{display:flex;flex-direction:column}
.summary .n{font-family:var(--mono);font-size:26px;font-weight:600}
.summary .l{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.summary .go .n{color:var(--go)} .summary .watch .n{color:var(--accent)}
.lane{margin:0 0 44px} .lane[open]>summary,.lane>h2{cursor:default}
.lane summary{cursor:pointer;list-style:none} .lane summary::-webkit-details-marker{display:none}
.lane h2{font-family:var(--serif);font-size:20px;margin:0;display:inline-flex;align-items:baseline;gap:10px}
.count{font-family:var(--mono);font-size:13px;color:var(--dim);font-weight:400}
.sub{color:var(--dim);font-size:13px;margin:4px 0 20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:20px 22px;margin-bottom:14px}
.card.dim{opacity:.72}
.card header{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}
.verdict{font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:.06em;
  padding:3px 8px;border-radius:4px;font-weight:600}
.v-pursue{background:rgba(63,185,80,.15);color:var(--go)}
.v-maybe{background:rgba(210,153,34,.15);color:var(--warn)}
.v-skip{background:rgba(110,118,129,.15);color:var(--stop)}
.v-watch{background:rgba(88,166,255,.15);color:var(--accent)}
.deadline{font-family:var(--mono);font-size:12px;color:var(--dim)}
.deadline.urgent{color:var(--warn)}
.conf{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--dim)}
.card h3{margin:0 0 3px;font-size:16px;font-weight:600;line-height:1.35}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{color:var(--accent)}
.agency{color:var(--dim);font-size:12px;margin:0 0 12px}
.nid{font-family:var(--mono);color:var(--ink);background:var(--line);
  padding:2px 6px;border-radius:3px;margin-right:8px;font-size:11px}
.rationale{font-family:var(--serif);font-size:15px;line-height:1.6;margin:0 0 14px}
.evidence{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:560px){.evidence{grid-template-columns:1fr}}
.evidence h4{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--dim);margin:0 0 6px}
.evidence ul{margin:0;padding-left:16px;font-size:13px;color:#c9d1d9}
.evidence li{margin-bottom:3px}
.concerns h4{color:var(--warn)}
.card.watch{border-style:dashed}
.opened{background:rgba(63,185,80,.08);border:1px solid var(--go);
  border-radius:12px;padding:20px 22px;margin:0 0 32px}
.opened h2{font-family:var(--serif);font-size:20px;margin:0;color:var(--go);
  display:inline-flex;align-items:baseline;gap:10px}
.opened ul{list-style:none;margin:14px 0 0;padding:0}
.opened li{padding:10px 0;border-top:1px solid var(--line)}
.opened li a{color:var(--ink);text-decoration:none;font-weight:600;font-size:15px}
.opened li a:hover{color:var(--go)}
.opened .meta{display:block;font-family:var(--mono);font-size:12px;color:var(--dim);margin-top:3px}
.brief{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.brief summary{cursor:pointer;font-family:var(--mono);font-size:12px;color:var(--accent);
  text-transform:uppercase;letter-spacing:.05em}
.brief.pending{font-family:var(--mono);font-size:12px;color:var(--dim);font-style:italic}
.brief-row{display:grid;grid-template-columns:120px 1fr;gap:12px;margin-top:10px;font-size:13px}
.brief-row .bl{color:var(--dim);font-family:var(--mono);font-size:11px;text-transform:uppercase}
.verify{color:var(--warn);text-transform:none;font-size:10px}
.brief-row .bv{color:#c9d1d9;line-height:1.5}
.brief-src{display:inline-block;margin-top:12px;font-family:var(--mono);font-size:12px;color:var(--accent);text-decoration:none}
@media(max-width:560px){.brief-row{grid-template-columns:1fr}}

.brief{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}
.brief summary{cursor:pointer;font-family:var(--mono);font-size:12px;color:var(--accent);
  text-transform:uppercase;letter-spacing:.05em}
.brief.pending{font-family:var(--mono);font-size:12px;color:var(--dim);font-style:italic}
.brief-row{display:grid;grid-template-columns:120px 1fr;gap:12px;margin-top:10px;font-size:13px}
.brief-row .bl{color:var(--dim);font-family:var(--mono);font-size:11px;text-transform:uppercase}
.verify{color:var(--warn);text-transform:none;font-size:10px}
.brief-row .bv{color:#c9d1d9;line-height:1.5}
.brief-src{display:inline-block;margin-top:12px;font-family:var(--mono);font-size:12px;color:var(--accent);text-decoration:none}
@media(max-width:560px){.brief-row{grid-template-columns:1fr}}


.lane>summary{cursor:pointer;display:block}
.lane>summary h2{display:inline-flex;align-items:baseline;gap:10px}
.chev{font-family:var(--mono);color:var(--dim);transition:transform .15s;display:inline-block}
.lane[open]>summary .chev{transform:rotate(90deg)}
.lane>summary:hover h2{color:var(--accent)}

footer{color:var(--dim);font-size:12px;font-family:var(--mono);border-top:1px solid var(--line);
  padding-top:20px;margin-top:40px}
</style></head><body><div class="wrap">
<header class="top">
  <h1>Opportunity Brief</h1>
  <div class="meta">Hera Health Solutions · generated {{STAMP}}</div>
  <div class="summary">
    <div class="stat"><span class="n">{{NR}}</span><span class="l">Read &amp; reasoned</span></div>
    <div class="stat go"><span class="n">{{NP}}</span><span class="l">Worth pursuing</span></div>
    <div class="stat"><span class="n">{{NS}}</span><span class="l">Ruled out, with reasons</span></div>
    <div class="stat watch"><span class="n">{{NW}}</span><span class="l">Watching</span></div>
  </div>
</header>
{{BODY}}
<footer>Reasoned against capability profile. Each verdict reflects modality-and-capability fit, not keyword match. Skips are defensible — expand to audit.</footer>
</div></body></html>"""


if __name__ == "__main__":
    build()

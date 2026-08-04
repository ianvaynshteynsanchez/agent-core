from datetime import date

from app.db.store import connect
from app.reason.relevance import is_relevant

MIN_DAYS = 10          # below this, too close to write a real proposal
URGENT_DAYS = 21       # flag these as time-critical


def _days_left(due, today):
    if not due:
        return None
    try:
        return (date.fromisoformat(due) - today).days
    except ValueError:
        return None


def shortlist(include_forecasted=True, agencies=None, verbose=True,
              with_counts=False):
    """Cheap structured filter. No tokens, no API calls.
    Returns opportunity rows worth spending reasoning on."""
    conn = connect()
    today = date.today()
    rows = conn.execute("SELECT * FROM opportunity").fetchall()

    kept, buckets = [], {
        "expired": 0, "too_soon": 0, "wrong_agency": 0,
        "posted_ok": 0, "forecasted": 0, "no_date": 0, "off_topic": 0,
    }

    for r in rows:
        r = dict(r)
        days = _days_left(r["due_date"], today)
        r["days_left"] = days

        if agencies and r["agency"] not in agencies:
            buckets["wrong_agency"] += 1
            continue

        if not is_relevant(r):
            buckets["off_topic"] = buckets.get("off_topic", 0) + 1
            continue

        if r["status"] == "forecasted":
            if not include_forecasted:
                continue
            r["lane"] = "forecasted"
            buckets["forecasted"] += 1
            kept.append(r)
            continue

        # posted from here on
        if days is None:
            r["lane"] = "posted_no_date"
            buckets["no_date"] += 1
            kept.append(r)
        elif days < 0:
            buckets["expired"] += 1
        elif days < MIN_DAYS:
            buckets["too_soon"] += 1
        else:
            r["lane"] = "urgent" if days < URGENT_DAYS else "posted"
            buckets["posted_ok"] += 1
            kept.append(r)

    conn.close()

    if verbose:
        print(f"{len(rows)} total ->")
        for k, v in buckets.items():
            print(f"  {k:16} {v}")
        print(f"  {'SHORTLISTED':16} {len(kept)}")

    kept.sort(key=lambda x: (x["days_left"] is None, x["days_left"]))
    if with_counts:
        buckets["scanned"] = len(rows)
        buckets["shortlisted"] = len(kept)
        return kept, buckets
    return kept


if __name__ == "__main__":
    hits = shortlist()
    print("\nshortlist:")
    for r in hits[:20]:
        d = r["days_left"]
        d = f"{d}d" if d is not None else "no date"
        print(f"  [{r.get('lane','?'):14}] {d:>8}  {r['title'][:50]}")

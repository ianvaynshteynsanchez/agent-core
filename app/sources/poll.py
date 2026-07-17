from datetime import datetime, timezone

from app.db.store import connect
from app.sources import grants_gov

FIELDS = [
    "id", "source", "native_id", "title", "agency", "branch", "program",
    "phase", "status", "release_date", "open_date", "close_date", "due_date",
    "url", "description", "raw_json", "first_seen", "last_seen",
]


def upsert(conn, row):
    """Returns True if this is genuinely new (drives 'found it in time')."""
    existing = conn.execute(
        "SELECT id FROM opportunity WHERE id = ?", (row["id"],)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE opportunity SET last_seen=?, status=?, due_date=? WHERE id=?",
            (row["last_seen"], row["status"], row["due_date"], row["id"]),
        )
        return False

    cols = ", ".join(FIELDS)
    marks = ", ".join("?" for _ in FIELDS)
    conn.execute(
        f"INSERT INTO opportunity ({cols}) VALUES ({marks})",
        [row[f] for f in FIELDS],
    )
    return True


def poll(keywords, fetch_details=True, limit_fetch=10):
    conn = connect()
    seen, new_ids = set(), []

    for kw in keywords:
        print(f"searching: {kw}")
        for hit in grants_gov.search(keyword=kw):
            if hit["id"] in seen:
                continue
            seen.add(hit["id"])
            if upsert(conn, grants_gov.to_row(hit)):
                new_ids.append(hit["id"])

    conn.commit()
    print(f"\n{len(seen)} opportunities seen, {len(new_ids)} new")

    if fetch_details and new_ids:
        print(f"fetching descriptions for {min(len(new_ids), limit_fetch)} new...")
        for oid in new_ids[:limit_fetch]:
            detail = grants_gov.fetch(oid)
            if not detail:
                continue
            syn = detail.get("synopsis", {})
            conn.execute(
                "UPDATE opportunity SET description=?, url=COALESCE(?, url) WHERE id=?",
                (syn.get("synopsisDesc"), syn.get("fundingDescLinkUrl"),
                 f"grants_gov:{oid}"),
            )
        conn.commit()

    conn.close()
    return new_ids


if __name__ == "__main__":
    poll([
        '"drug delivery"',
        '"long acting injectable"',
        '"controlled release"',
        '"implantable device"',
        '"drug device combination"',
        '"sustained release"',
        "implant",
    ])

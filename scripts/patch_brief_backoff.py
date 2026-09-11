"""refresh_pursues() force-refetches every non-ok brief on every run, forever.
Add a widening backoff, with a became_posted override so the transition event
we actually care about is never delayed."""
import pathlib, shutil, sys

path = pathlib.Path("app/detail/cache.py")
src = path.read_text()

OLD_INS1 = '''            "INSERT OR REPLACE INTO brief VALUES (?,?,?,?,?,?)",
            (opp_id, native_id, status, None, url,
             datetime.now(timezone.utc).isoformat()),'''
NEW_INS1 = '''            "INSERT OR REPLACE INTO brief "
            "(opportunity_id, native_id, status, answers, url, created_at, attempts) "
            "VALUES (?,?,?,?,?,?,?)",
            (opp_id, native_id, status, None, url,
             datetime.now(timezone.utc).isoformat(), _attempts(conn, opp_id) + 1),'''

OLD_INS2 = '''        "INSERT OR REPLACE INTO brief VALUES (?,?,?,?,?,?)",
        (opp_id, native_id, "ok", json.dumps(brief["answers"]),
         brief["url"], datetime.now(timezone.utc).isoformat()),'''
NEW_INS2 = '''        "INSERT OR REPLACE INTO brief "
        "(opportunity_id, native_id, status, answers, url, created_at, attempts) "
        "VALUES (?,?,?,?,?,?,?)",
        (opp_id, native_id, "ok", json.dumps(brief["answers"]),
         brief["url"], datetime.now(timezone.utc).isoformat(), 0),'''

HELPERS = '''RETRY_AFTER_DAYS = [3, 7, 14, 30]


def _attempts(conn, opp_id):
    row = conn.execute(
        "SELECT attempts FROM brief WHERE opportunity_id=?", (opp_id,)).fetchone()
    return (row["attempts"] or 0) if row else 0


def _should_retry(conn, opp_id):
    """True if an unpublished brief is due for another attempt.

    A became_posted event inside the last 7 days always wins: that transition
    is the thing we are waiting for, and must never be delayed by the backoff.
    """
    row = conn.execute(
        "SELECT b.attempts, b.created_at, o.became_posted "
        "FROM brief b JOIN opportunity o ON o.id = b.opportunity_id "
        "WHERE b.opportunity_id=?", (opp_id,)).fetchone()
    if not row:
        return True

    if row["became_posted"]:
        try:
            age = (datetime.now(timezone.utc)
                   - datetime.fromisoformat(row["became_posted"])).days
            if age <= 7:
                return True
        except (ValueError, TypeError):
            return True   # unparseable timestamp: retry rather than suppress

    n = row["attempts"] or 0
    wait = RETRY_AFTER_DAYS[min(n, len(RETRY_AFTER_DAYS) - 1)]
    try:
        since = (datetime.now(timezone.utc)
                 - datetime.fromisoformat(row["created_at"])).days
    except (ValueError, TypeError):
        return True
    return since >= wait


'''

OLD_LOOP = '''    built = 0
    for r in rows:
        before = get_or_build(r["id"], r["native_id"])
        # retry unpublished ones (they may have gone live since last attempt)
        if before["status"] != "ok":
            before = get_or_build(r["id"], r["native_id"], force=True)
        if before["status"] == "ok":
            built += 1
    return built, len(rows)'''

NEW_LOOP = '''    built = 0
    for r in rows:
        before = get_or_build(r["id"], r["native_id"])
        # retry unpublished ones only when they are due (or just went live)
        if before["status"] != "ok":
            c = connect()
            due = _should_retry(c, r["id"])
            c.close()
            if due:
                before = get_or_build(r["id"], r["native_id"], force=True)
        if before["status"] == "ok":
            built += 1
    return built, len(rows)'''

if "RETRY_AFTER_DAYS" in src:
    sys.exit("already patched - no change made")
for name, old in (("insert1", OLD_INS1), ("insert2", OLD_INS2), ("loop", OLD_LOOP)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/detail/cache.py.bak")
src = src.replace("def get_or_build(", HELPERS + "def get_or_build(", 1)
for old, new in ((OLD_INS1, NEW_INS1), (OLD_INS2, NEW_INS2), (OLD_LOOP, NEW_LOOP)):
    src = src.replace(old, new, 1)
path.write_text(src)
print("patched OK")

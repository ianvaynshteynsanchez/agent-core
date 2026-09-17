"""Compare the live database against schema.sql and report column drift.

Four times now a column has been added to a live DB by hand without updating
schema.sql, so a fresh clone built a table the code writes to but that lacked
the column. The failure is loud but late - it surfaces on someone else's
machine. This surfaces it here instead.

Run directly:  python -m app.db.check
Or from the pipeline, where it logs a warning rather than raising.
"""
import re
import sqlite3

from app.db.store import DB_PATH, SCHEMA


def _schema_columns():
    """Table -> set of column names, parsed from schema.sql."""
    with open(SCHEMA) as f:
        sql = f.read()
    out = {}
    for m in re.finditer(
            r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\((.*?)\n\);",
            sql, re.DOTALL | re.IGNORECASE):
        table, body = m.group(1), m.group(2)
        cols = set()
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            if not line or line.startswith("--"):
                continue
            if re.match(r"(PRIMARY|FOREIGN|UNIQUE|CHECK|CONSTRAINT)\b",
                        line, re.IGNORECASE):
                continue
            name = line.split()[0].strip('"`[]')
            if name:
                cols.add(name)
        out[table] = cols
    return out


def _live_columns(path=None):
    """Table -> set of column names, from the live database."""
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    out = {}
    for (t,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"):
        out[t] = {r["name"] for r in
                  conn.execute(f"SELECT name FROM pragma_table_info('{t}')")}
    conn.close()
    return out


def drift(path=None):
    """Return a list of human-readable drift descriptions. Empty means clean."""
    want, have = _schema_columns(), _live_columns(path)
    problems = []
    for table in sorted(set(want) | set(have)):
        if table not in have:
            problems.append(f"{table}: in schema.sql, missing from database")
            continue
        if table not in want:
            problems.append(f"{table}: in database, missing from schema.sql")
            continue
        only_live = have[table] - want[table]
        only_file = want[table] - have[table]
        if only_live:
            problems.append(
                f"{table}: in database but NOT schema.sql -> "
                f"{', '.join(sorted(only_live))} (a fresh clone will break)")
        if only_file:
            problems.append(
                f"{table}: in schema.sql but NOT database -> "
                f"{', '.join(sorted(only_file))} (ALTER never ran here)")
    return problems


if __name__ == "__main__":
    import sys
    found = drift()
    if not found:
        print(f"schema clean: {DB_PATH} matches schema.sql")
        sys.exit(0)
    print(f"SCHEMA DRIFT in {DB_PATH}:")
    for p in found:
        print(f"  {p}")
    sys.exit(1)

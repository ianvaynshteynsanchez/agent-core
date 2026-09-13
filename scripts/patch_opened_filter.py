"""The just-opened banner shows every transition, relevant or not. Scope it to
opportunities that made the shortlist - a transition on something the relevance
gate already rejected is noise."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD = '''    just_opened = conn.execute(
        """SELECT id, title, agency, due_date, url, became_posted,
                  julianday('now') - julianday(became_posted) AS days_ago
           FROM opportunity
           WHERE became_posted IS NOT NULL
             AND julianday('now') - julianday(became_posted) <= 7
           ORDER BY became_posted DESC"""
    ).fetchall()'''

NEW = '''    just_opened = conn.execute(
        """SELECT id, title, agency, due_date, url, became_posted,
                  julianday('now') - julianday(became_posted) AS days_ago
           FROM opportunity
           WHERE became_posted IS NOT NULL
             AND julianday('now') - julianday(became_posted) <= 7
             AND id IN ({})
           ORDER BY became_posted DESC""".format(
            ",".join("?" * len(ids)) or "''"
        ),
        list(ids),
    ).fetchall()'''

if "AND id IN ({})" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak14")
path.write_text(src.replace(OLD, NEW, 1))
print("patched OK")

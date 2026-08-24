"""Dashboard title and byline are hardcoded to one client. Derive from CLIENT."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD_TITLE = '''<title>Opportunity Brief — Hera Health</title>'''
NEW_TITLE = '''<title>Opportunity Brief — {{CLIENT}}</title>'''

OLD_META = '''  <div class="meta">Hera Health Solutions · generated {{STAMP}}</div>'''
NEW_META = '''  <div class="meta">{{CLIENT}} · generated {{STAMP}}</div>'''

OLD_REPL = '''.replace("{{NT}}", str(counts.get("scanned", 0)))'''
NEW_REPL = '''.replace("{{NT}}", str(counts.get("scanned", 0))) \\
        .replace("{{CLIENT}}", CLIENT_LABEL)'''

OLD_OUT = '''OUT = os.getenv("DASHBOARD_OUT", "dashboard.html")'''
NEW_OUT = '''OUT = os.getenv("DASHBOARD_OUT", "dashboard.html")
_LABELS = {"hera": "Hera Health Solutions", "soni": "Viren Soni, PhD"}
CLIENT_LABEL = _LABELS.get(os.getenv("CLIENT", "hera"),
                           os.getenv("CLIENT", "hera").title())'''

if "CLIENT_LABEL" in src:
    sys.exit("already patched - no change made")
for name, old in (("title", OLD_TITLE), ("meta", OLD_META),
                  ("repl", OLD_REPL), ("out", OLD_OUT)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak8")
for old, new in ((OLD_TITLE, NEW_TITLE), (OLD_META, NEW_META),
                 (OLD_REPL, NEW_REPL), (OLD_OUT, NEW_OUT)):
    src = src.replace(old, new, 1)
path.write_text(src)
print("patched OK (backup at app/dashboard/build.py.bak8)")

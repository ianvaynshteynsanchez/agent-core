"""Render native_id on each card - without it, nothing is lookup-able."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD = '''      <p class="agency">{_esc(a.get('agency'))}</p>'''
NEW = '''      <p class="agency"><span class="nid">{_esc(a.get('native_id'))}</span>{_esc(a.get('agency'))}</p>'''

OLD_CSS = '''.agency{color:var(--dim);font-size:12px;margin:0 0 12px}'''
NEW_CSS = '''.agency{color:var(--dim);font-size:12px;margin:0 0 12px}
.nid{font-family:var(--mono);color:var(--ink);background:var(--line);
  padding:2px 6px;border-radius:3px;margin-right:8px;font-size:11px}'''

if ".nid" in src:
    sys.exit("already patched - no change made")
for name, old in (("card", OLD), ("css", OLD_CSS)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak4")
src = src.replace(OLD, NEW, 1).replace(OLD_CSS, NEW_CSS, 1)
path.write_text(src)
print("patched OK (backup at app/dashboard/build.py.bak4)")

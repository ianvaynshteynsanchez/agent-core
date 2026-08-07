"""Make the dashboard output path configurable, so a run against a second
database doesn't silently overwrite the first subject's dashboard."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD = '''OUT = "dashboard.html"'''
NEW = '''OUT = os.getenv("DASHBOARD_OUT", "dashboard.html")'''

if "DASHBOARD_OUT" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND (OUT) - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak7")
src = src.replace(OLD, NEW, 1)

if "\nimport os" not in src and not src.startswith("import os"):
    src = src.replace("import html", "import html\nimport os", 1)

path.write_text(src)
print("patched OK (backup at app/dashboard/build.py.bak7)")

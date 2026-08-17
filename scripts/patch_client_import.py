"""new_profile_version.py references CLIENT without importing it."""
import pathlib, shutil, sys

path = pathlib.Path("scripts/new_profile_version.py")
src = path.read_text()

if "import CLIENT" in src or "load import" in src and "CLIENT" in src.split("(version")[0]:
    sys.exit("already imported - no change made")

OLD = "from app.db.store import connect"
NEW = "from app.db.store import connect\nfrom app.profile.load import CLIENT"

if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - paste the file's import block and I'll re-aim")

shutil.copy(path, "scripts/new_profile_version.py.bak3")
path.write_text(src.replace(OLD, NEW, 1))
print("patched OK")

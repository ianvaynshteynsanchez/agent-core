"""Eval runs at temperature 0.1 return different scores on identical inputs
(11/11, 9/11, 10/11 across three runs). Make temperature configurable so the
eval can pin it to 0 and actually measure changes."""
import pathlib, shutil, sys

path = pathlib.Path("app/reason/assess.py")
src = path.read_text()

OLD = '''        temperature=0.1,'''
NEW = '''        temperature=ASSESS_TEMP,'''

OLD_IMP = '''from app.db.store import connect'''
NEW_IMP = '''from app.db.store import connect

import os
ASSESS_TEMP = float(os.getenv("ASSESS_TEMP", "0.1"))'''

if "ASSESS_TEMP" in src:
    sys.exit("already patched - no change made")
for name, old in (("temp", OLD), ("import", OLD_IMP)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/reason/assess.py.bak5")
src = src.replace(OLD_IMP, NEW_IMP, 1).replace(OLD, NEW, 1)
path.write_text(src)
print("patched OK")

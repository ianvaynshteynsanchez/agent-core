"""Pin eval runs to temperature 0. Must be set before assess is imported,
since ASSESS_TEMP is read at module load."""
import pathlib, shutil, sys

path = pathlib.Path("app/evals/reasoner.py")
src = path.read_text()

OLD = '''import sys
import time'''
NEW = '''import os
os.environ.setdefault("ASSESS_TEMP", "0")  # evals must be reproducible

import sys
import time'''

if 'ASSESS_TEMP", "0"' in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/evals/reasoner.py.bak4")
path.write_text(src.replace(OLD, NEW, 1))
print("patched OK")

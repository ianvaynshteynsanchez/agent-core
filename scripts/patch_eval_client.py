"""LABELS is hardcoded to one file, so a second client's cases can't be added.
Derive it from CLIENT, same convention as run.sh: hera keeps the plain name."""
import pathlib, shutil, sys

path = pathlib.Path("app/evals/reasoner.py")
src = path.read_text()

OLD = '''LABELS = "evals/verdicts.txt"'''
NEW = '''import os
_CLIENT = os.getenv("CLIENT", "hera")
LABELS = ("evals/verdicts.txt" if _CLIENT == "hera"
          else f"evals/verdicts-{_CLIENT}.txt")'''

OLD_DOC = '''Labels live in evals/verdicts.txt, one per line:
    <opportunity_id> | <expected verdict> | <note>'''
NEW_DOC = '''Labels live in evals/verdicts.txt (or evals/verdicts-<client>.txt for
non-default clients), one per line:
    <opportunity_id> | <expected verdict> | <note> | <phrases the rationale must not contain>'''

if "verdicts-{_CLIENT}" in src:
    sys.exit("already patched - no change made")
for name, old in (("labels", OLD), ("docstring", OLD_DOC)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/evals/reasoner.py.bak3")
src = src.replace(OLD, NEW, 1).replace(OLD_DOC, NEW_DOC, 1)
path.write_text(src)
print("patched OK")

"""Retry on json_validate_failed too. The model occasionally emits malformed
JSON (e.g. `"confidence": 0. nine`), which killed the whole eval run."""
import pathlib, shutil, sys

path = pathlib.Path("app/evals/reasoner.py")
src = path.read_text()

OLD = '''            if "rate_limit" in str(e) or "429" in str(e):
                wait = 8 * (attempt + 1)'''
NEW = '''            msg = str(e)
            if ("json_validate_failed" in msg or "Failed to generate JSON" in msg):
                print("        malformed JSON from model, retrying")
                time.sleep(2)
                continue
            if "rate_limit" in msg or "429" in msg:
                wait = 8 * (attempt + 1)'''

if "malformed JSON" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/evals/reasoner.py.bak6")
path.write_text(src.replace(OLD, NEW, 1))
print("patched OK")

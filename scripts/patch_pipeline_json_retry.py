"""do_assess() retries rate limits but not malformed JSON. The model
occasionally emits invalid output (seen: `"confidence": 0. nine`), which
currently loses that opportunity from the run."""
import pathlib, shutil, sys

path = pathlib.Path("app/pipeline.py")
src = path.read_text()

OLD = '''                msg = str(e)
                if "rate_limit" in msg or "429" in msg:'''
NEW = '''                msg = str(e)
                if "json_validate_failed" in msg or "Failed to generate JSON" in msg:
                    log("assess", "  malformed JSON from model, retrying")
                    time.sleep(2)
                    continue
                if "rate_limit" in msg or "429" in msg:'''

if "malformed JSON" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/pipeline.py.bak10")
src = src.replace(OLD, NEW, 1)
if "\nimport time" not in src:
    src = src.replace("import traceback", "import time\nimport traceback", 1)
path.write_text(src)
print("patched OK")

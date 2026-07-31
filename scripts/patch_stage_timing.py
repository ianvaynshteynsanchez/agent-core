"""One-shot: add per-stage elapsed timing to pipeline.stage()."""
import pathlib, shutil, sys

path = pathlib.Path("app/pipeline.py")
src = path.read_text()

OLD = '''def stage(name, fn, *args, **kwargs):
    """Run a stage; never let it kill the pipeline."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log(name, f"FAILED: {e}")
        traceback.print_exc()
        return None'''

NEW = '''def stage(name, fn, *args, **kwargs):
    """Run a stage; never let it kill the pipeline."""
    t0 = time.monotonic()
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log(name, f"FAILED: {e}")
        traceback.print_exc()
        return None
    finally:
        elapsed = time.monotonic() - t0
        if elapsed >= 5:
            log(name, f"took {elapsed:.0f}s")'''

if "time.monotonic" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - stage() differs from expected; nothing written")

shutil.copy(path, "app/pipeline.py.bak")
src = src.replace(OLD, NEW)
if "import time" not in src:
    src = src.replace("import traceback", "import time\nimport traceback", 1)
path.write_text(src)
print("patched OK (backup at app/pipeline.py.bak)")

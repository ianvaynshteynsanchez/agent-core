"""Log schema drift at the start of each run. Four instances so far, each one
found late and by accident."""
import pathlib, shutil, sys

path = pathlib.Path("app/pipeline.py")
src = path.read_text()

OLD = '''    stage("net", wait_for_dns)'''
NEW = '''    try:
        from app.db.check import drift as _drift
        for _p in _drift():
            log("schema", f"DRIFT: {_p}")
    except Exception as _e:
        log("schema", f"check failed: {_e}")

    stage("net", wait_for_dns)'''

if "DRIFT:" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/pipeline.py.bak11")
path.write_text(src.replace(OLD, NEW, 1))
print("patched OK")

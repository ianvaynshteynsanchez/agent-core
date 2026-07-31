"""One-shot: remove the duplicated do_prune_versions def and its double call."""
import pathlib, shutil, sys

path = pathlib.Path("app/pipeline.py")
src = path.read_text()

BODY = '''def do_prune_versions():
    """Remove assessments from superseded profile versions. Prevents the
    dashboard from stacking contradictory verdicts across versions."""
    conn = connect()
    pv = conn.execute("SELECT MAX(version) v FROM profile").fetchone()["v"]
    n = conn.execute(
        "SELECT COUNT(*) c FROM assessment WHERE profile_version < ?", (pv,)
    ).fetchone()["c"]
    if n:
        conn.execute("DELETE FROM assessment WHERE profile_version < ?", (pv,))
        conn.commit()
        log("prune", f"removed {n} assessments from old profile versions")
    conn.close()
    return n
'''

DOUBLE_CALL = '''    stage("prune-v", do_prune_versions)
    stage("prune-v", do_prune_versions)'''
SINGLE_CALL = '''    stage("prune-v", do_prune_versions)'''

if src.count(BODY) != 2:
    sys.exit(f"ANCHOR: expected 2 copies of body, found {src.count(BODY)} - nothing written")
if DOUBLE_CALL not in src:
    sys.exit("ANCHOR: double stage() call not found - nothing written")

shutil.copy(path, "app/pipeline.py.bak3")
src = src.replace(BODY + "\n\n", "", 1)      # drop the first copy
src = src.replace(DOUBLE_CALL, SINGLE_CALL, 1)
path.write_text(src)
print("patched OK (backup at app/pipeline.py.bak3)")

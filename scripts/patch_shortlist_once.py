"""shortlist() runs twice per pipeline (do_assess + do_prune), scanning 531
opportunities against ~52 relevance terms each time. Compute once, pass it in."""
import pathlib, shutil, sys

path = pathlib.Path("app/pipeline.py")
src = path.read_text()

OLD_ASSESS = '''    todo = [r for r in shortlist(verbose=False)'''
NEW_ASSESS = '''    todo = [r for r in (_shortlist or shortlist(verbose=False))'''

OLD_PRUNE = '''    ids = {r["id"] for r in shortlist(verbose=False)}'''
NEW_PRUNE = '''    ids = {r["id"] for r in (_shortlist or shortlist(verbose=False))}'''

OLD_SIG_A = '''def do_assess():'''
NEW_SIG_A = '''def do_assess(_shortlist=None):'''

OLD_SIG_P = '''def do_prune():'''
NEW_SIG_P = '''def do_prune(_shortlist=None):'''

OLD_RUN = '''    stage("poll", do_poll)'''
NEW_RUN = '''    stage("poll", do_poll)
    from app.reason.filter import shortlist as _sl
    _cached = _sl(verbose=False)
    log("shortlist", f"{len(_cached)} shortlisted (computed once)")'''

OLD_CALLS = '''    stage("prune", do_prune)'''
NEW_CALLS = '''    stage("prune", do_prune, _cached)'''

OLD_ACALL = '''    stage("assess", do_assess)'''
NEW_ACALL = '''    stage("assess", do_assess, _cached)'''

if "_shortlist=None" in src:
    sys.exit("already patched - no change made")
for name, old in (("assess body", OLD_ASSESS), ("prune body", OLD_PRUNE),
                  ("assess sig", OLD_SIG_A), ("prune sig", OLD_SIG_P),
                  ("run", OLD_RUN), ("prune call", OLD_CALLS),
                  ("assess call", OLD_ACALL)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/pipeline.py.bak9")
for old, new in ((OLD_SIG_A, NEW_SIG_A), (OLD_SIG_P, NEW_SIG_P),
                 (OLD_ASSESS, NEW_ASSESS), (OLD_PRUNE, NEW_PRUNE),
                 (OLD_RUN, NEW_RUN), (OLD_CALLS, NEW_CALLS),
                 (OLD_ACALL, NEW_ACALL)):
    src = src.replace(old, new, 1)
path.write_text(src)
print("patched OK (backup at app/pipeline.py.bak9)")

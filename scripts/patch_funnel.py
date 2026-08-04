"""Expose shortlist's bucket counts so the dashboard can show the funnel:
N scanned -> N read in full -> N worth pursuing."""
import pathlib, shutil, sys

path = pathlib.Path("app/reason/filter.py")
src = path.read_text()

OLD_SIG = '''def shortlist(include_forecasted=True, agencies=None, verbose=True):'''
NEW_SIG = '''def shortlist(include_forecasted=True, agencies=None, verbose=True,
              with_counts=False):'''

OLD_BUCKETS = '''    kept, buckets = [], {
        "expired": 0, "too_soon": 0, "wrong_agency": 0,
        "posted_ok": 0, "forecasted": 0, "no_date": 0,
    }'''
NEW_BUCKETS = '''    kept, buckets = [], {
        "expired": 0, "too_soon": 0, "wrong_agency": 0,
        "posted_ok": 0, "forecasted": 0, "no_date": 0, "off_topic": 0,
    }'''

OLD_RET = '''    kept.sort(key=lambda x: (x["days_left"] is None, x["days_left"]))
    return kept'''
NEW_RET = '''    kept.sort(key=lambda x: (x["days_left"] is None, x["days_left"]))
    if with_counts:
        buckets["scanned"] = len(rows)
        buckets["shortlisted"] = len(kept)
        return kept, buckets
    return kept'''

if "with_counts" in src:
    sys.exit("already patched - no change made")
for name, old in (("sig", OLD_SIG), ("buckets", OLD_BUCKETS), ("ret", OLD_RET)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/reason/filter.py.bak")
src = src.replace(OLD_SIG, NEW_SIG, 1)
src = src.replace(OLD_BUCKETS, NEW_BUCKETS, 1)
src = src.replace(OLD_RET, NEW_RET, 1)
path.write_text(src)
print("patched OK (backup at app/reason/filter.py.bak)")

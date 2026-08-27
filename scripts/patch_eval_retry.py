"""Eval harness calls assess_one() with no retry, so a per-minute rate limit
kills the whole run. The pipeline already backs off; do the same here."""
import pathlib, shutil, sys

path = pathlib.Path("app/evals/reasoner.py")
src = path.read_text()

OLD = '''            data, _ = assess_one(conn, dict(opp), pv, ptext)'''
NEW = '''            data = None
            for attempt in range(5):
                try:
                    data, _ = assess_one(conn, dict(opp), pv, ptext)
                    break
                except Exception as e:
                    if "rate_limit" in str(e) or "429" in str(e):
                        wait = 8 * (attempt + 1)
                        print(f"        rate limited, waiting {wait}s")
                        time.sleep(wait)
                        continue
                    raise
            if data is None:
                print(f"  RATELIMIT {opp['title'][:50]}")
                missing += 1
                continue'''

if "rate limited, waiting" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/evals/reasoner.py.bak2")
src = src.replace(OLD, NEW, 1)
if "\nimport time" not in src:
    src = src.replace("import sys", "import sys\nimport time", 1)
path.write_text(src)
print("patched OK")

"""Add --runs N calibration mode: assess each case N times, report the majority
outcome and flag cases that weren't unanimous. Default stays 1."""
import pathlib, shutil, sys

path = pathlib.Path("app/evals/reasoner.py")
src = path.read_text()

OLD_SIG = '''def run(live=False):'''
NEW_SIG = '''def _assess_with_retry(conn, opp, pv, ptext):
    """One assessment with rate-limit backoff. Returns (verdict, rationale) or None."""
    for attempt in range(5):
        try:
            data, _ = assess_one(conn, dict(opp), pv, ptext)
            return (data.get("verdict") or "").lower(), data.get("rationale", "")
        except Exception as e:
            if "rate_limit" in str(e) or "429" in str(e):
                wait = 8 * (attempt + 1)
                print(f"        rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            raise
    return None


def _outcome(actual, expected, rationale, banned):
    """PASS | FAIL | WEAK for one assessment."""
    if actual != expected:
        return "FAIL"
    if [b for b in banned if b in (rationale or "").lower()]:
        return "WEAK"
    return "PASS"


def run(live=False, runs=1):'''

OLD_LIVE = '''        if live:
            data = None
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
                continue
            actual = (data.get("verdict") or "").lower()
            rationale = data.get("rationale", "")'''

NEW_LIVE = '''        if live:
            results = []
            for _ in range(runs):
                got = _assess_with_retry(conn, opp, pv, ptext)
                if got is None:
                    break
                results.append(got)
            if not results:
                print(f"  RATELIMIT {opp['title'][:50]}")
                missing += 1
                continue
            outcomes = [_outcome(a, expected, r, banned) for a, r in results]
            majority = max(set(outcomes), key=outcomes.count)
            if runs > 1:
                n = outcomes.count(majority)
                tag = f"({n}/{runs} stable)" if n == runs else \\
                      f"({n}/{runs} - also {', '.join(sorted(set(outcomes) - {majority}))})"
                if n < runs:
                    unstable.append(opp["title"][:45])
                print(f"  {majority:5} {expected:6} {opp['title'][:45]} {tag}")
                if majority == "PASS":
                    agree += 1
                elif majority == "WEAK":
                    weak += 1
                else:
                    disagree += 1
                continue
            actual, rationale = results[0]'''

OLD_COUNT = '''    agree = disagree = missing = weak = 0'''
NEW_COUNT = '''    agree = disagree = missing = weak = 0
    unstable = []'''

OLD_MAIN = '''    run(live="--live" in sys.argv)'''
NEW_MAIN = '''    _n = 1
    if "--runs" in sys.argv:
        _n = int(sys.argv[sys.argv.index("--runs") + 1])
    run(live="--live" in sys.argv, runs=_n)'''

if "--runs" in src:
    sys.exit("already patched - no change made")
for name, old in (("sig", OLD_SIG), ("live", OLD_LIVE),
                  ("counters", OLD_COUNT), ("main", OLD_MAIN)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/evals/reasoner.py.bak5")
for old, new in ((OLD_SIG, NEW_SIG), (OLD_COUNT, NEW_COUNT),
                 (OLD_LIVE, NEW_LIVE), (OLD_MAIN, NEW_MAIN)):
    src = src.replace(old, new, 1)
path.write_text(src)
print("patched OK")

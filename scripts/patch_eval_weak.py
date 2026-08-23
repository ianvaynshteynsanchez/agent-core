"""Add a third outcome to the eval harness: WEAK - right verdict, bad reasoning."""
import pathlib, shutil, sys

path = pathlib.Path("app/evals/reasoner.py")
src = path.read_text()

OLD_LOAD = '''            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                out.append((parts[0], parts[1].lower(), parts[2] if len(parts) > 2 else ""))
    return out'''

NEW_LOAD = '''            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                banned = []
                if len(parts) > 3 and parts[3]:
                    banned = [b.strip().lower() for b in parts[3].split(",") if b.strip()]
                out.append((parts[0], parts[1].lower(),
                            parts[2] if len(parts) > 2 else "", banned))
    return out'''

OLD_ITER = '''    agree = disagree = missing = 0
    for oid, expected, note in labels:'''

NEW_ITER = '''    agree = disagree = missing = weak = 0
    for oid, expected, note, banned in labels:'''

OLD_CHECK = '''        if actual == expected:
            agree += 1
            print(f"  PASS  {expected:6} {opp['title'][:55]}")'''

NEW_CHECK = '''        if actual == expected:
            hits = [b for b in banned if b in (rationale or "").lower()]
            if hits:
                weak += 1
                print(f"  WEAK  {expected:6} {opp['title'][:55]}")
                print(f"        right verdict, bad reasoning: {', '.join(hits)}")
                print(f"        model said: {rationale[:160]}...")
            else:
                agree += 1
                print(f"  PASS  {expected:6} {opp['title'][:55]}")'''

OLD_SUM = '''    total = agree + disagree
    pct = (agree / total * 100) if total else 0
    print(f"\\n  {agree}/{total} agree ({pct:.0f}%)  |  {missing} missing")
    return pct'''

NEW_SUM = '''    total = agree + disagree + weak
    pct = (agree / total * 100) if total else 0
    print(f"\\n  {agree}/{total} clean ({pct:.0f}%)  |  "
          f"{disagree} wrong verdict  |  {weak} weak reasoning  |  {missing} missing")
    return pct'''

if "WEAK" in src:
    sys.exit("already patched - no change made")
for name, old in (("load", OLD_LOAD), ("iter", OLD_ITER),
                  ("check", OLD_CHECK), ("summary", OLD_SUM)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/evals/reasoner.py.bak")
for old, new in ((OLD_LOAD, NEW_LOAD), (OLD_ITER, NEW_ITER),
                 (OLD_CHECK, NEW_CHECK), (OLD_SUM, NEW_SUM)):
    src = src.replace(old, new, 1)
path.write_text(src)
print("patched OK (backup at app/evals/reasoner.py.bak)")

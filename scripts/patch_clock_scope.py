"""Clock markers currently fire on every card. Scope them: a clock only flags
an opportunity that IS the mechanism it governs, and only in actionable lanes."""
import pathlib, shutil, sys

lp = pathlib.Path("app/profile/load.py")
s = lp.read_text()
OLD_P = '''        name, early, late = parts[0], parts[1], parts[2]
        note = parts[3] if len(parts) > 3 else ""'''
NEW_P = '''        name, early, late = parts[0], parts[1], parts[2]
        if len(parts) > 4:
            match = [m.strip().lower() for m in parts[3].split(",") if m.strip()]
            note = parts[4]
        else:
            match, note = [], (parts[3] if len(parts) > 3 else "")'''
OLD_OUT = '''            "note": note,'''
NEW_OUT = '''            "match": match,
            "note": note,'''

bp = pathlib.Path("app/dashboard/build.py")
b = bp.read_text()
OLD_SIG = '''def clock_flag(due):'''
NEW_SIG = '''def clock_flag(due, title="", native_id="", verdict=""):'''
OLD_GUARD = '''    if not due:
        return ""
    items = _clocks_cached()'''
NEW_GUARD = '''    if not due or verdict not in ("pursue", "maybe"):
        return ""
    items = _clocks_cached()'''
OLD_LOOP = '''    for c in items:
        latest, earliest = c.get("latest"), c.get("earliest")'''
NEW_LOOP = '''    hay = f"{title} {native_id}".lower()
    for c in items:
        terms = c.get("match") or []
        if terms and not any(t in hay for t in terms):
            continue
        latest, earliest = c.get("latest"), c.get("earliest")'''
OLD_CALL = '''      {clock_flag(a.get('due_date'))}'''
NEW_CALL = '''      {clock_flag(a.get('due_date'), a.get('title',''), a.get('native_id',''), a.get('verdict',''))}'''

if '"match": match' in s:
    sys.exit("already patched - no change made")
for n, o, t in (("parse", OLD_P, s), ("out", OLD_OUT, s), ("sig", OLD_SIG, b),
                ("guard", OLD_GUARD, b), ("loop", OLD_LOOP, b), ("call", OLD_CALL, b)):
    if o not in t:
        sys.exit(f"ANCHOR NOT FOUND ({n}) - nothing written")

shutil.copy(lp, "app/profile/load.py.bak3")
shutil.copy(bp, "app/dashboard/build.py.bak13")
lp.write_text(s.replace(OLD_P, NEW_P, 1).replace(OLD_OUT, NEW_OUT, 1))
for o, nw in ((OLD_SIG, NEW_SIG), (OLD_GUARD, NEW_GUARD),
              (OLD_LOOP, NEW_LOOP), (OLD_CALL, NEW_CALL)):
    b = b.replace(o, nw, 1)
bp.write_text(b)
print("patched OK")

"""Show the real funnel in the dashboard header."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD_CALL = '''    ids = {r["id"] for r in shortlist(verbose=False)}'''
NEW_CALL = '''    _rows, _counts = shortlist(verbose=False, with_counts=True)
    ids = {r["id"] for r in _rows}'''

OLD_RET = '''    return pursue, maybe, skip, [dict(r) for r in watching], [dict(r) for r in just_opened]'''
NEW_RET = '''    return (pursue, maybe, skip, [dict(r) for r in watching],
            [dict(r) for r in just_opened], _counts)'''

OLD_UNPACK = '''    pursue, maybe, skip, watching, just_opened = gather()'''
NEW_UNPACK = '''    pursue, maybe, skip, watching, just_opened, counts = gather()'''

OLD_STAT = '''    <div class="stat"><span class="n">{{NR}}</span><span class="l">Read &amp; reasoned</span></div>'''
NEW_STAT = '''    <div class="stat"><span class="n">{{NT}}</span><span class="l">Tracked</span></div>
    <div class="stat"><span class="n">{{NR}}</span><span class="l">Read in full</span></div>'''

OLD_REPL = '''.replace("{{NR}}", str(len(pursue) + len(maybe) + len(skip)))'''
NEW_REPL = '''.replace("{{NR}}", str(len(pursue) + len(maybe) + len(skip))) \\
        .replace("{{NT}}", str(counts.get("scanned", 0)))'''

if "{{NT}}" in src:
    sys.exit("already patched - no change made")
for name, old in (("call", OLD_CALL), ("ret", OLD_RET), ("unpack", OLD_UNPACK),
                  ("stat", OLD_STAT), ("repl", OLD_REPL)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak5")
for old, new in ((OLD_CALL, NEW_CALL), (OLD_RET, NEW_RET), (OLD_UNPACK, NEW_UNPACK),
                 (OLD_STAT, NEW_STAT), (OLD_REPL, NEW_REPL)):
    src = src.replace(old, new, 1)
path.write_text(src)
print("patched OK (backup at app/dashboard/build.py.bak5)")

"""Promote the skip lane: the rejection reasoning is the differentiator,
not the shortlist. Reorder, un-collapse, undim, and reframe the header stat."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD_BODY = '''        + section("Pursue", pursue, "Worth the proposal effort. Reasoning below.")
        + section("Maybe", maybe, "Borderline — read the concerns.")
        + section("Watching", watching, "Forecasted and relevant. Flagged early, before the synopsis is out.", watch=True)
        + section("Skip", skip, "Assessed and passed over. Expand to see why each was rejected.", collapsed=True)'''

NEW_BODY = '''        + section("Pursue", pursue, "Worth the proposal effort. Reasoning below.")
        + section("Ruled out", skip, "Read in full, then rejected \\u2014 each with the reason. This is the work you don\\'t have to redo.")
        + section("Maybe", maybe, "Borderline \\u2014 read the concerns.")
        + section("Watching", watching, "Forecasted and relevant. Flagged early, before the synopsis is out.", watch=True)'''

OLD_STAT = '''    <div class="stat go"><span class="n">{{NP}}</span><span class="l">Pursue</span></div>
    <div class="stat watch"><span class="n">{{NW}}</span><span class="l">Watching</span></div>
    <div class="stat"><span class="n">{{NS}}</span><span class="l">Skip</span></div>'''

NEW_STAT = '''    <div class="stat"><span class="n">{{NR}}</span><span class="l">Read &amp; reasoned</span></div>
    <div class="stat go"><span class="n">{{NP}}</span><span class="l">Worth pursuing</span></div>
    <div class="stat"><span class="n">{{NS}}</span><span class="l">Ruled out, with reasons</span></div>
    <div class="stat watch"><span class="n">{{NW}}</span><span class="l">Watching</span></div>'''

OLD_REPL = '''.replace("{{NS}}", str(len(skip)))'''
NEW_REPL = '''.replace("{{NS}}", str(len(skip))) \\
        .replace("{{NR}}", str(len(pursue) + len(maybe) + len(skip)))'''

for name, old in (("body", OLD_BODY), ("stat", OLD_STAT), ("repl", OLD_REPL)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")
if "{{NR}}" in src:
    sys.exit("already patched - no change made")

shutil.copy(path, "app/dashboard/build.py.bak")
src = src.replace(OLD_BODY, NEW_BODY, 1)
src = src.replace(OLD_STAT, NEW_STAT, 1)
src = src.replace(OLD_REPL, NEW_REPL, 1)
path.write_text(src)
print("patched OK (backup at app/dashboard/build.py.bak)")

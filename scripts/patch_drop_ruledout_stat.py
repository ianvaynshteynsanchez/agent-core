"""Four stats, not five - the lane heading already carries the ruled-out count."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

OLD = '''    <div class="stat"><span class="n">{{NS}}</span><span class="l">Ruled out, with reasons</span></div>
'''

if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak6")
src = src.replace(OLD, "", 1)
path.write_text(src)
print("patched OK (backup at app/dashboard/build.py.bak6)")

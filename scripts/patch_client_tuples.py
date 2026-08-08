"""Finish the CLIENT patch: both insert sites name 5 columns but pass 4 values."""
import pathlib, shutil, sys

TARGETS = [
    ("app/profile/generate.py", "app/profile/generate.py.bak2",
     '''            (version, content, datetime.now(timezone.utc).isoformat(), note),''',
     '''            (version, CLIENT, content, datetime.now(timezone.utc).isoformat(), note),'''),
    ("scripts/new_profile_version.py", "scripts/new_profile_version.py.bak2",
     '''    (version, content, datetime.now(timezone.utc).isoformat(), note),''',
     '''    (version, CLIENT, content, datetime.now(timezone.utc).isoformat(), note),'''),
]

edits = []
for fname, bak, old, new in TARGETS:
    p = pathlib.Path(fname)
    s = p.read_text()
    if "CLIENT, content" in s:
        sys.exit(f"already patched ({fname}) - no change made")
    if old not in s:
        sys.exit(f"ANCHOR NOT FOUND ({fname}) - nothing written")
    s = s.replace(old, new, 1)
    if "from app.profile.load import" in s and "CLIENT" not in s.split("\n")[0:30]:
        pass
    edits.append((p, s, bak))

for p, s, bak in edits:
    shutil.copy(p, bak)
    p.write_text(s)
    print(f"patched {p}")
print("\nNOTE: both files now reference CLIENT - check each imports it.")

"""Parse a ## Clocks section from the profile: eligibility windows that close,
which matter more than any individual deadline and which no matcher surfaces."""
import pathlib, shutil, sys

path = pathlib.Path("app/profile/load.py")
src = path.read_text()

HELPER = '''def clocks(md=None):
    """Eligibility windows from the profile's '## Clocks' section.

    Format per line: name | earliest close | latest close | note
    An empty earliest means a single known date. Returns a list of dicts with
    days remaining computed against the latest close.
    """
    from datetime import date
    md = md or active()[1]
    block = _section(md, "Clocks")
    out = []
    for line in block.splitlines():
        line = line.strip().lstrip("-* ").strip()
        if not line or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        name, early, late = parts[0], parts[1], parts[2]
        note = parts[3] if len(parts) > 3 else ""
        try:
            late_d = date.fromisoformat(late)
        except ValueError:
            continue
        try:
            early_d = date.fromisoformat(early) if early else None
        except ValueError:
            early_d = None
        out.append({
            "name": name,
            "earliest": early_d.isoformat() if early_d else None,
            "latest": late_d.isoformat(),
            "days_left": (late_d - date.today()).days,
            "days_left_earliest": (early_d - date.today()).days if early_d else None,
            "note": note,
        })
    return sorted(out, key=lambda c: c["days_left"])


'''

if "def clocks(" in src:
    sys.exit("already patched - no change made")
if "def trap_terms(" not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/profile/load.py.bak2")
path.write_text(src.replace("def trap_terms(", HELPER + "def trap_terms(", 1))
print("patched OK")

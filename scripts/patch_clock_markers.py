"""Flag opportunities whose deadline falls at or past an eligibility window.
The banner says a window closes; this says which opportunities it costs you."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

HELPER = '''_CLOCK_CACHE = None


def _clocks_cached():
    global _CLOCK_CACHE
    if _CLOCK_CACHE is None:
        try:
            from app.profile.load import clocks as _c
            _CLOCK_CACHE = _c()
        except Exception:
            _CLOCK_CACHE = []
    return _CLOCK_CACHE


def clock_flag(due):
    """Marker if this deadline sits at or past an eligibility window.

    Three cases: clear of every window (no marker), inside the uncertain band
    between earliest and latest close (flag as uncertain), or past the latest
    close (flag as outside). Marks only - never reorders or hides, because the
    dates are hand-entered and a wrong one should be visible, not silent.
    """
    if not due:
        return ""
    items = _clocks_cached()
    if not items:
        return ""
    out = ""
    for c in items:
        latest, earliest = c.get("latest"), c.get("earliest")
        if latest and due >= latest:
            out += (f"<div class='clock-flag past'>\\u26a0 Due after your "
                    f"{_esc(c['name'])} closes ({_esc(latest)})</div>")
        elif earliest and due >= earliest:
            out += (f"<div class='clock-flag edge'>\\u26a0 May fall outside your "
                    f"{_esc(c['name'])} \\u2014 confirm with a program officer</div>")
    return out


'''

OLD_CARD = '''      {brief_block(a.get('id',''))}'''
NEW_CARD = '''      {clock_flag(a.get('due_date'))}
      {brief_block(a.get('id',''))}'''

CSS_OLD = '''.brief{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}'''
CSS_NEW = '''.clock-flag{margin-top:12px;padding:8px 10px;border-radius:6px;
  font-family:var(--mono);font-size:12px;line-height:1.5}
.clock-flag.past{background:rgba(210,153,34,.12);color:var(--warn)}
.clock-flag.edge{background:rgba(139,148,158,.12);color:var(--dim)}
.brief{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}'''

if "clock_flag" in src:
    sys.exit("already patched - no change made")
for name, old in (("card", OLD_CARD), ("css", CSS_OLD)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak12")
src = src.replace("def card(", HELPER + "def card(", 1)
src = src.replace(OLD_CARD, NEW_CARD, 1).replace(CSS_OLD, CSS_NEW, 1)
path.write_text(src)
print("patched OK")

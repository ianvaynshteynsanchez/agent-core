"""Render eligibility clocks at the top of the dashboard. A window that closes
outranks any individual deadline, and no matcher surfaces it."""
import pathlib, shutil, sys

path = pathlib.Path("app/dashboard/build.py")
src = path.read_text()

HELPER = '''def clocks_banner():
    """Eligibility windows, if the profile declares any."""
    try:
        from app.profile.load import clocks as _clocks
        items = _clocks()
    except Exception:
        return ""
    if not items:
        return ""
    rows = ""
    for c in items:
        d = c["days_left"]
        de = c.get("days_left_earliest")
        if de and de != d:
            span = f"{de // 30}\\u2013{d // 30} months left"
        else:
            span = f"~{d // 30} months left"
        urgent = " urgent" if d < 365 else ""
        window = (f"{c['earliest']} to {c['latest']}" if c["earliest"]
                  else f"by {c['latest']}")
        rows += (f"<li><span class='cl-name'>{_esc(c['name'])}</span>"
                 f"<span class='cl-span{urgent}'>{span}</span>"
                 f"<span class='cl-meta'>{_esc(window)} \\u00b7 {_esc(c['note'])}</span></li>")
    return (f"<section class='clocks'><h2>Eligibility windows</h2>"
            f"<p class='sub'>These close whether or not anything is open. "
            f"A window that expires removes every opportunity behind it.</p>"
            f"<ul>{rows}</ul></section>")


'''

OLD_BODY = '''    body = (
        opened_banner(just_opened)'''
NEW_BODY = '''    body = (
        clocks_banner()
        + opened_banner(just_opened)'''

CSS_OLD = '''.opened{background:rgba(63,185,80,.08);border:1px solid var(--go);'''
CSS_NEW = '''.clocks{background:rgba(88,166,255,.06);border:1px solid var(--line);
  border-radius:12px;padding:18px 22px;margin:0 0 28px}
.clocks h2{font-family:var(--serif);font-size:18px;margin:0 0 4px}
.clocks ul{list-style:none;margin:12px 0 0;padding:0}
.clocks li{padding:10px 0;border-top:1px solid var(--line);display:grid;
  grid-template-columns:1fr auto;gap:4px 16px}
.cl-name{font-weight:600;font-size:15px}
.cl-span{font-family:var(--mono);font-size:13px;color:var(--accent);text-align:right}
.cl-span.urgent{color:var(--warn)}
.cl-meta{grid-column:1/-1;color:var(--dim);font-size:12px;line-height:1.5}
.opened{background:rgba(63,185,80,.08);border:1px solid var(--go);'''

if "clocks_banner" in src:
    sys.exit("already patched - no change made")
for name, old in (("body", OLD_BODY), ("css", CSS_OLD)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/dashboard/build.py.bak11")
src = src.replace("def build():", HELPER + "def build():", 1)
src = src.replace(OLD_BODY, NEW_BODY, 1).replace(CSS_OLD, CSS_NEW, 1)
path.write_text(src)
print("patched OK")

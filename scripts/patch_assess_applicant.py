"""Make the assess prompt subject-agnostic and add a career-stage rule.
Also fix current_profile(), which selects without a client filter."""
import pathlib, shutil, sys

path = pathlib.Path("app/reason/assess.py")
src = path.read_text()

OLD_SKIP = '''- "skip": definite mismatch in modality/capability, OR an explicit exclusion
  or eligibility rule that rules the company out.'''
NEW_SKIP = '''- "skip": definite mismatch in modality/capability, OR an explicit exclusion
  or eligibility rule that rules the applicant out. Eligibility includes whether
  the applicant's institutional role and career stage permit holding this
  mechanism at all - a mechanism the applicant cannot hold is a skip regardless
  of how well the science fits.'''

OLD_PROF = '''    row = conn.execute(
        "SELECT version, content FROM profile ORDER BY version DESC LIMIT 1"
    ).fetchone()'''
NEW_PROF = '''    from app.profile.load import CLIENT
    row = conn.execute(
        "SELECT version, content FROM profile WHERE client=? "
        "ORDER BY version DESC LIMIT 1", (CLIENT,)
    ).fetchone()'''

if "career stage permit" in src:
    sys.exit("already patched - no change made")
for name, old in (("skip rule", OLD_SKIP), ("current_profile", OLD_PROF)):
    if old not in src:
        sys.exit(f"ANCHOR NOT FOUND ({name}) - nothing written")

shutil.copy(path, "app/reason/assess.py.bak")
src = src.replace(OLD_SKIP, NEW_SKIP, 1).replace(OLD_PROF, NEW_PROF, 1)
path.write_text(src)
print("patched OK (backup at app/reason/assess.py.bak)")

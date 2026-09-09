"""Strip the clinical-trial designation from NIH titles before assessment.

Two prompt edits failed to stop the model reading "(Independent Clinical Trial
Required)" as a requirement that the applicant already possess trial
infrastructure. Removing the string is not something the model can reason
around. Narrow by design: only parentheticals containing "clinical trial".
"""
import pathlib, shutil, sys

path = pathlib.Path("app/reason/assess.py")
src = path.read_text()

OLD = '''        title=opp["title"],'''
NEW = '''        title=_strip_ct_designation(opp["title"]),'''

HELPER = '''def _strip_ct_designation(title):
    """Remove a trailing parenthetical containing a clinical-trial designation.

    NIH titles carry "(K99/R00 Independent Clinical Trial Required)" and
    similar. The designation describes what a candidate's project may propose,
    not infrastructure the applicant must hold - but the reasoner repeatedly
    read it as the latter. Activity codes inside the same parenthetical are
    preserved by keeping anything before the designation phrase.
    """
    import re as _re
    if not title:
        return title
    out = _re.sub(
        r"\\s*[-\\u2014]?\\s*(?:Independent\\s+)?Clinical\\s+Trial\\s+"
        r"(?:Required|Optional|Not\\s+Allowed)\\s*",
        " ", title, flags=_re.IGNORECASE)
    out = _re.sub(r"\\(\\s*\\)", "", out)
    return _re.sub(r"\\s{2,}", " ", out).strip()


'''

if "_strip_ct_designation" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/reason/assess.py.bak6")
src = src.replace("def assess_one(", HELPER + "def assess_one(", 1)
src = src.replace(OLD, NEW, 1)
path.write_text(src)
print("patched OK")

"""Prompt still frames every subject as a company, which biases the model
toward organizational-capability reasoning for individual applicants. Also add
the NIH clinical-trial designation rule, which two labeled cases currently fail."""
import pathlib, shutil, sys

path = pathlib.Path("app/reason/assess.py")
src = path.read_text()

OLD_OPEN = '''You are a grant strategist deciding whether a company should spend
time pursuing a funding opportunity. Be skeptical. Most opportunities are NOT a
good fit, and recommending a bad one wastes the company's scarce proposal effort.

COMPANY CAPABILITY PROFILE:'''
NEW_OPEN = '''You are a grant strategist deciding whether an applicant should spend
time pursuing a funding opportunity. The applicant may be an organization or an
individual researcher - the profile below says which. Be skeptical. Most
opportunities are NOT a good fit, and recommending a bad one wastes scarce
proposal effort.

NIH announcement titles carry a clinical-trial designation in parentheses:
"Clinical Trial Required," "Optional," or "Not Allowed." On fellowship and
career development awards (F and K series) this describes what the candidate's
proposed project may include - the candidate designs that project. It is never a
statement that the applicant must already possess trial infrastructure, a
patient cohort, or prior trial experience. Do not treat it as one.

APPLICANT CAPABILITY PROFILE:'''

if "APPLICANT CAPABILITY PROFILE" in src:
    sys.exit("already patched - no change made")
if OLD_OPEN not in src:
    sys.exit("ANCHOR NOT FOUND - nothing written")

shutil.copy(path, "app/reason/assess.py.bak4")
path.write_text(src.replace(OLD_OPEN, NEW_OPEN, 1))
print("patched OK")

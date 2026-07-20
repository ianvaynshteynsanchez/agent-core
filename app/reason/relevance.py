# Coarse keyword gate. Deliberately high-recall: catch anything plausibly
# drug-delivery, let the LLM reasoner make the real call. Cheap, no tokens.

RELEVANT = [
    "drug delivery", "long acting", "long-acting", "controlled release",
    "sustained release", "extended release", "depot", "implant",
    "drug device", "drug-device", "biodegradable polymer", "bioresorbable",
    "reformulation", "medication adherence", "contracept", "burst release",
    "subcutaneous", "subdermal", "transdermal", "formulation",
    "therapeutic delivery", "biomaterial", "SBIR", "STTR",
]

# Hard excludes: agencies/domains that can't plausibly fit, to kill obvious noise.
EXCLUDE_TITLE = [
    "astrophysics", "aircraft", "fire training", "border security",
    "mine health", "SNAP", "artificial intelligence advancing",
]


def is_relevant(opp):
    hay = f"{opp.get('title','')} {opp.get('description','') or ''}".lower()
    if any(x.lower() in hay for x in EXCLUDE_TITLE):
        return False
    return any(k.lower() in hay for k in RELEVANT)

import re
from collections import Counter


def fingerprint(line):
    """Normalize digits so '5/12' and '6/12' look the same."""
    return re.sub(r"\d+", "#", line).strip()


def strip_repeated_lines(pages, threshold=0.5):
    """Drop lines appearing on >= threshold fraction of pages (headers/footers)."""
    if len(pages) < 3:
        return pages

    counts = Counter()
    for page in pages:
        for fp in {fingerprint(l) for l in page.split("\n") if len(fingerprint(l)) > 20}:
            counts[fp] += 1

    cutoff = len(pages) * threshold
    junk = {fp for fp, c in counts.items() if c >= cutoff}
    if junk:
        print(f"  stripping {len(junk)} repeated header/footer lines")

    return [
        "\n".join(l for l in page.split("\n") if fingerprint(l) not in junk)
        for page in pages
    ]

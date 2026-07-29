"""Fetch full NOFO text from the NIH guide for high-value opportunities.

grants.gov gives ~300-char stubs. The real eligibility, budget, and review
criteria live on the NIH guide page, which we construct from the announcement
number. Not all announcements are published yet - handle that gracefully.
"""
import re

import requests

BASE = "https://grants.nih.gov/grants/guide"
TIMEOUT = 30


def guide_url(native_id):
    """PA-25-303 -> .../pa-files/PA-25-303.html ; RFA-* -> rfa-files"""
    if not native_id:
        return None
    nid = native_id.strip().upper()
    if nid.startswith("RFA-"):
        folder = "rfa-files"
    elif nid.startswith(("PA-", "PAR-", "PAS-")):
        folder = "pa-files"
    else:
        return None
    return f"{BASE}/{folder}/{nid}.html"


def strip_html(html):
    """Crude but effective: drop scripts/styles, unwrap tags, collapse space."""
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html,
                  flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"</td>|</th>", " | ", html, flags=re.IGNORECASE)
    html = re.sub(r"</td>|</th>", " | ", html, flags=re.IGNORECASE)
    html = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&#39;", "'").replace("&quot;", '"'))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = _drop_related_notices(text)
    return text.strip()


def _drop_related_notices(text):
    """Cut the 'Related Notices' block - administrative policy churn full of
    dates that poison deadline retrieval. Runs from the heading to the next
    major section (Key Dates / Purpose / Funding Opportunity)."""
    start = text.find("Related Notices")
    if start < 0:
        return text
    tail = text[start + len("Related Notices"):]
    stops = [tail.find(m) for m in ("Key Dates", "Purpose", "Funding Opportunity Purpose")
             if tail.find(m) >= 0]
    if not stops:
        return text
    end = start + len("Related Notices") + min(stops)
    return text[:start] + text[end:]


def fetch_full_text(native_id):
    """Returns (text, url, status). status: ok | not_published | unsupported | error"""
    url = guide_url(native_id)
    if not url:
        return None, None, "unsupported"
    try:
        r = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        return None, url, f"error: {e}"

    if r.status_code == 404:
        return None, url, "not_published"
    if r.status_code != 200:
        return None, url, f"error: HTTP {r.status_code}"

    text = strip_html(r.text)
    # A real NOFO is tens of thousands of chars; a 404 page is ~5k of stripped text.
    if len(text) < 8000:
        return None, url, "not_published"
    return text, url, "ok"


if __name__ == "__main__":
    for nid in ["PAR-24-312", "RFA-OD-25-008", "PA-27-100"]:
        text, url, status = fetch_full_text(nid)
        n = len(text) if text else 0
        print(f"{nid:16} {status:16} {n:>8,} chars")
        if text:
            for section in ["Eligible Organizations", "Award Budget",
                            "Application Due Date", "Review Criteria"]:
                print(f"     {'FOUND' if section in text else '  -  '}  {section}")

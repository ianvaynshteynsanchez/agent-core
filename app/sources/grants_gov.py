import json
import time
from datetime import datetime, timezone

import requests

SEARCH_URL = "https://api.grants.gov/v1/api/search2"
FETCH_URL = "https://api.grants.gov/v1/api/fetchOpportunity"
TIMEOUT = 30


def _post(url, payload, tries=3):
    """Any source can be down. Fail soft, never crash the poll."""
    for attempt in range(tries):
        try:
            r = requests.post(url, json=payload, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                wait = 5 * (attempt + 1)
                print(f"  {url.split('/')[-1]}: {r.status_code}, retry in {wait}s")
                time.sleep(wait)
                continue
            print(f"  {url.split('/')[-1]}: HTTP {r.status_code}")
            return None
        except requests.RequestException as e:
            print(f"  request failed: {e}")
            time.sleep(5 * (attempt + 1))
    return None


def search(keyword=None, statuses="posted|forecasted", rows=100, agency=None):
    """Stage 1: cheap metadata. No descriptions, no tokens."""
    payload = {"rows": rows, "oppStatuses": statuses}
    if keyword:
        payload["keyword"] = keyword
    if agency:
        payload["agencies"] = agency

    data = _post(SEARCH_URL, payload)
    if not data:
        return []
    return data.get("data", {}).get("oppHits", [])


def fetch(opportunity_id):
    """Stage 2: full text. Only call this for rows that survive filtering."""
    data = _post(FETCH_URL, {"opportunityId": int(opportunity_id)})
    if not data:
        return None
    return data.get("data", {})


def _parse_date(s):
    """grants.gov mixes formats: '12/03/2027' and 'Dec 03, 2027 12:00:00 AM EST'."""
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%b %d, %Y %I:%M:%S %p %Z", "%b %d, %Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def to_row(hit, detail=None):
    """Map API shapes onto our opportunity schema."""
    now = datetime.now(timezone.utc).isoformat()
    syn = (detail or {}).get("synopsis", {}) if detail else {}

    return {
        "id": f"grants_gov:{hit['id']}",
        "source": "grants_gov",
        "native_id": hit.get("number"),
        "title": hit.get("title"),
        "agency": hit.get("agency"),
        "branch": syn.get("agencyDetails", {}).get("code"),
        "program": None,
        "phase": None,
        "status": hit.get("oppStatus"),
        "release_date": _parse_date(hit.get("openDate")),
        "open_date": _parse_date(hit.get("openDate")),
        "close_date": _parse_date(hit.get("closeDate")),
        "due_date": _parse_date(syn.get("responseDate")) or _parse_date(hit.get("closeDate")),
        "url": syn.get("fundingDescLinkUrl")
               or f"https://www.grants.gov/search-results-detail/{hit['id']}",
        "description": syn.get("synopsisDesc"),
        "raw_json": json.dumps({"hit": hit, "detail": detail}),
        "first_seen": now,
        "last_seen": now,
    }

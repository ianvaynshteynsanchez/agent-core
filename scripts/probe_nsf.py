import json
import requests

# NSF's funding search API (different endpoint from the awards one that ignored our filter)
tries = [
    ("nsf funding v1", "https://www.nsf.gov/awardsearch/download", {}),
    ("nsf api funding", "https://api.nsf.gov/services/v1/funding.json", {"keyword": "drug delivery"}),
    ("nsf oppsearch", "https://www.nsf.gov/funding/opportunities.jsp", {}),
]

for name, url, params in tries:
    try:
        r = requests.get(url, params=params, timeout=20)
        print(f"{name}: {r.status_code} | {r.headers.get('content-type','?')[:40]}")
        print(f"   {r.text[:200]}")
    except Exception as e:
        print(f"{name}: FAILED {e}")
    print()

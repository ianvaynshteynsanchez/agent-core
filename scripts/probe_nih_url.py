import requests

for nid in ["PA-27-100", "PA-27-101", "PA-27-102"]:
    url = f"https://grants.nih.gov/grants/guide/pa-files/{nid}.html"
    try:
        r = requests.get(url, timeout=20)
        print(f"{nid}: {r.status_code} | {len(r.text):,} chars")
        if r.status_code == 200:
            has = [s for s in ["Eligib", "Award Budget", "Review Criteria",
                               "Application and Submission"] if s in r.text]
            print(f"   sections found: {has}")
    except Exception as e:
        print(f"{nid}: FAILED {e}")

import requests

cases = [
    ("PAR-24-312", "pa-files"),
    ("RFA-OD-25-008", "rfa-files"),
    ("PA-27-100", "pa-files"),
]
for nid, folder in cases:
    url = f"https://grants.nih.gov/grants/guide/{folder}/{nid}.html"
    r = requests.get(url, timeout=20)
    print(f"{nid:16} {r.status_code}  {len(r.text):>8,} chars  {url}")

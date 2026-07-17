import json
import requests

URL = "https://api.www.sbir.gov/public/api/solicitations"

r = requests.get(URL, params={"agency": "HHS", "rows": 3}, timeout=30)
print("status:", r.status_code)

data = r.json()
print("type:", type(data).__name__)

if isinstance(data, dict):
    print("top-level keys:", list(data.keys()))
    print("\n--- raw (truncated) ---")
    print(json.dumps(data, indent=2)[:4000])
else:
    print("count:", len(data))
    print(json.dumps(data[0], indent=2)[:3000])

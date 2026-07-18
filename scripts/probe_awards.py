import json
import requests

print("=== SBIR.gov awards ===")
try:
    r = requests.get(
        "https://api.www.sbir.gov/public/api/awards",
        params={"firm": "Hera Health Solutions", "rows": 10},
        timeout=30,
    )
    print("status:", r.status_code)
    print(r.text[:1500])
except Exception as e:
    print("failed:", e)

print("\n=== NSF awards ===")
try:
    r = requests.get(
        "https://api.nsf.gov/services/v1/awards.json",
        params={"awardeeName": "Hera Health Solutions", "printFields":
                "id,title,date,awardeeName,fundsObligatedAmt,abstractText"},
        timeout=30,
    )
    print("status:", r.status_code)
    print(r.text[:2500])
except Exception as e:
    print("failed:", e)

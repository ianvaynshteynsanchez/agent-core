import requests

for kw in ['drug delivery', '"drug delivery"', 'bioerodible', 'implant']:
    r = requests.post(
        'https://api.grants.gov/v1/api/search2',
        json={'keyword': kw, 'rows': 3, 'oppStatuses': 'posted|forecasted'},
        timeout=30,
    )
    d = r.json()['data']
    print(f'{kw}: {d["hitCount"]} hits')
    for h in d['oppHits'][:3]:
        print('   ', h['title'][:65])
    print()

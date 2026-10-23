import json, re, sys, requests
sys.path.insert(0, ".")
S = requests.Session()
evs = []
for off in range(0, 2000, 100):
    r = S.get("https://gamma-api.polymarket.com/events", params={"tag_slug": "daily-temperature", "closed": "false", "limit": 100, "offset": off}, timeout=30).json()
    evs += r
    if len(r) < 100:
        break
vistos, out = set(), []
for e in sorted(evs, key=lambda e: e.get("endDate") or "", reverse=True):
    ciudad = e.get("slug", "").split("-on-")[0]
    if ciudad in vistos:
        continue
    vistos.add(ciudad)
    out.append({"slug": e["slug"], "resolutionSource": e.get("resolutionSource"),
                "description": (e.get("description") or "")[:1800],
                "cajas": [m.get("groupItemTitle") for m in e.get("markets") or []]})
json.dump(out, open("diag/por_ciudad.json", "w"), indent=1, ensure_ascii=False)
print(len(out))

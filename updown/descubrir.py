"""Paso 0 (una sola vez): encontrar como se llaman en gamma los mercados "Up or Down" de cripto.
Escribe updown/descubrimiento.json. Solo lee; no opera ni toca nada."""
import json, os, re, sys, time
import requests

S = requests.Session(); S.headers["User-Agent"] = "polymarket-clima-updown/0.1 (investigacion personal)"
G = "https://gamma-api.polymarket.com"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "descubrimiento.json")
res = {"series": [], "busqueda": {}, "tags": [], "eventos_muestra": {}}

def get(path, **p):
    for i in range(3):
        try:
            r = S.get(G + path, params=p, timeout=40)
            if r.status_code == 200:
                return r.json()
            print(path, p, r.status_code, file=sys.stderr)
        except Exception as ex:
            print(path, ex, file=sys.stderr)
        time.sleep(2)
    return None

# 1. series
for off in range(0, 3000, 100):
    j = get("/series", limit=100, offset=off)
    if not j:
        break
    for s in j:
        txt = json.dumps(s).lower()
        if re.search(r"up.?or.?down|updown|up-down|\b5m\b|\b15m\b|hourly", txt):
            res["series"].append({k: s.get(k) for k in ("id", "slug", "title", "seriesType", "recurrence", "active", "closed", "volume", "liquidity", "startDate", "createdAt")})
    if len(j) < 100:
        break

# 2. busqueda
for q in ["bitcoin up or down", "ethereum up or down", "solana up or down", "btc updown"]:
    j = get("/public-search", q=q, limit_per_type=20)
    if j:
        res["busqueda"][q] = {"events": [{k: e.get(k) for k in ("slug", "title", "seriesSlug", "startDate", "endDate", "closed")} for e in (j.get("events") or [])],
                              "tags": j.get("tags")}

# 3. tags
for off in range(0, 2000, 100):
    j = get("/tags", limit=100, offset=off)
    if not j:
        break
    for t in j:
        if re.search(r"up.?or.?down|updown|crypto|5m|15m|hourly|bitcoin", json.dumps(t).lower()):
            res["tags"].append({k: t.get(k) for k in ("id", "slug", "label")})
    if len(j) < 100:
        break

# 4. eventos de muestra por cada serie encontrada (abiertos y cerrados)
for s in res["series"][:40]:
    for cerrado in ("false", "true"):
        j = get("/events", series_slug=s["slug"], closed=cerrado, limit=3, order="endDate", ascending="false")
        if j:
            res["eventos_muestra"][f"{s['slug']}|{cerrado}"] = [
                {"slug": e.get("slug"), "title": e.get("title"), "startDate": e.get("startDate"), "endDate": e.get("endDate"),
                 "tags": [t.get("slug") for t in (e.get("tags") or [])],
                 "markets": [{k: m.get(k) for k in ("question", "conditionId", "outcomes", "outcomePrices", "clobTokenIds", "feesEnabled", "feeSchedule", "resolutionSource", "description", "closed", "startDate", "endDate", "volumeNum")} for m in (e.get("markets") or [])[:1]]}
                for e in j]
        time.sleep(0.2)
# 5. slugs adivinados (patron btc-updown-5m-<ts>)
ts = int(time.time()) // 300 * 300 - 3600
for slug in [f"btc-updown-5m-{ts}", f"btc-updown-15m-{int(time.time())//900*900-3600}", f"eth-updown-5m-{ts}"]:
    j = get("/events", slug=slug)
    res["eventos_muestra"]["adivinado|" + slug] = j

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print(f"series {len(res['series'])}, tags {len(res['tags'])}, muestras {len(res['eventos_muestra'])}")

"""Sonda (una sola vez): mira la forma de las respuestas de los endpoints de recompensas y reembolsos.
No opera. Guarda muestras chicas en maker/sonda/ (nada de archivos grandes)."""
import json
import os
import time
from collections import Counter, defaultdict

import requests

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonda")
os.makedirs(C, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-maker/1.0 (investigacion personal)"


def guardar(n, d):
    with open(os.path.join(C, n), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)


def get(url, **p):
    try:
        r = S.get(url, params=p, timeout=40)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:2000])
    except Exception as e:
        return -1, str(e)


# 1. mercados con recompensa: paginar con dedupe (la corrida anterior dio 100000 = cursor sin avanzar)
vistos, cursores, pags = {}, [], 0
cur = ""
for _ in range(60):
    st, d = get("https://clob.polymarket.com/rewards/markets/multi", **({"next_cursor": cur} if cur else {}))
    if st != 200 or not isinstance(d, dict):
        guardar("rewards_error.json", {"st": st, "d": d})
        break
    pags += 1
    nuevos = 0
    for m in d.get("data") or []:
        if m["condition_id"] not in vistos:
            vistos[m["condition_id"]] = m
            nuevos += 1
    cursores.append((d.get("next_cursor"), len(d.get("data") or []), nuevos, d.get("count"), d.get("limit")))
    cur = d.get("next_cursor")
    if not cur or cur == "LTE=" or nuevos == 0:
        break
print("paginas", pags, "mercados distintos con recompensa:", len(vistos))
guardar("rewards_paginas.json", cursores[:20])
guardar("rewards_muestra.json", list(vistos.values())[:3])
# resumen: pozo diario por mercado
pozo = Counter()
n = Counter()
for m in vistos.values():
    tasa = sum((x.get("rewards_daily_rate") or 0) for x in (m.get("rewards_config") or []))
    slug = m.get("event_slug") or ""
    grupo = ("temperatura" if "temperature" in slug else
             "cripto" if any(k in slug for k in ("bitcoin", "ethereum", "btc", "eth", "solana", "xrp")) else "otros")
    pozo[grupo] += tasa
    n[grupo] += 1
print("pozo diario US$ por grupo:", dict(pozo), "mercados:", dict(n))
guardar("rewards_resumen.json", {"pozo": pozo, "n": n,
                                  "temperatura": [{"slug": m["market_slug"], "pozo": m.get("rewards_config"),
                                                   "spread_max": m.get("rewards_max_spread"), "min": m.get("rewards_min_size"),
                                                   "comp": m.get("market_competitiveness"), "spread": m.get("spread")}
                                                  for m in vistos.values() if "temperature" in (m.get("event_slug") or "")][:40]})

# 2. trades con takerOnly=false
evs = S.get("https://gamma-api.polymarket.com/events", params={"tag_slug": "daily-temperature", "closed": "false", "limit": 5}, timeout=30).json()
guardar("evento_temp.json", {k: v for k, v in evs[0].items() if k != "markets"} | {"market0": evs[0]["markets"][0]})
cid = evs[0]["markets"][0]["conditionId"]
for t in ("true", "false"):
    st, d = get("https://data-api.polymarket.com/trades", market=cid, limit=20, takerOnly=t)
    guardar(f"trades_takerOnly_{t}.json", {"st": st, "d": d})

# 3. actividad REWARD / MAKER_REBATE de billeteras conocidas (lo que cobran de verdad)
for w in ("0x2e3ecedec4b004c61670f0dcda382ec0da1f0f92", "0x65f7226a82e093e5115e47ec2f4f7e733cd28b98"):
    for tipo in ("REWARD", "MAKER_REBATE"):
        todo, off = [], 0
        while off < 3000:
            st, d = get("https://data-api.polymarket.com/activity", user=w, limit=500, offset=off, type=tipo)
            if st != 200 or not isinstance(d, list) or not d:
                break
            todo += d
            off += 500
            if len(d) < 500:
                break
        guardar(f"activity_{w[:8]}_{tipo}.json", todo[:30])
        por_dia = defaultdict(float)
        for x in todo:
            por_dia[time.strftime("%Y-%m-%d", time.gmtime(x.get("timestamp") or 0))] += float(x.get("usdcSize") or 0)
        print(w[:8], tipo, len(todo), "total US$", round(sum(por_dia.values()), 2), "dias", len(por_dia))
        guardar(f"activity_{w[:8]}_{tipo}_por_dia.json", dict(sorted(por_dia.items())))
    st, d = get("https://clob.polymarket.com/rebates/current", date=time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400)), maker_address=w)
    guardar(f"rebates_{w[:8]}.json", {"st": st, "d": d if not isinstance(d, list) else d[:20]})

# 4. subgrafo de ordenes (quien es maker en cada llenado)
q = '{ orderFilledEvents(first: 3, orderBy: timestamp, orderDirection: desc) { id timestamp maker taker makerAssetId takerAssetId makerAmountFilled takerAmountFilled fee } }'
for url in ("https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn",
            "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/polymarket-orderbook-resync/prod/gn"):
    try:
        r = S.post(url, json={"query": q}, timeout=40)
        guardar(f"subgrafo_{url.split('/')[-3]}.json", {"st": r.status_code, "d": r.text[:3000]})
    except Exception as e:
        guardar(f"subgrafo_{url.split('/')[-3]}.json", {"err": str(e)})

# 5. POST /books en lote
tok = [json.loads(m["clobTokenIds"])[0] for e in evs for m in e["markets"] if m.get("clobTokenIds")][:30]
r = S.post("https://clob.polymarket.com/books", json=[{"token_id": t} for t in tok], timeout=40)
guardar("books_lote.json", {"st": r.status_code, "n": len(r.json()) if r.status_code == 200 else None,
                             "muestra": (r.json()[:1] if r.status_code == 200 else r.text[:500])})
print("listo")

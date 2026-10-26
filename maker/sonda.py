"""Sonda (una sola vez): mira la forma de las respuestas de los endpoints de recompensas y reembolsos.
No opera. Guarda muestras en maker/sonda/."""
import json
import os
import time
from collections import Counter

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


# 1. mercados con recompensa (todas las paginas)
todos, cur = [], ""
for _ in range(200):
    st, d = get("https://clob.polymarket.com/rewards/markets/multi", page_size=500, **({"next_cursor": cur} if cur else {}))
    if st != 200 or not isinstance(d, dict):
        guardar("rewards_error.json", {"st": st, "d": d})
        break
    todos += d.get("data") or []
    cur = d.get("next_cursor")
    if not cur or cur == "LTE=":
        break
guardar("rewards_muestra.json", todos[:5])
print("mercados con recompensa:", len(todos))
claves = Counter(k for m in todos for k in m)
print(claves.most_common(60))
guardar("rewards_todos.json", todos)

# 2. el endpoint viejo /rewards/markets (por si da otra cosa)
st, d = get("https://clob.polymarket.com/rewards/markets/current")
guardar("rewards_current.json", {"st": st, "d": d if not isinstance(d, dict) else {k: (v[:5] if isinstance(v, list) else v) for k, v in d.items()}})

# 3. trades de un mercado de temperatura con takerOnly=false
evs = S.get("https://gamma-api.polymarket.com/events", params={"tag_slug": "daily-temperature", "closed": "false", "limit": 5}, timeout=30).json()
guardar("evento_temp.json", evs[:1])
cid = evs[0]["markets"][0]["conditionId"]
for t in ("true", "false"):
    st, d = get("https://data-api.polymarket.com/trades", market=cid, limit=50, takerOnly=t)
    guardar(f"trades_takerOnly_{t}.json", {"st": st, "d": d})

# 4. actividad de billeteras conocidas (hello.67 y la segunda de rivales/) con tipo REWARD / MAKER_REBATE
for w in ("0x2e3ecedec4b004c61670f0dcda382ec0da1f0f92", "0x65f7226a82e093e5115e47ec2f4f7e733cd28b98"):
    for tipo in ("REWARD", "MAKER_REBATE", None):
        p = {"user": w, "limit": 100}
        if tipo:
            p["type"] = tipo
        st, d = get("https://data-api.polymarket.com/activity", **p)
        guardar(f"activity_{w[:8]}_{tipo}.json", {"st": st, "d": d})
        if isinstance(d, list):
            print(w[:8], tipo, len(d), Counter(x.get("type") for x in d))
    st, d = get("https://clob.polymarket.com/rebates/current", date=time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400)), maker_address=w)
    guardar(f"rebates_{w[:8]}.json", {"st": st, "d": d})

# 5. subgrafo de ordenes (para ver quien es el maker de cada llenado)
q = '{ orderFilledEvents(first: 5, orderBy: timestamp, orderDirection: desc) { id timestamp maker taker makerAssetId takerAssetId makerAmountFilled takerAmountFilled fee } }'
for url in ("https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn",
            "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/polymarket-orderbook-resync/prod/gn"):
    try:
        r = S.post(url, json={"query": q}, timeout=40)
        guardar(f"subgrafo_{url.split('/')[-3]}.json", {"st": r.status_code, "d": r.text[:3000]})
    except Exception as e:
        guardar(f"subgrafo_{url.split('/')[-3]}.json", {"err": str(e)})

# 6. POST /books en lote
tok = [json.loads(m["clobTokenIds"])[0] for e in evs for m in e["markets"]][:30]
r = S.post("https://clob.polymarket.com/books", json=[{"token_id": t} for t in tok], timeout=40)
guardar("books_lote.json", {"st": r.status_code, "n": len(r.json()) if r.status_code == 200 else None,
                             "muestra": (r.json()[:1] if r.status_code == 200 else r.text[:500])})
print("listo")

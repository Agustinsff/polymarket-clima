"""
INVESTIGACION (sin operar): mercados de clima de Polymarket que NO son la temperatura diaria por ciudad
(anomalia global del mes, lluvia, nieve, huracanes, etc.).

Baja de Polymarket (corre en GitHub Actions porque el contenedor no llega):
  otros_clima/datos/tags.csv          etiquetas de gamma que parecen de clima
  otros_clima/datos/mercados.csv.gz   un renglon por mercado: evento, pregunta, regla, fuente, fechas, volumen, precio final
  otros_clima/datos/libros.csv.gz     libro actual (bid/ask y costo de 10/50/100 acciones) de los mercados abiertos
  otros_clima/datos/precios.csv.gz    historia de precio por hora del Si de los mercados cerrados (para calibracion)
El analisis va aparte (otros_clima/analizar.py).

Uso: python otros_clima/bajar.py
"""

import csv
import gzip
import json
import os
import re
import time
from datetime import datetime, timezone

import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(CARPETA, "datos")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-otros/1.0 (investigacion personal)"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
CLIMA = re.compile(r"weather|climate|hurricane|temperat|rain|snow|storm|tornado|heat|precip|nino|nina|arctic|"
                   r"sea-ice|cyclone|typhoon|flood|drought|wildfire|noaa|nasa-giss|global-temp", re.I)
DATA = "https://data-api.polymarket.com/trades"
# familias donde bajamos todas las operaciones de los cerrados (lo demas es contexto)
FAMILIAS = re.compile(r"temperature increase|hottest|precipitation|inches of snow|tornado|named storms|hurricanes will form|"
                      r"sea ice|earthquakes|rain in|rainfall|el ni", re.I)
DIARIA = re.compile(r"^(highest|lowest)-temperature-in-")


def log(m):
    print(datetime.now(timezone.utc).strftime("%H:%M:%S"), m, flush=True)


def get(url, params=None):
    for i in range(5):
        try:
            r = S.get(url, params=params, timeout=40)
            if r.status_code == 429:
                time.sleep(5 * (i + 1))
                continue
            if r.status_code >= 400:
                log(f"{r.status_code} {url} {params} {r.text[:200]}")
                return None
            return r.json()
        except Exception as ex:
            log(f"error {url}: {ex}")
            time.sleep(3 * (i + 1))
    return None


def tags():
    out, off = [], 0
    while off < 20000:
        r = get(GAMMA + "/tags", {"limit": 100, "offset": off})
        if not r:
            break
        out += r
        if len(r) < 100:
            break
        off += 100
    log(f"{len(out)} etiquetas en gamma")
    return [t for t in out if CLIMA.search((t.get("slug") or "") + " " + (t.get("label") or ""))]


def eventos(slug, cerrado):
    """offset llega hasta 2100; despues sigue con /events/keyset"""
    out, off = [], 0
    while off < 2100:
        r = get(GAMMA + "/events", {"tag_slug": slug, "closed": cerrado, "limit": 100, "offset": off,
                                    "order": "endDate", "ascending": "false"})
        if not r:
            break
        out += r
        if len(r) < 100:
            break
        off += 100
    else:
        cursor, vistos = None, {e["id"] for e in out}
        for _ in range(200):
            p = {"tag_slug": slug, "closed": cerrado, "limit": 100}
            if cursor:
                p["next_cursor"] = cursor
            r = get(GAMMA + "/events/keyset", p)
            if not r:
                break
            lote = (r.get("events") or r.get("data") or []) if isinstance(r, dict) else r
            if _ == 0:
                log(f"keyset claves: {list(r)[:10] if isinstance(r, dict) else 'lista'}")
            nuevos = [e for e in lote if e["id"] not in vistos]
            vistos |= {e["id"] for e in nuevos}
            out += nuevos
            cursor = r.get("next_cursor") if isinstance(r, dict) else None
            if not lote or not cursor:
                break
    return out


def costo(niveles, n):
    """precio medio de llenar n acciones recorriendo los niveles [(precio, tamano)], None si no alcanza"""
    falta, gasto = n, 0.0
    for p, s in niveles:
        q = min(falta, s)
        gasto += q * p
        falta -= q
        if falta <= 1e-9:
            return round(gasto / n, 4)
    return None


def main():
    os.makedirs(DATOS, exist_ok=True)
    ts = tags()
    with open(os.path.join(DATOS, "tags.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug", "label"])
        for t in ts:
            w.writerow([t.get("id"), t.get("slug"), t.get("label")])
    slugs = sorted({t["slug"] for t in ts if t.get("slug")} | {"weather", "climate", "hurricanes", "climate-science"})
    log("etiquetas de clima: " + ", ".join(slugs))

    evs = {}
    for s in slugs:
        if s == "daily-temperature":
            continue
        for cerrado in ("false", "true"):
            r = eventos(s, cerrado)
            n0 = len(evs)
            for e in r:
                if DIARIA.match(e.get("slug") or ""):
                    continue
                e.setdefault("_tags", set()).add(s)
                if e["id"] in evs:
                    evs[e["id"]]["_tags"].add(s)
                else:
                    evs[e["id"]] = e
            log(f"{s} cerrado={cerrado}: {len(r)} eventos, {len(evs) - n0} nuevos (sin diarias)")
    log(f"{len(evs)} eventos de clima que no son la temperatura diaria")

    filas = []
    for e in evs.values():
        for mk in e.get("markets") or []:
            try:
                toks = json.loads(mk.get("clobTokenIds") or "[]")
                precios = json.loads(mk.get("outcomePrices") or "[]")
                nombres = json.loads(mk.get("outcomes") or "[]")
            except Exception:
                toks, precios, nombres = [], [], []
            filas.append({
                "evento_id": e.get("id"), "evento_slug": e.get("slug"), "evento": e.get("title"),
                "tags": "|".join(sorted(e["_tags"])), "mercado_id": mk.get("id"), "condition_id": mk.get("conditionId") or "", "neg_risk": mk.get("negRisk"), "slug": mk.get("slug"),
                "pregunta": mk.get("question"), "caja": mk.get("groupItemTitle") or "",
                "resultados": "|".join(nombres), "token_si": toks[0] if toks else "",
                "token_no": toks[1] if len(toks) > 1 else "", "precio_final_si": precios[0] if precios else "",
                "cerrado": mk.get("closed"), "activo": mk.get("active"),
                "inicio": mk.get("startDate") or e.get("startDate") or "", "fin": mk.get("endDate") or e.get("endDate") or "",
                "cerrado_hora": mk.get("closedTime") or "", "volumen": mk.get("volumeNum") or mk.get("volume") or "",
                "liquidez": mk.get("liquidityNum") or mk.get("liquidity") or "", "best_bid": mk.get("bestBid") or "",
                "best_ask": mk.get("bestAsk") or "", "ultimo": mk.get("lastTradePrice") or "",
                "comision": json.dumps(mk.get("feeSchedule")) if mk.get("feeSchedule") else (mk.get("feesEnabled") or ""),
                "uma": mk.get("umaResolutionStatus") or "",
                "fuente": mk.get("resolutionSource") or e.get("resolutionSource") or "",
                "regla": re.sub(r"\s+", " ", mk.get("description") or e.get("description") or "")[:2500],
            })
    if not filas:
        log("sin mercados")
        return
    with gzip.open(os.path.join(DATOS, "mercados.csv.gz"), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    log(f"{len(filas)} mercados")

    # --- libro actual de los abiertos ------------------------------------------------
    abiertos = [x for x in filas if x["cerrado"] in (False, "False", "false") and x["token_si"]]
    with gzip.open(os.path.join(DATOS, "libros.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mercado_id", "hora", "bid", "ask", "prof_bid_usd", "prof_ask_usd",
                    "compra10", "compra50", "compra100", "venta10", "venta50", "venta100"])
        for i, x in enumerate(abiertos):
            b = get(CLOB + "/book", {"token_id": x["token_si"]})
            if not b:
                continue
            bids = sorted(((float(l["price"]), float(l["size"])) for l in b.get("bids") or []), reverse=True)
            asks = sorted((float(l["price"]), float(l["size"])) for l in b.get("asks") or [])
            w.writerow([x["mercado_id"], datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        bids[0][0] if bids else "", asks[0][0] if asks else "",
                        round(sum(p * s for p, s in bids), 2), round(sum(p * s for p, s in asks), 2),
                        costo(asks, 10), costo(asks, 50), costo(asks, 100),
                        costo(bids, 10), costo(bids, 50), costo(bids, 100)])
            if i % 100 == 0:
                log(f"libros {i}/{len(abiertos)}")

    # --- historia de precio por hora de los cerrados ------------------------------------
    # interval=max viene vacio en los mercados viejos: se pide por tramos de 14 dias entre inicio y fin+30 dias
    cerrados = [x for x in filas if x["cerrado"] in (True, "True", "true") and x["token_si"]]
    ahora = int(time.time())
    n, vacios = 0, 0
    with gzip.open(os.path.join(DATOS, "precios.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mercado_id", "t", "p"])
        for i, x in enumerate(cerrados):
            h = []
            try:
                t0 = int(datetime.fromisoformat(x["inicio"].replace("Z", "+00:00")).timestamp())
                t1 = min(int(datetime.fromisoformat(x["fin"].replace("Z", "+00:00")).timestamp()) + 30 * 86400, ahora)
            except Exception:
                t0 = t1 = None
            if t0 and t1 and t1 > t0 and FAMILIAS.search(x["evento"] or ""):
                for a in range(max(t0, t1 - 400 * 86400), t1, 14 * 86400):
                    r = get(CLOB + "/prices-history", {"market": x["token_si"], "startTs": a,
                                                       "endTs": min(a + 14 * 86400, t1), "fidelity": 60})
                    h += (r or {}).get("history") or []
            else:
                r = get(CLOB + "/prices-history", {"market": x["token_si"], "interval": "max", "fidelity": 60})
                h = (r or {}).get("history") or []
            if not h:
                vacios += 1
            for y in h:
                w.writerow([x["mercado_id"], y.get("t"), y.get("p")])
            n += len(h)
            if i % 200 == 0:
                log(f"precios {i}/{len(cerrados)}: {n} puntos, {vacios} vacios")
    log(f"precios: {n} puntos, {vacios} mercados sin historia")

    # --- operaciones (lado taker) de los cerrados de las familias que interesan ----------
    sel = [x for x in cerrados if x["condition_id"] and FAMILIAS.search(x["evento"] or "")]
    n = 0
    with gzip.open(os.path.join(DATOS, "trades.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mercado_id", "outcome_index", "side", "price", "size", "timestamp", "wallet"])
        for i, x in enumerate(sel):
            off = 0
            while True:
                r = get(DATA, {"market": x["condition_id"], "limit": 1000, "offset": off, "takerOnly": "true"})
                if not r:
                    break
                for t in r:
                    w.writerow([x["mercado_id"], t.get("outcomeIndex"), t.get("side"), t.get("price"), t.get("size"),
                                t.get("timestamp"), t.get("proxyWallet")])
                n += len(r)
                if len(r) < 1000 or off >= 3000:
                    if off >= 3000 and len(r) == 1000:
                        log(f"tope de 4000 operaciones en {x['slug']}")
                    break
                off += 1000
            if i % 100 == 0:
                log(f"operaciones {i}/{len(sel)}: {n}")
    log(f"{n} operaciones en {len(sel)} mercados")

if __name__ == "__main__":
    main()

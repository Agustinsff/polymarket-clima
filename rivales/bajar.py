"""
INVESTIGACION (sin operar): quien nos gana del otro lado en los mercados de temperatura.

Baja de Polymarket, para los eventos de temperatura cerrados de los ultimos N dias:
  rivales/eventos.csv.gz   un renglon por caja: evento, ciudad, fecha, conditionId, tokens, si gano
  rivales/trades.csv.gz    todas las operaciones (lado taker) de esas cajas: billetera, lado, precio, tamano, hora
  rivales/precios.csv.gz   historia de precio por minuto (clob prices-history) de las cajas de los ultimos dias
El analisis se hace aparte (rivales/analizar.py). Corre en GitHub Actions porque el contenedor no llega a Polymarket.

Uso: python rivales/bajar.py DIAS [DIAS_PRECIOS]
"""

import csv
import gzip
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-rivales/1.0 (investigacion personal)"
GAMMA = "https://gamma-api.polymarket.com/events"
DATA = "https://data-api.polymarket.com/trades"
CLOB = "https://clob.polymarket.com/prices-history"


def log(m):
    print(datetime.now(timezone.utc).strftime("%H:%M:%S"), m, flush=True)


def get(url, params, intentos=5):
    for i in range(intentos):
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


def eventos(dias):
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out, off = [], 0
    while True:
        r = get(GAMMA, {"tag_slug": "daily-temperature", "closed": "true", "limit": 100, "offset": off,
                        "end_date_min": desde, "order": "endDate", "ascending": "false"})
        if not r:
            break
        out += r
        log(f"gamma offset {off}: {len(r)} eventos")
        if len(r) < 100:
            break
        off += 100
    return out


def main():
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 21
    dias_precios = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    evs = eventos(dias)
    log(f"{len(evs)} eventos cerrados en {dias} dias")
    if evs:
        e0 = dict(evs[0])
        m0 = (e0.pop("markets", None) or [{}])[0]
        log("ejemplo evento: " + json.dumps({k: e0[k] for k in list(e0)[:40]}, default=str)[:3000])
        log("ejemplo mercado: " + json.dumps(m0, default=str)[:3000])

    filas_ev = []
    for e in evs:
        m = re.match(r"^(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})", e.get("slug", ""))
        if not m:
            continue
        fecha = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%B %d %Y").date().isoformat()
        src = e.get("resolutionSource") or ""
        for mk in e.get("markets") or []:
            try:
                toks = json.loads(mk.get("clobTokenIds") or "[]")
                precios = json.loads(mk.get("outcomePrices") or "[]")
            except Exception:
                toks, precios = [], []
            filas_ev.append({
                "evento_id": e.get("id"), "slug": e["slug"], "tipo": m.group(1), "ciudad": m.group(2), "fecha": fecha,
                "fuente": src, "caja": mk.get("groupItemTitle") or mk.get("question"),
                "condition_id": mk.get("conditionId"), "token_si": toks[0] if toks else "",
                "token_no": toks[1] if len(toks) > 1 else "", "precio_final_si": precios[0] if precios else "",
                "inicio_mercado": mk.get("startDate") or e.get("startDate") or "", "fin": mk.get("endDate") or e.get("endDate") or "",
                "cerrado_hora": mk.get("closedTime") or "", "volumen": mk.get("volumeNum") or mk.get("volume") or "",
                "fee": mk.get("feesEnabled") if "feesEnabled" in mk else "",
            })
    with gzip.open(os.path.join(CARPETA, "eventos.csv.gz"), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_ev[0]))
        w.writeheader()
        w.writerows(filas_ev)
    log(f"{len(filas_ev)} cajas")

    # --- operaciones -----------------------------------------------------------
    campos = ["condition_id", "asset", "outcome_index", "side", "price", "size", "timestamp", "wallet", "name",
              "pseudonym", "tx"]
    n_tot, primero = 0, True
    with gzip.open(os.path.join(CARPETA, "trades.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(campos)
        for i, fe in enumerate(filas_ev):
            cid = fe["condition_id"]
            if not cid:
                continue
            off = 0
            while True:
                r = get(DATA, {"market": cid, "limit": 1000, "offset": off, "takerOnly": "true"})
                if not r:
                    break
                if primero:
                    log("ejemplo trade: " + json.dumps(r[0], default=str)[:1500])
                    primero = False
                for t in r:
                    w.writerow([cid, t.get("asset"), t.get("outcomeIndex"), t.get("side"), t.get("price"), t.get("size"),
                                t.get("timestamp"), t.get("proxyWallet"), (t.get("name") or "")[:40],
                                (t.get("pseudonym") or "")[:40], t.get("transactionHash")])
                n_tot += len(r)
                if len(r) < 1000 or off >= 9000:
                    if off >= 9000 and len(r) == 1000:
                        log(f"tope de 10000 operaciones en {fe['slug']} {fe['caja']}")
                    break
                off += 1000
            if i % 200 == 0:
                log(f"cajas {i}/{len(filas_ev)}, operaciones {n_tot}")
    log(f"{n_tot} operaciones")

    # --- historia de precios por minuto (ultimos dias) ---------------------------
    lim = (datetime.now(timezone.utc) - timedelta(days=dias_precios)).date().isoformat()
    n_p, vacios = 0, 0
    with gzip.open(os.path.join(CARPETA, "precios.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition_id", "t", "p"])
        sel = [fe for fe in filas_ev if fe["fecha"] >= lim and fe["token_si"]]
        for i, fe in enumerate(sel):
            try:
                fin = int(datetime.fromisoformat(fe["fin"].replace("Z", "+00:00")).timestamp())
            except Exception:
                fin = int(time.time())
            fin = min(fin + 86400, int(time.time()))
            r = get(CLOB, {"market": fe["token_si"], "startTs": fin - 4 * 86400, "endTs": fin, "fidelity": 1})
            h = (r or {}).get("history") or []
            if not h:
                r = get(CLOB, {"market": fe["token_si"], "interval": "max", "fidelity": 1})
                h = (r or {}).get("history") or []
            if not h:
                vacios += 1
            for x in h:
                w.writerow([fe["condition_id"], x.get("t"), x.get("p")])
            n_p += len(h)
            if i % 200 == 0:
                log(f"precios {i}/{len(sel)}: {n_p} puntos, {vacios} vacios")
    log(f"precios: {n_p} puntos, {vacios} cajas sin historia")


if __name__ == "__main__":
    main()

"""
INVESTIGACION (sin operar): ¿dejar ordenes como maker paga? Ver maker/REGLA.md.

Cada INTERVALO segundos saca una foto del libro de todas las cajas vivas de temperatura y de las series
de cripto que sigue cripto.py, y simula una orden nuestra de TAM acciones por lado a 1 c (y a 2 c) del
precio medio:
  maker/datos/fotos_AAAA-MM-DD.csv.gz    una fila por caja y foto: pozo, competencia, estimacion de recompensa
  maker/datos/llenados.csv               cada vez que un taker opero a un precio peor que nuestra orden
  maker/datos/estado.json

Uso: python maker/medir.py MINUTOS   (lo encadena el workflow maker.yml en la rama medidor-maker)
"""

import csv
import gzip
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from estaciones import TZ, tasa_de  # noqa: E402
import pronostico  # noqa: E402
import cripto  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FIN = date(2026, 11, 9)
INTERVALO = 300            # segundos entre fotos
TAM = 100                  # acciones por lado
DISTANCIAS = [0.01, 0.02]  # a cuantos centavos del medio ponemos la orden
REBATE = {"clima": 0.25, "cripto": 0.20}
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
F_LLEN = os.path.join(CARPETA, "llenados.csv")
F_EST = os.path.join(CARPETA, "estado.json")
S = pronostico.S
BOOKS = "https://clob.polymarket.com/books"
TRADES = "https://data-api.polymarket.com/trades"

COLS = ["ts", "grupo", "serie", "evento", "caja", "cid", "hora_local", "horas_hasta_fin", "tasa", "pozo",
        "spread_max", "tam_min", "medio", "bid", "ask", "bid_tam", "ask_tam", "comp"]
for d in DISTANCIAS:
    COLS += [f"rec_{int(d * 100)}c", f"nbid_{int(d * 100)}c", f"nask_{int(d * 100)}c"]
COLS_LLEN = ["ts", "ts_foto", "grupo", "serie", "evento", "caja", "cid", "token", "dist_c", "lado", "precio_nuestro",
             "acciones", "precio_taker", "tasa", "reembolso", "medio_foto", "fin_evento", "gano"]


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def leer_json(n, defecto):
    try:
        with open(n, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def guardar_json(n, d):
    with open(n + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(n + ".tmp", n)


def puntaje(v, s):
    return ((v - s) / v) ** 2 if 0 <= s < v else 0.0


def redondear(p, tick, abajo):
    k = p / tick
    k = math.floor(k + 1e-9) if abajo else math.ceil(k - 1e-9)
    return round(k * tick, 4)


# ---------------------------------------------------------------------------
# cajas vivas (misma lista que libros.py) con los datos de recompensa de gamma
# ---------------------------------------------------------------------------

def datos_caja(m):
    if m.get("closed") or not m.get("clobTokenIds") or not m.get("conditionId"):
        return None
    try:
        p = float(json.loads(m.get("outcomePrices") or "[]")[0])
    except (ValueError, IndexError):
        return None
    if not 0.03 <= p <= 0.97:
        return None
    pozo = sum((x.get("rewardsDailyRate") or 0) for x in (m.get("clobRewards") or []))
    return {"caja": m.get("groupItemTitle") or m.get("question", ""), "cid": m["conditionId"],
            "token": json.loads(m["clobTokenIds"])[0], "tasa": tasa_de(m), "pozo": pozo,
            "spread_max": (m.get("rewardsMaxSpread") or 0) / 100, "tam_min": m.get("rewardsMinSize") or 0,
            "tick": float(m.get("orderPriceMinTickSize") or 0.01)}


def cajas_vivas(ahora):
    out = []
    try:
        for e in pronostico.eventos_abiertos():
            fin = datetime.fromisoformat(e["fin"].replace("Z", "+00:00")) if e.get("fin") else None
            hl = ahora.astimezone(ZoneInfo(TZ[e["ciudad"]])).hour
            for m in e["markets"]:
                c = datos_caja(m)
                if c:
                    c.update(grupo="clima", serie=f"{e['tipo']}|{e['ciudad']}", evento=e["slug"], hora_local=hl,
                             horas=round((fin - ahora).total_seconds() / 3600, 1) if fin else "",
                             fin=e.get("fin") or "")
                    out.append(c)
    except Exception as ex:
        log(f"clima fallo: {ex}")
    n_clima = len(out)
    for activo, tipo, serie in cripto.SERIES:
        try:
            evs = S.get("https://gamma-api.polymarket.com/events",
                        params={"series_slug": serie, "closed": "false", "limit": 50}, timeout=30).json()
        except Exception as ex:
            log(f"gamma fallo {serie}: {ex}")
            continue
        for e in evs:
            if not e.get("endDate"):
                continue
            horas = (datetime.fromisoformat(e["endDate"].replace("Z", "+00:00")) - ahora).total_seconds() / 3600
            if not 0 < horas <= 72:
                continue
            for m in e.get("markets", []):
                c = datos_caja(m)
                if c:
                    c.update(grupo="cripto", serie=f"{activo}|{tipo}", evento=e["slug"], hora_local=ahora.hour,
                             horas=round(horas, 1), fin=e["endDate"])
                    out.append(c)
    log(f"{n_clima} cajas de clima y {len(out) - n_clima} de cripto")
    return out


def libros(tokens):
    """POST /books en lotes de 50: {token: (bids, asks)} ordenados del mejor al peor."""
    out = {}
    for i in range(0, len(tokens), 50):
        lote = tokens[i:i + 50]
        try:
            r = S.post(BOOKS, json=[{"token_id": t} for t in lote], timeout=40)
            r.raise_for_status()
            for b in r.json():
                bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
                asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
                out[b["asset_id"]] = (bids, asks)
        except Exception as ex:
            log(f"books fallo: {ex}")
    return out


def trades_desde(cid, desde_ts):
    """Operaciones taker de la caja posteriores a desde_ts, en terminos del token Yes:
    [(ts, lado_taker 'BUY'/'SELL' del Yes, precio Yes, acciones)]."""
    out = []
    for intento in range(2):
        try:
            r = S.get(TRADES, params={"market": cid, "limit": 100, "takerOnly": "true"}, timeout=30)
            r.raise_for_status()
            break
        except Exception:
            time.sleep(2)
    else:
        return None
    for t in r.json() or []:
        ts = int(t.get("timestamp") or 0)
        if ts <= desde_ts:
            continue
        p, q = float(t.get("price") or 0), float(t.get("size") or 0)
        lado = t.get("side")
        if t.get("outcomeIndex") == 1:      # opero el token No: lo pasamos a Yes
            p, lado = 1 - p, ("SELL" if lado == "BUY" else "BUY")
        out.append((ts, lado, round(p, 4), q))
    return out


# ---------------------------------------------------------------------------

def foto(est):
    ahora = datetime.now(timezone.utc)
    ts = int(ahora.timestamp())
    cajas = cajas_vivas(ahora)
    libs = libros([c["token"] for c in cajas])
    filas, ordenes = [], {}
    for c in cajas:
        lib = libs.get(c["token"])
        if not lib or not lib[0] or not lib[1]:
            continue
        bids, asks = lib
        medio = (bids[0][0] + asks[0][0]) / 2
        v, minimo = c["spread_max"], c["tam_min"]
        if v > 0:
            q1 = sum(puntaje(v, medio - p) * t for p, t in bids if t >= minimo)
            q2 = sum(puntaje(v, p - medio) * t for p, t in asks if t >= minimo)
            comp = max(min(q1, q2), max(q1, q2) / 3) if 0.10 <= medio <= 0.90 else min(q1, q2)
        else:
            comp = ""
        fila = [ts, c["grupo"], c["serie"], c["evento"], c["caja"], c["cid"], c["hora_local"], c["horas"], c["tasa"],
                c["pozo"], c["spread_max"], minimo, round(medio, 4), bids[0][0], asks[0][0],
                round(bids[0][1], 1), round(asks[0][1], 1), round(comp, 2) if comp != "" else ""]
        for d in DISTANCIAS:
            tam = max(TAM, minimo)
            nb = redondear(medio - d, c["tick"], True)
            na = redondear(medio + d, c["tick"], False)
            if v > 0 and c["pozo"] > 0:
                # Q_min de la formula oficial: el menor de los dos lados (los dos de 'tam' acciones)
                nuestro = min(puntaje(v, medio - nb), puntaje(v, na - medio)) * tam
                rec = round(c["pozo"] * nuestro / (nuestro + comp), 3) if nuestro > 0 else 0
            else:
                rec = 0
            fila += [rec, nb, na]
            ordenes[(c["token"], d)] = (c, nb, na, tam, medio)
        filas.append(fila)
    # guardar la foto
    os.makedirs(CARPETA, exist_ok=True)
    f_dia = os.path.join(CARPETA, f"fotos_{ahora:%Y-%m-%d}.csv.gz")
    nuevo = not os.path.exists(f_dia)
    with gzip.open(f_dia, "at", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(COLS)
        w.writerows(filas)
    log(f"{len(filas)} cajas guardadas")
    # llenados: comparar las ordenes de la foto ANTERIOR con lo que se opero desde entonces
    CL = ["cid", "token", "grupo", "serie", "evento", "caja", "nb", "na", "tam", "medio", "tasa", "dist", "fin"]
    previas = [dict(zip(CL, o)) for o in (est.get("ordenes") or [])]
    desde = est.get("ts_foto") or 0
    llen = []
    if previas and desde:
        cids = sorted({o["cid"] for o in previas})
        with ThreadPoolExecutor(8) as ex:
            ops = dict(zip(cids, ex.map(lambda cid: trades_desde(cid, desde), cids)))
        for o in previas:
            tr = ops.get(o["cid"])
            if not tr:
                continue
            for lado, precio, ours in (("SELL", o["nb"], "compra"), ("BUY", o["na"], "venta")):
                resto = o["tam"]
                for t_ts, t_lado, t_p, t_q in sorted(tr):
                    if resto <= 0:
                        break
                    peor = (t_lado == "SELL" and t_p < precio) or (t_lado == "BUY" and t_p > precio)
                    if t_lado != lado or not peor:
                        continue
                    q = min(resto, t_q)
                    resto -= q
                    reemb = round(REBATE.get(o["grupo"], 0) * o["tasa"] * q * precio * (1 - precio), 4)
                    llen.append([t_ts, desde, o["grupo"], o["serie"], o["evento"], o["caja"], o["cid"], o["token"],
                                 o["dist"], ours, precio, q, t_p, o["tasa"], reemb, o["medio"], o["fin"], ""])
        if llen:
            nuevo = not os.path.exists(F_LLEN)
            with open(F_LLEN, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                if nuevo:
                    w.writerow(COLS_LLEN)
                w.writerows(llen)
        log(f"{len(llen)} llenados simulados ({sum(1 for t in ops.values() if t is None)} cajas sin trades)")
    est["ordenes"] = [[c["cid"], tok, c["grupo"], c["serie"], c["evento"], c["caja"], nb, na, tam, round(medio, 4),
                       c["tasa"], int(d * 100), c["fin"]] for (tok, d), (c, nb, na, tam, medio) in ordenes.items()]
    est["ts_foto"] = ts
    guardar_json(F_EST, est)


def resolver():
    """Anota gano=0/1 en los llenados de eventos ya cerrados."""
    if not os.path.exists(F_LLEN):
        return
    with open(F_LLEN, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    ahora = datetime.now(timezone.utc)
    pend = sorted({r["cid"] for r in filas if r["gano"] == "" and r["fin"]
                   and datetime.fromisoformat(r["fin"].replace("Z", "+00:00")) < ahora})
    if not pend:
        return
    res = {}
    for cid in pend[:300]:
        try:
            r = S.get(f"https://clob.polymarket.com/markets/{cid}", timeout=20).json()
        except Exception:
            continue
        if not r.get("closed"):
            continue
        for t in r.get("tokens", []):
            if t.get("outcome") == "Yes" and t.get("winner") is not None:
                res[cid] = 1 if t["winner"] else 0
    if not res:
        return
    for r in filas:
        if r["gano"] == "" and r["cid"] in res:
            r["gano"] = res[r["cid"]]
    with open(F_LLEN + ".tmp", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS_LLEN, delimiter=";")
        w.writeheader()
        w.writerows(filas)
    os.replace(F_LLEN + ".tmp", F_LLEN)
    log(f"resueltos {len(res)} mercados")


def main(minutos):
    os.makedirs(CARPETA, exist_ok=True)
    est = leer_json(F_EST, {})
    fin = time.time() + minutos * 60
    while time.time() < fin:
        if date.today() > FIN:
            log(f"periodo terminado ({FIN})")
            return
        t0 = time.time()
        try:
            foto(est)
        except Exception as ex:
            log(f"foto fallo: {ex}")
        espera = INTERVALO - (time.time() - t0)
        if time.time() + max(espera, 0) >= fin:
            break
        time.sleep(max(espera, 5))
    try:
        resolver()
    except Exception as ex:
        log(f"resolver fallo: {ex}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)

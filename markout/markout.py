"""
Medicion de llenados del bot maker en real (regla en markout/REGLA.md): para cada llenado de la billetera, cuanto
se movio el precio medio del token a 5, 30, 60 y 180 min, y contra la resolucion. Todo con datos publicos, sin tocar
el bot. Uso: python markout/markout.py <billetera> [--salida markout] [--desde 2026-11-07T18:00Z]
Escribe <salida>/datos/llenados.csv (acumula, sin repetir) e <salida>/informe.md.
"""
import argparse
import csv
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

BILLETERA = "0x1dACF01B09Fb319A0BbD3939DbA57E4f7Cd63Ae0"   # billetera del bot (publica en Polymarket; Agus autorizo ponerla aca 8-nov)
DATA = "https://data-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
GAMMA = "https://gamma-api.polymarket.com"
HORIZONTES = {"m5": 300, "m30": 1800, "m60": 3600, "m180": 10800}
CORTE_LUZ = (datetime(2026, 11, 7, 20, 5, tzinfo=timezone.utc).timestamp(),
             datetime(2026, 11, 7, 20, 30, tzinfo=timezone.utc).timestamp())
COLUMNAS = ["id", "momento_utc", "ciudad", "caja", "evento", "condition_id", "token", "lado", "outcome", "precio",
            "acciones", "fin_evento", "horas_al_fin", "corte_luz", "p0", "antes", "m5", "m30", "m60", "m180", "resuelto",
            "ganador", "m_res"]
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-markout"


def get(url, params=None, intentos=4):
    for i in range(intentos):
        try:
            r = S.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(5 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as ex:                      # noqa: BLE001
            if i == intentos - 1:
                raise
            print(f"reintento {url}: {ex!r}", file=sys.stderr)
            time.sleep(2 * (i + 1))


def llenados(billetera, desde_ts):
    """Operaciones TRADE de la billetera desde `desde_ts` (data-api v2, paginado por cursor)."""
    out, cursor = [], None
    while True:
        params = {"user": billetera, "type": "TRADE", "limit": 100}
        if cursor:
            params["cursor"] = cursor
        r = get(f"{DATA}/v2/activity", params)
        datos = r.get("data", [])
        out += [d for d in datos if d.get("timestamp", 0) >= desde_ts]
        cursor = (r.get("pagination") or {}).get("next_cursor")
        if not datos or not cursor or min(d.get("timestamp", 0) for d in datos) < desde_ts:
            break
    return out


def historia(token, desde, hasta):
    """Precio medio del token por minuto (aprox.) entre `desde` y `hasta` (epoch)."""
    r = get(f"{CLOB}/prices-history", {"market": token, "startTs": int(desde), "endTs": int(hasta), "fidelity": 1})
    h = sorted(((int(x["t"]), float(x["p"])) for x in r.get("history", [])), key=lambda x: x[0])
    return h


def precio_en(h, t):
    """Ultimo precio registrado hasta t (None si no hay)."""
    p = None
    for tt, pp in h:
        if tt > t:
            break
        p = pp
    return p


def mercado(cid):
    r = get(f"{GAMMA}/markets", {"condition_ids": cid})
    return r[0] if r else {}


def ciudad_de(slug):
    # highest-temperature-in-tel-aviv-on-november-8-2026-22c -> tel aviv
    s = slug.replace("highest-temperature-in-", "").replace("lowest-temperature-in-", "")
    return s.split("-on-")[0].replace("-", " ") if "-on-" in s else s


def caja_de(titulo):
    # "Will the highest temperature in Tokyo be 17°C on November 8?" -> "17°C"
    if " be " in titulo:
        return titulo.split(" be ", 1)[1].split(" on ")[0]
    return titulo[:30]


def signo(lado):
    return 1 if lado == "BUY" else -1


def calcular(billetera, desde_ts, viejos):
    ahora = time.time()
    ops = llenados(billetera, desde_ts)
    filas = {f["id"]: f for f in viejos}
    por_token = defaultdict(list)
    for o in ops:
        oid = f"{o.get('transaction_hash', '')[:18]}:{o['token_id'][-8:]}:{o['side']}:{o['price']}"
        if oid in filas and filas[oid].get("m180") not in ("", None) and filas[oid].get("resuelto") == "1":
            continue                                   # ya esta completa
        por_token[o["token_id"]].append((oid, o))
    mercados = {}
    for token, lista in por_token.items():
        t0 = min(o["timestamp"] for _, o in lista)
        t1 = max(o["timestamp"] for _, o in lista) + HORIZONTES["m180"] + 120
        h = historia(token, t0 - 900, min(t1, ahora))
        for oid, o in lista:
            cid = o["condition_id"]
            if cid not in mercados:
                mercados[cid] = mercado(cid)
            m = mercados[cid]
            ts = int(o["timestamp"])
            precio = float(o["price"])
            sg = signo(o["side"])
            p0 = precio_en(h, ts)
            fin = m.get("endDate") or ""
            try:
                fin_ts = datetime.fromisoformat(fin.replace("Z", "+00:00")).timestamp()
            except ValueError:
                fin_ts = None
            fila = {
                "id": oid, "momento_utc": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "ciudad": ciudad_de(o.get("event_slug", "")), "caja": caja_de(o.get("title", "")),
                "evento": o.get("event_slug", ""), "condition_id": cid, "token": token, "lado": o["side"],
                "outcome": o.get("outcome", ""), "precio": precio, "acciones": float(o["size"]), "fin_evento": fin,
                "horas_al_fin": round((fin_ts - ts) / 3600, 1) if fin_ts else "",
                "corte_luz": 1 if CORTE_LUZ[0] <= ts <= CORTE_LUZ[1] else 0,
                "p0": p0 if p0 is not None else "",
                "antes": round(sg * (p0 - precio) * 100, 2) if p0 is not None else "",
            }
            for k, seg in HORIZONTES.items():
                if ts + seg > ahora:
                    fila[k] = ""
                else:
                    pk = precio_en(h, ts + seg)
                    fila[k] = round(sg * (pk - precio) * 100, 2) if pk is not None else ""
            resuelto = bool(m.get("closed")) and m.get("umaResolutionStatus") in ("resolved", None) and m.get("closed")
            ganador = ""
            if resuelto:
                try:
                    precios = json.loads(m.get("outcomePrices") or "[]")
                    idx = int(o.get("outcome_index", 0))
                    ganador = 1 if float(precios[idx]) >= 0.99 else 0
                except (ValueError, IndexError, TypeError):
                    resuelto = False
            fila["resuelto"] = "1" if resuelto else "0"
            fila["ganador"] = ganador
            fila["m_res"] = round(sg * (ganador - precio) * 100, 2) if resuelto else ""
            filas[oid] = fila
    return sorted(filas.values(), key=lambda f: f["momento_utc"])


def resumen(filas, col):
    v = [(float(f[col]), float(f["acciones"])) for f in filas if f.get(col) not in ("", None)]
    if not v:
        return None
    n = len(v)
    media = sum(x for x, _ in v) / n
    pond = sum(x * q for x, q in v) / sum(q for _, q in v)
    sd = math.sqrt(sum((x - media) ** 2 for x, _ in v) / (n - 1)) if n > 1 else 0.0
    ee = sd / math.sqrt(n) if n > 1 else 0.0
    t = media / ee if ee > 0 else 0.0
    return {"n": n, "acc": sum(q for _, q in v), "media": media, "pond": pond, "ee": ee, "t": t}


def tabla(filas, titulo, grupos):
    lin = [f"### {titulo}", "", "| grupo | n | acciones | antes ¢ | m5 ¢ | m30 ¢ | m60 ¢ | m180 ¢ | a la resolución ¢ (n) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for nombre, sel in grupos:
        if not sel:
            continue
        celdas = [nombre, str(len(sel)), f"{sum(float(f['acciones']) for f in sel):.0f}"]
        for col in ("antes", "m5", "m30", "m60", "m180"):
            r = resumen(sel, col)
            celdas.append("—" if not r else f"{r['pond']:+.1f} (t {r['t']:+.1f})" if col != "antes" else f"{r['pond']:+.1f}")
        r = resumen(sel, "m_res")
        celdas.append("—" if not r else f"{r['pond']:+.1f} (t {r['t']:+.1f}, n {r['n']})")
        lin.append("| " + " | ".join(celdas) + " |")
    return lin + [""]


def informe(filas, ruta, billetera_ok):
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    con_dato = [f for f in filas if f.get("m60") not in ("", None)]
    dias = len({f["momento_utc"][:10] for f in filas})
    r60 = resumen(filas, "m60")
    lin = [f"# Llenados del bot maker en real: ¿el precio se va a favor o en contra? ({hoy}Z)", "",
           f"Regla: markout/REGLA.md. Llenados: {len(filas)} ({sum(float(f['acciones']) for f in filas):.0f} acciones) en {dias} día(s); "
           f"con 60 min de historia: {len(con_dato)}. Positivo = a favor nuestro (ponderado por acciones; t = media simple / error típico).", ""]
    if r60:
        veredicto = ("no pierden (≥ 0, t ≥ 2)" if r60["pond"] >= 0 and r60["t"] >= 2 else
                     "pierden menos que la distancia (entre −2 y 0): neutro" if -2 <= r60["pond"] < 0 else
                     "pierden más que la distancia (< −2, t ≤ −2): candidatos a cambiar" if r60["pond"] < -2 and r60["t"] <= -2 else
                     "sin señal clara todavía")
        minimo = "" if len(filas) >= 100 and dias >= 5 else " **Todavía informativo: la regla pide ≥ 100 llenados en ≥ 5 días.**"
        lin += [f"**m60 ponderado {r60['pond']:+.1f} ¢ (simple {r60['media']:+.1f}, t {r60['t']:+.1f}, n {r60['n']}): {veredicto}.**{minimo}", ""]
    def grupo(fn):
        g = defaultdict(list)
        for f in filas:
            g[fn(f)].append(f)
        return sorted(g.items())
    lin += tabla(filas, "Total y por lado", [("todos", filas)] + grupo(lambda f: "compra" if f["lado"] == "BUY" else "venta"))
    lin += tabla(filas, "Por ciudad", grupo(lambda f: f["ciudad"]))
    lin += tabla(filas, "Por caja", grupo(lambda f: f"{f['ciudad']} {f['caja']} ({f['evento'][-15:]})"))
    lin += tabla(filas, "Por hora UTC del llenado", grupo(lambda f: f"{(int(f['momento_utc'][11:13]) // 4) * 4:02d}–{(int(f['momento_utc'][11:13]) // 4) * 4 + 3:02d} h"))
    def franja(f):
        try:
            h = float(f["horas_al_fin"])
        except (TypeError, ValueError):
            return "sin fin"
        return "<6 h al fin" if h < 6 else "6–24 h" if h < 24 else ">24 h"
    lin += tabla(filas, "Por horas que faltaban para el fin del evento", grupo(franja))
    lin += tabla(filas, "Corte de luz del 7-nov (órdenes que quedaron solas)", grupo(lambda f: "en el corte" if f["corte_luz"] in (1, "1") else "normal"))
    if not billetera_ok:
        lin += ["", "_Sin billetera (variable MAKER_WALLET vacía): no se bajaron llenados nuevos._"]
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lin) + "\n")
    print("\n".join(lin[:6]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("billetera", nargs="?", default=os.environ.get("MAKER_WALLET") or BILLETERA)
    ap.add_argument("--salida", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--desde", default="2026-11-07T18:00Z")
    a = ap.parse_args()
    desde_ts = datetime.fromisoformat(a.desde.replace("Z", "+00:00")).timestamp()
    os.makedirs(os.path.join(a.salida, "datos"), exist_ok=True)
    f_csv = os.path.join(a.salida, "datos", "llenados.csv")
    viejos = []
    if os.path.exists(f_csv):
        with open(f_csv, encoding="utf-8") as f:
            viejos = list(csv.DictReader(f))
    filas = calcular(a.billetera, desde_ts, viejos) if a.billetera else viejos
    with open(f_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            w.writerow({k: fila.get(k, "") for k in COLUMNAS})
    informe(filas, os.path.join(a.salida, "informe.md"), bool(a.billetera))


if __name__ == "__main__":
    main()

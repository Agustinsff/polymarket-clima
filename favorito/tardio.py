"""
FAVORITO TARDIO EN PAPEL (regla en favorito/REGLA.md). NO usa plata, NO pone ordenes.
A 6-2 min del cierre de los "Bitcoin/Ethereum Up or Down" de 1 hora mira el libro real de Up y Down y,
si 10 acciones de un lado cuestan entre 70 y 90 c, anota la compra. Liquida con el resultado del mercado.

Uso: python favorito/tardio.py            (foto + liquidar; la corre el reloj en el minuto 53-58)
     python favorito/tardio.py resumen    (favorito/resultados.md)
Archivos: favorito/fotos.csv, favorito/ops.csv, favorito/estado.json
"""
import csv
import json
import math
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
from estaciones import fee, tasa_de, tasa_fila, asegurar_columnas  # noqa: E402

F = lambda n: os.path.join(CARPETA, n)
F_FOTOS, F_OPS, F_EST, F_RES = F("fotos.csv"), F("ops.csv"), F("estado.json"), F("resultados.md")
SERIES = {"btc-up-or-down-hourly": "BTC", "eth-up-or-down-hourly": "ETH"}
MIN_DESDE, MIN_HASTA = 53, 58          # minuto de la hora en que vale registrar
LO, HI = 0.70, 0.90
ACC = 10
FIN_OPS = "2026-11-16 23:59:59"
COLS_F = ["momento_utc", "activo", "evento", "condition_id", "min_al_cierre", "lado", "bid", "ask", "p10", "p50", "ask_tam", "bid_tam"]
COLS_O = ["momento_utc", "activo", "evento", "condition_id", "min_al_cierre", "lado", "precio", "acciones", "tasa_comision"]
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-favorito/1.0 (investigacion personal)"


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def leer(n):
    if not os.path.exists(n):
        return []
    with open(n, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def agregar(n, cols, filas):
    if not filas:
        return
    asegurar_columnas(n, cols)
    nuevo = not os.path.exists(n)
    with open(n, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(cols)
        w.writerows(filas)


def cargar():
    try:
        with open(F_EST, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"hechos": {}, "ganadoras": {}, "perdidas": []}


def guardar(e):
    with open(F_EST + ".tmp", "w", encoding="utf-8") as f:
        json.dump(e, f, indent=0)
    os.replace(F_EST + ".tmp", F_EST)


def libro(token):
    b = S.get("https://clob.polymarket.com/book", params={"token_id": token}, timeout=20).json()
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
    return bids, asks


def precio_medio(niveles, cantidad):
    falta, total = cantidad, 0.0
    for precio, tam in niveles:
        toma = min(falta, tam)
        total += toma * precio
        falta -= toma
        if falta <= 1e-9:
            return round(total / cantidad, 4)
    return None


def foto():
    est = cargar()
    ahora = datetime.now(timezone.utc)
    hora = ahora.strftime("%Y-%m-%d %H")
    if not MIN_DESDE <= ahora.minute <= MIN_HASTA:
        log(f"fuera de ventana (minuto {ahora.minute}); no se registra")
        if ahora.minute > MIN_HASTA and hora not in est["hechos"] and hora not in est["perdidas"]:
            est["perdidas"].append(hora)
            guardar(est)
        return
    if hora in est["hechos"]:
        return
    fotos, ops = [], []
    for serie, activo in SERIES.items():
        try:
            evs = S.get("https://gamma-api.polymarket.com/events",
                        params={"series_slug": serie, "closed": "false", "limit": 20}, timeout=30).json()
        except Exception as ex:
            log(f"gamma fallo {serie}: {ex}")
            continue
        for e in evs:
            try:
                fin = datetime.fromisoformat(e["endDate"].replace("Z", "+00:00"))
            except Exception:
                continue
            mins = (fin - ahora).total_seconds() / 60
            if not 1 <= mins <= 8:
                continue
            m = (e.get("markets") or [None])[0]
            if not m or m.get("closed"):
                continue
            try:
                toks = json.loads(m["clobTokenIds"]); outs = json.loads(m.get("outcomes") or '["Up","Down"]')
            except Exception:
                continue
            califica = []
            for lado, tok in zip(outs, toks):
                try:
                    bids, asks = libro(tok)
                except Exception as ex:
                    log(f"libro fallo {e['slug']} {lado}: {ex}")
                    continue
                p10, p50 = precio_medio(asks, ACC), precio_medio(asks, 50)
                fotos.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), activo, e["slug"], m["conditionId"], round(mins, 1), lado,
                              bids[0][0] if bids else None, asks[0][0] if asks else None, p10, p50,
                              asks[0][1] if asks else None, bids[0][1] if bids else None])
                if p10 is not None and LO <= p10 < HI:
                    califica.append((lado, p10))
                time.sleep(0.1)
            if len(califica) == 1 and ahora.strftime("%Y-%m-%d %H:%M:%S") <= FIN_OPS:
                lado, p10 = califica[0]
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), activo, e["slug"], m["conditionId"], round(mins, 1), lado, p10, ACC, tasa_de(m)])
    if fotos:                       # sin libros (red caida) la hora cuenta como perdida
        est["hechos"][hora] = ahora.strftime("%H:%M")
        est["hechos"] = dict(list(est["hechos"].items())[-200:])
        guardar(est)
    agregar(F_FOTOS, COLS_F, fotos)
    agregar(F_OPS, COLS_O, ops)
    log(f"favorito: {len(fotos)} libros, {len(ops)} operaciones simuladas")


def liquidar():
    est = cargar()
    gan = est.setdefault("ganadoras", {})
    pend = {o["condition_id"]: o for o in leer(F_OPS) if o["condition_id"] not in gan}
    for cid in list(pend)[:100]:
        try:
            r = S.get(f"https://clob.polymarket.com/markets/{cid}", timeout=20).json()
        except Exception:
            continue
        if r.get("closed"):
            for t in r.get("tokens", []):
                if t.get("winner"):
                    gan[cid] = t.get("outcome")
        time.sleep(0.1)
    guardar(est)


def evaluar(extra=0.0):
    gan = cargar().get("ganadoras", {})
    out = []
    for o in leer(F_OPS):
        g = gan.get(o["condition_id"])
        if g is None:
            out.append((o, None)); continue
        p, q = min(float(o["precio"]) + extra, 0.999), float(o["acciones"])
        gana = g == o["lado"]
        out.append((o, q * ((1 - p) if gana else -p) - q * fee(p, tasa_fila(o))))
    return out


def boot(bl, n=2000):
    v = list(bl.values())
    if len(v) < 2:
        return float("nan")
    rnd = random.Random(7)
    return sum(sum(rnd.choice(v) for _ in v) <= 0 for _ in range(n)) / n


def resumen():
    est = cargar()
    lineas = [f"# Favorito tardío en papel (regla en REGLA.md) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z\n"]
    for extra, txt in ((0.0, "precio del libro"), (0.01, "con 1 ¢ extra")):
        ev = evaluar(extra)
        liq = [(o, r) for o, r in ev if r is not None]
        puesto = sum(float(o["precio"]) * float(o["acciones"]) for o, r in liq)
        bl = defaultdict(float); act = defaultdict(float)
        for o, r in liq:
            bl[o["momento_utc"][:10]] += r; act[o["activo"]] += r
        neto = sum(r for o, r in liq)
        gan = sum(1 for o, r in liq if r > 0)
        lineas.append(f"- **{txt}**: {len(ev)} ops ({len(liq)} liquidadas, {gan} ganadas), neto US$ {neto:+.2f} sobre US$ {puesto:.2f} "
                      f"(ROI {100 * neto / puesto if puesto else 0:+.1f} %), {len(bl)} días, P(≤0) {boot(bl):.2f}, "
                      f"BTC {act.get('BTC', 0):+.2f} / ETH {act.get('ETH', 0):+.2f}")
    fotos = leer(F_FOTOS)
    hechos = est.get("hechos", {})
    horas = len(hechos)
    if hechos:
        primera = datetime.strptime(min(hechos), "%Y-%m-%d %H").replace(tzinfo=timezone.utc)
        total = int((datetime.now(timezone.utc) - primera).total_seconds() // 3600) + 1
    else:
        total = 0
    lineas.append(f"- Horas registradas: {horas} de {total} desde la primera; perdidas (el reloj no llegó al minuto 53–58): {total - horas}; libros mirados: {len(fotos)}.")
    if fotos:
        sp = [float(f["ask"]) - float(f["bid"]) for f in fotos if f["ask"] and f["bid"]]
        sp.sort()
        lineas.append(f"- Spread mediano del libro a esa hora: {100 * sp[len(sp) // 2]:.1f} ¢ ({len(sp)} libros).")
    with open(F_RES, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "resumen":
        resumen()
    else:
        foto(); liquidar(); resumen()

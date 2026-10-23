"""
PROFUNDIDAD DEL LIBRO: cuanto cuesta de verdad entrar en cada mercado que siguen los bots.

Cada hora saca una foto del libro de ordenes de las cajas "vivas" (precio entre 3 y 97 c) de:
  - clima: todos los eventos de temperatura abiertos (mismos que usa pronostico.py)
  - cripto: BTC/ETH above, rango y toca que vencen en las proximas 72 h (mismas series que cripto.py)

Para cada caja guarda el costo de entrar como taker, recorriendo el libro real y con la comision:
  costo = (precio medio pagado - precio medio del libro) + comision, en centavos por accion
para 10, 50 y 100 acciones, comprando Yes (contra las ventas) y comprando No (vendiendo Yes
contra las compras). Tambien guarda cuantas acciones hay a menos de 2 c del medio.

No opera ni cambia ninguna prueba: solo mide. Deja de medir sola despues de FIN.

Uso:
  python libros.py          -> una foto (el reloj la corre cada hora)
  python libros.py resumen  -> escribe libros_informe.md con el resumen por mercado y horario
"""

import csv
import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from statistics import median
from zoneinfo import ZoneInfo

from estaciones import TZ, fee
import pronostico
import cripto

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FIN = date(2026, 11, 2)          # periodo de medicion: hasta la revision siguiente a la del 26-oct
TAMANOS = [10, 50, 100]
CARPETA = os.path.dirname(os.path.abspath(__file__))
F_CSV = os.path.join(CARPETA, "libros.csv")
F_INF = os.path.join(CARPETA, "libros_informe.md")
S = pronostico.S
COLS = (["momento_utc", "grupo", "serie", "evento", "caja", "hora_local", "horas_hasta_fin", "medio", "bid", "ask",
         "bid_tam", "ask_tam", "prof2_compra", "prof2_venta"]
        + [f"costo_yes_{n}" for n in TAMANOS] + [f"costo_no_{n}" for n in TAMANOS])


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def vivas(markets):
    """Cajas abiertas cuyo precio (segun gamma) esta entre 3 y 97 c: el resto casi no se opera."""
    out = []
    for m in markets:
        if m.get("closed") or not m.get("clobTokenIds"):
            continue
        try:
            p = float(json.loads(m.get("outcomePrices") or "[]")[0])
        except (ValueError, IndexError):
            continue
        if 0.03 <= p <= 0.97:
            out.append((m.get("groupItemTitle") or m.get("question", ""), json.loads(m["clobTokenIds"])[0]))
    return out


def costo(niveles, cantidad, medio, lado):
    """Centavos por accion por encima del medio (comprando Yes) o por debajo (vendiendo Yes = comprar No),
    con comision. Vacio si el libro no alcanza."""
    p = pronostico.precio_medio(niveles, cantidad)
    if p is None:
        return ""
    desliz = (p - medio) if lado == "yes" else (medio - p)
    return round((desliz + fee(p)) * 100, 2)


def foto():
    ahora = datetime.now(timezone.utc)
    if ahora.date() > FIN:
        log(f"periodo de medicion terminado ({FIN}); no se toma foto")
        return
    cajas = []   # (grupo, serie, evento, caja, hora_local, horas_hasta_fin, token)
    try:
        for e in pronostico.eventos_abiertos():
            fin = datetime.fromisoformat(e["fin"].replace("Z", "+00:00")) if e.get("fin") else None
            hl = ahora.astimezone(ZoneInfo(TZ[e["ciudad"]])).hour
            for caja, tok in vivas(e["markets"]):
                cajas.append(("clima", f"{e['tipo']}|{e['ciudad']}", e["slug"], caja, hl,
                              round((fin - ahora).total_seconds() / 3600, 1) if fin else "", tok))
    except Exception as ex:
        log(f"clima fallo: {ex}")
    n_clima = len(cajas)
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
            for caja, tok in vivas(e.get("markets", [])):
                cajas.append(("cripto", f"{activo}|{tipo}", e["slug"], caja, ahora.hour, round(horas, 1), tok))
    log(f"{n_clima} cajas de clima y {len(cajas) - n_clima} de cripto")
    with ThreadPoolExecutor(8) as ex:
        libs = list(ex.map(pronostico.libro, [c[-1] for c in cajas]))
    filas = []
    for c, lib in zip(cajas, libs):
        if not lib or not lib[0] or not lib[1]:
            continue
        bids, asks = lib
        medio = (bids[0][0] + asks[0][0]) / 2
        p2c = sum(t for p, t in bids if medio - p <= 0.02 + 1e-9)
        p2v = sum(t for p, t in asks if p - medio <= 0.02 + 1e-9)
        filas.append([ahora.strftime("%Y-%m-%d %H:%M"), *c[:-1], round(medio, 4), bids[0][0], asks[0][0],
                      round(bids[0][1], 1), round(asks[0][1], 1), round(p2c, 1), round(p2v, 1)]
                     + [costo(asks, n, medio, "yes") for n in TAMANOS]
                     + [costo(bids, n, medio, "no") for n in TAMANOS])
    nuevo = not os.path.exists(F_CSV)
    with open(F_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(COLS)
        w.writerows(filas)
    log(f"{len(filas)} libros guardados")


# ---------------------------------------------------------------------------

def num(x):
    return float(x) if x not in ("", None) else None


def stats(filas, n=10):
    """Costo tipico de entrar con n acciones (el mejor de los dos lados no: se promedian Yes y No)."""
    cs, falta = [], 0
    for f in filas:
        for lado in ("yes", "no"):
            v = num(f[f"costo_{lado}_{n}"])
            if v is None:
                falta += 1
            else:
                cs.append(v)
    if not cs:
        return None
    spr = [(num(f["ask"]) - num(f["bid"])) * 100 for f in filas]
    return {"n": len(filas), "spread": median(spr), "c10": median(cs),
            "barato": sum(1 for v in cs if v <= 2) / len(cs) * 100, "no_llena": falta / (len(cs) + falta) * 100,
            "prof2": median(num(f["prof2_compra"]) + num(f["prof2_venta"]) for f in filas)}


def tabla(titulo, grupos, n=10, minimo=5):
    lin = [f"### {titulo}", "", f"| | libros | spread mediano (c) | costo mediano {n} acc. (c) | % entradas ≤2 c | "
           f"% sin libro para {n} | acciones a ≤2 c del medio |", "|---|---|---|---|---|---|---|"]
    filas = []
    for k, fs in grupos.items():
        s = stats(fs, n)
        if s and s["n"] >= minimo:
            filas.append((s["c10"], k, s))
    for _, k, s in sorted(filas, key=lambda x: (x[0], str(x[1]))):
        lin.append(f"| {k} | {s['n']} | {s['spread']:.1f} | {s['c10']:.1f} | {s['barato']:.0f} % | "
                   f"{s['no_llena']:.0f} % | {s['prof2']:.0f} |")
    return lin + [""]


def resumen():
    if not os.path.exists(F_CSV):
        print("Todavia no hay fotos.")
        return
    with open(F_CSV, encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f, delimiter=";") if 0.05 <= float(r["medio"]) <= 0.95]
    fotos = sorted({r["momento_utc"] for r in filas})
    clima = [r for r in filas if r["grupo"] == "clima"]
    cri = [r for r in filas if r["grupo"] == "cripto"]
    lin = ["# Profundidad del libro: costo real de entrar", "",
           f"{len(fotos)} fotos ({fotos[0] if fotos else '-'} a {fotos[-1] if fotos else '-'} UTC), solo cajas entre 5 y 95 c.",
           "Costo = lo que se paga por encima del precio medio del libro + comision de taker, en centavos por accion, "
           "promediando comprar Yes y comprar No. Generado por `python libros.py resumen`.", ""]
    g = defaultdict(list)
    for r in clima:
        g[r["serie"]].append(r)
    lin += tabla("Clima por ciudad y tipo", g)
    g = defaultdict(list)
    for r in clima:
        g[f"{int(r['hora_local']) // 3 * 3:02d}-{int(r['hora_local']) // 3 * 3 + 2:02d} h local"].append(r)
    lin += tabla("Clima por hora local de la ciudad", g)
    g = defaultdict(list)
    for r in clima:
        h = num(r["horas_hasta_fin"])
        if h is not None:
            g["≤12 h" if h <= 12 else "12-24 h" if h <= 24 else "24-36 h" if h <= 36 else ">36 h"].append(r)
    lin += tabla("Clima por horas hasta el cierre", g)
    for n in (50, 100):
        g = defaultdict(list)
        for r in clima:
            g[r["serie"].split("|")[0]].append(r)
        lin += tabla(f"Clima con {n} acciones", g, n)
    g = defaultdict(list)
    for r in cri:
        g[r["serie"]].append(r)
    lin += tabla("Cripto por activo y tipo", g)
    g = defaultdict(list)
    for r in cri:
        g[f"{int(r['hora_local']) // 4 * 4:02d}-{int(r['hora_local']) // 4 * 4 + 3:02d} h UTC"].append(r)
    lin += tabla("Cripto por hora UTC", g)
    g = defaultdict(list)
    for r in cri:
        h = num(r["horas_hasta_fin"])
        g["≤6 h" if h <= 6 else "6-24 h" if h <= 24 else "24-72 h"].append(r)
    lin += tabla("Cripto por horas hasta el cierre", g)
    for n in (50, 100):
        g = defaultdict(list)
        for r in cri:
            g[r["serie"]].append(r)
        lin += tabla(f"Cripto con {n} acciones", g, n)
    with open(F_INF, "w", encoding="utf-8") as f:
        f.write("\n".join(lin))
    print("\n".join(lin))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "resumen":
        resumen()
    else:
        foto()

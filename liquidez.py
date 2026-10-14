"""
Medicion de la competencia por las RECOMPENSAS DE LIQUIDEZ (sin poner plata).

Cada vez que se ejecuta saca una "foto" del libro de ordenes de los mercados
de temperatura de Buenos Aires y Sao Paulo (hoy, manana y pasado) y calcula,
con la formula oficial de Polymarket, cuanto cobraria por dia alguien que
dejara ordenes de compra y venta de X acciones a 1 o 2 centavos del precio medio.

Formula (docs.polymarket.com, liquidity rewards):
  puntaje de una orden = ((v - s) / v)^2 * tamano   (v = spread maximo, s = distancia al medio)
  se cuenta cada lado; lo de un solo lado se divide por 3
  la recompensa diaria se reparte segun el puntaje de cada uno (foto cada minuto)

Tambien guarda el precio medio en cada foto, para medir despues cuanto se
mueve el precio (el riesgo de que te "tomen" las ordenes).

Uso:
  python liquidez.py          -> una foto (la tarea programada lo corre cada 15 min)
  python liquidez.py resumen  -> resumen de todas las fotos
"""

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import requests

from monitor import CIUDADES, GAMMA_API, slug_evento

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(CARPETA, "liquidez.csv")
BOOK_API = "https://clob.polymarket.com/book"
CONFIGS = [(50, 0.01), (100, 0.01), (200, 0.01), (100, 0.02)]   # (acciones, distancia al medio)
COLUMNAS = ["momento_utc", "ciudad", "fecha_mercado", "horas_hasta_el_dia", "caja",
            "recompensa_diaria", "spread_max", "tamano_min", "medio", "mejor_compra",
            "mejor_venta", "puntaje_competencia"] + [f"est_{x}acc_{int(o*100)}c" for x, o in CONFIGS]


def puntaje(v, s):
    return ((v - s) / v) ** 2 if s < v else 0.0


def foto_evento(ciudad, fecha, ahora):
    r = requests.get(GAMMA_API, params={"slug": slug_evento(ciudad, fecha)}, timeout=30)
    r.raise_for_status()
    eventos = r.json()
    if not eventos:
        return []
    inicio_dia = datetime(fecha.year, fecha.month, fecha.day, 3, tzinfo=timezone.utc)  # 00:00 local (UTC-3)
    horas = round((inicio_dia - ahora).total_seconds() / 3600, 1)
    filas = []
    for m in eventos[0].get("markets", []):
        tasa = sum(x.get("rewardsDailyRate") or 0 for x in (m.get("clobRewards") or []))
        if not tasa or m.get("closed"):
            continue
        v = (m.get("rewardsMaxSpread") or 0) / 100
        minimo = m.get("rewardsMinSize") or 0
        token = json.loads(m["clobTokenIds"])[0]
        b = requests.get(BOOK_API, params={"token_id": token}, timeout=20).json()
        bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
        asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
        if not bids or not asks or v <= 0:
            continue
        medio = (bids[0][0] + asks[0][0]) / 2
        q1 = sum(puntaje(v, medio - p) * t for p, t in bids if t >= minimo)
        q2 = sum(puntaje(v, p - medio) * t for p, t in asks if t >= minimo)
        if 0.10 <= medio <= 0.90:
            comp = max(min(q1, q2), max(q1, q2) / 3)
        else:
            comp = min(q1, q2)
        estimaciones = []
        for x, off in CONFIGS:
            nuestro = puntaje(v, off) * x if x >= minimo else 0
            estimaciones.append(round(tasa * nuestro / (nuestro + comp), 2) if nuestro else 0)
        filas.append([ahora.strftime("%Y-%m-%d %H:%M"), ciudad["nombre"], fecha.isoformat(), horas,
                      m["groupItemTitle"], tasa, v, minimo, round(medio, 4), bids[0][0], asks[0][0],
                      round(comp, 2)] + estimaciones)
    return filas


def tomar_foto():
    ahora = datetime.now(timezone.utc)
    hoy = (ahora - timedelta(hours=3)).date()
    filas = []
    for ciudad in CIUDADES:
        for d in range(0, 3):
            try:
                filas += foto_evento(ciudad, hoy + timedelta(days=d), ahora)
            except Exception as e:
                print(f"Error {ciudad['nombre']} {hoy + timedelta(days=d)}: {e}")
    nuevo = not os.path.exists(ARCHIVO)
    with open(ARCHIVO, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(COLUMNAS)
        for fila in filas:
            w.writerow([str(x).replace(".", ",") if isinstance(x, float) else x for x in fila])
    print(f"{ahora:%Y-%m-%d %H:%M} UTC: {len(filas)} cajas con recompensa registradas.")


def resumen():
    if not os.path.exists(ARCHIVO):
        print("Todavia no hay fotos.")
        return
    with open(ARCHIVO, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    n = lambda x: float(x.replace(",", "."))
    fotos = sorted({f["momento_utc"] for f in filas})
    print(f"\n=== Resumen recompensas de liquidez: {len(fotos)} fotos ({fotos[0]} a {fotos[-1]} UTC) ===")
    print("Recompensa diaria estimada si mantuvieras ordenes de los dos lados en TODAS las cajas")
    print("con recompensa de los mercados de MANANA (promedio de las fotos):\n")
    for ciudad in sorted({f["ciudad"] for f in filas}):
        sub = [f for f in filas if f["ciudad"] == ciudad and 0 < n(f["horas_hasta_el_dia"]) <= 27]
        por_foto = defaultdict(lambda: defaultdict(float))
        pozo = defaultdict(float)
        for f in sub:
            for x, off in CONFIGS:
                por_foto[f["momento_utc"]][(x, off)] += n(f[f"est_{x}acc_{int(off*100)}c"])
            pozo[f["momento_utc"]] += n(f["recompensa_diaria"])
        if not por_foto:
            continue
        print(f"  {ciudad} (pozo promedio ${sum(pozo.values()) / len(pozo):.0f}/dia):")
        for x, off in CONFIGS:
            vals = [v[(x, off)] for v in por_foto.values()]
            print(f"    {x} acciones a {int(off*100)}c del medio: ${sum(vals) / len(vals):.2f}/dia "
                  f"(min ${min(vals):.2f}, max ${max(vals):.2f})")
    # movimiento del precio entre fotos (riesgo de que te tomen las ordenes)
    print("\n  Movimiento del precio medio entre fotos consecutivas (cajas de manana):")
    serie = defaultdict(list)
    for f in filas:
        if 0 < n(f["horas_hasta_el_dia"]) <= 27:
            serie[(f["ciudad"], f["fecha_mercado"], f["caja"])].append((f["momento_utc"], n(f["medio"])))
    for ciudad in sorted({k[0] for k in serie}):
        saltos = []
        for k, s in serie.items():
            if k[0] != ciudad:
                continue
            s.sort()
            saltos += [abs(b[1] - a[1]) for a, b in zip(s, s[1:])]
        if saltos:
            mayores = sum(1 for x in saltos if x > 0.01) / len(saltos) * 100
            print(f"    {ciudad}: promedio {sum(saltos) / len(saltos) * 100:.1f}c; "
                  f"se movio mas de 1c en el {mayores:.0f}% de los intervalos")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "resumen":
        resumen()
    else:
        tomar_foto()

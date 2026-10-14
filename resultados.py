"""
Resultados: compara lo que dijo el mercado y lo que dijo el modelo con lo que paso.

Que hace:
  1. Lee registro.csv (lo que anoto monitor.py).
  2. Para cada dia que ya termino, busca:
       - la maxima real medida por la estacion (observaciones METAR horarias,
         archivo publico de la Universidad Estatal de Iowa), y
       - la caja que gano en Polymarket (si el mercado ya resolvio).
  3. Guarda eso en resultados.csv.
  4. Calcula quien acerto mas: el mercado o el modelo (puntaje Brier: mas bajo = mejor).

Uso:
  python resultados.py
"""

import csv
import io
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

import requests

from monitor import CIUDADES, GAMMA_API, leer_caja, slug_evento

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_REGISTRO = os.path.join(CARPETA, "registro.csv")
ARCHIVO_RESULTADOS = os.path.join(CARPETA, "resultados.csv")
IEM_API = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

CODIGOS = {"Buenos Aires": "SAEZ", "Sao Paulo": "SBGR"}


# ---------------------------------------------------------------------------
# LECTURA DE ARCHIVOS
# ---------------------------------------------------------------------------

def numero(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    return float(texto.replace(",", "."))


def leer_registro():
    if not os.path.exists(ARCHIVO_REGISTRO):
        return []
    with open(ARCHIVO_REGISTRO, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def leer_resultados():
    res = {}
    if os.path.exists(ARCHIVO_RESULTADOS):
        with open(ARCHIVO_RESULTADOS, encoding="utf-8-sig", newline="") as f:
            for fila in csv.DictReader(f, delimiter=";"):
                res[(fila["ciudad"], fila["fecha"])] = fila
    return res


def guardar_resultados(res):
    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ciudad", "fecha", "maxima_estacion", "caja_ganadora_polymarket"])
        for (ciudad, fecha), fila in sorted(res.items(), key=lambda x: (x[0][1], x[0][0])):
            w.writerow([ciudad, fecha, fila.get("maxima_estacion", ""),
                        fila.get("caja_ganadora_polymarket", "")])


# ---------------------------------------------------------------------------
# DATOS REALES
# ---------------------------------------------------------------------------

def maxima_estacion(ciudad, fecha):
    """Maxima del dia (hora local) segun las observaciones METAR de la estacion."""
    fin = fecha + timedelta(days=1)
    params = {
        "station": CODIGOS[ciudad["nombre"]],
        "data": "tmpc",
        "year1": fecha.year, "month1": fecha.month, "day1": fecha.day,
        "year2": fin.year, "month2": fin.month, "day2": fin.day,
        "tz": ciudad["zona_horaria"],
        "format": "onlycomma", "latlon": "no", "missing": "M",
        "report_type": [3, 4],
    }
    r = requests.get(IEM_API, params=params, timeout=60)
    r.raise_for_status()
    temps = []
    for fila in csv.DictReader(io.StringIO(r.text)):
        if fila.get("valid", "").startswith(fecha.isoformat()) and fila.get("tmpc") not in (None, "", "M"):
            temps.append(float(fila["tmpc"]))
    if len(temps) < 12:  # muy pocos datos: mejor no decidir
        return None
    return round(max(temps))


def caja_ganadora(ciudad, fecha):
    """Caja que resolvio 'Yes' en Polymarket, o None si todavia no resolvio."""
    r = requests.get(GAMMA_API, params={"slug": slug_evento(ciudad, fecha)}, timeout=20)
    r.raise_for_status()
    eventos = r.json()
    if not eventos:
        return None
    for m in eventos[0].get("markets", []):
        precios = json.loads(m.get("outcomePrices") or "[]")
        if m.get("closed") and precios and float(precios[0]) >= 0.99:
            return m.get("groupItemTitle")
    return None


def caja_de_temperatura(titulos, temp):
    for t in titulos:
        bajo, alto = leer_caja(t)
        if (bajo is None or temp >= bajo) and (alto is None or temp <= alto):
            return t
    return None


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------

def main():
    registro = leer_registro()
    if not registro:
        print("Todavia no hay registro.csv. Corre primero monitor.py.")
        return

    resultados = leer_resultados()
    hoy = date.today()
    ciudades = {c["nombre"]: c for c in CIUDADES}

    # 1) Completar resultados de dias ya terminados
    pendientes = sorted({(f["ciudad"], f["fecha_mercado"]) for f in registro})
    print("\n=== Buscando resultados reales ===")
    for nombre, fecha_txt in pendientes:
        fecha = date.fromisoformat(fecha_txt)
        if fecha >= hoy or nombre not in ciudades:
            continue
        actual = resultados.get((nombre, fecha_txt), {})
        if actual.get("maxima_estacion") and actual.get("caja_ganadora_polymarket"):
            continue  # ya completo
        ciudad = ciudades[nombre]
        fila = dict(actual)
        try:
            maxima = maxima_estacion(ciudad, fecha)
            if maxima is not None:
                fila["maxima_estacion"] = str(maxima)
        except Exception as e:
            print(f"  {nombre} {fecha_txt}: no pude leer la estacion ({e})")
        try:
            ganadora = caja_ganadora(ciudad, fecha)
            if ganadora:
                fila["caja_ganadora_polymarket"] = ganadora
        except Exception as e:
            print(f"  {nombre} {fecha_txt}: no pude leer Polymarket ({e})")
        if fila:
            resultados[(nombre, fecha_txt)] = fila
            print(f"  {nombre} {fecha_txt}: estacion {fila.get('maxima_estacion', '?')}°C | "
                  f"Polymarket resolvio: {fila.get('caja_ganadora_polymarket') or 'todavia no'}")
    guardar_resultados(resultados)

    # 2) Evaluar: quien acerto mas
    # Agrupamos cada "foto" del monitor (un momento, una ciudad, un dia)
    fotos = defaultdict(list)
    for f in registro:
        fotos[(f["momento"], f["ciudad"], f["fecha_mercado"])].append(f)

    stats = defaultdict(lambda: {"n": 0, "brier_mercado": 0.0, "brier_modelo": 0.0,
                                 "acierto_mercado": 0, "acierto_modelo": 0,
                                 "dias": set(), "errores": []})
    for (momento, nombre, fecha_txt), filas in fotos.items():
        res = resultados.get((nombre, fecha_txt))
        if not res:
            continue
        titulos = [f["caja"] for f in filas]
        ganadora = res.get("caja_ganadora_polymarket")
        if not ganadora and res.get("maxima_estacion"):
            ganadora = caja_de_temperatura(titulos, float(res["maxima_estacion"]))
        if not ganadora:
            continue

        bm = bo = 0.0
        for f in filas:
            y = 1.0 if f["caja"] == ganadora else 0.0
            pm = numero(f["precio_mercado"]) or 0.0
            po = numero(f["prob_modelo"]) or 0.0
            bm += (pm - y) ** 2
            bo += (po - y) ** 2
        favorita_mercado = max(filas, key=lambda f: numero(f["precio_mercado"]) or 0)["caja"]
        favorita_modelo = max(filas, key=lambda f: numero(f["prob_modelo"]) or 0)["caja"]

        s = stats[nombre]
        s["n"] += 1
        s["brier_mercado"] += bm
        s["brier_modelo"] += bo
        s["acierto_mercado"] += favorita_mercado == ganadora
        s["acierto_modelo"] += favorita_modelo == ganadora
        s["dias"].add(fecha_txt)
        media = numero(filas[0].get("media_modelo"))
        if res.get("maxima_estacion") and media is not None:
            s["errores"].append(float(res["maxima_estacion"]) - media)

    print("\n=== Mercado vs. modelo ===")
    if not stats:
        print("Todavia no hay dias terminados para evaluar. Volve a correrlo manana.")
        return
    for nombre, s in stats.items():
        n = s["n"]
        print(f"\n--- {nombre} ({len(s['dias'])} dias, {n} fotos) ---")
        print(f"  Puntaje Brier (mas bajo = mejor):  mercado {s['brier_mercado'] / n:.3f}"
              f"   modelo {s['brier_modelo'] / n:.3f}")
        print(f"  Su caja favorita gano:             mercado {s['acierto_mercado']}/{n}"
              f"     modelo {s['acierto_modelo']}/{n}")
        if s["errores"]:
            sesgo = sum(s["errores"]) / len(s["errores"])
            print(f"  Sesgo de la estacion: en promedio marco {sesgo:+.1f}°C respecto del modelo")
    print("\nCon pocos dias estos numeros son casi ruido. Necesitamos 2-3 semanas.")


if __name__ == "__main__":
    main()

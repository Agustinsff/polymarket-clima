"""
CARRERA DE FUENTES: cual publica primero cada METAR de Ezeiza (SAEZ).

Consulta varias fuentes cada pocos segundos y anota la PRIMERA vez que ve cada
reporte en cada fuente. Sirve para saber si existe una fuente lo bastante rapida
como para competir con los bots que "cosechan" cajas muertas.

Fuentes:
  noaa_api   aviationweather.gov/api (JSON)                  cada 5 s
  noaa_txt   tgftp.nws.noaa.gov (archivo de texto de SAEZ)   cada 5 s
  iem        mesonet.agron.iastate.edu (actual)              cada 30 s
  ogimet     ogimet.com                                      cada 60 s (son estrictos)

Resultado: carrera.csv (fuente; hora_observacion_utc; visto_utc; segundos_tras_observacion; reporte)

Uso:
  python carrera.py 350     -> corre 350 minutos (GitHub Actions corta a las 6 h)
  python carrera.py resumen -> quien gana
"""

import csv
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(CARPETA, "carrera.csv")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-carrera/1.0 (investigacion personal)"


def ahora():
    return datetime.now(timezone.utc)


def hora_desde_metar(raw, ref):
    """'SAEZ 141700Z ...' -> datetime UTC 17:00 del dia 14 (mes/anio de ref)."""
    m = re.search(r"SAEZ (\d{2})(\d{2})(\d{2})Z", raw)
    if not m:
        return None
    dia, hh, mm = map(int, m.groups())
    t = ref.replace(day=dia, hour=hh, minute=mm, second=0, microsecond=0) if dia <= 31 else None
    if t and t > ref + timedelta(hours=1):          # cambio de mes
        t = (t.replace(day=1) - timedelta(days=1)).replace(day=dia)
    return t


def f_noaa_api():
    j = S.get("https://aviationweather.gov/api/data/metar",
              params={"ids": "SAEZ", "format": "json", "hours": 2}, timeout=10).json()
    return [x["rawOb"] for x in j]


def f_noaa_txt():
    t = S.get("https://tgftp.nws.noaa.gov/data/observations/metar/stations/SAEZ.TXT", timeout=10).text
    return [l.strip() for l in t.splitlines() if l.startswith("SAEZ")]


def f_iem():
    j = S.get("https://mesonet.agron.iastate.edu/json/current.py",
              params={"station": "SAEZ", "network": "AR__ASOS"}, timeout=15).json()
    raw = (j.get("last_ob") or {}).get("raw")
    return [raw] if raw else []


def f_ogimet():
    fin = ahora()
    ini = fin - timedelta(hours=2)
    t = S.get("https://www.ogimet.com/cgi-bin/getmetar",
              params={"icao": "SAEZ", "begin": ini.strftime("%Y%m%d%H%M"), "end": fin.strftime("%Y%m%d%H%M")},
              timeout=20).text
    # formato: SAEZ,YYYY,MM,DD,HH,mm,METAR SAEZ ...=
    return [l.split(",", 6)[6].replace("METAR ", "").replace("SPECI ", "").rstrip("=").strip()
            for l in t.splitlines() if l.startswith("SAEZ,") and len(l.split(",", 6)) == 7]


FUENTES = {"noaa_api": (f_noaa_api, 5), "noaa_txt": (f_noaa_txt, 5), "iem": (f_iem, 30), "ogimet": (f_ogimet, 60)}


def normalizar(raw):
    raw = raw.replace("METAR ", "").replace("SPECI ", "").replace("COR ", "").strip().rstrip("=")
    return " ".join(raw.split()[:2])  # "SAEZ 141700Z" identifica el reporte


def correr(minutos):
    vistos = set()
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, encoding="utf-8") as f:
            for fila in csv.DictReader(f, delimiter=";"):
                vistos.add((fila["fuente"], fila["reporte_id"]))
    nuevo = not os.path.exists(ARCHIVO)
    f = open(ARCHIVO, "a", newline="", encoding="utf-8")
    w = csv.writer(f, delimiter=";")
    if nuevo:
        w.writerow(["fuente", "reporte_id", "hora_observacion_utc", "visto_utc", "segundos_tras_observacion", "reporte"])
    proxima = {k: 0.0 for k in FUENTES}
    fin = time.time() + minutos * 60
    errores = defaultdict(int)
    while time.time() < fin:
        for nombre, (fn, cada) in FUENTES.items():
            if time.time() < proxima[nombre]:
                continue
            proxima[nombre] = time.time() + cada
            try:
                reportes = fn()
            except Exception:
                errores[nombre] += 1
                continue
            t = ahora()
            for raw in reportes:
                rid = normalizar(raw)
                if (nombre, rid) in vistos:
                    continue
                vistos.add((nombre, rid))
                obs = hora_desde_metar(raw, t)
                seg = round((t - obs).total_seconds()) if obs else ""
                w.writerow([nombre, rid, obs.strftime("%Y-%m-%d %H:%M") if obs else "",
                            t.strftime("%Y-%m-%d %H:%M:%S"), seg, raw])
                f.flush()
                print(f"{t:%H:%M:%S} {nombre:9s} {rid} (+{seg}s)", flush=True)
        time.sleep(1)
    f.close()
    print("Errores por fuente:", dict(errores))


def resumen():
    with open(ARCHIVO, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    por_rep = defaultdict(dict)
    for x in filas:
        if x["segundos_tras_observacion"] != "":
            por_rep[x["reporte_id"]][x["fuente"]] = int(x["segundos_tras_observacion"])
    # solo reportes que vimos nacer (el primero que aparecio, a menos de 30 min)
    reps = {r: v for r, v in por_rep.items() if min(v.values()) < 1800}
    print(f"\n=== Carrera de fuentes: {len(reps)} reportes de SAEZ ===")
    print(f"  {'Fuente':<10}{'reportes':>9}{'gana':>6}{'mediana s':>11}{'p10 s':>8}{'p90 s':>8}")
    for fuente in sorted({x["fuente"] for x in filas}):
        segs = sorted(v[fuente] for v in reps.values() if fuente in v)
        gana = sum(1 for v in reps.values() if fuente in v and v[fuente] == min(v.values()))
        if segs:
            q = lambda p: segs[int(p * (len(segs) - 1))]
            print(f"  {fuente:<10}{len(segs):>9}{gana:>6}{q(0.5):>11}{q(0.1):>8}{q(0.9):>8}")
    print("\nReferencia: los bots cosechadores operan ~1-2 min despues de la hora de observacion.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "resumen":
        resumen()
    else:
        correr(float(sys.argv[1]) if len(sys.argv) > 1 else 350)

"""
INVESTIGACION (sin operar): historia de METAR de las estaciones de Polymarket, con la hora en que
aviationweather.gov los publico (receiptTime). Corre en GitHub Actions (el contenedor no llega a NOAA/IEM).

  velocidad/datos/metar_awc.csv.gz  aviationweather (los dias que guarde): obs, recibido, tipo, temp, raw
  velocidad/datos/metar_iem.csv.gz  IEM (30+ dias, sin hora de publicacion): obs, tipo, raw

Uso: python velocidad/bajar_metar.py DIAS
"""

import csv
import gzip
import io
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estaciones_vel import ESTACIONES  # noqa: E402

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-velocidad/1.0 (investigacion personal)"
AWC = "https://aviationweather.gov/api/data/metar"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"


def log(m):
    print(datetime.now(timezone.utc).strftime("%H:%M:%S"), m, flush=True)


def get(url, params, json_=True):
    for i in range(5):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(5 * (i + 1))
                continue
            if r.status_code == 204:
                return [] if json_ else ""
            if r.status_code >= 400:
                log(f"{r.status_code} {url} {params} {r.text[:200]}")
                return None
            return r.json() if json_ else r.text
        except Exception as ex:
            log(f"error {url}: {ex}")
            time.sleep(3 * (i + 1))
    return None


def awc(dias):
    filas, vistos = [], set()
    hoy = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for d in range(dias):
        fin = hoy - timedelta(hours=24 * d)
        for i in range(0, len(ESTACIONES), 25):
            j = get(AWC, {"ids": ",".join(ESTACIONES[i:i + 25]), "format": "json", "hours": 25,
                          "date": fin.strftime("%Y-%m-%dT%H:%M:%SZ")})
            for x in j or []:
                k = (x.get("icaoId"), x.get("obsTime"), x.get("rawOb"))
                if k in vistos:
                    continue
                vistos.add(k)
                filas.append([x.get("icaoId"), x.get("obsTime"), x.get("reportTime"), x.get("receiptTime"),
                              x.get("metarType"), x.get("temp"), x.get("rawOb")])
            time.sleep(0.5)
        log(f"awc dia -{d}: {len(filas)} reportes acumulados")
    with gzip.open(os.path.join(CARPETA, "metar_awc.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["icao", "obs_epoch", "report_time", "receipt_time", "tipo", "temp", "raw"])
        w.writerows(filas)


def iem(dias):
    d0 = datetime.now(timezone.utc) - timedelta(days=dias)
    d1 = datetime.now(timezone.utc) + timedelta(days=1)
    with gzip.open(os.path.join(CARPETA, "metar_iem.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["icao", "valid_utc", "raw"])
        for est in ESTACIONES:
            sid = est[1:] if est.startswith("K") else est
            t = get(IEM, {"station": sid, "data": "metar", "year1": d0.year, "month1": d0.month, "day1": d0.day,
                          "year2": d1.year, "month2": d1.month, "day2": d1.day, "tz": "Etc/UTC",
                          "format": "onlycomma", "latlon": "no", "missing": "empty", "trace": "empty",
                          "report_type": [3, 4]}, json_=False)
            n = 0
            for r in csv.DictReader(io.StringIO(t or "")):
                w.writerow([est, r.get("valid"), r.get("metar")])
                n += 1
            log(f"iem {est}: {n}")
            time.sleep(1)


if __name__ == "__main__":
    os.makedirs(CARPETA, exist_ok=True)
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    awc(dias)
    iem(dias)

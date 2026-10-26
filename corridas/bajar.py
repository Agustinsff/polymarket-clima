"""
INVESTIGACION (sin operar): baja las corridas originales de GFS 0,25 y ECMWF IFS 0,25 (datos abiertos) desde los
buckets publicos de AWS y guarda la temperatura a 2 m en el punto de grilla mas cercano a cada estacion.
Ver corridas/REGLA.md. A diferencia de Polymarket, AWS si se alcanza desde el contenedor.

Uso: python corridas/bajar.py 2026-10-05T00 2026-10-23T18
Escribe corridas/datos/pronos.csv.gz      modelo, corrida, paso_h, estacion, temp_c
        corridas/datos/disponible.csv.gz  modelo, corrida, paso_h, last_modified (hora del archivo en el bucket)
Necesita: pip install eccodes numpy
"""

import csv
import gzip
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import eccodes
import numpy as np
import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
GFS = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
ECM = "https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com"
PASOS = {"gfs": list(range(3, 97)), "ecmwf": list(range(3, 91, 3))}
_loc = threading.local()


def ses():
    if not hasattr(_loc, "s"):
        _loc.s = requests.Session()
    return _loc.s


def estaciones():
    e = json.load(open(os.path.join(RAIZ, "estaciones.json")))
    e["HKO"] = {"lat": 22.302, "lon": 114.174}
    return {k: (v["lat"], v["lon"]) for k, v in e.items()}


def listar(base, prefijo):
    """{clave: LastModified} de un prefijo del bucket (con paginado)."""
    out, token = {}, None
    while True:
        p = {"list-type": "2", "prefix": prefijo}
        if token:
            p["continuation-token"] = token
        r = ses().get(base + "/", params=p, timeout=60)
        r.raise_for_status()
        for k, lm in re.findall(r"<Key>([^<]+)</Key><LastModified>([^<]+)</LastModified>", r.text):
            out[k] = lm
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", r.text)
        if not m:
            return out
        token = m.group(1)


def valores(grib, puntos):
    g = eccodes.codes_new_from_message(grib)
    try:
        ni, nj = eccodes.codes_get(g, "Ni"), eccodes.codes_get(g, "Nj")
        la0 = eccodes.codes_get(g, "latitudeOfFirstGridPointInDegrees")
        lo0 = eccodes.codes_get(g, "longitudeOfFirstGridPointInDegrees")
        dla = eccodes.codes_get(g, "jDirectionIncrementInDegrees")
        dlo = eccodes.codes_get(g, "iDirectionIncrementInDegrees")
        neg = eccodes.codes_get(g, "jScansPositively") == 0
        v = eccodes.codes_get_values(g).reshape(nj, ni)
    finally:
        eccodes.codes_release(g)
    out = {}
    for est, (la, lo) in puntos.items():
        i = round((la0 - la) / dla) if neg else round((la - la0) / dla)
        j = round(((lo - lo0) % 360) / dlo) % ni
        out[est] = float(v[i, j]) - 273.15
    return out


def getr(url):
    for i in range(8):
        try:
            r = ses().get(url, timeout=60)
            if r.status_code in (200, 404):
                return r
        except Exception:
            pass
        time.sleep(1 + i)
    return None


def rango(url, a, b):
    for i in range(8):
        try:
            r = ses().get(url, headers={"Range": f"bytes={a}-{b}"}, timeout=90)
            if r.status_code in (200, 206):
                return r.content
        except Exception:
            pass
        time.sleep(1 + i)
    return None


def tarea_gfs(run, paso, puntos):
    d, h = run.strftime("%Y%m%d"), run.strftime("%H")
    url = f"{GFS}/gfs.{d}/{h}/atmos/gfs.t{h}z.pgrb2.0p25.f{paso:03d}"
    r = getr(url + ".idx")
    if r is None or r.status_code != 200:
        return None
    idx = r.text.splitlines()
    for n, lin in enumerate(idx):
        if ":TMP:2 m above ground:" in lin:
            a = int(lin.split(":")[1])
            b = int(idx[n + 1].split(":")[1]) - 1 if n + 1 < len(idx) else ""
            g = rango(url, a, b)
            return valores(g, puntos) if g else None
    return None


def tarea_ecm(run, paso, puntos):
    d, h = run.strftime("%Y%m%d"), run.strftime("%H")
    for carpeta in ("oper", "scda"):
        base = f"{ECM}/{d}/{h}z/ifs/0p25/{carpeta}/{d}{h}0000-{paso}h-{carpeta}-fc"
        r = getr(base + ".index")
        if r is None or r.status_code != 200:
            continue
        for lin in r.text.splitlines():
            j = json.loads(lin)
            if j.get("param") == "2t" and j.get("levtype") == "sfc":
                g = rango(base + ".grib2", j["_offset"], j["_offset"] + j["_length"] - 1)
                return valores(g, puntos) if g else None
    return None


def disponibilidad(run):
    d, h = run.strftime("%Y%m%d"), run.strftime("%H")
    out = []
    lg = listar(GFS, f"gfs.{d}/{h}/atmos/gfs.t{h}z.pgrb2.0p25.f0")
    for k, lm in lg.items():
        m = re.search(r"\.f(\d{3})$", k)
        if m and int(m.group(1)) in PASOS["gfs"]:
            out.append(("gfs", int(m.group(1)), lm))
    le = listar(ECM, f"{d}/{h}z/ifs/0p25/")
    for k, lm in le.items():
        m = re.search(r"-(\d+)h-(oper|scda)-fc\.grib2$", k)
        if m and int(m.group(1)) in PASOS["ecmwf"]:
            out.append(("ecmwf", int(m.group(1)), lm))
    return out


def main():
    t0 = datetime.strptime(sys.argv[1], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
    t1 = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
    puntos = estaciones()
    runs = []
    while t0 <= t1:
        runs.append(t0)
        t0 += timedelta(hours=6)
    os.makedirs(os.path.join(CARPETA, "datos"), exist_ok=True)
    with gzip.open(os.path.join(CARPETA, "datos", "disponible.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "corrida", "paso_h", "last_modified"])
        with ThreadPoolExecutor(8) as ex:
            for run, filas in zip(runs, ex.map(disponibilidad, runs)):
                for mo, paso, lm in filas:
                    w.writerow([mo, run.strftime("%Y-%m-%dT%H"), paso, lm])
    tareas = [(mo, run, paso) for run in runs for mo in ("gfs", "ecmwf") for paso in PASOS[mo]]
    print(f"{len(runs)} corridas, {len(tareas)} campos", flush=True)

    def hacer(t):
        mo, run, paso = t
        return t, (tarea_gfs if mo == "gfs" else tarea_ecm)(run, paso, puntos)

    faltan = 0
    with gzip.open(os.path.join(CARPETA, "datos", "pronos.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["modelo", "corrida", "paso_h", "estacion", "temp_c"])
        with ThreadPoolExecutor(24) as ex:
            for n, ((mo, run, paso), vals) in enumerate(ex.map(hacer, tareas)):
                if not vals:
                    faltan += 1
                    continue
                for est, v in vals.items():
                    w.writerow([mo, run.strftime("%Y-%m-%dT%H"), paso, est, f"{v:.2f}"])
                if n % 500 == 0:
                    print(n, mo, run, paso, flush=True)
    print(f"listo; campos que faltaron: {faltan}", flush=True)


if __name__ == "__main__":
    main()

"""
PRONOSTICO PROPIO - PASO 1: JUNTAR LOS DATOS HISTORICOS (no opera, no toca a ningun bot).

Baja y guarda, para las 47 estaciones de propio/estaciones.json (todas las ciudades con mercado):

  obs   Temperatura real: todos los METAR desde DESDE (archivo de Iowa State, IEM), con la temperatura
        en decimas del grupo T si esta. Se guarda cada reporte (rutina o SPECI) y el maximo/minimo
        de cada dia local con la regla de hoy (solo rutina) y con la vieja (rutina + SPECI).
        Hong Kong: maximo y minimo diario oficial del Observatorio (HKO), que es con lo que resuelve.
  pron  Pronosticos pasados: lo que decia cada modelo de Open-Meteo ("previous runs") el mismo dia y
        1, 2 y 3 dias antes, como maximo/minimo del dia local en la estacion. Por mes y por modelo.
        Antes de bajar un modelo en una estacion se prueba con una semana: si no tiene datos ahi
        (modelos regionales), se salta.
  mos   Solo EE.UU.: los pronosticos por estacion que publica el servicio meteorologico (MOS de GFS
        y NAM, y el NBM, que es la mezcla oficial), archivados por IEM. Son el "pronostico ajustado
        por estacion" oficial: la vara contra la que se mide el nuestro.

Todo es reanudable: estado.json anota que mes de que fuente ya esta. Cada corrida sigue donde quedo,
respeta un presupuesto de llamadas a Open-Meteo (el plan gratis permite 10.000 "llamadas" por dia,
y un pedido de un mes cuenta como ~2) y un tiempo maximo. El mes en curso se vuelve a bajar
siempre, asi los datos quedan al dia.

Uso: python propio/datos.py [sonda|obs|pron|mos|todo] --salida DIR [--presupuesto N] [--minutos M]
"""

import argparse
import csv
import gzip
import io
import json
import math
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
EST = json.load(open(os.path.join(AQUI, "estaciones.json"), encoding="utf-8"))

DESDE = date(2023, 1, 1)
# Pronosticos: antes de mediados de 2024 Open-Meteo solo guarda la corrida del mismo dia (sin los
# horizontes 1-3 dias) para casi todos los modelos (probado el 2-nov-2026), asi que no vale la pena.
DESDE_PRON = date(2024, 6, 1)
HORIZONTES = [0, 1, 2, 3]          # 0 = corrida del mismo dia
# Modelos de Open-Meteo. Los 11 de modelos/ (con historia comprobada) primero; despues regionales
# y otros que se prueban (si no tienen historia o no cubren la estacion, se saltan solos).
MODELOS = [
    "ecmwf_ifs025", "ecmwf_aifs025_single", "icon_seamless", "gfs_seamless", "ecmwf_ifs",
    "ukmo_seamless", "meteofrance_seamless", "gem_seamless", "jma_seamless", "cma_grapes_global",
    "best_match",
    # regionales / extra (alta resolucion)
    "ncep_hrrr_conus", "ncep_nbm_conus", "gfs_graphcast025", "kma_seamless", "dmi_seamless",
    "knmi_seamless", "metno_seamless", "meteoswiss_icon_seamless", "icon_d2", "icon_eu",
    "ukmo_uk_deterministic_2km", "jma_msm", "bom_access_global", "meteofrance_arome_france",
]
MOS_MODELOS = ["NBS", "NBE", "GFS", "NAM", "MEX"]   # MEX = GFS extendido; IEM acepta AVN|ETA|GFS|LAV|MEX|NAM|NBE|NBS
PREV = "https://previous-runs-api.open-meteo.com/v1/forecast"
IEM_ASOS = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
IEM_MOS = "https://mesonet.agron.iastate.edu/cgi-bin/request/mos.py"
HKO = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
CAMBIO_REGLA = "2026-10-23"        # desde aca Polymarket cuenta solo METAR de rutina

S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-propio/1.0 (investigacion personal)"
T0 = time.time()
CANDADO = threading.RLock()


class SinCupo(Exception):
    pass


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", file=sys.stderr, flush=True)


def get(url, params, intentos=4, timeout=120):
    for i in range(intentos):
        try:
            r = S.get(url, params=params, timeout=timeout)
        except Exception as e:
            log(f"{url} fallo ({e}), reintento")
            time.sleep(5 * (i + 1))
            continue
        if r.status_code == 429:
            txt = r.text.lower()
            if "daily" in txt or "hourly" in txt:   # cupo del dia/hora gastado: se sigue manana
                raise SinCupo(r.text[:200])
            time.sleep(20 * (i + 1))
            continue
        if r.status_code >= 500:
            time.sleep(10 * (i + 1))
            continue
        return r
    return None


def meses(desde, hasta):
    d = date(desde.year, desde.month, 1)
    while d <= hasta:
        sig = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        yield d, min(sig - timedelta(days=1), hasta)
        d = sig


# ---------------------------------------------------------------------------
# ARCHIVOS: CSV comprimidos con una clave por fila; se reescriben enteros (son chicos).

def leer(ruta):
    if not os.path.exists(ruta):
        return []
    with gzip.open(ruta, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escribir(ruta, filas, cols):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    os.replace(tmp, ruta)


class Estado:
    def __init__(self, salida):
        self.ruta = os.path.join(salida, "estado.json")
        self.d = json.load(open(self.ruta)) if os.path.exists(self.ruta) else {}
        self.d.setdefault("hecho", {})
        self.d.setdefault("sin_datos", {})
        self.d.setdefault("llamadas_om", {})

    def hecho(self, clave):
        return clave in self.d["hecho"]

    def marcar(self, clave, n):
        with CANDADO:
            self.d["hecho"][clave] = n

    def guardar(self):
        with CANDADO:
            tmp = self.ruta + ".tmp"
            json.dump(self.d, open(tmp, "w"), indent=0, sort_keys=True)
            os.replace(tmp, self.ruta)


def mes_cerrado(fin_mes, hoy, margen=4):
    """Un mes se da por terminado (no se vuelve a bajar) cuando paso hace mas de 'margen' dias."""
    return fin_mes < hoy - timedelta(days=margen)


def listo(est, clave, cerrado, hoy):
    """Ya bajado: mes cerrado bajado despues de cerrar (valor numerico), o mes abierto bajado hoy."""
    v = est.d["hecho"].get(clave)
    if v is None:
        return False
    return (cerrado and not isinstance(v, str)) or v == hoy.isoformat()


# ---------------------------------------------------------------------------
# OBSERVACIONES

def temp_raw(raw):
    """Temperatura de un METAR crudo: decimas del grupo T si esta, si no la del cuerpo."""
    g = re.search(r"\bT([01])(\d{3})[01]\d{3}\b", raw)
    if g:
        return (-1 if g.group(1) == "1" else 1) * int(g.group(2)) / 10, "T"
    g = re.search(r"\s(M?\d{2})/(M?\d{2})?\s", raw)
    if g:
        t = g.group(1)
        return float(-int(t[1:]) if t.startswith("M") else int(t)), "C"
    return None, None


def iem_anio(icao, ini, fin, tipo):
    base = {"data": "metar", "tz": "Etc/UTC", "format": "onlycomma", "latlon": "no", "missing": "empty",
            "year1": ini.year, "month1": ini.month, "day1": ini.day,
            "year2": fin.year, "month2": fin.month, "day2": fin.day, "report_type": tipo}
    for sid in ([icao, icao[1:]] if icao.startswith("K") else [icao]):
        r = get(IEM_ASOS, dict(base, station=sid), timeout=300)
        if r is not None and r.status_code == 200:
            filas = list(csv.DictReader(io.StringIO(r.text)))
            if filas:
                return filas
    return []


def obs_estacion(icao, info, salida, est, hoy):
    ruta = os.path.join(salida, "obs", f"{icao}.csv.gz")
    filas = {(f["utc"], f["tipo"]): f for f in leer(ruta)}
    cambio = False
    for anio in range(DESDE.year, hoy.year + 1):
        ini, fin = date(anio, 1, 1), min(date(anio, 12, 31), hoy)
        clave = f"obs|{icao}|{anio}"
        cerrado = mes_cerrado(fin, hoy)
        if cerrado and est.hecho(clave):
            continue
        if not cerrado:          # anio en curso: solo los ultimos 20 dias (lo de antes ya esta)
            ultimo = max((f["utc"][:10] for f in filas.values() if f["utc"][:4] == str(anio)), default=None)
            if ultimo:
                ini = max(ini, date.fromisoformat(ultimo) - timedelta(days=20))
        n = 0
        for tipo, letra in (("3", "R"), ("4", "S")):     # 3 = rutina, 4 = SPECI
            for f in iem_anio(icao, ini - timedelta(days=1), fin + timedelta(days=1), tipo):
                raw = f.get("metar") or ""
                t, fuente = temp_raw(raw.replace("SPECI ", ""))
                if t is None:
                    continue
                k = (f["valid"], letra if not raw.startswith("SPECI") else "S")
                filas[k] = {"utc": f["valid"], "tipo": k[1], "temp": t, "fuente": fuente}
                n += 1
            time.sleep(1)
        log(f"obs {icao} {anio}: {n} reportes")
        if n:
            cambio = True
        est.marcar(clave, n)
        est.guardar()
    if cambio:
        orden = sorted(filas.values(), key=lambda f: (f["utc"], f["tipo"]))
        escribir(ruta, orden, ["utc", "tipo", "temp", "fuente"])


def diaria_metar(icao, info, salida):
    """Max/min por dia local: regla de hoy (solo rutina) y vieja (rutina + SPECI)."""
    zona = ZoneInfo(info["tz"])
    dias = defaultdict(lambda: {"R": [], "S": []})
    for f in leer(os.path.join(salida, "obs", f"{icao}.csv.gz")):
        ts = datetime.strptime(f["utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        dias[ts.astimezone(zona).date().isoformat()][f["tipo"]].append(float(f["temp"]))
    out = []
    for d in sorted(dias):
        r, s = dias[d]["R"], dias[d]["S"]
        if len(r) < 12:          # dia con pocos reportes: no se usa
            continue
        out.append({"icao": icao, "fecha": d, "max": max(r), "min": min(r), "n": len(r),
                    "max_con_speci": max(r + s), "min_con_speci": min(r + s), "n_speci": len(s),
                    "regla": "rutina" if d >= CAMBIO_REGLA else "con_speci"})
    return out


def diaria_hko():
    """Maximo y minimo diario oficial del Observatorio de Hong Kong (con lo que resuelve Polymarket)."""
    vals = {}
    for tipo, campo in (("CLMMAXT", "max"), ("CLMMINT", "min")):
        r = get(HKO, {"dataType": tipo, "rformat": "csv", "station": "HKO"})
        if r is None or r.status_code != 200:
            log(f"HKO {tipo}: {None if r is None else r.status_code}")
            continue
        for fila in csv.reader(io.StringIO(r.content.decode("utf-8-sig", "replace"))):
            try:
                a, m, d, v = int(fila[0]), int(fila[1]), int(fila[2]), float(fila[3])
            except (ValueError, IndexError):
                continue
            f = date(a, m, d)
            if f >= DESDE:
                vals.setdefault(f.isoformat(), {})[campo] = v
    return [{"icao": "HKO", "fecha": d, "max": v.get("max"), "min": v.get("min"), "n": "",
             "max_con_speci": v.get("max"), "min_con_speci": v.get("min"), "n_speci": "", "regla": "hko"}
            for d, v in sorted(vals.items())]


def obs(salida, est, hoy, apurar):
    for icao, info in EST.items():
        if icao == "HKO":
            continue
        if apurar():
            log("obs: se acabo el tiempo, sigue en la proxima corrida")
            break
        obs_estacion(icao, info, salida, est, hoy)
    filas = []
    for icao, info in EST.items():
        filas += diaria_hko() if icao == "HKO" else diaria_metar(icao, info, salida)
    escribir(os.path.join(salida, "obs_diaria.csv.gz"), filas,
             ["icao", "fecha", "max", "min", "n", "max_con_speci", "min_con_speci", "n_speci", "regla"])
    log(f"obs_diaria: {len(filas)} dias-estacion")


# ---------------------------------------------------------------------------
# PRONOSTICOS (Open-Meteo previous runs)

def variables():
    return ["temperature_2m"] + [f"temperature_2m_previous_day{h}" for h in HORIZONTES if h > 0]


def peso(ini, fin):
    """Llamadas que cuenta Open-Meteo: 1 por cada 2 semanas (con hasta 10 variables)."""
    return max(1.0, ((fin - ini).days + 1) / 14)


def pedir_om(info, modelo, ini, fin, est):
    hoy = datetime.now(timezone.utc).date().isoformat()
    est.d["llamadas_om"][hoy] = est.d["llamadas_om"].get(hoy, 0) + peso(ini, fin)
    r = get(PREV, {"latitude": info["lat"], "longitude": info["lon"], "hourly": ",".join(variables()),
                   "models": modelo, "timezone": info["tz"], "elevation": info["elev"],
                   "start_date": ini.isoformat(), "end_date": fin.isoformat()})
    if r is None:
        return None, "sin respuesta"
    if r.status_code != 200:
        return None, f"{r.status_code} {r.text[:150]}"
    try:
        return r.json().get("hourly", {}), None
    except ValueError:
        return None, f"respuesta no JSON: {r.text[:100]!r}"


def por_dia(h):
    """{(fecha, horizonte): (max, min, horas)} con dias de al menos 20 horas con dato."""
    out = {}
    for hz in HORIZONTES:
        vals = h.get("temperature_2m" if hz == 0 else f"temperature_2m_previous_day{hz}")
        if not vals:
            continue
        dia = defaultdict(list)
        for t, v in zip(h.get("time", []), vals):
            if v is not None:
                dia[t[:10]].append(v)
        for d, vs in dia.items():
            if len(vs) >= 20:
                out[(d, hz)] = (max(vs), min(vs), len(vs))
    return out


def cubre(icao, info, modelo, est, hoy):
    """Prueba barata (una semana reciente): el modelo tiene datos en esta estacion?"""
    clave = f"{icao}|{modelo}"
    if clave in est.d["sin_datos"]:
        return False
    if est.hecho(f"cubre|{clave}"):
        return True
    ini = hoy - timedelta(days=10)
    h, err = pedir_om(info, modelo, ini, ini + timedelta(days=6), est)
    if err or not por_dia(h or {}):
        est.d["sin_datos"][clave] = err or "sin datos en la ultima semana"
        log(f"pron {icao} {modelo}: no cubre ({est.d['sin_datos'][clave]})")
        est.guardar()
        return False
    est.marcar(f"cubre|{clave}", 1)
    return True


def pron(salida, est, hoy, apurar, presupuesto):
    hasta = hoy - timedelta(days=1)
    gastado = lambda: est.d["llamadas_om"].get(datetime.now(timezone.utc).date().isoformat(), 0)  # noqa: E731
    cols = ["fecha", "modelo", "h", "max", "min", "horas"]
    # Orden: primero los meses recientes (mas utiles), despues para atras; dentro, todos los modelos
    # y estaciones. Asi, si el cupo se corta, lo que hay ya sirve.
    lista = list(meses(DESDE_PRON, hasta))[::-1]
    datos = {}
    try:
        for ini, fin in lista:
            for modelo in MODELOS:
                for icao, info in EST.items():
                    clave = f"pron|{icao}|{modelo}|{ini:%Y-%m}"
                    cerrado = mes_cerrado(fin, hoy)
                    if listo(est, clave, cerrado, hoy):
                        continue
                    if est.d["hecho"].get(f"vacio|{icao}|{modelo}", "") > ini.isoformat():
                        continue     # el modelo no tenia historia tan atras en esta estacion
                    if apurar() or gastado() + peso(ini, fin) > presupuesto:
                        raise SinCupo(f"presupuesto/tiempo (gastado hoy {gastado():.0f})")
                    if not cubre(icao, info, modelo, est, hoy):
                        continue
                    h, err = pedir_om(info, modelo, ini, fin, est)
                    if err:
                        log(f"pron {icao} {modelo} {ini:%Y-%m}: {err}")
                        if err.startswith("400"):      # fecha fuera de la historia del modelo
                            est.d["hecho"][f"vacio|{icao}|{modelo}"] = fin.isoformat()
                        continue
                    dias = por_dia(h)
                    if not any(hz > 0 for (_, hz) in dias):   # solo la corrida del mismo dia: no sirve
                        # sin datos: con 2 meses seguidos vacios se asume que no hay historia mas atras
                        seguidos = est.d["hecho"].get(f"vacios|{icao}|{modelo}", 0) + 1
                        est.d["hecho"][f"vacios|{icao}|{modelo}"] = seguidos
                        if seguidos >= 2:
                            est.d["hecho"][f"vacio|{icao}|{modelo}"] = fin.isoformat()
                        est.marcar(clave, 0)
                        continue
                    est.d["hecho"][f"vacios|{icao}|{modelo}"] = 0
                    if icao not in datos:
                        datos[icao] = {(f["fecha"], f["modelo"], f["h"]): f
                                       for f in leer(os.path.join(salida, "pron", f"{icao}.csv.gz"))}
                    for (d, hz), (mx, mn, n) in dias.items():
                        datos[icao][(d, modelo, str(hz))] = {"fecha": d, "modelo": modelo, "h": hz,
                                                             "max": round(mx, 2), "min": round(mn, 2), "horas": n}
                    est.marcar(clave, len(dias) if cerrado else hoy.isoformat())
                    time.sleep(0.3)
                # guardar al terminar cada modelo de cada mes
                for icao, filas in datos.items():
                    escribir(os.path.join(salida, "pron", f"{icao}.csv.gz"),
                             sorted(filas.values(), key=lambda f: (f["fecha"], f["modelo"], int(f["h"]))), cols)
                est.guardar()
            log(f"pron {ini:%Y-%m} listo (gastado hoy {gastado():.0f})")
    except SinCupo as e:
        log(f"pron: se corta ({e}); sigue en la proxima corrida")
    for icao, filas in datos.items():
        escribir(os.path.join(salida, "pron", f"{icao}.csv.gz"),
                 sorted(filas.values(), key=lambda f: (f["fecha"], f["modelo"], int(f["h"]))), cols)
    est.guardar()


# ---------------------------------------------------------------------------
# MOS / NBM de EE.UU. (IEM)

MOS_COLS = ["modelo", "runtime", "ftime", "n_x", "tmp"]


def mos(salida, est, hoy, apurar):
    """IEM tarda ~10 s por pedido: se bajan 4 estaciones a la vez."""
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda icao: mos_estacion(icao, salida, est, hoy, apurar),
                    [k for k in EST if k.startswith("K")]))


def mos_estacion(icao, salida, est, hoy, apurar):
    cols = MOS_COLS
    if True:
        ruta = os.path.join(salida, "mos", f"{icao}.csv.gz")
        filas = None
        for modelo in MOS_MODELOS:
            if est.d["sin_datos"].get(f"mos|{modelo}"):
                continue
            for ini, fin in list(meses(DESDE, hoy))[::-1]:
                clave = f"mos|{icao}|{modelo}|{ini:%Y-%m}"
                if listo(est, clave, mes_cerrado(fin, hoy), hoy):
                    continue
                if est.d["hecho"].get(f"vacio|{icao}|{modelo}", "") > ini.isoformat():
                    continue
                if apurar():
                    log("mos: se acabo el tiempo")
                    break
                r = get(IEM_MOS, {"station": icao, "model": modelo, "format": "csv",
                                  "sts": f"{ini.isoformat()}T00:00Z",
                                  "ets": f"{(fin + timedelta(days=1)).isoformat()}T00:00Z"}, timeout=300)
                time.sleep(1)
                if r is None or r.status_code != 200:
                    msg = "sin respuesta" if r is None else f"{r.status_code} {r.text[:150]}"
                    log(f"mos {icao} {modelo} {ini:%Y-%m}: {msg}")
                    if r is not None and r.status_code in (400, 422) and ini.year == hoy.year and ini.month == hoy.month:
                        est.d["sin_datos"][f"mos|{modelo}"] = msg   # el modelo no existe en IEM
                        break
                    continue
                leidas = list(csv.DictReader(io.StringIO(r.text)))
                leidas = [{"modelo": modelo, "runtime": f.get("runtime"), "ftime": f.get("ftime"),
                           "n_x": f.get("n_x") or f.get("x_n") or f.get("txn") or "", "tmp": f.get("tmp", "")}
                          for f in leidas]
                leidas = [f for f in leidas if f["n_x"] not in ("", None, "None")]
                if not leidas:
                    est.d["hecho"][f"vacio|{icao}|{modelo}"] = fin.isoformat()
                    est.marcar(clave, 0)
                    log(f"mos {icao} {modelo} {ini:%Y-%m}: vacio, no se busca mas atras")
                    if ini.year == hoy.year and ini.month == hoy.month:
                        log(f"   columnas: {r.text[:200]!r}")
                    break
                if filas is None:
                    filas = {(f["modelo"], f["runtime"], f["ftime"]): f for f in leer(ruta)}
                for f in leidas:
                    filas[(f["modelo"], f["runtime"], f["ftime"])] = f
                est.marcar(clave, len(leidas) if mes_cerrado(fin, hoy) else hoy.isoformat())
            if filas is not None:
                escribir(ruta, sorted(filas.values(), key=lambda f: (f["modelo"], f["runtime"], f["ftime"])), cols)
            est.guardar()
            log(f"mos {icao} {modelo} listo")


# ---------------------------------------------------------------------------
# SONDA: hasta donde llega la historia de cada modelo (una estacion por region)

def sonda(salida, est):
    pruebas = {"KLGA": None, "EHAM": None, "RJTT": None, "SAEZ": None}
    fechas = [date(2022, 6, 1), date(2023, 1, 10), date(2024, 1, 10), date(2024, 7, 10), date(2025, 1, 10),
              date(2025, 7, 10), date(2026, 3, 10)]
    out = {}
    for icao in pruebas:
        info = EST[icao]
        for modelo in MODELOS:
            fila = {}
            for f in fechas:
                h, err = pedir_om(info, modelo, f, f + timedelta(days=2), est)
                dias = por_dia(h or {})
                fila[f.isoformat()] = err[:60] if err else ",".join(sorted({str(hz) for (_, hz) in dias})) or "-"
                time.sleep(0.2)
            out[f"{icao}|{modelo}"] = fila
            log(f"sonda {icao} {modelo}: {fila}")
    for modelo in MOS_MODELOS:
        r = get(IEM_MOS, {"station": "KLGA", "model": modelo, "format": "csv",
                          "sts": "2024-01-10T00:00Z", "ets": "2024-01-11T00:00Z"})
        out[f"mos|{modelo}"] = None if r is None else f"{r.status_code} {r.text[:300]}"
    r = get(HKO, {"dataType": "CLMMAXT", "rformat": "csv", "station": "HKO"})
    out["hko"] = None if r is None else f"{r.status_code} {r.text[:200]}"
    json.dump(out, open(os.path.join(salida, "sonda.json"), "w"), indent=1)
    est.guardar()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("que", choices=["sonda", "obs", "pron", "mos", "todo"])
    ap.add_argument("--salida", required=True)
    ap.add_argument("--presupuesto", type=float, default=8000, help="llamadas Open-Meteo por dia (UTC)")
    ap.add_argument("--minutos", type=float, default=300)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    est = Estado(a.salida)
    hoy = datetime.now(timezone.utc).date()
    apurar = lambda: (time.time() - T0) / 60 > a.minutos  # noqa: E731
    if a.que == "sonda":
        sonda(a.salida, est)
        return
    if a.que in ("obs", "todo"):
        obs(a.salida, est, hoy, apurar)
    if a.que in ("pron", "todo"):
        pron(a.salida, est, hoy, apurar, a.presupuesto)
    if a.que in ("mos", "todo"):
        mos(a.salida, est, hoy, apurar)
    est.guardar()


if __name__ == "__main__":
    main()

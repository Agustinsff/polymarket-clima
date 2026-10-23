"""
QUE MODELO DE PRONOSTICO RINDE MEJOR, POR CIUDAD Y POR HORIZONTE (investigacion, no toca a los bots).

Para cada serie (maxima o minima de cada ciudad) y cada dia de los ultimos DIAS dias:
  - pronostico de cada modelo global de Open-Meteo ("previous runs") hecho 1, 2, 3 y 5 dias antes:
    maximo/minimo del dia local en la estacion oficial;
  - temperatura real: maximo/minimo de los METAR (IEM), con la misma regla que calib/calibracion.py
    (hasta el 22-oct con SPECI, desde el 23-oct solo los de rutina; decimas del grupo T).

Se compara cada modelo:
  - crudo: error medio absoluto (EMA) y sesgo;
  - corregido: restando el sesgo de esa serie/modelo/horizonte medido SOLO con dias anteriores
    (los que ya se conocian cuando salio el pronostico). Es lo justo: un bot puede hacer eso.
  - caja exacta: % de dias en que el pronostico corregido cae en la caja ganadora
    (1 °C, o 2 °F en EE.UU.).
Ademas se prueba si elegir "el mejor modelo de cada ciudad" sirve de verdad: se elige con la
primera mitad de los dias y se mide en la segunda.

Los ensambles (GFS y ECMWF, lo que usa pronostico.py) no tienen historia en Open-Meteo: se comparan
solo con lo que anotaron los bots en pronostico.csv (desde el 20-oct).

Salida: modelos/dias.csv, modelos/resumen.json y modelos/informe.md.
error = real - pronostico, en °C.
"""

import csv
import io
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from estaciones import TZ  # noqa: E402

DIAS = 60
HASTA = datetime.now(timezone.utc).date() - timedelta(days=1)
DESDE = HASTA - timedelta(days=DIAS - 1)
HORIZONTES = [1, 2, 3, 5]
MIN_PREVIOS = 5      # dias anteriores para estimar el sesgo antes de corregir
COBERTURA = 0.9      # un modelo entra en la comparacion de una serie si tiene >= 90% de los dias
# nombre corto -> modelo de Open-Meteo (los que tienen historia en "previous runs", ver sonda.txt)
MODELOS = {
    "GFS": "gfs_seamless", "ECMWF": "ecmwf_ifs025", "ECMWF-9km": "ecmwf_ifs", "ECMWF-IA": "ecmwf_aifs025_single",
    "ICON": "icon_seamless", "GEM": "gem_seamless", "JMA": "jma_seamless", "MeteoFrance": "meteofrance_seamless",
    "UKMO": "ukmo_seamless", "CMA": "cma_grapes_global", "BestMatch": "best_match",
}
COMBINADOS = {"GFS+ECMWF": ["GFS", "ECMWF"]}   # base que usa el bot (con ensambles)

OUT = os.path.join(RAIZ, "modelos")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-modelos/1.0 (investigacion personal)"
PREV = "https://previous-runs-api.open-meteo.com/v1/forecast"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
CAMBIO_FUENTE = "2026-10-23"   # hasta el 22-oct contaban tambien los SPECI


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", file=sys.stderr, flush=True)


def get(url, params, intentos=4, timeout=90):
    for i in range(intentos):
        try:
            r = S.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                time.sleep(15 * (i + 1))
                continue
            return r
        except Exception as e:
            log(f"{url} fallo ({e}), reintento")
            time.sleep(3 * (i + 1))
    return None


def redondear(v):
    return math.floor(v + 0.5 + 1e-9)


def caja(c, en_f):
    """Caja de Polymarket de una temperatura en °C: grado entero, o par de °F (66-67, 68-69...)."""
    return redondear(c * 1.8 + 32) // 2 if en_f else redondear(c)


# ---------------------------------------------------------------------------
# DATOS

def series():
    """{serie: (icao, en_f)} a partir de lo que vieron los bots."""
    out = {}
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            out[r["serie"]] = (r["icao"], "°F" in r["caja"])
    return out


def pronosticos(icao, lat, lon, tz):
    """{(fecha, modelo, horizonte): (max, min)}."""
    out = {}
    variables = ",".join(f"temperature_2m_previous_day{h}" for h in HORIZONTES)
    for corto, m in MODELOS.items():
        r = get(PREV, {"latitude": lat, "longitude": lon, "hourly": variables, "models": m, "timezone": tz,
                       "start_date": DESDE.isoformat(), "end_date": HASTA.isoformat()})
        if r is None or r.status_code != 200:
            log(f"open-meteo {icao} {m}: {None if r is None else r.status_code} {'' if r is None else r.text[:150]}")
            continue
        h = r.json().get("hourly", {})
        for hz in HORIZONTES:
            vals = h.get(f"temperature_2m_previous_day{hz}")
            if not vals:
                continue
            por_dia = defaultdict(list)
            for t, v in zip(h["time"], vals):
                if v is not None:
                    por_dia[t[:10]].append(v)
            for d, vs in por_dia.items():
                if len(vs) >= 20:
                    out[(d, corto, hz)] = (max(vs), min(vs))
        time.sleep(0.4)
    return out


def temp_raw(raw):
    """Como estaciones.temp_metar pero sobre el texto crudo de IEM (sin SPECI)."""
    if raw.startswith("SPECI") or " SPECI " in raw[:20]:
        return None
    g = re.search(r"\bT([01])(\d{3})[01]\d{3}\b", raw)
    if g:
        return (-1 if g.group(1) == "1" else 1) * int(g.group(2)) / 10
    g = re.search(r"\s(M?\d{2})/(M?\d{2})?\s", raw)
    if g:
        t = g.group(1)
        return -int(t[1:]) if t.startswith("M") else int(t)
    return None


def metar(icao, tz):
    """{fecha_local: (max, min)} como resolvia Polymarket ese dia (misma regla que calib/calibracion.py)."""
    ini = DESDE - timedelta(days=1)
    fin = HASTA + timedelta(days=2)
    base = {"data": "metar", "tz": "Etc/UTC", "format": "onlycomma", "latlon": "no", "missing": "empty",
            "year1": ini.year, "month1": ini.month, "day1": ini.day,
            "year2": fin.year, "month2": fin.month, "day2": fin.day}
    zona = ZoneInfo(tz)
    dias = defaultdict(list)
    for tipo in ("3", "4"):          # 3 = rutina, 4 = especiales (SPECI)
        filas = []
        for sid in ([icao, icao[1:]] if icao.startswith("K") else [icao]):
            r = get(IEM, dict(base, station=sid, report_type=tipo), timeout=180)
            if r is None or r.status_code != 200:
                continue
            filas = list(csv.DictReader(io.StringIO(r.text)))
            if filas:
                break
        for f in filas:
            try:
                t = temp_raw(f["metar"].replace("SPECI ", ""))
                ts = datetime.strptime(f["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except Exception:
                continue
            d = ts.astimezone(zona).date().isoformat()
            if t is not None and (tipo == "3" or d < CAMBIO_FUENTE):
                dias[d].append(t)
        time.sleep(1)
    return {d: (max(v), min(v)) for d, v in dias.items() if len(v) >= 12}


# ---------------------------------------------------------------------------
# CUENTAS

def corregir(filas):
    """Agrega 'corr' a cada fila: pronostico + sesgo medio de los dias ANTERIORES a la emision
    (fecha - horizonte) de la misma serie/modelo/horizonte. None si hay menos de MIN_PREVIOS."""
    grupos = defaultdict(list)
    for f in filas:
        grupos[(f["serie"], f["modelo"], f["horizonte"])].append(f)
    for g in grupos.values():
        g.sort(key=lambda f: f["fecha"])
        for f in g:
            emision = (datetime.fromisoformat(f["fecha"]) - timedelta(days=f["horizonte"])).date().isoformat()
            prev = [x["real"] - x["pron"] for x in g if x["fecha"] < emision]
            f["corr"] = f["pron"] + sum(prev) / len(prev) if len(prev) >= MIN_PREVIOS else None


def stats(fs):
    """Metricas de una lista de filas (ya filtradas a dias comparables)."""
    if not fs:
        return None
    err = [f["real"] - f["pron"] for f in fs]
    errc = [f["real"] - f["corr"] for f in fs]
    return {"n": len(fs), "sesgo": round(sum(err) / len(err), 2),
            "ema_crudo": round(sum(map(abs, err)) / len(err), 3),
            "ema_corr": round(sum(map(abs, errc)) / len(errc), 3),
            "caja_corr": round(sum(caja(f["corr"], f["en_f"]) == caja(f["real"], f["en_f"]) for f in fs) / len(fs), 3),
            "caja_cruda": round(sum(caja(f["pron"], f["en_f"]) == caja(f["real"], f["en_f"]) for f in fs) / len(fs), 3)}


def comparables(filas):
    """{(serie, horizonte): {modelo: [filas]}} usando solo los dias en que todos los modelos con buena
    cobertura tienen pronostico corregido (asi todos se miden sobre los mismos dias)."""
    por = defaultdict(lambda: defaultdict(dict))
    for f in filas:
        if f["corr"] is not None:
            por[(f["serie"], f["horizonte"])][f["modelo"]][f["fecha"]] = f
    out = {}
    for k, mods in por.items():
        total = max(len(v) for v in mods.values())
        buenos = {m: v for m, v in mods.items() if len(v) >= COBERTURA * total}
        dias = set.intersection(*(set(v) for v in buenos.values()))
        out[k] = {m: [v[d] for d in sorted(dias)] for m, v in buenos.items()}
    return out


def media(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def resumen_global(comp, h):
    """Promedio por modelo sobre todas las series (cada serie pesa igual) para el horizonte h."""
    acc = defaultdict(lambda: defaultdict(list))
    for (serie, hz), mods in comp.items():
        if hz != h:
            continue
        for m, fs in mods.items():
            s = stats(fs)
            if s and s["n"] >= 10:
                for k in ("ema_crudo", "ema_corr", "caja_corr", "sesgo"):
                    acc[m][k].append(s[k] if k != "sesgo" else abs(s[k]))
                acc[m]["series"].append(1)
    return {m: {"series": len(v["series"]), "ema_crudo": round(media(v["ema_crudo"]), 3),
                "ema_corr": round(media(v["ema_corr"]), 3), "caja_corr": round(media(v["caja_corr"]), 3),
                "sesgo_abs": round(media(v["sesgo"]), 2)} for m, v in acc.items()}


def eleccion_fuera_de_muestra(comp, h):
    """Elegir el mejor modelo (y el mejor trio) de cada serie con la 1a mitad de los dias y medirlo en la 2a,
    contra GFS+ECMWF y contra el promedio de todos. Devuelve EMA corregido y % caja en la 2a mitad."""
    res = defaultdict(lambda: defaultdict(list))
    por_serie = {}
    for (serie, hz), mods in comp.items():
        if hz != h or not mods:
            continue
        n = min(len(v) for v in mods.values())
        if n < 20:
            continue
        mitad = n // 2
        ema1 = {m: media([abs(f["real"] - f["corr"]) for f in v[:mitad]]) for m, v in mods.items()
                if m not in ("Promedio", *COMBINADOS)}
        orden = sorted(ema1, key=ema1.get)
        mejor, trio = orden[0], orden[:3]
        segunda = {m: v[mitad:] for m, v in mods.items()}
        dias2 = [f["fecha"] for f in segunda[mejor]]

        def prom(ms):
            filas = []
            for i in range(len(dias2)):
                fs = [segunda[m][i] for m in ms]
                filas.append({"real": fs[0]["real"], "en_f": fs[0]["en_f"],
                              "corr": sum(f["corr"] for f in fs) / len(fs)})
            return filas

        cand = {"mejor de la 1a mitad": segunda[mejor], "trio de la 1a mitad": prom(trio)}
        for nombre in ("GFS+ECMWF", "Promedio", "GFS", "ECMWF"):
            if nombre in segunda:
                cand[nombre] = segunda[nombre]
        for nombre, fs in cand.items():
            res[nombre]["ema"].append(media([abs(f["real"] - f["corr"]) for f in fs]))
            res[nombre]["caja"].append(media([caja(f["corr"], f["en_f"]) == caja(f["real"], f["en_f"]) for f in fs]))
        # el mejor de la 2a mitad, para ver si se repite
        ema2 = {m: media([abs(f["real"] - f["corr"]) for f in v]) for m, v in segunda.items()
                if m not in ("Promedio", *COMBINADOS)}
        por_serie[serie] = {"mejor_1a": mejor, "mejor_2a": min(ema2, key=ema2.get),
                            "puesto_en_2a": sorted(ema2, key=ema2.get).index(mejor) + 1, "modelos": len(ema2)}
    tabla = {k: {"series": len(v["ema"]), "ema_corr": round(media(v["ema"]), 3), "caja_corr": round(media(v["caja"]), 3)}
             for k, v in res.items()}
    return tabla, por_serie


def bots_vs_modelos(filas):
    """Ensamble que anoto el bot (primera foto de cada dia, ~1 dia antes) contra los modelos a 1 dia, mismos dias.
    Sin corregir sesgo (hay pocos dias)."""
    prim = {}
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            k = (r["serie"], r["fecha"])
            if k not in prim or r["momento_utc"] < prim[k]["momento_utc"]:
                prim[k] = r
    idx = {(f["serie"], f["fecha"], f["modelo"]): f for f in filas if f["horizonte"] == 1}
    acc = defaultdict(list)
    for (serie, fecha), r in prim.items():
        base = idx.get((serie, fecha, "GFS"))
        if base is None:
            continue
        en_f = "°F" in r["caja"]
        ens = (float(r["media_cruda"]) - 32) / 1.8 if en_f else float(r["media_cruda"])
        acc["Ensamble del bot"].append(abs(base["real"] - ens))
        for m in list(MODELOS) + ["Promedio", *COMBINADOS]:
            f = idx.get((serie, fecha, m))
            if f:
                acc[m].append(abs(f["real"] - f["pron"]))
    return {m: {"n": len(v), "ema_crudo": round(media(v), 3)} for m, v in acc.items() if v}


# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    ser = series()
    sta = json.load(open(os.path.join(RAIZ, "estaciones.json"), encoding="utf-8"))
    icaos = {i: TZ[s.split("|")[1]] for s, (i, _) in ser.items() if i != "HKO"}   # HKO no tiene METAR
    log(f"{len(ser)} series, {len(icaos)} estaciones, {DESDE} a {HASTA}, {len(MODELOS)} modelos")

    with ThreadPoolExecutor(3) as ex:
        pron = dict(zip(icaos, ex.map(lambda i: pronosticos(i, sta[i]["lat"], sta[i]["lon"], icaos[i]), icaos)))
    log("pronosticos listos: " + ", ".join(f"{i}:{len(v)}" for i, v in pron.items()))
    with ThreadPoolExecutor(3) as ex:
        obs = dict(zip(icaos, ex.map(lambda i: metar(i, icaos[i]), icaos)))
    log("metar listos: " + ", ".join(f"{i}:{len(v)}" for i, v in obs.items()))

    filas = []
    for s, (icao, en_f) in sorted(ser.items()):
        if icao not in icaos:
            continue
        ix = 0 if s.startswith("highest") else 1
        for k in range(DIAS):
            d = (DESDE + timedelta(days=k)).isoformat()
            o = obs[icao].get(d)
            if not o:
                continue
            for hz in HORIZONTES:
                vals = {m: pron[icao][(d, m, hz)][ix] for m in MODELOS if (d, m, hz) in pron[icao]}
                if not vals:
                    continue
                vals["Promedio"] = sum(vals.values()) / len(vals)
                for c, ms in COMBINADOS.items():
                    if all(m in vals for m in ms):
                        vals[c] = sum(vals[m] for m in ms) / len(ms)
                for m, v in vals.items():
                    filas.append({"serie": s, "fecha": d, "icao": icao, "en_f": en_f, "horizonte": hz,
                                  "modelo": m, "pron": round(v, 2), "real": o[ix]})
    log(f"{len(filas)} filas")
    corregir(filas)
    with open(os.path.join(OUT, "dias.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["serie", "fecha", "icao", "en_f", "horizonte", "modelo", "pron", "corr", "real"],
                           delimiter=";")
        w.writeheader()
        for x in filas:
            w.writerow(dict(x, en_f=int(x["en_f"]), corr="" if x["corr"] is None else round(x["corr"], 2)))

    comp = comparables(filas)
    glob = {h: resumen_global(comp, h) for h in HORIZONTES}
    fuera = {h: eleccion_fuera_de_muestra(comp, h) for h in HORIZONTES}
    por_serie = {}
    for (serie, hz), mods in comp.items():
        por_serie.setdefault(serie, {})[hz] = {m: stats(fs) for m, fs in mods.items()}
    bots = bots_vs_modelos(filas)
    resumen = {"desde": DESDE.isoformat(), "hasta": HASTA.isoformat(), "global": glob,
               "fuera_de_muestra": {h: v[0] for h, v in fuera.items()},
               "eleccion_por_serie": {h: v[1] for h, v in fuera.items()}, "por_serie": por_serie, "bots": bots}
    json.dump(resumen, open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    informe(resumen)
    log("listo")


def informe(r):
    L = [f"# Comparacion de modelos de pronostico ({r['desde']} a {r['hasta']})", "",
         "Error = real (METAR) - pronostico, en °C. EMA = error medio absoluto. 'Corregido' = restando el sesgo",
         "de esa serie medido solo con los dias anteriores. Caja = % de dias en la caja ganadora (1 °C o 2 °F).",
         "Cada serie (ciudad + maxima/minima) pesa igual; todos los modelos se miden sobre los mismos dias.", ""]
    for h in HORIZONTES:
        g = r["global"][h]
        L += [f"## Horizonte {h} dia(s)", "", "| Modelo | Series | EMA crudo | EMA corregido | Caja (corr.) | |sesgo| |",
              "|---|---|---|---|---|---|"]
        for m, v in sorted(g.items(), key=lambda kv: kv[1]["ema_corr"]):
            L.append(f"| {m} | {v['series']} | {v['ema_crudo']:.2f} | {v['ema_corr']:.2f} | {v['caja_corr']:.0%} | {v['sesgo_abs']:.2f} |")
        f = r["fuera_de_muestra"][h]
        if f:
            L += ["", "Elegir modelo por ciudad (elegido con la 1a mitad, medido en la 2a):", "",
                  "| Regla | Series | EMA corregido | Caja |", "|---|---|---|---|"]
            for k, v in sorted(f.items(), key=lambda kv: kv[1]["ema_corr"]):
                L.append(f"| {k} | {v['series']} | {v['ema_corr']:.2f} | {v['caja_corr']:.0%} |")
            el = r["eleccion_por_serie"][h]
            if el:
                rep = sum(1 for v in el.values() if v["puesto_en_2a"] <= 3)
                L.append(f"\nEl mejor modelo de la 1a mitad quedo entre los 3 mejores de la 2a en {rep} de {len(el)} series.")
        L.append("")
    L += ["## Mejor modelo por serie (horizonte 1 dia, EMA corregido, todos los dias)", "",
          "| Serie | n | Mejor | EMA | 2o | EMA | GFS+ECMWF | Promedio |", "|---|---|---|---|---|---|---|---|"]
    for serie, hs in sorted(r["por_serie"].items()):
        mods = {m: s for m, s in hs.get(1, {}).items() if s and m not in ("Promedio", *COMBINADOS)}
        if not mods:
            continue
        o = sorted(mods, key=lambda m: mods[m]["ema_corr"])
        base = hs[1].get("GFS+ECMWF") or {}
        pr = hs[1].get("Promedio") or {}
        L.append(f"| {serie} | {mods[o[0]]['n']} | {o[0]} | {mods[o[0]]['ema_corr']:.2f} | {o[1] if len(o) > 1 else ''} | "
                 f"{mods[o[1]]['ema_corr']:.2f} | {base.get('ema_corr', float('nan')):.2f} | {pr.get('ema_corr', float('nan')):.2f} |")
    L += ["", "## Ensamble del bot contra los modelos (mismos dias, sin corregir, desde el 20-oct)", "",
          "| Modelo | n | EMA crudo |", "|---|---|---|"]
    for m, v in sorted(r["bots"].items(), key=lambda kv: kv[1]["ema_crudo"]):
        L.append(f"| {m} | {v['n']} | {v['ema_crudo']:.2f} |")
    open(os.path.join(OUT, "informe.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()

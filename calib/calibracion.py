"""
CALIBRACION DEL PRONOSTICO POR CIUDAD (investigacion, en papel; no toca a los bots).

Para cada serie (maxima o minima de cada ciudad) y cada dia de los ultimos DIAS dias:
  - pronostico del dia anterior de GFS y ECMWF (Open-Meteo "previous runs", corrida de ~24 h antes),
    maximo/minimo del dia local en la estacion oficial;
  - temperatura real: maximo/minimo de los METAR de rutina de esa estacion (archivo de IEM),
    en decimas del grupo T, como cuenta Polymarket desde el 21-oct (estaciones.temp_metar);
  - caja ganadora de Polymarket (gamma), cuando hubo mercado.
Ademas compara los pronosticos que anotaron los bots (pronostico.csv) con lo real.

Salida: calib/dias.csv (un renglon por serie y dia) y calib/informe.md.
error = real - pronostico, en °C (positivo = el modelo se quedo corto).
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
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from estaciones import TZ, leer_caja, estacion_de_evento  # noqa: E402

DIAS = 45
HASTA = datetime.now(timezone.utc).date() - timedelta(days=1)
DESDE = HASTA - timedelta(days=DIAS - 1)
MIN_PREVIOS = 5     # dias previos para estimar el sesgo antes de "corregir" (sin mirar el futuro)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "calib")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-calibracion/1.0 (investigacion personal)"
GAMMA = "https://gamma-api.polymarket.com/events"
PREV = "https://previous-runs-api.open-meteo.com/v1/forecast"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
MODELOS = {"gfs": ["gfs_global", "gfs025", "gfs_seamless"], "ecmwf": ["ecmwf_ifs025", "ecmwf_ifs"]}


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", file=sys.stderr, flush=True)


def get(url, params, intentos=3, timeout=60):
    for i in range(intentos):
        try:
            r = S.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                time.sleep(5 * (i + 1))
                continue
            return r
        except Exception as e:
            log(f"{url} fallo ({e}), reintento")
            time.sleep(2 * (i + 1))
    return None


def redondear(v):
    return math.floor(v + 0.5 + 1e-9)


def a_unidad(c, en_f):
    return c * 1.8 + 32 if en_f else c


# ---------------------------------------------------------------------------

def series():
    """{serie: icao} a partir de lo que vieron los bots."""
    out = {}
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            out[r["serie"]] = r["icao"]
    return out


def pronosticos(icao, lat, lon, tz):
    """{(fecha, modelo): (max, min)} del pronostico del dia anterior."""
    out = {}
    for nombre, alias in MODELOS.items():
        for m in alias:
            r = get(PREV, {"latitude": lat, "longitude": lon, "hourly": "temperature_2m_previous_day1",
                           "models": m, "timezone": tz, "start_date": DESDE.isoformat(),
                           "end_date": HASTA.isoformat()})
            if r is None or r.status_code != 200:
                log(f"open-meteo {icao} {m}: {None if r is None else r.status_code} {'' if r is None else r.text[:150]}")
                continue
            h = r.json().get("hourly", {})
            clave = next((k for k in h if k.startswith("temperature_2m_previous_day1")), None)
            if not clave:
                continue
            por_dia = defaultdict(list)
            for t, v in zip(h["time"], h[clave]):
                if v is not None:
                    por_dia[t[:10]].append(v)
            for d, vs in por_dia.items():
                if len(vs) >= 20:
                    out[(d, nombre)] = (max(vs), min(vs))
            break
        time.sleep(0.3)
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
    """{fecha_local: (max, min, n_reportes)} con los METAR de rutina (IEM)."""
    ini = DESDE - timedelta(days=1)
    fin = HASTA + timedelta(days=2)
    base = {"data": "metar", "tz": "Etc/UTC", "format": "onlycomma", "latlon": "no", "missing": "empty",
            "report_type": "3", "year1": ini.year, "month1": ini.month, "day1": ini.day,
            "year2": fin.year, "month2": fin.month, "day2": fin.day}
    filas = []
    for sid in ([icao, icao[1:]] if icao.startswith("K") else [icao]):
        r = get(IEM, dict(base, station=sid), timeout=120)
        if r is None or r.status_code != 200:
            continue
        filas = list(csv.DictReader(io.StringIO(r.text)))
        if filas:
            break
    zona = ZoneInfo(tz)
    dias = defaultdict(list)
    for f in filas:
        try:
            t = temp_raw(f["metar"])
            ts = datetime.strptime(f["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if t is not None:
            dias[ts.astimezone(zona).date().isoformat()].append(t)
    return {d: (max(v), min(v), len(v)) for d, v in dias.items() if len(v) >= 12}


def ganadora(tipo, ciudad, d):
    slug = f"{tipo}-temperature-in-{ciudad}-on-{d:%B}-{d.day}-{d.year}".lower()
    r = get(GAMMA, {"slug": slug}, timeout=30)
    if r is None or r.status_code != 200 or not r.json():
        return None, None
    ev = r.json()[0]
    est = estacion_de_evento(ev)
    for m in ev.get("markets", []):
        try:
            if m.get("closed") and json.loads(m.get("outcomePrices") or "[]")[0] in ("1", 1):
                return m["groupItemTitle"], est
        except Exception:
            pass
    return None, est


def en_caja(v, caja):
    lo, hi, _ = leer_caja(caja)
    return (lo is None or v >= lo) and (hi is None or v <= hi)


# ---------------------------------------------------------------------------

def bots(ser_real):
    """Error de lo que anotaron los bots (primera foto de cada dia en pronostico.csv)."""
    prim = {}
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            k = (r["serie"], r["fecha"])
            if k not in prim or r["momento_utc"] < prim[k]["momento_utc"]:
                prim[k] = r
    out = []
    for (serie, fecha), r in prim.items():
        real = ser_real.get((serie, fecha))
        if real is None:
            continue
        en_f = "°F" in r["caja"]
        media_c = (float(r["media_cruda"]) - 32) / 1.8 if en_f else float(r["media_cruda"])
        out.append((serie, fecha, real - media_c, float(r["sesgo_usado"])))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    ser = series()
    sta = json.load(open(os.path.join(RAIZ, "estaciones.json"), encoding="utf-8"))
    sta["HKO"] = {"lat": 22.302, "lon": 114.174}
    icaos = {}
    for s, i in ser.items():
        icaos[i] = TZ[s.split("|")[1]]
    log(f"{len(ser)} series, {len(icaos)} estaciones, {DESDE} a {HASTA}")

    with ThreadPoolExecutor(4) as ex:
        pron = dict(zip(icaos, ex.map(lambda i: pronosticos(i, sta[i]["lat"], sta[i]["lon"], icaos[i]), icaos)))
    log("pronosticos listos")
    with ThreadPoolExecutor(3) as ex:
        obs = dict(zip(icaos, ex.map(lambda i: metar(i, icaos[i]) if i != "HKO" else {}, icaos)))
    log("metar listos: " + ", ".join(f"{i}:{len(v)}" for i, v in obs.items()))
    tareas = [(s, DESDE + timedelta(days=k)) for s in ser for k in range(DIAS)]
    with ThreadPoolExecutor(8) as ex:
        gans = dict(zip(tareas, ex.map(lambda t: ganadora(*t[0].split("|"), t[1]), tareas)))
    log("ganadoras listas")

    filas = []
    for s, icao in sorted(ser.items()):
        tipo = s.split("|")[0]
        ix = 0 if tipo == "highest" else 1
        for k in range(DIAS):
            d = (DESDE + timedelta(days=k)).isoformat()
            g = pron[icao].get((d, "gfs"))
            e = pron[icao].get((d, "ecmwf"))
            o = obs[icao].get(d)
            caja, est_ev = gans[(s, DESDE + timedelta(days=k))]
            if not (g or e) or not (o or caja):
                continue
            pg = g[ix] if g else None
            pe = e[ix] if e else None
            comb = sum(x for x in (pg, pe) if x is not None) / len([x for x in (pg, pe) if x is not None])
            real = o[ix] if o else None
            en_f = ("°F" in caja) if caja else icao.startswith("K")   # EE.UU. usa cajas en °F
            filas.append({"serie": s, "fecha": d, "icao": icao, "estacion_mercado": est_ev or "",
                          "gfs": None if pg is None else round(pg, 2), "ecmwf": None if pe is None else round(pe, 2),
                          "combinado": round(comb, 2), "real_metar": real, "caja_ganadora": caja or "",
                          "metar_en_caja": "" if (real is None or not caja) else int(en_caja(redondear(a_unidad(real, en_f)), caja)),
                          "en_f": int(en_f)})
    with open(os.path.join(OUT, "dias.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=";")
        w.writeheader()
        w.writerows(filas)
    log(f"{len(filas)} dias-serie")
    informe(filas)


def stats(errs):
    n = len(errs)
    if not n:
        return None
    m = sum(errs) / n
    mae = sum(abs(x) for x in errs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in errs) / (n - 1)) if n > 1 else float("nan")
    return n, m, mae, sd


def informe(filas):
    por = defaultdict(list)
    for f in filas:
        por[f["serie"]].append(f)
    res = []
    ser_real = {}
    for s, fs in por.items():
        fs.sort(key=lambda x: x["fecha"])
        errs, errs_g, errs_e = [], [], []
        hit_c, hit_k, n_c, n_k, previos = 0, 0, 0, 0, []
        for f in fs:
            if f["real_metar"] is not None:
                ser_real[(s, f["fecha"])] = f["real_metar"]
                err = f["real_metar"] - f["combinado"]
                errs.append(err)
                if f["gfs"] is not None:
                    errs_g.append(f["real_metar"] - f["gfs"])
                if f["ecmwf"] is not None:
                    errs_e.append(f["real_metar"] - f["ecmwf"])
            # acierto de caja: la caja ganadora (o, sin mercado, el grado redondeado del METAR)
            en_f = bool(f["en_f"])
            if f["caja_ganadora"]:
                ok = lambda c: en_caja(redondear(a_unidad(c, en_f)), f["caja_ganadora"])
            elif f["real_metar"] is not None:
                obj = redondear(a_unidad(f["real_metar"], en_f))
                if en_f:     # cajas de 2 °F: comparar con un margen equivalente
                    ok = lambda c: abs(redondear(a_unidad(c, True)) - obj) <= 1
                else:
                    ok = lambda c: redondear(c) == obj
            else:
                continue
            n_c += 1
            hit_c += ok(f["combinado"])
            if len(previos) >= MIN_PREVIOS:
                n_k += 1
                hit_k += ok(f["combinado"] + sum(previos) / len(previos))
            if f["real_metar"] is not None:
                previos.append(f["real_metar"] - f["combinado"])
        st = stats(errs)
        if not st:
            continue
        sg, se = stats(errs_g), stats(errs_e)
        res.append({"serie": s, "n": st[0], "sesgo": st[1], "mae": st[2], "desvio": st[3],
                    "mae_gfs": sg[2] if sg else None, "mae_ecmwf": se[2] if se else None,
                    "acierto": hit_c / n_c if n_c else None, "n_caja": n_c,
                    "acierto_corr": hit_k / n_k if n_k else None, "n_corr": n_k,
                    "metar_vs_caja": sum(int(f["metar_en_caja"]) for f in fs if f["metar_en_caja"] != ""),
                    "n_metar_caja": sum(1 for f in fs if f["metar_en_caja"] != ""),
                    "estaciones_mercado": sorted({f["estacion_mercado"] for f in fs if f["estacion_mercado"]})})
    json.dump(res, open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    b = bots(ser_real)
    L = [f"# Calibración del pronóstico por ciudad ({DESDE} a {HASTA})", "",
         "error = real − pronóstico (°C). Pronóstico: GFS+ECMWF del día anterior (Open-Meteo, corrida ~24 h antes). "
         "Real: máximo/mínimo de los METAR de rutina de la estación oficial (IEM). "
         f"Acierto de caja: el pronóstico redondeado cae en la caja ganadora; 'corregido' suma el sesgo de los días previos (≥{MIN_PREVIOS}).",
         "", "Ordenado por desvío (el error que queda después de corregir el sesgo, que es lo que los bots no pueden aprender).", ""]
    for tipo, titulo in (("highest", "Máximas"), ("lowest", "Mínimas")):
        L += [f"## {titulo}", "", "| ciudad | días | sesgo | error medio abs. | desvío | MAE GFS | MAE ECMWF | acierto caja | acierto corregido | METAR=caja |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for r in sorted((r for r in res if r["serie"].startswith(tipo)), key=lambda r: r["desvio"] if r["n"] > 1 else 99):
            f2 = lambda x: "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.2f}"
            L.append(f"| {r['serie'].split('|')[1]} | {r['n']} | {r['sesgo']:+.2f} | {r['mae']:.2f} | {f2(r['desvio'])} | "
                     f"{f2(r['mae_gfs'])} | {f2(r['mae_ecmwf'])} | "
                     f"{'' if r['acierto'] is None else format(r['acierto'], '.0%')} ({r['n_caja']}) | "
                     f"{'' if r['acierto_corr'] is None else format(r['acierto_corr'], '.0%')} ({r['n_corr']}) | "
                     f"{r['metar_vs_caja']}/{r['n_metar_caja']} |")
        L.append("")
    if b:
        L += ["## Lo que anotaron los bots (pronostico.csv, primera foto)", "",
              "| serie | fecha | error crudo | sesgo que usó |", "|---|---|---|---|"]
        for s, fe, err, sg in sorted(b):
            L.append(f"| {s} | {fe} | {err:+.2f} | {sg:+.2f} |")
        L.append("")
    open(os.path.join(OUT, "informe.md"), "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "informe":
        with open(os.path.join(OUT, "dias.csv"), encoding="utf-8") as f:
            fs = []
            for r in csv.DictReader(f, delimiter=";"):
                for k in ("gfs", "ecmwf", "combinado", "real_metar"):
                    r[k] = float(r[k]) if r[k] not in ("", None) else None
                r["en_f"] = int(r["en_f"])
                fs.append(r)
        informe(fs)
    else:
        main()

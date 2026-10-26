"""
INVESTIGACION (no opera): ¿la regla nueva de resolucion (METAR de rutina) encarece las cajas altas?
Regla fija en regla_metar/REGLA.md. Corre cada hora desde Actions (el contenedor no llega a Polymarket).

Cada corrida:
  - fotos:      libro real de TODAS las cajas de cada evento de temperatura cuando la estacion esta en uno de los
                momentos de la regla (M0 = 06-07 h local del dia anterior, M1 = 06-07 h del dia, M2 = 12-13 h del dia)
                -> datos/fotos.csv (una foto por evento y momento)
  - resultados: caja ganadora de los eventos ya cerrados desde el 23-oct -> datos/resultados.csv
  - metar:      todos los METAR y SPECI de aviationweather de las estaciones (cada ~6 h) -> datos/metar.csv.gz

Deja de sacar fotos despues de FIN_FOTOS y de buscar resultados despues de FIN.

Uso: python regla_metar/recolector.py
"""

import csv
import gzip
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from estaciones import TZ, estacion_de_evento, tasa_de  # noqa: E402
import pronostico  # noqa: E402

DESDE = date(2026, 10, 23)        # primer dia con la regla nueva
HASTA = date(2026, 11, 6)         # ultimo dia de evento que entra
FIN_FOTOS = date(2026, 11, 7)
FIN = date(2026, 11, 10)
ACCIONES = 10
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
F_FOTOS = os.path.join(CARPETA, "fotos.csv")
F_RES = os.path.join(CARPETA, "resultados.csv")
F_METAR = os.path.join(CARPETA, "metar.csv.gz")
F_EST = os.path.join(CARPETA, "estado.json")
S = pronostico.S
GAMMA = "https://gamma-api.polymarket.com/events"
AWC = "https://aviationweather.gov/api/data/metar"
MESES = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
         "november", "december"]

COLS_FOTOS = ["momento_utc", "momento", "hora_local", "serie", "fecha", "icao", "slug", "caja", "bid", "ask", "medio",
              "si_10", "no_10", "tasa_comision"]
COLS_RES = ["serie", "fecha", "icao", "slug", "fuente", "caja", "gano"]
COLS_METAR = ["icao", "obs_epoch", "tipo", "temp", "raw"]


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def cargar_estado():
    try:
        with open(F_EST, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def guardar_estado(est):
    with open(F_EST, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, indent=1, sort_keys=True)


def agregar(nombre, cols, filas):
    if not filas:
        return
    nuevo = not os.path.exists(nombre)
    with open(nombre, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(cols)
        w.writerows(filas)


def evento(e):
    """Datos de un evento de temperatura diaria o None si no entra."""
    m = re.match(r"^(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})$", e.get("slug", ""))
    if not m or m.group(2) not in TZ:
        return None
    icao = estacion_de_evento(e)
    if not icao or icao == "HKO":
        return None
    fuente = "aviationweather" if "aviationweather" in (e.get("resolutionSource") or "") + " ".join(
        (x.get("description") or "") for x in (e.get("markets") or [])[:1]) + (e.get("description") or "") else "otra"
    fecha = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%B %d %Y").date()
    return {"tipo": m.group(1), "ciudad": m.group(2), "serie": f"{m.group(1)}|{m.group(2)}", "icao": icao,
            "fecha": fecha, "slug": e["slug"], "fuente": fuente, "markets": e.get("markets") or []}


def momento(ev, ahora):
    """Momento de la regla en que esta la estacion ahora (M0, M1, M2) o None."""
    loc = ahora.astimezone(ZoneInfo(TZ[ev["ciudad"]]))
    if loc.date() == ev["fecha"] - timedelta(days=1) and loc.hour in (6, 7):
        return "M0", loc.hour
    if loc.date() == ev["fecha"] and loc.hour in (6, 7):
        return "M1", loc.hour
    if loc.date() == ev["fecha"] and loc.hour in (12, 13):
        return "M2", loc.hour
    return None, loc.hour


def fotos(est):
    ahora = datetime.now(timezone.utc)
    if ahora.date() > FIN_FOTOS:
        log("fotos: periodo terminado")
        return
    evs = []
    for off in range(0, 3000, 100):
        r = S.get(GAMMA, params={"tag_slug": "daily-temperature", "closed": "false", "limit": 100, "offset": off},
                  timeout=30).json()
        evs += r
        if len(r) < 100:
            break
    hechas = set(est.get("fotos", []))
    pendientes = []
    for e in evs:
        ev = evento(e)
        if not ev or not DESDE <= ev["fecha"] <= HASTA:
            continue
        mom, hl = momento(ev, ahora)
        if not mom or f"{ev['slug']}|{mom}" in hechas:
            continue
        cajas = [(m.get("groupItemTitle") or m.get("question", ""), tasa_de(m), json.loads(m["clobTokenIds"])[0])
                 for m in ev["markets"] if m.get("clobTokenIds") and not m.get("closed")]
        if cajas:
            pendientes.append((ev, mom, hl, cajas))
    toks = [c[2] for _, _, _, cs in pendientes for c in cs]
    with ThreadPoolExecutor(8) as ex:
        libs = dict(zip(toks, ex.map(pronostico.libro, toks)))
    filas = []
    for ev, mom, hl, cajas in pendientes:
        if any(libs.get(t) is None for _, _, t in cajas):   # sin todos los libros la foto no sirve: se reintenta
            log(f"faltan libros en {ev['slug']} {mom}")
            continue
        for caja, tasa, tok in cajas:
            bids, asks = libs[tok]
            bid = bids[0][0] if bids else ""
            ask = asks[0][0] if asks else ""
            medio = round((bid + ask) / 2, 4) if bids and asks else ""
            si = pronostico.precio_medio(asks, ACCIONES)
            vs = pronostico.precio_medio(bids, ACCIONES)
            filas.append([ahora.strftime("%Y-%m-%d %H:%M"), mom, hl, ev["serie"], ev["fecha"].isoformat(), ev["icao"],
                          ev["slug"], caja, bid, ask, medio, "" if si is None else si,
                          "" if vs is None else round(1 - vs, 4), tasa])
        hechas.add(f"{ev['slug']}|{mom}")
    agregar(F_FOTOS, COLS_FOTOS, filas)
    est["fotos"] = sorted(hechas)
    log(f"fotos: {len(pendientes)} eventos en momento, {len(filas)} cajas guardadas")


def resultados(est):
    hoy = datetime.now(timezone.utc).date()
    if hoy > FIN:
        return
    listos = set(est.get("resultados", []))
    pedir = []
    d = DESDE
    while d <= min(HASTA, hoy - timedelta(days=1)):
        for tipo in ("highest", "lowest"):
            for ciudad in TZ:
                slug = f"{tipo}-temperature-in-{ciudad}-on-{MESES[d.month - 1]}-{d.day}-{d.year}"
                if slug not in listos:
                    pedir.append((slug, d))
        d += timedelta(days=1)

    def uno(x):
        try:
            return x, S.get(GAMMA, params={"slug": x[0]}, timeout=30).json()
        except Exception as ex:
            log(f"gamma fallo {x[0]}: {ex}")
            return x, None

    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(uno, pedir))
    filas = []
    for (slug, d), j in res:
        if j is None:
            continue
        if not j:                              # no existe ese evento (ciudad sin mercado ese dia)
            if (hoy - d).days >= 3:
                listos.add(slug)
            continue
        ev = evento(j[0])
        if not ev:
            listos.add(slug)
            continue
        cajas, hay = [], False
        for m in ev["markets"]:
            try:
                pr = json.loads(m.get("outcomePrices") or "[]")
            except ValueError:
                pr = []
            gano = int(bool(m.get("closed") and pr and float(pr[0]) >= 0.99))
            hay |= bool(gano)
            cajas.append((m.get("groupItemTitle") or m.get("question", ""), gano))
        if not hay:
            if (hoy - d).days >= 5:           # se da por perdido (disputa o sin resolver)
                listos.add(slug)
            continue
        for caja, gano in cajas:
            filas.append([ev["serie"], d.isoformat(), ev["icao"], slug, ev["fuente"], caja, gano])
        listos.add(slug)
    agregar(F_RES, COLS_RES, filas)
    est["resultados"] = sorted(listos)
    log(f"resultados: {len(pedir)} consultados, {len({f[3] for f in filas})} eventos nuevos con ganadora")


def metar(est):
    ahora = datetime.now(timezone.utc)
    ult = est.get("metar_ultimo")
    if ult and (ahora - datetime.fromisoformat(ult)).total_seconds() < 5.5 * 3600 or ahora.date() > FIN:
        return
    ests = sorted(set(icaos_de_resultados()))
    if not ests:
        return
    desde = datetime.fromisoformat(ult) - timedelta(hours=6) if ult else datetime(2026, 10, 22, tzinfo=timezone.utc)
    vistos, filas = set(), []
    if os.path.exists(F_METAR):
        with gzip.open(F_METAR, "rt", newline="") as f:
            for r in csv.DictReader(f):
                vistos.add((r["icao"], r["obs_epoch"], r["raw"]))
    for icao in ests:
        fin = ahora + timedelta(hours=1)
        while fin > desde:
            try:
                j = S.get(AWC, params={"ids": icao, "format": "json", "hours": 73,
                                       "date": fin.strftime("%Y-%m-%dT%H:%M:%SZ")}, timeout=60).json()
            except Exception as ex:
                log(f"awc fallo {icao}: {ex}")
                j = []
            for x in j or []:
                k = (x.get("icaoId"), str(x.get("obsTime")), x.get("rawOb"))
                if k not in vistos:
                    vistos.add(k)
                    filas.append([*k[:2], x.get("metarType"), x.get("temp"), k[2]])
            fin -= timedelta(hours=72)
            time.sleep(0.3)
    viejas = []
    if os.path.exists(F_METAR):
        with gzip.open(F_METAR, "rt", newline="") as f:
            viejas = list(csv.reader(f))[1:]
    with gzip.open(F_METAR, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS_METAR)
        w.writerows(viejas + [[f[0], f[1], f[2], f[3], f[4]] for f in filas])
    est["metar_ultimo"] = ahora.isoformat(timespec="seconds")
    log(f"metar: {len(ests)} estaciones, {len(filas)} reportes nuevos")


def icaos_de_resultados():
    if not os.path.exists(F_RES):
        return []
    with open(F_RES, encoding="utf-8") as f:
        return [r["icao"] for r in csv.DictReader(f, delimiter=";")]


if __name__ == "__main__":
    os.makedirs(CARPETA, exist_ok=True)
    est = cargar_estado()
    for paso in (fotos, resultados, metar):
        try:
            paso(est)
        except Exception as ex:
            log(f"{paso.__name__} fallo: {ex}")
        guardar_estado(est)

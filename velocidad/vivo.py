"""
INVESTIGACION (sin operar): ¿llegariamos a tiempo a una caja que un METAR acaba de matar?

Mira aviationweather.gov cada pocos segundos (la fuente con la que resuelve Polymarket desde el
23-oct-2026) y tambien el archivo de ciclo de tgftp.nws.noaa.gov. Cuando un METAR de rutina mata una
caja (la maxima del dia ya paso su techo, o la minima ya bajo de su piso), anota el libro real de esa
caja en el momento en que lo vimos y 10 s, 30 s, 1, 2, 5 y 15 min despues, y a los 15 min baja las
operaciones de ese mercado (para ver quien llego antes que nosotros y a que precio).

No compra ni vende nada.

Archivos (velocidad/datos/):
  vivo_metar.csv    cada reporte nuevo: estacion, hora de observacion, fuente, cuando lo vimos, receiptTime
  vivo_muertes.csv  cada caja muerta: estacion, mercado, caja, temperatura, horas (obs/publicado/visto), precio antes
  vivo_libros.csv   el libro del Si de esa caja a cada demora: mejor bid, acciones y US$ que se podian ganar
  vivo_trades.csv   operaciones del mercado entre 30 min antes de la obs y 15 min despues de verla

Uso: python velocidad/vivo.py MINUTOS
"""

import csv
import heapq
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))
from estaciones import TZ, leer_caja, redondear, temp_metar  # noqa: E402
from estaciones_vel import CIUDAD_ESTACION, ESTACIONES  # noqa: E402

CARPETA = os.path.join(AQUI, "datos")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-velocidad/1.0 (investigacion personal)"
AWC = "https://aviationweather.gov/api/data/metar"
TGFTP = "https://tgftp.nws.noaa.gov/data/observations/metar/cycles/{:02d}Z.TXT"
GAMMA = "https://gamma-api.polymarket.com/events"
BOOK = "https://clob.polymarket.com/book"
TRADES = "https://data-api.polymarket.com/trades"
DEMORAS = [0, 10, 30, 60, 120, 300, 900]   # segundos despues de verlo en aviationweather
CADA_AWC = 4
CADA_TGFTP = 10


def log(m):
    print(datetime.now(timezone.utc).strftime("%H:%M:%S"), m, flush=True)


def anotar(nombre, cols, fila):
    ruta = os.path.join(CARPETA, nombre)
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(cols)
        w.writerow(fila)


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-4] if t else ""


# ---------------------------------------------------------------------------
# MERCADOS
# ---------------------------------------------------------------------------

def series_abiertas():
    """Mercados de temperatura abiertos de hoy (hora local) con estacion METAR conocida."""
    evs = []
    for off in range(0, 2000, 100):
        r = S.get(GAMMA, params={"tag_slug": "daily-temperature", "closed": "false", "limit": 100, "offset": off},
                  timeout=30).json()
        if not r:
            break
        evs += r
        if len(r) < 100:
            break
    out = []
    for e in evs:
        m = re.match(r"^(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})$", e.get("slug", ""))
        if not m or m.group(2) not in CIUDAD_ESTACION or m.group(2) not in TZ:
            continue
        icao = CIUDAD_ESTACION[m.group(2)]
        x = re.search(r"ids=([A-Z0-9]{4})", e.get("resolutionSource") or "", re.I)
        if x:
            icao = x.group(1).upper()
        tz = ZoneInfo(TZ[m.group(2)])
        fecha = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%B %d %Y").date()
        inicio = datetime(fecha.year, fecha.month, fecha.day, tzinfo=tz)
        fin = inicio + timedelta(days=1)
        out.append({"tipo": m.group(1), "ciudad": m.group(2), "icao": icao, "fecha": fecha.isoformat(),
                    "inicio": inicio.timestamp(), "fin": fin.timestamp(), "markets": e.get("markets", [])})
    return out


def libro(token):
    b = S.get(BOOK, params={"token_id": token}, timeout=10).json()
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
    return bids, asks


def resumen_libro(bids, asks):
    """Para una caja muerta el Si vale 0: lo que se puede ganar es vender Si (o comprar No) a los bids."""
    def suma(minimo):
        acc = sum(q for p, q in bids if p >= minimo)
        usd = sum(p * q for p, q in bids if p >= minimo)
        return round(acc, 2), round(usd, 2)
    a1, u1 = suma(0.01)
    a2, u2 = suma(0.02)
    a5, u5 = suma(0.05)
    return [bids[0][0] if bids else "", bids[0][1] if bids else "", asks[0][0] if asks else "",
            a1, u1, a2, u2, a5, u5]


# ---------------------------------------------------------------------------
# BUCLE
# ---------------------------------------------------------------------------

def correr(minutos):
    os.makedirs(CARPETA, exist_ok=True)
    fin = time.time() + minutos * 60
    rutina = {}        # icao -> {obs_epoch: temp_c}   (solo reportes de rutina, cuentan para resolver)
    visto = set()      # (fuente, icao, obs, raw)
    muertas = set()    # condition_id ya registradas
    series, ult_series = [], 0
    agenda = []        # heap (cuando, n, tarea)
    n_tarea = 0
    tg_mod = {}
    ult_tg = 0
    primera = True

    while time.time() < fin:
        t_vuelta = time.time()
        try:
            if time.time() - ult_series > 120:
                series = series_abiertas()
                ult_series = time.time()
                if primera:
                    log(f"{len(series)} series abiertas, {len({s['icao'] for s in series})} estaciones")

            # 1) aviationweather (la fuente oficial de resolucion)
            nuevos = []
            for i in range(0, len(ESTACIONES), 25):
                j = S.get(AWC, params={"ids": ",".join(ESTACIONES[i:i + 25]), "format": "json",
                                       "hours": 30 if primera else 2}, timeout=15).json()
                ahora = time.time()
                for x in j or []:
                    k = ("awc", x.get("icaoId"), x.get("obsTime"), x.get("rawOb"))
                    if k in visto:
                        continue
                    visto.add(k)
                    c = temp_metar(x)
                    if c is not None:
                        rutina.setdefault(x["icaoId"], {})[x["obsTime"]] = c
                    if primera:
                        continue
                    rec = x.get("receiptTime")
                    anotar("vivo_metar.csv", ["icao", "obs_utc", "fuente", "visto_utc", "receipt_utc", "tipo", "raw"],
                           [x["icaoId"], iso(x["obsTime"]), "awc", iso(ahora), rec or "", x.get("metarType"),
                            x.get("rawOb")])
                    if c is not None:
                        nuevos.append((x["icaoId"], x["obsTime"], c, rec, ahora))
            if primera:
                for s in series:   # lo que ya estaba muerto antes de arrancar no cuenta
                    for m, _ in cajas_muertas(s, rutina.get(s["icao"], {})):
                        muertas.add(m["conditionId"])
                primera = False
                log(f"arranque: {sum(len(v) for v in rutina.values())} reportes de rutina, {len(muertas)} cajas ya muertas")

            # 2) tgftp (archivo de ciclo de NOAA): solo para comparar que fuente publica primero
            if time.time() - ult_tg > CADA_TGFTP:
                ult_tg = time.time()
                h = datetime.now(timezone.utc).hour
                for hh in {h, (h - 1) % 24}:
                    url = TGFTP.format(hh)
                    r = S.get(url, timeout=15, headers={"If-Modified-Since": tg_mod[url]} if url in tg_mod else {})
                    if r.status_code != 200:
                        continue
                    tg_mod[url] = r.headers.get("Last-Modified", "")
                    ahora = time.time()
                    for linea in r.text.splitlines():
                        g = re.match(r"^(?:METAR |SPECI |COR )*([A-Z0-9]{4}) (\d{6})Z", linea.strip())
                        if not g or g.group(1) not in ESTACIONES:
                            continue
                        k = ("tgftp", g.group(1), g.group(2), linea.strip())
                        if k in visto:
                            continue
                        visto.add(k)
                        anotar("vivo_metar.csv", ["icao", "obs_utc", "fuente", "visto_utc", "receipt_utc", "tipo", "raw"],
                               [g.group(1), g.group(2), "tgftp", iso(ahora), "", "", linea.strip()])

            # 3) cajas que mato un reporte nuevo
            for icao, obs, c, rec, ahora in nuevos:
                for s in series:
                    if s["icao"] != icao or not (s["inicio"] <= obs < s["fin"]):
                        continue
                    for m, extremo in cajas_muertas(s, rutina.get(icao, {})):
                        cid = m["conditionId"]
                        if cid in muertas:
                            continue
                        muertas.add(cid)
                        token_si = json.loads(m["clobTokenIds"])[0]
                        anotar("vivo_muertes.csv",
                               ["condition_id", "icao", "ciudad", "tipo", "fecha", "caja", "extremo", "temp_c",
                                "obs_utc", "receipt_utc", "visto_utc", "seg_obs_a_visto", "bid_gamma_antes",
                                "ask_gamma_antes", "ultimo_gamma_antes"],
                               [cid, icao, s["ciudad"], s["tipo"], s["fecha"], m.get("groupItemTitle"), extremo, c,
                                iso(obs), rec or "", iso(ahora), round(ahora - obs), m.get("bestBid"), m.get("bestAsk"),
                                m.get("lastTradePrice")])
                        log(f"MUERTA {s['ciudad']} {s['tipo']} {m.get('groupItemTitle')} (extremo {extremo}), "
                            f"{ahora - obs:.0f} s despues de la obs, bid antes {m.get('bestBid')}")
                        for d in DEMORAS:
                            n_tarea += 1
                            heapq.heappush(agenda, (ahora + d, n_tarea, ("libro", cid, token_si, d, ahora)))
                        n_tarea += 1
                        heapq.heappush(agenda, (ahora + 900, n_tarea, ("trades", cid, obs, ahora)))

            # 4) tareas agendadas (libros a cada demora, operaciones a los 15 min)
            while agenda and agenda[0][0] <= time.time():
                _, _, tarea = heapq.heappop(agenda)
                try:
                    if tarea[0] == "libro":
                        _, cid, token, d, t0 = tarea
                        bids, asks = libro(token)
                        anotar("vivo_libros.csv",
                               ["condition_id", "demora_s", "seg_reales", "momento_utc", "mejor_bid", "tam_mejor_bid",
                                "mejor_ask", "acc_bid_1c", "usd_bid_1c", "acc_bid_2c", "usd_bid_2c", "acc_bid_5c",
                                "usd_bid_5c"],
                               [cid, d, round(time.time() - t0, 1), iso(time.time())] + resumen_libro(bids, asks))
                    else:
                        _, cid, obs, t0 = tarea
                        tr = S.get(TRADES, params={"market": cid, "limit": 1000, "takerOnly": "true"}, timeout=30).json()
                        for x in tr or []:
                            ts = int(x.get("timestamp") or 0)
                            if obs - 1800 <= ts <= t0 + 900:
                                anotar("vivo_trades.csv",
                                       ["condition_id", "timestamp", "outcome_index", "side", "price", "size", "wallet",
                                        "name"],
                                       [cid, ts, x.get("outcomeIndex"), x.get("side"), x.get("price"), x.get("size"),
                                        x.get("proxyWallet"), x.get("name") or x.get("pseudonym")])
                except Exception as ex:
                    log(f"error en tarea {tarea[0]}: {ex}")
        except Exception as ex:
            log(f"Error (sigue): {ex}")
        time.sleep(max(0.2, CADA_AWC - (time.time() - t_vuelta)))

    # que no queden libros sin anotar si cortamos con tareas pendientes
    log(f"fin; {len(agenda)} tareas sin hacer, {len(muertas)} cajas muertas vistas")


def cajas_muertas(s, obs):
    """Cajas de una serie que ya no pueden ganar con los reportes de rutina del dia local (margen 0)."""
    vals = [c for t, c in obs.items() if s["inicio"] <= t < s["fin"]]
    if not vals:
        return []
    out = []
    for m in s["markets"]:
        if m.get("closed"):
            continue
        try:
            lo, hi, en_f = leer_caja(m["groupItemTitle"])
        except Exception:
            continue
        r = [redondear(c, en_f) for c in vals]
        if s["tipo"] == "highest" and hi is not None and max(r) > hi:
            out.append((m, max(r)))
        elif s["tipo"] == "lowest" and lo is not None and min(r) < lo:
            out.append((m, min(r)))
    return out


if __name__ == "__main__":
    correr(float(sys.argv[1]) if len(sys.argv) > 1 else 330)

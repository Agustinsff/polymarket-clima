"""
PRONOSTICO vs MERCADO en TODAS las ciudades (en papel, no usa plata).

Dos veces por dia (lo llama el reloj a las 10:05 y 20:05 de Montevideo):
  1. Busca todos los mercados de temperatura (maxima y minima) del DIA SIGUIENTE
     de cada ciudad (dia local de esa ciudad).
  2. Baja el ensemble gratuito de Open-Meteo (GFS + ECMWF, ~80 escenarios)
     para la estacion oficial de cada mercado.
  3. Calcula la probabilidad de cada caja y la compara con el precio.
  4. Anota todo en pronostico.csv y, si la diferencia es grande, una operacion
     simulada en pronostico_ops.csv (dos versiones: "taker" = comprar ya pagando
     comision, y "maker" = dejar la orden en el libro y ver si alguien la toma).

Calibracion: cada serie (ciudad + maxima/minima) aprende su propio sesgo y error
con sus resultados reales (ver calibrar()). Mientras no tenga MIN_DIAS dias,
usa valores por defecto y sus operaciones se marcan como "sin calibrar".

Uso:
  python pronostico.py            -> foto de ahora
  python pronostico.py liquidar   -> completa resultados de dias terminados
  python pronostico.py resumen    -> como viene cada ciudad
"""

import csv
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from estaciones import TZ, EXCLUIR, leer_caja, centro_caja, fee

# ---- reglas fijadas ANTES de mirar resultados (no cambiarlas sobre la marcha) ----
UMBRAL = 0.10        # diferencia minima modelo - precio (puntos de probabilidad)
PRECIO_MIN = 0.03    # no comprar nada por debajo de 3 c ...
PRECIO_MAX = 0.90    # ... ni por encima de 90 c
ACCIONES = 10        # tamano de cada operacion simulada
MIN_DIAS = 7         # dias con resultado para considerar calibrada una serie
PRIOR_K = 5          # cuanto "pesa" el valor por defecto frente a los datos
# valores por defecto en °C: el maximo horario del modelo suele quedar corto
# frente al maximo de la estacion (y el minimo horario, un poco alto)
PRIOR = {"highest": {"sesgo": 0.5, "error": 1.6}, "lowest": {"sesgo": -0.3, "error": 1.6}}
MODELOS = "gfs025,ecmwf_ifs025"

CARPETA = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(CARPETA, n)
F_CSV, F_OPS, F_EST, F_STA = F("pronostico.csv"), F("pronostico_ops.csv"), F("pronostico_estado.json"), F("estaciones.json")
GAMMA = "https://gamma-api.polymarket.com/events"
ENS = "https://ensemble-api.open-meteo.com/v1/ensemble"
TRADES = "https://data-api.polymarket.com/trades"
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-pronostico/1.0 (investigacion personal)"

COLS = ["momento_utc", "serie", "fecha", "icao", "horas_hasta", "caja", "condition_id", "p_modelo", "bid", "ask",
        "media_cruda", "dispersion", "n_escenarios", "sesgo_usado", "error_usado", "calibrada"]
COLS_OPS = ["momento_utc", "serie", "fecha", "caja", "condition_id", "lado", "modo", "precio", "p_modelo", "calibrada",
            "acciones", "fin_utc"]


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def leer(nombre):
    if not os.path.exists(nombre):
        return []
    with open(nombre, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def agregar(nombre, cols, filas):
    nuevo = not os.path.exists(nombre)
    with open(nombre, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(cols)
        w.writerows(filas)


def cargar(nombre, defecto):
    try:
        with open(nombre, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defecto


def guardar(nombre, d):
    with open(nombre + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, indent=0, ensure_ascii=False)
    os.replace(nombre + ".tmp", nombre)


# ---------------------------------------------------------------------------

def eventos_abiertos():
    evs = []
    for off in range(0, 2000, 100):
        r = S.get(GAMMA, params={"tag_slug": "daily-temperature", "closed": "false", "limit": 100, "offset": off},
                  timeout=30).json()
        evs += r
        if len(r) < 100:
            break
    out = []
    for e in evs:
        m = re.match(r"^(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})$", e.get("slug", ""))
        st = re.search(r"site=([a-z0-9]{4})", e.get("resolutionSource") or "", re.I)
        if not m or not st or m.group(2) not in TZ:
            continue
        icao = st.group(1).upper()
        if icao in EXCLUIR:
            continue
        fecha = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%B %d %Y").date()
        out.append({"tipo": m.group(1), "ciudad": m.group(2), "icao": icao, "fecha": fecha, "slug": e["slug"],
                    "fin": e.get("endDate"), "markets": e.get("markets", [])})
    return out


def coordenadas(icaos):
    sta = cargar(F_STA, {})
    faltan = sorted(i for i in icaos if i not in sta)
    for i in range(0, len(faltan), 50):
        try:
            j = S.get("https://aviationweather.gov/api/data/stationinfo",
                      params={"ids": ",".join(faltan[i:i + 50]), "format": "json"}, timeout=30).json()
            for x in j:
                sta[x["icaoId"]] = {"lat": x["lat"], "lon": x["lon"], "elev": x.get("elev")}
        except Exception as e:
            log(f"stationinfo fallo: {e}")
    faltan = sorted(i for i in icaos if i not in sta)
    if faltan:   # plan B: el METAR tambien trae lat/lon
        try:
            j = S.get("https://aviationweather.gov/api/data/metar",
                      params={"ids": ",".join(faltan), "format": "json", "hours": 3}, timeout=30).json()
            for x in j:
                if x.get("lat") is not None:
                    sta[x["icaoId"]] = {"lat": x["lat"], "lon": x["lon"], "elev": x.get("elev")}
        except Exception as e:
            log(f"metar fallo: {e}")
    guardar(F_STA, sta)
    return sta


def escenarios(lat, lon, tz, fecha, tipo):
    """Maximo (o minimo) del dia local para cada escenario del ensemble, en °C."""
    r = S.get(ENS, params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m", "models": MODELOS,
                           "timezone": tz, "start_date": fecha.isoformat(), "end_date": fecha.isoformat()},
              timeout=40)
    r.raise_for_status()
    h = r.json()["hourly"]
    out = []
    for k, v in h.items():
        if not k.startswith("temperature_2m"):
            continue
        v = [x for x in v if x is not None]
        if len(v) >= 20:
            out.append(max(v) if tipo == "highest" else min(v))
    return out


def calibrar():
    """Sesgo y error de cada serie, con sus dias terminados (primera foto de cada dia)."""
    est = cargar(F_EST, {})
    gan = est.get("ganadoras", {})
    por_dia = {}
    for r in leer(F_CSV):
        clave = (r["serie"], r["fecha"])
        if clave not in por_dia or r["momento_utc"] < por_dia[clave]["momento_utc"]:
            por_dia[clave] = r
    errores = defaultdict(list)
    for (serie, fecha), r in por_dia.items():
        g = gan.get(f"{serie}|{fecha}")
        if not g or num(r["media_cruda"]) is None:
            continue
        c = centro_caja(g)
        if c is None:
            continue
        en_f = "°F" in g
        err = (c - num(r["media_cruda"])) / (1.8 if en_f else 1.0)   # siempre en °C
        errores[serie].append(err)
    calib = {}
    for serie, errs in errores.items():
        tipo = serie.split("|")[0]
        n = len(errs)
        pr = PRIOR[tipo]
        media = sum(errs) / n
        sesgo = (n * media + PRIOR_K * pr["sesgo"]) / (n + PRIOR_K)
        var = sum((e - sesgo) ** 2 for e in errs) / n if n else 0
        error = math.sqrt((n * var + PRIOR_K * pr["error"] ** 2) / (n + PRIOR_K))
        calib[serie] = {"n": n, "sesgo": round(sesgo, 2), "error": round(max(error, 0.6), 2)}
    return calib


def foto():
    evs = eventos_abiertos()
    ahora = datetime.now(timezone.utc)
    objetivo = []
    for e in evs:
        tz = ZoneInfo(TZ[e["ciudad"]])
        if e["fecha"] == (ahora.astimezone(tz) + timedelta(days=1)).date():
            objetivo.append(e)
    log(f"{len(evs)} eventos abiertos, {len(objetivo)} del dia siguiente")
    sta = coordenadas({e["icao"] for e in objetivo})
    calib = calibrar()
    filas, ops = [], []
    cache = {}
    for e in objetivo:
        serie = f"{e['tipo']}|{e['ciudad']}"
        if e["icao"] not in sta:
            continue
        tz = TZ[e["ciudad"]]
        clave = (e["icao"], e["fecha"], e["tipo"])
        try:
            if clave not in cache:
                cache[clave] = escenarios(sta[e["icao"]]["lat"], sta[e["icao"]]["lon"], tz, e["fecha"], e["tipo"])
                time.sleep(0.5)
            esc = cache[clave]
        except Exception as ex:
            log(f"open-meteo fallo {serie}: {ex}")
            continue
        if len(esc) < 10:
            continue
        cal = calib.get(serie)
        calibrada = bool(cal and cal["n"] >= MIN_DIAS)
        sesgo = cal["sesgo"] if cal else PRIOR[e["tipo"]]["sesgo"]
        error = cal["error"] if cal else PRIOR[e["tipo"]]["error"]
        media = sum(esc) / len(esc)
        disp = math.sqrt(sum((x - media) ** 2 for x in esc) / (len(esc) - 1))
        # incertidumbre extra de cada escenario: lo que falta para llegar al error tipico
        extra = math.sqrt(max(error ** 2 - disp ** 2, 0.5 ** 2))
        inicio = datetime(e["fecha"].year, e["fecha"].month, e["fecha"].day, tzinfo=ZoneInfo(tz))
        horas = round((inicio - ahora).total_seconds() / 3600, 1)
        for m in e["markets"]:
            if m.get("closed"):
                continue
            try:
                lo, hi, en_f = leer_caja(m["groupItemTitle"])
            except Exception:
                continue
            k = 1.8 if en_f else 1.0
            cv = (lambda c: c * 1.8 + 32) if en_f else (lambda c: c)
            bajo = -math.inf if lo is None else lo - 0.5
            alto = math.inf if hi is None else hi + 0.5
            p = 0.0
            for x in esc:
                c = cv(x + sesgo)
                s = extra * k
                p += (1.0 if alto == math.inf else ncdf((alto - c) / s)) - \
                     (0.0 if bajo == -math.inf else ncdf((bajo - c) / s))
            p /= len(esc)
            bid, ask = num(m.get("bestBid")), num(m.get("bestAsk"))
            filas.append([ahora.strftime("%Y-%m-%d %H:%M"), serie, e["fecha"].isoformat(), e["icao"], horas,
                          m["groupItemTitle"], m["conditionId"], round(p, 4), bid, ask, round(cv(media), 2),
                          round(disp * k, 2), len(esc), sesgo, error, int(calibrada)])
            fin = e["fin"] or ""
            # --- operaciones simuladas (reglas fijas) ---
            if ask and PRECIO_MIN <= ask <= PRECIO_MAX and p - ask >= UMBRAL:
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(), m["groupItemTitle"],
                            m["conditionId"], "Yes", "taker", ask, round(p, 4), int(calibrada), ACCIONES, fin])
            if bid and PRECIO_MIN <= 1 - bid <= PRECIO_MAX and bid - p >= UMBRAL:
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(), m["groupItemTitle"],
                            m["conditionId"], "No", "taker", round(1 - bid, 4), round(p, 4), int(calibrada), ACCIONES, fin])
            # maker: dejamos la orden donde esta el mejor precio del mismo lado y esperamos
            if bid and PRECIO_MIN <= bid <= PRECIO_MAX and p - bid >= UMBRAL:
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(), m["groupItemTitle"],
                            m["conditionId"], "Yes", "maker", bid, round(p, 4), int(calibrada), ACCIONES, fin])
            if ask and PRECIO_MIN <= 1 - ask <= PRECIO_MAX and ask - p >= UMBRAL:
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(), m["groupItemTitle"],
                            m["conditionId"], "No", "maker", round(1 - ask, 4), round(p, 4), int(calibrada), ACCIONES, fin])
            # colas baratas (lo que hacen las billeteras "cola barata" que ganan): solo si el modelo
            # le da al menos 2,5 veces el precio. El backtest del 20-oct mostro que comprar colas
            # baratas SIN elegir pierde 60-75%: lo que importa es elegir bien.
            if ask and 0.01 <= ask <= 0.10 and p >= 2.5 * ask and p - ask >= 0.04:
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(), m["groupItemTitle"],
                            m["conditionId"], "Yes", "cola_taker", ask, round(p, 4), int(calibrada), ACCIONES, fin])
            if bid and 0.01 <= bid <= 0.10 and p >= 2.5 * bid and p - bid >= 0.04:
                ops.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(), m["groupItemTitle"],
                            m["conditionId"], "Yes", "cola_maker", bid, round(p, 4), int(calibrada), ACCIONES, fin])
    agregar(F_CSV, COLS, filas)
    agregar(F_OPS, COLS_OPS, ops)
    log(f"{len(filas)} cajas anotadas, {len(ops)} operaciones simuladas")


# ---------------------------------------------------------------------------

def trades(cid):
    out = []
    for off in range(0, 3001, 500):
        r = S.get(TRADES, params={"market": cid, "limit": 500, "offset": off, "takerOnly": "true"}, timeout=30).json()
        for t in r:
            yes = t["outcomeIndex"] == 0
            py = t["price"] if yes else 1 - t["price"]
            compra_yes = (t["side"] == "BUY") == yes
            out.append((t["timestamp"], py, t["size"], compra_yes))
        if len(r) < 500:
            break
    return out


F_HOY, F_HOY_OPS = F("hoy.csv"), F("hoy_ops.csv")   # los escribe hoy.py (pronostico del mismo dia)


def liquidar():
    """Ganadora de cada dia terminado + si las ordenes 'maker' se habrian llenado
    (para pronostico.py y para hoy.py)."""
    est = cargar(F_EST, {})
    gan = est.setdefault("ganadoras", {})
    llen = est.setdefault("maker_llenado", {})
    pend = defaultdict(set)
    hoy = datetime.now(timezone.utc).date()
    for r in leer(F_CSV) + leer(F_HOY):
        clave = f"{r['serie']}|{r['fecha']}"
        if clave not in gan and r["fecha"] < (hoy - timedelta(days=1)).isoformat():
            tipo, ciudad = r["serie"].split("|")
            pend[clave] = (tipo, ciudad, r["fecha"])
    for clave, (tipo, ciudad, fecha) in list(pend.items())[:400]:
        d = datetime.fromisoformat(fecha)
        slug = f"{tipo}-temperature-in-{ciudad}-on-{d:%B}-{d.day}-{d.year}".lower()
        try:
            ev = S.get(GAMMA, params={"slug": slug}, timeout=30).json()
        except Exception:
            continue
        if not ev:
            continue
        for m in ev[0].get("markets", []):
            try:
                if m.get("closed") and json.loads(m.get("outcomePrices") or "[]")[0] in ("1", 1):
                    gan[clave] = m["groupItemTitle"]
                    est.setdefault("cid_ganadoras", {})[m["conditionId"]] = 1
            except Exception:
                pass
        if clave in gan:
            for m in ev[0].get("markets", []):
                est.setdefault("cid_ganadoras", {}).setdefault(m["conditionId"], 0)
        time.sleep(0.2)
    # ordenes maker: llenada si DESPUES de ponerla alguien opero a un precio peor que el nuestro
    # (estrictamente: si opero justo a nuestro precio, asumimos que habia otros antes en la fila)
    for o in leer(F_OPS) + leer(F_HOY_OPS):
        if not o["modo"].endswith("maker"):
            continue
        k = f"{o['condition_id']}|{o['momento_utc']}|{o['lado']}"
        if k in llen or o["condition_id"] not in est.get("cid_ganadoras", {}):
            continue
        t0 = datetime.strptime(o["momento_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
        precio = float(o["precio"])
        try:
            tr = trades(o["condition_id"])
        except Exception:
            continue
        q = 0.0
        for ts, py, size, compra_yes in tr:
            if ts <= t0:
                continue
            if o["lado"] == "Yes" and not compra_yes and py < precio - 1e-9:
                q += size
            if o["lado"] == "No" and compra_yes and py > 1 - precio + 1e-9:
                q += size
        llen[k] = round(min(q, float(o["acciones"])), 2)
        time.sleep(0.2)
    guardar(F_EST, est)
    log(f"ganadoras conocidas: {len(gan)}; ordenes maker revisadas: {len(llen)}")


def evaluar(f_csv=F_CSV, f_ops=F_OPS):
    """Devuelve (por_serie, operaciones) para el resumen."""
    est = cargar(F_EST, {})
    gan_cid = est.get("cid_ganadoras", {})
    llen = est.get("maker_llenado", {})
    # Brier modelo vs mercado: primera foto de cada dia y serie
    primera = {}
    filas = leer(f_csv)
    for r in filas:
        k = (r["serie"], r["fecha"])
        primera.setdefault(k, r["momento_utc"])
        primera[k] = min(primera[k], r["momento_utc"])
    br = defaultdict(lambda: {"n": 0, "dias": set(), "modelo": 0.0, "mercado": 0.0})
    for r in filas:
        if r["momento_utc"] != primera[(r["serie"], r["fecha"])] or r["condition_id"] not in gan_cid:
            continue
        bid, ask, p = num(r["bid"]), num(r["ask"]), num(r["p_modelo"])
        if bid is None or ask is None or ask - bid > 0.2:
            continue
        y = gan_cid[r["condition_id"]]
        b = br[r["serie"]]
        b["n"] += 1
        b["dias"].add(r["fecha"])
        b["modelo"] += (p - y) ** 2
        b["mercado"] += ((bid + ask) / 2 - y) ** 2
    ops = []
    for o in leer(f_ops):
        if o["condition_id"] not in gan_cid:
            ops.append((o, None, None))
            continue
        y = gan_cid[o["condition_id"]]
        gana = (y == 1) == (o["lado"] == "Yes")
        p = float(o["precio"])
        if o["modo"].endswith("taker") or o["modo"] == "no80_90":
            q = float(o["acciones"])
            res = q * ((1 - p) if gana else -p) - q * fee(p)
        else:
            q = llen.get(f"{o['condition_id']}|{o['momento_utc']}|{o['lado']}")
            if q is None:
                ops.append((o, None, None))
                continue
            res = q * ((1 - p) if gana else -p)     # maker: sin comision
        ops.append((o, res, q))
    return br, ops


def resumen():
    br, ops = evaluar()
    print("Brier por serie (mas bajo = mejor). Primera foto del dia anterior.")
    for s, b in sorted(br.items()):
        print(f"  {s:32s} dias {len(b['dias']):3d}  modelo {b['modelo'] / b['n']:.4f}  mercado {b['mercado'] / b['n']:.4f}")
    for modo in ("taker", "maker", "cola_taker", "cola_maker"):
        for cal in ("0", "1"):
            xs = [r for o, r, q in ops if o["modo"] == modo and o["calibrada"] == cal and r is not None]
            print(f"{modo} calibrada={cal}: {len(xs)} liquidadas, neto {sum(xs):+.2f}")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "foto"
    {"foto": foto, "liquidar": liquidar, "resumen": resumen}[a]()

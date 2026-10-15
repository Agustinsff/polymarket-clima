"""
COSECHADOR EN PAPEL, multi-ciudad (NO usa plata, NO pone ordenes).

Idea: cuando la estacion oficial ya marco una temperatura que hace IMPOSIBLE
una caja (p.ej. la maxima ya llego a 22 y la caja "19°C" no puede ganar), a veces
quedan ordenes viejas de gente que todavia paga por el "Yes" de esa caja.
Venderles ese "Yes" (= comprar el "No") es casi ganancia segura.

Los bots rapidos se llevan casi todo en los primeros minutos. Este bot es
LENTO a proposito (usa NOAA, ~4 min de demora) y busca las oportunidades que
quedan despues, en todas las ciudades.

Reglas de seguridad (fijadas antes de empezar):
  - MARGEN: la caja tiene que estar superada por al menos 1 grado de mas
    (p.ej. maxima 22 -> se consideran muertas las cajas de 20 o menos, no la de 21).
  - Se excluyen estaciones donde vimos que el METAR no coincidio con la
    resolucion oficial (Paris LFPB, Lucknow VILK).
  - Solo "vende" si alguien paga al menos PRECIO_MIN por el Yes, y como maximo
    ACC_MAX acciones por caja.

Archivos: cosecha.csv (operaciones simuladas), cosecha_estado.json (estado).
Uso:
  python cosechador.py 340      -> corre 340 minutos
  python cosechador.py resumen
"""

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

MARGEN = 1
PRECIO_MIN = 0.03
ACC_MAX = 100
EXCLUIR = {"LFPB", "VILK"}
ESPERA = 60

TZ = {"london": "Europe/London", "paris": "Europe/Paris", "ankara": "Europe/Istanbul", "munich": "Europe/Berlin",
      "shanghai": "Asia/Shanghai", "milan": "Europe/Rome", "madrid": "Europe/Madrid", "warsaw": "Europe/Warsaw",
      "chongqing": "Asia/Shanghai", "wuhan": "Asia/Shanghai", "shenzhen": "Asia/Shanghai", "amsterdam": "Europe/Amsterdam",
      "helsinki": "Europe/Helsinki", "jeddah": "Asia/Riyadh", "lucknow": "Asia/Kolkata", "singapore": "Asia/Singapore",
      "kuala-lumpur": "Asia/Kuala_Lumpur", "cape-town": "Africa/Johannesburg", "karachi": "Asia/Karachi",
      "manila": "Asia/Manila", "nyc": "America/New_York", "dallas": "America/Chicago", "atlanta": "America/New_York",
      "miami": "America/New_York", "chicago": "America/Chicago", "austin": "America/Chicago", "denver": "America/Denver",
      "houston": "America/Chicago", "seattle": "America/Los_Angeles", "los-angeles": "America/Los_Angeles",
      "san-francisco": "America/Los_Angeles", "sao-paulo": "America/Sao_Paulo",
      "buenos-aires": "America/Argentina/Buenos_Aires", "toronto": "America/Toronto", "mexico-city": "America/Mexico_City",
      "panama-city": "America/Panama", "seoul": "Asia/Seoul", "wellington": "Pacific/Auckland", "tokyo": "Asia/Tokyo",
      "beijing": "Asia/Shanghai", "chengdu": "Asia/Shanghai", "busan": "Asia/Seoul", "guangzhou": "Asia/Shanghai",
      "qingdao": "Asia/Shanghai"}

CARPETA = os.path.dirname(os.path.abspath(__file__))
F_CSV = os.path.join(CARPETA, "cosecha.csv")
F_EST = os.path.join(CARPETA, "cosecha_estado.json")
GAMMA = "https://gamma-api.polymarket.com/events"
BOOK = "https://clob.polymarket.com/book"
AWC = "https://aviationweather.gov/api/data/metar"
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-cosechador/1.0 (investigacion personal)"


def log(m):
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}Z {m}", flush=True)


def fee(p):
    return 0.05 * p * (1 - p)


def leer_caja(t):
    f = "°F" in t
    t = re.sub(r"°[CF]", "", t).strip().lower()
    if "or below" in t:
        return None, int(t.replace("or below", "")), f
    if "or higher" in t or "or above" in t:
        return int(re.sub(r"or (higher|above)", "", t)), None, f
    m = re.match(r"^(-?\d+)-(-?\d+)$", t)
    if m:
        return int(m.group(1)), int(m.group(2)), f
    return int(t), int(t), f


def cargar():
    if os.path.exists(F_EST):
        with open(F_EST, encoding="utf-8") as f:
            return json.load(f)
    return {"llenado": {}, "liquidadas": {}}


def guardar(e):
    with open(F_EST + ".tmp", "w", encoding="utf-8") as f:
        json.dump(e, f)
    os.replace(F_EST + ".tmp", F_EST)


def anotar(fila):
    nuevo = not os.path.exists(F_CSV)
    with open(F_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(["momento_utc", "serie", "fecha_local", "caja", "estacion", "extremo_actual", "precio_yes",
                        "acciones", "ganancia_si_sale_bien", "seg_desde_obs", "seg_desde_publicacion_noaa", "condition_id"])
        w.writerow(fila)


# ---------------------------------------------------------------------------
# MERCADOS DEL DIA
# ---------------------------------------------------------------------------

def series_de_hoy():
    evs = []
    for off in range(0, 1200, 100):
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
        st = re.search(r"site=([a-z0-9]{4})", e.get("resolutionSource") or "", re.I)
        if not m or not st or m.group(2) not in TZ:
            continue
        icao = st.group(1).upper()
        if icao in EXCLUIR:
            continue
        tz = ZoneInfo(TZ[m.group(2)])
        hoy_local = datetime.now(tz).date()
        fecha = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%B %d %Y").date()
        if fecha != hoy_local:
            continue
        inicio = datetime(fecha.year, fecha.month, fecha.day, tzinfo=tz).astimezone(timezone.utc)
        out.append({"tipo": m.group(1), "ciudad": m.group(2), "icao": icao, "fecha": fecha.isoformat(),
                    "inicio": inicio.timestamp(), "slug": e["slug"], "markets": e.get("markets", [])})
    return out


def metars(icaos, horas):
    datos = {}
    lista = sorted(icaos)
    for i in range(0, len(lista), 40):
        j = S.get(AWC, params={"ids": ",".join(lista[i:i + 40]), "format": "json", "hours": horas}, timeout=30).json()
        for x in j:
            if x.get("temp") is None:
                continue
            rec = datetime.fromisoformat(x["receiptTime"].replace("Z", "+00:00")).timestamp() if x.get("receiptTime") else None
            datos.setdefault(x["icaoId"], {})[x["obsTime"]] = (float(x["temp"]), rec)
    return datos


# ---------------------------------------------------------------------------
# BUCLE
# ---------------------------------------------------------------------------

def correr(minutos):
    est = cargar()
    fin = time.time() + minutos * 60
    obs = {}
    series = []
    ult_series = 0
    ult_liq = 0
    primera = True
    while time.time() < fin:
        try:
            if time.time() - ult_series > 120:   # precios de gamma frescos cada 2 min
                series = series_de_hoy()
                ult_series = time.time()
                if primera:
                    log(f"Series de hoy: {len(series)} ({len({s['icao'] for s in series})} estaciones)")
            nuevos = metars({s["icao"] for s in series}, 26 if primera else 2)
            primera = False
            for k, v in nuevos.items():
                obs.setdefault(k, {}).update(v)
            ahora = time.time()
            diag = {"momento_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "series": len(series),
                    "estaciones_con_datos": sum(1 for k in {x["icao"] for x in series} if obs.get(k)),
                    "cajas_muertas": 0, "muertas_con_comprador": 0}
            for s in series:
                o = [(t, c, rec) for t, (c, rec) in obs.get(s["icao"], {}).items() if t >= s["inicio"]]
                if not o:
                    continue
                for m in s["markets"]:
                    if m.get("closed"):
                        continue
                    try:
                        lo, hi, en_f = leer_caja(m["groupItemTitle"])
                    except Exception:
                        continue
                    vals = [round(c * 9 / 5 + 32) if en_f else round(c) for _, c, _ in o]
                    if s["tipo"] == "highest":
                        extremo = max(vals)
                        muerta = hi is not None and extremo >= hi + 1 + MARGEN
                        t_ref = min(t for (t, c, r), v in zip(o, vals) if v >= hi + 1 + MARGEN) if muerta else None
                    else:
                        extremo = min(vals)
                        muerta = lo is not None and extremo <= lo - 1 - MARGEN
                        t_ref = min(t for (t, c, r), v in zip(o, vals) if v <= lo - 1 - MARGEN) if muerta else None
                    if not muerta:
                        continue
                    diag["cajas_muertas"] += 1
                    if float(m.get("bestBid") or 0) >= PRECIO_MIN:
                        diag["muertas_con_comprador"] += 1
                    cid = m["conditionId"]
                    ya = est["llenado"].get(cid, 0)
                    if ya >= ACC_MAX or float(m.get("bestBid") or 0) < PRECIO_MIN:
                        continue   # solo miramos el libro si alguien paga algo por el Yes
                    token = json.loads(m["clobTokenIds"])[0]
                    b = S.get(BOOK, params={"token_id": token}, timeout=20).json()
                    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
                    for p, tam in bids:
                        if p < PRECIO_MIN or ya >= ACC_MAX:
                            break
                        q = min(tam, ACC_MAX - ya)
                        ya += q
                        rec = obs[s["icao"]][t_ref][1]
                        anotar([datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                f"{s['tipo']}|{s['ciudad']}", s["fecha"], m["groupItemTitle"], s["icao"], extremo,
                                p, round(q, 2), round(q * (p - fee(p)), 3), round(ahora - t_ref),
                                round(ahora - rec) if rec else "", cid])
                        log(f"COSECHA {s['ciudad']} {s['tipo']} {m['groupItemTitle']} (extremo {extremo}): "
                            f"{q:.0f} acc a {p:.3f} -> +${q * (p - fee(p)):.2f} si sale bien")
                    est["llenado"][cid] = ya
            est["diagnostico"] = diag
            est.setdefault("max_muertas_con_comprador", 0)
            est["max_muertas_con_comprador"] = max(est["max_muertas_con_comprador"], diag["muertas_con_comprador"])
            if time.time() - ult_liq > 1800:
                liquidar(est)
                ult_liq = time.time()
            guardar(est)
        except Exception as e:
            log(f"Error (sigue): {e}")
        time.sleep(ESPERA)
    liquidar(est)
    guardar(est)


def liquidar(est):
    if not os.path.exists(F_CSV):
        return
    with open(F_CSV, encoding="utf-8") as f:
        cids = {r["condition_id"]: r["serie"] for r in csv.DictReader(f, delimiter=";")}
    for cid in cids:
        if cid in est["liquidadas"]:
            continue
        try:
            r = S.get(f"https://clob.polymarket.com/markets/{cid}", timeout=20).json()
        except Exception:
            continue
        if r.get("closed"):
            for t in r.get("tokens", []):
                if t.get("outcome") == "Yes" and t.get("winner") is not None:
                    est["liquidadas"][cid] = 1 if t["winner"] else 0  # 1 = la caja GANO (malo para nosotros)


def resumen():
    est = cargar()
    if not os.path.exists(F_CSV):
        print("Todavia no hay cosechas. Ultimo ciclo:", est.get("diagnostico"))
        return
    with open(F_CSV, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    ganado = perdido = pendiente = 0.0
    n_ok = n_mal = n_pend = 0
    por_serie = {}
    for r in filas:
        p, q = float(r["precio_yes"]), float(r["acciones"])
        res = est["liquidadas"].get(r["condition_id"])
        if res is None:
            pendiente += q * (p - fee(p))
            n_pend += 1
            continue
        g = q * (p - fee(p)) if res == 0 else -q * (1 - p) - q * fee(p)
        por_serie[r["serie"]] = por_serie.get(r["serie"], 0) + g
        if g >= 0:
            ganado += g
            n_ok += 1
        else:
            perdido += g
            n_mal += 1
    print(f"\nUltimo ciclo: {est.get('diagnostico')}")
    print(f"\n=== Cosechador en papel: {len(filas)} operaciones ===")
    print(f"Liquidadas: {n_ok} bien (+${ganado:.2f}), {n_mal} mal (${perdido:.2f}) | pendientes: {n_pend} (+${pendiente:.2f} si salen bien)")
    print(f"Resultado neto liquidado: ${ganado + perdido:+.2f}")
    for k, v in sorted(por_serie.items(), key=lambda x: -x[1])[:15]:
        print(f"  {k:<28}{v:+8.2f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "resumen":
        resumen()
    else:
        correr(float(sys.argv[1]) if len(sys.argv) > 1 else 340)

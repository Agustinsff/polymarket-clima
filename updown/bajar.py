"""Paso 1: bajar los mercados "Up or Down" cerrados y el precio historico del Up dentro de cada ventana.
Regla en updown/REGLA.md. Solo lee (gamma + clob prices-history). Guarda updown/datos/<serie>.json.gz
(incremental: lo ya bajado no se vuelve a pedir). Corre en Actions (el contenedor no llega a Polymarket)."""
import gzip, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import threading
import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(CARPETA, "datos")
os.makedirs(DATOS, exist_ok=True)
G, HIST = "https://gamma-api.polymarket.com/events", "https://clob.polymarket.com/prices-history"
DIAS = int(os.environ.get("DIAS", 60))
LIMITE_MIN = int(os.environ.get("LIMITE_MIN", 200))
T0 = time.time()
# serie -> (activo, ventana en segundos, dias hacia atras, fidelidad de prices-history en minutos)
SERIES = {
    "btc-up-or-down-hourly": ("BTC", 3600, DIAS, 1), "eth-up-or-down-hourly": ("ETH", 3600, DIAS, 1),
    "btc-up-or-down-4h": ("BTC", 14400, DIAS, 1), "eth-up-or-down-4h": ("ETH", 14400, DIAS, 1),
    "btc-up-or-down-daily": ("BTC", 86400, DIAS, 5), "eth-up-or-down-daily": ("ETH", 86400, DIAS, 5),
    "btc-up-or-down-15m": ("BTC", 900, 3, 1),       # solo muestra (REGLA.md)
}
_l = threading.local()


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def ses():
    if not hasattr(_l, "s"):
        _l.s = requests.Session()
        _l.s.headers["User-Agent"] = "polymarket-clima-updown/0.1 (investigacion personal)"
    return _l.s


def get(url, params):
    for i in range(4):
        try:
            r = ses().get(url, params=params, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(8 * (i + 1)); continue
            return None
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def eventos(serie, dias):
    """Eventos cerrados de la serie con fin dentro de los ultimos `dias`."""
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    out, off = [], 0
    while True:
        j = get(G, {"series_slug": serie, "closed": "true", "limit": 100, "offset": off, "order": "endDate", "ascending": "false"})
        if not j:
            break
        for e in j:
            fin = datetime.fromisoformat(e["endDate"].replace("Z", "+00:00"))
            if fin < desde:
                return out
            out.append(e)
        if len(j) < 100:
            break
        off += 100
    return out


def historia(token, t0, t1, fid):
    j = get(HIST, {"market": token, "startTs": t0, "endTs": t1, "fidelity": fid})
    return [[x["t"], x["p"]] for x in (j or {}).get("history", [])]


def bajar_serie(serie, activo, ventana, dias, fid):
    ruta = os.path.join(DATOS, serie + ".json.gz")
    hecho = {}
    if os.path.exists(ruta):
        with gzip.open(ruta, "rt", encoding="utf-8") as f:
            hecho = json.load(f)
    evs = eventos(serie, dias)
    log(f"{serie}: {len(evs)} eventos cerrados, {len(hecho)} ya bajados")
    pend = [e for e in evs if e["slug"] not in hecho]

    def uno(e):
        m = (e.get("markets") or [None])[0]
        if not m:
            return e["slug"], None
        try:
            toks = json.loads(m["clobTokenIds"]); pr = json.loads(m.get("outcomePrices") or "[]")
            outs = json.loads(m.get("outcomes") or '["Up","Down"]')
        except Exception:
            return e["slug"], None
        fin = int(datetime.fromisoformat(e["endDate"].replace("Z", "+00:00")).timestamp())
        ini = fin - ventana
        i_up = outs.index("Up") if "Up" in outs else 0
        gano = None
        if pr and len(pr) == 2:
            pu = float(pr[i_up]); gano = 1 if pu >= 0.99 else 0 if pu <= 0.01 else 0.5
        h = historia(toks[i_up], ini - ventana // 10, fin + 120, fid)
        fs = m.get("feeSchedule") or {}
        return e["slug"], {"activo": activo, "ventana": ventana, "ini": ini, "fin": fin, "gano_up": gano, "cid": m["conditionId"],
                           "tasa": (fs.get("rate") if m.get("feesEnabled") is not False else 0.0),
                           "fuente": (m.get("resolutionSource") or "")[:80], "volumen": m.get("volumeNum"), "h": h}

    n = 0
    with ThreadPoolExecutor(6) as ex:
        for slug, d in ex.map(uno, pend):
            if d is not None:
                hecho[slug] = d; n += 1
            if n % 200 == 0 and n:
                with gzip.open(ruta, "wt", encoding="utf-8") as f:
                    json.dump(hecho, f, separators=(",", ":"))
            if time.time() - T0 > LIMITE_MIN * 60:
                log("limite de tiempo; se sigue en la proxima corrida"); break
    with gzip.open(ruta, "wt", encoding="utf-8") as f:
        json.dump(hecho, f, separators=(",", ":"))
    log(f"{serie}: {n} nuevos, total {len(hecho)}")


if __name__ == "__main__":
    for serie, (activo, ventana, dias, fid) in SERIES.items():
        if time.time() - T0 > LIMITE_MIN * 60:
            break
        bajar_serie(serie, activo, ventana, dias, fid)

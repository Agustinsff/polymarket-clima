"""
CRIPTO EN PAPEL: mercados diarios de Bitcoin y Ethereum en Polymarket.
(NO usa plata, NO pone ordenes.)

Tres tipos (todos con el precio de Binance):
  above : "Bitcoin above ___ on <fecha>?"   precio a las 12:00 ET por encima del strike
  rango : "Bitcoin price on <fecha>?"         precio a las 12:00 ET dentro de un rango
  toca  : "What price will Bitcoin hit on <fecha>?"  el precio toca el valor en algun
          momento del dia (de 00:00 a 24:00 ET)

Cada mercado paga 1 si el precio de BTC/USDT (o ETH/USDT) en Binance, en la vela de
1 minuto que cierra a las 12:00 hora de Nueva York, termina por encima del strike.
Es una "opcion digital", y las opciones tienen un precio teorico conocido:

    P(arriba) = Phi( ln(S/K) / (sigma*raiz(t)) - sigma*raiz(t)/2 )

  S = precio actual (Binance), K = strike, t = tiempo que falta (en anios),
  sigma = volatilidad implicita del mercado de opciones (indice DVOL de Deribit).

Para "toca" se usa la formula de la barrera: P(tocar) = 2 * (1 - Phi(|ln(H/S)| / (sigma*raiz(t)))).

Backtest (20-oct-2026, may-oct, 283 dias, 2121 operaciones de los tres tipos): comprar
el lado que el modelo ve al menos 5 puntos mas barato dio +6,7 % con 1 c de
deslizamiento (P de que sea suerte ~4 %). Ethereum +17 % (P ~0,6 %), Bitcoin ~0 %.
Por eso se prueba en papel, con las reglas fijas de abajo.

REGLAS FIJAS (decididas antes de empezar, no cambiarlas):
  - Se mira cada mercado cuando le faltan 48, 24, 12, 6, 3 y 1 h (+-30 min);
    los de "toca" a 18, 12, 6, 3 y 1 h.
  - Precio REAL del libro (mejor ask para comprar Yes, mejor bid -> No a 1-bid).
  - Operar si modelo - precio >= 5 puntos; precio entre 3 y 97 c; 10 acciones.
  - Una sola operacion por mercado y horizonte.

Archivos: cripto.csv (fotos), cripto_ops.csv (operaciones), cripto_estado.json.
Uso: python cripto.py          (foto; la corre el reloj cada 15 min)
     python cripto.py liquidar
     python cripto.py resumen
"""

import csv
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

HORIZONTES = {"above": [48, 24, 12, 6, 3, 1], "rango": [48, 24, 12, 6, 3, 1], "toca": [18, 12, 6, 3, 1]}
TOLERANCIA_H = 0.5
BORDE = 0.05
PRECIO_MIN, PRECIO_MAX = 0.03, 0.97
ACCIONES = 10
SERIES = [("BTC", "above", "btc-multi-strikes-weekly"), ("ETH", "above", "ethereum-multi-strikes-weekly"),
          ("BTC", "rango", "bitcoin-neg-risk-weekly"), ("ETH", "rango", "ethereum-neg-risk-weekly"),
          ("BTC", "toca", "bitcoin-hit-price-daily"), ("ETH", "toca", "ethereum-hit-price-daily")]

CARPETA = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(CARPETA, n)
F_CSV, F_OPS, F_EST = F("cripto.csv"), F("cripto_ops.csv"), F("cripto_estado.json")
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-cripto/1.0 (investigacion personal)"

COLS = ["momento_utc", "activo", "tipo", "evento", "horizonte", "horas", "strike", "condition_id", "spot", "dvol",
        "p_modelo", "bid", "ask", "ask_tam", "bid_tam"]
COLS_OPS = ["momento_utc", "activo", "tipo", "evento", "horizonte", "strike", "condition_id", "lado", "precio",
            "p_modelo", "acciones"]


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee(p):
    return 0.05 * p * (1 - p)


def leer(n):
    if not os.path.exists(n):
        return []
    with open(n, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def agregar(n, cols, filas):
    if not filas:
        return
    nuevo = not os.path.exists(n)
    with open(n, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(cols)
        w.writerows(filas)


def cargar():
    try:
        with open(F_EST, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar(e):
    with open(F_EST + ".tmp", "w", encoding="utf-8") as f:
        json.dump(e, f, indent=0)
    os.replace(F_EST + ".tmp", F_EST)


def spot(activo):
    r = S.get("https://data-api.binance.vision/api/v3/ticker/price", params={"symbol": f"{activo}USDT"}, timeout=20)
    return float(r.json()["price"])


def dvol(activo):
    fin = int(time.time() * 1000)
    r = S.get("https://www.deribit.com/api/v2/public/get_volatility_index_data",
              params={"currency": activo, "resolution": 3600, "start_timestamp": fin - 4 * 3600 * 1000,
                      "end_timestamp": fin}, timeout=20).json()
    datos = r["result"]["data"]
    return float(datos[-1][4])


def extremos_desde(activo, desde_ts):
    """Maximo y minimo (velas de 1 min, high/low) desde el inicio de la ventana de 'toca'."""
    hi, lo = -1e18, 1e18
    st = int(desde_ts * 1000)
    for _ in range(3):
        r = S.get("https://data-api.binance.vision/api/v3/klines",
                  params={"symbol": f"{activo}USDT", "interval": "1m", "startTime": st, "limit": 1000}, timeout=20).json()
        if not r:
            break
        for x in r:
            hi, lo = max(hi, float(x[2])), min(lo, float(x[3]))
        st = r[-1][0] + 60000
        if len(r) < 1000:
            break
    return hi, lo


def num(t):
    return float(re.sub(r"[^0-9.]", "", t))


def prob(tipo, titulo, s, sq, ext):
    """Probabilidad del 'Yes' segun el modelo. sq = sigma * raiz(t)."""
    d = lambda k: phi(math.log(s / k) / sq - sq / 2)   # P(precio final > k)
    t = titulo.strip()
    if tipo == "above":
        return d(num(t))
    if tipo == "rango":
        if t.startswith("<"):
            return 1 - d(num(t))
        if t.startswith(">") or t.endswith("+"):
            return d(num(t))
        a, b = t.split("-")
        return d(num(a)) - d(num(b))
    # toca
    h = num(t)
    sube = "↑" in t or h > s
    hi, lo = ext
    if (sube and hi >= h) or (not sube and lo <= h):
        return None      # ya toco: el mercado esta decidido, no se opera
    return min(1.0, 2 * (1 - phi(abs(math.log(h / s)) / sq)))


def libro(token):
    b = S.get("https://clob.polymarket.com/book", params={"token_id": token}, timeout=20).json()
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
    return (bids[0] if bids else (None, None)), (asks[0] if asks else (None, None))


def foto():
    est = cargar()
    hechos = est.setdefault("hechos", {})
    ahora = datetime.now(timezone.utc)
    filas, ops = [], []
    cache = {}
    for activo, tipo, serie in SERIES:
        try:
            evs = S.get("https://gamma-api.polymarket.com/events",
                        params={"series_slug": serie, "closed": "false", "limit": 50}, timeout=30).json()
        except Exception as ex:
            log(f"gamma fallo {serie}: {ex}")
            continue
        tocan = []
        for e in evs:
            if not e.get("endDate"):
                continue
            fin = datetime.fromisoformat(e["endDate"].replace("Z", "+00:00"))
            horas = (fin - ahora).total_seconds() / 3600
            for h in HORIZONTES[tipo]:
                if abs(horas - h) <= TOLERANCIA_H and f"{e['slug']}|{h}" not in hechos:
                    tocan.append((e, h, horas))
        if not tocan:
            continue
        if activo not in cache:
            cache[activo] = (spot(activo), dvol(activo))
        s, v = cache[activo]
        sig = v / 100
        for e, h, horas in tocan:
            hechos[f"{e['slug']}|{h}"] = ahora.strftime("%Y-%m-%d %H:%M")
            sq = sig * math.sqrt(horas / 8760)
            ext = (None, None)
            if tipo == "toca":
                inicio = datetime.fromisoformat(e["startDate"].replace("Z", "+00:00")).timestamp()
                ext = extremos_desde(activo, inicio)
            for m in e.get("markets", []):
                if m.get("closed"):
                    continue
                try:
                    tok_yes = json.loads(m["clobTokenIds"])[0]
                    p = prob(tipo, m["groupItemTitle"], s, sq, ext)
                except Exception:
                    continue
                if p is None:
                    continue
                try:
                    (bid, bid_t), (ask, ask_t) = libro(tok_yes)
                except Exception:
                    continue
                filas.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), activo, tipo, e["slug"], h, round(horas, 2),
                              m["groupItemTitle"], m["conditionId"], s, v, round(p, 4), bid, ask, ask_t, bid_t])
                base = [ahora.strftime("%Y-%m-%d %H:%M:%S"), activo, tipo, e["slug"], h, m["groupItemTitle"],
                        m["conditionId"]]
                if ask is not None and PRECIO_MIN <= ask <= PRECIO_MAX and p - ask >= BORDE:
                    ops.append(base + ["Yes", ask, round(p, 4), ACCIONES])
                elif bid is not None and PRECIO_MIN <= 1 - bid <= PRECIO_MAX and bid - p >= BORDE:
                    ops.append(base + ["No", round(1 - bid, 4), round(p, 4), ACCIONES])
                time.sleep(0.1)
    # limpiar marcas de mas de 4 dias
    est["hechos"] = {k: t for k, t in hechos.items() if t >= datetime.fromtimestamp(time.time() - 4 * 86400,
                                                                                         timezone.utc).strftime("%Y-%m-%d")}
    guardar(est)
    agregar(F_CSV, COLS, filas)
    agregar(F_OPS, COLS_OPS, ops)
    log(f"cripto: {len(filas)} strikes mirados, {len(ops)} operaciones simuladas")


def liquidar():
    est = cargar()
    gan = est.setdefault("ganadoras", {})
    cids = {r["condition_id"] for r in leer(F_CSV)} - set(gan)
    for cid in list(cids)[:300]:
        try:
            r = S.get(f"https://clob.polymarket.com/markets/{cid}", timeout=20).json()
        except Exception:
            continue
        if r.get("closed"):
            for t in r.get("tokens", []):
                if t.get("outcome") == "Yes" and t.get("winner") is not None:
                    gan[cid] = 1 if t["winner"] else 0
        time.sleep(0.1)
    guardar(est)


def evaluar():
    gan = cargar().get("ganadoras", {})
    ops, brier = [], {"n": 0, "modelo": 0.0, "mercado": 0.0}
    for r in leer(F_CSV):
        y = gan.get(r["condition_id"])
        try:
            bid, ask, p = float(r["bid"]), float(r["ask"]), float(r["p_modelo"])
        except (TypeError, ValueError):
            continue
        if y is None or ask - bid > 0.10 or not 0.03 <= (bid + ask) / 2 <= 0.97:
            continue
        brier["n"] += 1
        brier["modelo"] += (p - y) ** 2
        brier["mercado"] += ((bid + ask) / 2 - y) ** 2
    for o in leer(F_OPS):
        y = gan.get(o["condition_id"])
        if y is None:
            ops.append((o, None))
            continue
        p, q = float(o["precio"]), float(o["acciones"])
        gana = (y == 1) == (o["lado"] == "Yes")
        ops.append((o, q * ((1 - p) if gana else -p) - q * fee(p)))
    return brier, ops


def resumen():
    b, ops = evaluar()
    liq = [r for o, r in ops if r is not None]
    costo = sum(float(o["precio"]) * float(o["acciones"]) for o, r in ops if r is not None)
    print(f"Operaciones: {len(ops)} ({len(liq)} liquidadas). Neto US${sum(liq):+.2f} sobre US${costo:.2f} invertidos.")
    for clave in sorted({(o["activo"], o["tipo"]) for o, r in ops}):
        xs = [r for o, r in ops if (o["activo"], o["tipo"]) == clave and r is not None]
        print(f"  {clave[0]} {clave[1]}: {len(xs)} liquidadas, neto {sum(xs):+.2f}")
    if b["n"]:
        print(f"Brier en {b['n']} strikes: modelo {b['modelo'] / b['n']:.4f} vs mercado {b['mercado'] / b['n']:.4f}")


if __name__ == "__main__":
    {"foto": foto, "liquidar": liquidar, "resumen": resumen}[sys.argv[1] if len(sys.argv) > 1 else "foto"]()

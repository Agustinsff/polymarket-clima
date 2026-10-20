"""
SOMBRA MAKER (en papel): que hubiera pasado si, en vez de comprar al toque
(pagando comision), dejabamos la orden en el libro y esperabamos a que alguien
la tome.

  1. Cosechador: cada caja que detecta "muerta" (cosecha_muertas.csv) recibe
     ordenes de venta del Yes a 2, 3 y 5 centavos (= comprar el No a 98/97/95)
     hasta 100 acciones. Se llena si DESPUES alguien compro el Yes a un precio
     MAYOR que el nuestro (si compro justo a nuestro precio, suponemos que habia
     otros antes en la fila: es la cuenta prudente).
  2. Prueba SP 14 hs: para cada operacion de la regla fija, la misma operacion
     pero esperando en el mejor precio del mismo lado (bid) en vez de pagar el ask.
     La regla fija NO se toca; esto es solo una comparacion.

Los makers no pagan comision. Resultado en sombra_maker.json.
Uso: python sombra_maker.py   (lo corre el reloj dos veces por dia)
"""

import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

PRECIOS = [0.02, 0.03, 0.05]
ACC = 100
CARPETA = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(CARPETA, n)
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-sombra/1.0 (investigacion personal)"


def num(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def leer(nombre):
    if not os.path.exists(F(nombre)):
        return []
    with open(F(nombre), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def ganadora(cid):
    """1 si la caja gano, 0 si perdio, None si todavia no se sabe."""
    r = S.get(f"https://clob.polymarket.com/markets/{cid}", timeout=20).json()
    if not r.get("closed"):
        return None
    for t in r.get("tokens", []):
        if t.get("outcome") == "Yes" and t.get("winner") is not None:
            return 1 if t["winner"] else 0
    return None


def trades(cid):
    out = []
    for off in range(0, 3001, 500):
        r = S.get("https://data-api.polymarket.com/trades",
                  params={"market": cid, "limit": 500, "offset": off, "takerOnly": "true"}, timeout=30).json()
        for t in r:
            yes = t["outcomeIndex"] == 0
            py = t["price"] if yes else 1 - t["price"]
            out.append((t["timestamp"], py, t["size"], (t["side"] == "BUY") == yes))
        if len(r) < 500:
            break
    return out


def cosechador(res):
    hechas = res.setdefault("cosechador", {})
    for r in leer("cosecha_muertas.csv"):
        cid = r["condition_id"]
        if cid in hechas:
            continue
        try:
            g = ganadora(cid)
            if g is None:
                continue
            tr = trades(cid)
        except Exception:
            continue
        t0 = int(r["ts_detectada"])
        fila = {"serie": r["serie"], "fecha": r["fecha_local"], "caja": r["caja"], "gano": g}
        for p in PRECIOS:
            q = min(ACC, sum(s for ts, py, s, compra in tr if ts > t0 and compra and py > p + 1e-9))
            fila[str(p)] = {"acciones": round(q, 1), "resultado": round(q * p if g == 0 else -q * (1 - p), 2)}
        hechas[cid] = fila
        time.sleep(0.2)


def sp(res):
    hechas = res.setdefault("sp14", {})
    libro = {(r["fecha"], r["caja"]): r for r in leer("papel_libro.csv")}
    eventos = {}
    for o in leer("papel_operaciones.csv"):
        k = f"{o['fecha']}|{o['caja']}|{o['lado']}"
        if k in hechas or not o.get("ganadora"):
            continue
        d = datetime.fromisoformat(o["fecha"])
        slug = f"highest-temperature-in-sao-paulo-on-{d:%B}-{d.day}-{d.year}".lower()
        try:
            if slug not in eventos:
                eventos[slug] = S.get("https://gamma-api.polymarket.com/events", params={"slug": slug}, timeout=30).json()
            mk = [m for m in eventos[slug][0]["markets"] if m["groupItemTitle"] == o["caja"]]
            if not mk:
                continue
            tr = trades(mk[0]["conditionId"])
        except Exception:
            continue
        b = libro.get((o["fecha"], o["caja"]), {})
        # 14:15 de Sao Paulo = 17:15 UTC
        t0 = datetime(d.year, d.month, d.day, 17, 15, tzinfo=timezone.utc).timestamp()
        gano_yes = o["ganadora"] == o["caja"]
        if o["lado"] == "Yes":
            # orden de compra del Yes en el mejor bid (yes_mejor_venta = precio al que se podia vender = bid)
            p = num(b.get("yes_mejor_venta"))
            q = 0 if p is None else sum(s for ts, py, s, compra in tr if ts > t0 and not compra and py < p - 1e-9)
            gana = gano_yes
        else:
            # orden de compra del No en su mejor bid = 1 - ask del Yes (yes_mejor_compra = ask del Yes)
            ask_yes = num(b.get("yes_mejor_compra"))
            p = None if ask_yes is None else round(1 - ask_yes, 4)
            q = 0 if p is None else sum(s for ts, py, s, compra in tr if ts > t0 and compra and py > 1 - p + 1e-9)
            gana = not gano_yes
        q = min(q, num(o["acciones"]))
        hechas[k] = {"precio_maker": p, "precio_taker": num(o["precio_medio"]), "acciones": round(q, 1),
                     "resultado_maker": round(q * ((1 - p) if gana else -p), 2) if p else 0.0}
        time.sleep(0.2)


def main():
    try:
        with open(F("sombra_maker.json"), encoding="utf-8") as f:
            res = json.load(f)
    except (OSError, ValueError):
        res = {}
    for fn in (cosechador, sp):
        try:
            fn(res)
        except Exception as e:
            print("error en", fn.__name__, e)
    with open(F("sombra_maker.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=0, ensure_ascii=False)
    print("sombra_maker.json actualizado:", {k: len(v) for k, v in res.items()})


if __name__ == "__main__":
    main()

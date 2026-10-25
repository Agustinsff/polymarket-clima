"""
ARBITRAJE DE PRECIOS QUE NO SUMAN 1: solo mide, no opera. La regla esta fija en arbitraje/REGLA.md.

Saca fotos del libro de ordenes lo mas seguido posible (objetivo cada 10 s) de:
  - temperatura: todos los eventos abiertos (comprar todos los Si / todos los No)
  - otros negRisk: los 40 de mas volumen 24 h
  - binarios: los 20 de mas volumen 24 h (Si + No)
y anota, por evento y por foto, cuanto se gana comprando juegos completos recorriendo el libro real.

Uso:
  python arbitraje/medir.py MINUTOS   -> mide durante MINUTOS y escribe arbitraje/datos/fotos_<inicio>.csv.gz
"""

import csv
import gzip
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

GAMMA = "https://gamma-api.polymarket.com/events"
BOOKS = "https://clob.polymarket.com/books"
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
INTERVALO = 10          # segundos entre fotos (objetivo)
REELEGIR = 600          # cada cuanto se vuelven a pedir los eventos a gamma
N_OTROS, N_BIN = 40, 20
TASA_VIEJA = 0.05

S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-arbitraje/1.0 (investigacion personal)"

COLS = ["ts", "grupo", "slug", "aumentado", "n", "tasa_max", "min_orden", "edad_libro_s",
        "suma_ask_si", "suma_ask_no",
        "borde_si_c", "juegos_si", "ganancia_si", "ganancia_min_si",
        "borde_no_c", "juegos_no", "ganancia_no", "ganancia_min_no", "espejo"]


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", flush=True)


def tasa_de(m):
    if m.get("feesEnabled") is False:
        return 0.0
    fs = m.get("feeSchedule")
    if isinstance(fs, dict) and fs.get("rate") is not None:
        return float(fs["rate"])
    return TASA_VIEJA


def fee(p, tasa):
    return tasa * p * (1 - p)


def gamma(params):
    out = []
    for off in range(0, 3000, 100):
        for intento in range(3):
            try:
                r = S.get(GAMMA, params={**params, "limit": 100, "offset": off}, timeout=30).json()
                break
            except Exception as e:
                log(f"gamma fallo ({e}), reintento")
                time.sleep(3)
        else:
            r = []
        out += r
        if len(r) < 100:
            break
    return out


def patas(e):
    """Mercados medibles del evento: (token_si, token_no, tasa, min_orden)."""
    out = []
    for m in e.get("markets", []):
        if m.get("closed") or not m.get("active") or not m.get("enableOrderBook") or not m.get("clobTokenIds"):
            continue
        toks = json.loads(m["clobTokenIds"])
        if len(toks) != 2:
            continue
        out.append((toks[0], toks[1], tasa_de(m), float(m.get("orderMinSize") or 5)))
    return out


def elegir():
    temp = gamma({"tag_slug": "daily-temperature", "closed": "false"})
    slugs_temp = {e["slug"] for e in temp}
    todos = gamma({"closed": "false", "active": "true", "order": "volume24hr", "ascending": "false"})[:1500]
    evs = []
    for e in temp:
        p = patas(e)
        if len(p) >= 2:
            evs.append({"grupo": "temperatura", "slug": e["slug"], "aum": bool(e.get("negRiskAugmented")), "patas": p})
    otros = bins = 0
    for e in todos:
        if e["slug"] in slugs_temp:
            continue
        p = patas(e)
        if e.get("negRisk") and len(p) >= 2 and otros < N_OTROS:
            evs.append({"grupo": "negrisk", "slug": e["slug"], "aum": bool(e.get("negRiskAugmented")), "patas": p})
            otros += 1
        elif not e.get("negRisk") and len(e.get("markets", [])) == 1 and len(p) == 1 and bins < N_BIN:
            evs.append({"grupo": "binario", "slug": e["slug"], "aum": False, "patas": p})
            bins += 1
    log(f"eventos: {sum(x['grupo'] == 'temperatura' for x in evs)} temperatura, {otros} negRisk, {bins} binarios; "
        f"tokens {2 * sum(len(x['patas']) for x in evs)}")
    return evs


def bajar_libros(tokens):
    tokens = list(tokens)
    tandas = [tokens[i:i + 100] for i in range(0, len(tokens), 100)]

    def una(t):
        for intento in range(3):
            try:
                r = S.post(BOOKS, json=[{"token_id": x} for x in t], timeout=20)
                if r.status_code == 429:
                    time.sleep(2 + intento * 2)
                    continue
                return r.json()
            except Exception:
                time.sleep(1)
        return []

    libros = {}
    with ThreadPoolExecutor(6) as ex:
        for res in ex.map(una, tandas):
            for b in res or []:
                if isinstance(b, dict) and b.get("asset_id"):
                    asks = sorted(((float(a["price"]), float(a["size"])) for a in b.get("asks", [])), key=lambda x: x[0])
                    bid = max((float(x["price"]) for x in b.get("bids", [])), default=None)
                    libros[b["asset_id"]] = (asks, int(b.get("timestamp") or 0), bid)
    return libros


def juegos(piernas, cobro, min_orden):
    """piernas: [(asks ordenados, tasa)]. Compra juegos completos mientras el juego siguiente cueste < cobro.
    Devuelve (borde del primer juego en c, juegos maximos, ganancia maxima US$, ganancia comprando el minimo)."""
    if any(not a for a, _ in piernas):
        return None
    idx = [0] * len(piernas)
    resto = [a[0][1] for a, _ in piernas]
    q = gan = 0.0
    gan_min = None
    borde = None
    while True:
        precios = [piernas[i][0][idx[i]][0] for i in range(len(piernas))]
        costo = sum(p + fee(p, piernas[i][1]) for i, p in enumerate(precios))
        margen = cobro - costo
        if borde is None:
            borde = margen * 100
        dq = min(resto)
        if gan_min is None and q + dq >= min_orden:
            gan_min = gan + margen * (min_orden - q)
        if margen <= 0:
            break
        q += dq
        gan += margen * dq
        fin = False
        for i in range(len(piernas)):
            resto[i] -= dq
            if resto[i] <= 1e-9:
                idx[i] += 1
                if idx[i] >= len(piernas[i][0]):
                    fin = True
                else:
                    resto[i] = piernas[i][0][idx[i]][1]
        if fin:
            break
    if gan_min is None:      # no hay profundidad para el minimo en alguna pata
        gan_min = float("nan")
    return borde, q, gan, gan_min


def foto(evs, libros, ts):
    filas = []
    for e in evs:
        p = e["patas"]
        n = len(p)
        if any(t not in libros or nt not in libros for t, nt, _, _ in p):
            continue
        min_orden = max(x[3] for x in p)
        edad = ts - min(min(libros[t][1], libros[nt][1]) for t, nt, _, _ in p) / 1000
        si = juegos([(libros[t][0], tasa) for t, _, tasa, _ in p], 1.0, min_orden)
        no = juegos([(libros[nt][0], tasa) for _, nt, tasa, _ in p], float(n - 1) if n > 1 else 1.0, min_orden) \
            if e["grupo"] != "binario" else None
        if e["grupo"] == "binario":     # Si + No del mismo mercado
            t, nt, tasa, _ = p[0]
            si = juegos([(libros[t][0], tasa), (libros[nt][0], tasa)], 1.0, min_orden)
            n = 2

        suma_si = sum(libros[t][0][0][0] for t, _, _, _ in p if libros[t][0]) if e["grupo"] != "binario" else \
            sum(libros[x][0][0][0] for x in p[0][:2] if libros[x][0])
        suma_no = sum(libros[nt][0][0][0] for _, nt, _, _ in p if libros[nt][0]) if e["grupo"] != "binario" else ""
        fila = [round(ts, 1), e["grupo"], e["slug"], int(e["aum"]), n, max(x[2] for x in p), min_orden, round(edad),
                round(suma_si, 4), round(suma_no, 4) if suma_no != "" else ""]
        for r in (si, no):
            fila += ["", "", "", ""] if r is None else [round(r[0], 3), round(r[1], 2), round(r[2], 4),
                                                         "" if r[3] != r[3] else round(r[3], 4)]
        # control: el ask del No es 1 - bid del Si (libro espejado)? fraccion de mercados donde se cumple
        pares = [(libros[nt][0][0][0], libros[t][2]) for t, nt, _, _ in p if libros[nt][0] and libros[t][2] is not None]
        fila.append(round(sum(abs(a + b - 1) < 1e-6 for a, b in pares) / len(pares), 2) if pares else "")
        filas.append(fila)
    return filas


def main():
    minutos = float(sys.argv[1]) if len(sys.argv) > 1 else 5
    os.makedirs(CARPETA, exist_ok=True)
    inicio = time.time()
    nombre = os.path.join(CARPETA, f"fotos_{datetime.now(timezone.utc):%Y%m%dT%H%MZ}.csv.gz")
    evs, ult = elegir(), time.time()
    n_fotos = n_op = 0
    with gzip.open(nombre, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        while time.time() - inicio < minutos * 60:
            t0 = time.time()
            if t0 - ult > REELEGIR:
                try:
                    evs, ult = elegir(), t0
                except Exception as e:
                    log(f"no pude reelegir eventos: {e}")
            tokens = {x for e in evs for t, nt, _, _ in e["patas"] for x in (t, nt)}
            libros = bajar_libros(tokens)
            filas = foto(evs, libros, time.time())
            w.writerows(filas)
            n_fotos += 1
            ops = [r for r in filas if (r[13] not in ("", None) and r[13] >= 0.01) or
                   (r[17] not in ("", None) and r[17] >= 0.01)]
            n_op += len(ops)
            dur = time.time() - t0
            if n_fotos % 30 == 1 or ops:
                log(f"foto {n_fotos}: {len(libros)}/{len(tokens)} libros, {len(filas)} eventos, {dur:.1f}s, "
                    f"oportunidades {len(ops)}" + "".join(f"\n   {r[1]} {r[2]} si={r[12]} no={r[16]}" for r in ops[:5]))
            if n_fotos % 60 == 0:
                f.flush()
            time.sleep(max(0, INTERVALO - dur))
    log(f"listo: {n_fotos} fotos, {n_op} filas con oportunidad -> {nombre}")


if __name__ == "__main__":
    main()

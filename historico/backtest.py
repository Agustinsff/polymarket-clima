"""
BACKTEST: el promedio de 11 modelos (sesgo corregido) contra los precios historicos de Polymarket
(investigacion, no toca a los bots). Las reglas estan en historico/REGLAS.md y se fijaron antes de
bajar los precios.

  python historico/backtest.py bajar      -> baja ganadoras y precios (red: Polymarket); guarda historico/cache.json.gz
  python historico/backtest.py analizar   -> solo cuentas, con el cache (no usa red)
  python historico/backtest.py            -> las dos cosas

Salida: historico/informe.md, historico/resumen.json, historico/ops.csv.gz
"""

import csv
import gzip
import json
import math
import os
import random
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from estaciones import TZ, leer_caja  # noqa: E402

OUT = os.path.join(RAIZ, "historico")
CACHE = os.path.join(OUT, "cache.json.gz")
GAMMA = "https://gamma-api.polymarket.com/events"
HIST = "https://clob.polymarket.com/prices-history"
HORIZONTES = (1, 2, 3)
VENTANA = 6 * 3600           # el precio es el ultimo punto en las 6 h previas a la decision
LIMITE_MIN = int(os.environ.get("LIMITE_MIN", 150))   # corta la bajada (se sigue en la proxima corrida)

# ---- reglas fijas (REGLAS.md) ----
MODELOS = ("Promedio", "GFS+ECMWF")
K_POOL = 10
MIN_PREVIOS = 10
SIGMA_MIN = 0.5
UMBRALES = (0.10, 0.05)
PRECIO_MIN, PRECIO_MAX = 0.03, 0.90
ACCIONES = 10
TRAMOS = ((0, .10), (.10, .30), (.30, .70), (.70, .90), (.90, 1.01))
COSTOS_FIJOS = (0.0, 0.01, 0.02, 0.03)
REMUESTREOS = 2000
SUMA_MIN, SUMA_MAX = 0.90, 1.15   # agregado despues (ver analizar)

_ses = threading.local()


def log(m):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {m}", file=sys.stderr, flush=True)


def http():
    if not hasattr(_ses, "s"):
        import requests
        _ses.s = requests.Session()
        _ses.s.headers["User-Agent"] = "polymarket-clima-historico/1.0 (investigacion personal)"
    return _ses.s


def get(url, params, intentos=4):
    for i in range(intentos):
        try:
            r = http().get(url, params=params, timeout=40)
            if r.status_code == 429:
                time.sleep(10 * (i + 1))
                continue
            if r.status_code == 200:
                return r.json()
            return None
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def slug(serie, fecha):
    tipo, ciudad = serie.split("|")
    d = datetime.fromisoformat(fecha)
    return f"{tipo}-temperature-in-{ciudad}-on-{d:%B}-{d.day}-{d.year}".lower()


def momento(serie, fecha, h):
    """Decision para el horizonte h: 06:00 local del dia D - (h - 1), en segundos UTC."""
    d = datetime.fromisoformat(fecha) - timedelta(days=h - 1)
    return int(datetime(d.year, d.month, d.day, 6, tzinfo=ZoneInfo(TZ[serie.split("|")[1]])).timestamp())


def cargar_cache():
    if os.path.exists(CACHE):
        with gzip.open(CACHE, "rt", encoding="utf-8") as f:
            return json.load(f)
    return {"eventos": {}, "spread": {}}


def guardar_cache(c):
    with gzip.open(CACHE, "wt", encoding="utf-8") as f:
        json.dump(c, f, separators=(",", ":"))


def historia(token, t0, t1):
    """[(ts, p)] del Yes entre t0 y t1."""
    for fid in (10, 60):
        j = get(HIST, {"market": token, "startTs": t0, "endTs": t1, "fidelity": fid})
        if j and j.get("history"):
            return [(x["t"], x["p"]) for x in j["history"]]
    return []


def precio_en(h, t):
    xs = [p for ts, p in h if t - VENTANA <= ts <= t]
    return xs[-1] if xs else None


def leer_dias():
    """{(serie, fecha): {"en_f":..., "real":..., (modelo, h): (corr, emision)}}"""
    out = defaultdict(dict)
    with gzip.open(os.path.join(RAIZ, "modelos", "dias.csv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["modelo"] not in MODELOS or int(r["horizonte"]) not in HORIZONTES:
                continue
            d = out[(r["serie"], r["fecha"])]
            d["en_f"] = r["en_f"] == "1"
            d["real"] = float(r["real"])
            if r["corr"]:
                d[(r["modelo"], int(r["horizonte"]))] = float(r["corr"])
    return out


# ---------------------------------------------------------------------------
# BAJAR

def bajar_evento(serie, fecha):
    evs = get(GAMMA, {"slug": slug(serie, fecha)})
    if evs is None:
        return None                      # error de red: se reintenta otra vez
    if not evs:
        return {"sin_mercado": 1}
    t3, t1 = momento(serie, fecha, 3), momento(serie, fecha, 1)
    cajas, hay_ganadora = [], False
    for m in evs[0].get("markets", []):
        try:
            leer_caja(m["groupItemTitle"])
            token = json.loads(m["clobTokenIds"])[0]
            pr = json.loads(m.get("outcomePrices") or "[]")
        except Exception:
            continue
        gano = int(bool(m.get("closed") and pr and float(pr[0]) >= 0.99))
        hay_ganadora |= bool(gano)
        h = historia(token, t3 - VENTANA, t1)
        cajas.append({"caja": m["groupItemTitle"], "gano": gano,
                      "p": {str(k): precio_en(h, momento(serie, fecha, k)) for k in HORIZONTES}, "n": len(h)})
    if not hay_ganadora:
        return {"sin_ganadora": 1}
    return {"cajas": cajas}


def bajar_spread(cache, fin):
    """Precio historico en cada foto de pronostico.csv (para medir cuanto se paga de mas)."""
    fotos = defaultdict(list)
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["bid"] and r["ask"]:
                fotos[(r["serie"], r["fecha"])].append(r)
    pend = [k for k in fotos if f"{k[0]}|{k[1]}" not in cache["spread"]]
    log(f"spread: {len(pend)} eventos por bajar")

    def trabajo(k):
        evs = get(GAMMA, {"slug": slug(*k)})
        if not evs:
            return k, None
        tok = {}
        for m in evs[0].get("markets", []):
            try:
                tok[m["conditionId"]] = json.loads(m["clobTokenIds"])[0]
            except Exception:
                pass
        out = []
        por_cid = defaultdict(list)
        for r in fotos[k]:
            por_cid[r["condition_id"]].append(r)
        for cid, rs in por_cid.items():
            if cid not in tok:
                continue
            ts = [int(datetime.strptime(r["momento_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
                  for r in rs]
            h = historia(tok[cid], min(ts) - VENTANA, max(ts) + 600)
            for r, t in zip(rs, ts):
                p = precio_en(h, t)
                if p is not None:
                    out.append([p, float(r["bid"]), float(r["ask"])])
        return k, out

    with ThreadPoolExecutor(8) as ex:
        for i, (k, res) in enumerate(ex.map(trabajo, pend)):
            if res is not None:
                cache["spread"][f"{k[0]}|{k[1]}"] = res
            if time.time() > fin:
                break


def bajar():
    fin = time.time() + LIMITE_MIN * 60
    cache = cargar_cache()
    dias = leer_dias()
    pend = [k for k in sorted(dias) if f"{k[0]}|{k[1]}" not in cache["eventos"]]
    log(f"{len(dias)} serie-dias, {len(pend)} por bajar")
    hechos = 0
    with ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(bajar_evento, *k): k for k in pend}
        for fu in futs:
            k = futs[fu]
            if time.time() > fin:
                ex.shutdown(cancel_futures=True)
                break
            try:
                res = fu.result()
            except Exception as e:
                log(f"{k}: {e}")
                res = None
            if res is not None:
                cache["eventos"][f"{k[0]}|{k[1]}"] = res
            hechos += 1
            if hechos % 250 == 0:
                log(f"  {hechos}/{len(pend)}")
                guardar_cache(cache)
    guardar_cache(cache)
    bajar_spread(cache, time.time() + max(2, LIMITE_MIN // 6) * 60)
    guardar_cache(cache)
    n = defaultdict(int)
    for v in cache["eventos"].values():
        n["con cajas" if "cajas" in v else next(iter(v))] += 1
    log(f"eventos en cache: {dict(n)}; spread: {len(cache['spread'])} eventos")


# ---------------------------------------------------------------------------
# CUENTAS

def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def sigmas(dias):
    """{(modelo, h, serie, fecha): sigma} con errores de dias cuyo resultado se conocia antes de la emision."""
    out = {}
    for m in MODELOS:
        for h in HORIZONTES:
            err = defaultdict(list)          # fecha -> [(serie, error^2)]
            for (serie, fecha), d in dias.items():
                if (m, h) in d:
                    err[fecha].append((serie, (d["real"] - d[(m, h)]) ** 2))
            fechas = sorted(err)
            # acumulados hasta cada fecha (sin incluirla)
            acum, pool, ser = {}, [0.0, 0], defaultdict(lambda: [0.0, 0])
            for f in fechas:
                acum[f] = (tuple(pool), {s: tuple(v) for s, v in ser.items()})
                for s, e2 in err[f]:
                    pool[0] += e2
                    pool[1] += 1
                    ser[s][0] += e2
                    ser[s][1] += 1
            for (serie, fecha), d in dias.items():
                if (m, h) not in d:
                    continue
                emision = (datetime.fromisoformat(fecha) - timedelta(days=h)).date().isoformat()
                previas = [f for f in fechas if f >= emision]
                if not previas:
                    continue
                (sp, np_), sers = acum[previas[0]]
                ss, ns = sers.get(serie, (0.0, 0))
                if ns < MIN_PREVIOS:
                    continue
                s2 = (ss + K_POOL * sp / np_) / (ns + K_POOL)
                out[(m, h, serie, fecha)] = max(math.sqrt(s2), SIGMA_MIN)
    return out


def p_caja(titulo, centro_c, sigma_c, en_f):
    lo, hi, _ = leer_caja(titulo)
    c, s = (centro_c * 1.8 + 32, sigma_c * 1.8) if en_f else (centro_c, sigma_c)
    a = 1.0 if hi is None else ncdf((hi + 0.5 - c) / s)
    b = 0.0 if lo is None else ncdf((lo - 0.5 - c) / s)
    return max(a - b, 0.0)


def tramo(p):
    for i, (a, b) in enumerate(TRAMOS):
        if a <= p < b:
            return i
    return len(TRAMOS) - 1


def mediana(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def costos_medidos(cache):
    """Por tramo de precio historico: mediana de (ask - hist) y de (hist - bid)."""
    yes, no = defaultdict(list), defaultdict(list)
    for filas in cache["spread"].values():
        for p, bid, ask in filas:
            if ask - bid > 0.5:          # libro vacio de un lado
                continue
            yes[tramo(p)].append(ask - p)
            no[tramo(p)].append(p - bid)
    return ({i: mediana(yes[i]) for i in range(len(TRAMOS))}, {i: mediana(no[i]) for i in range(len(TRAMOS))},
            {i: len(yes[i]) for i in range(len(TRAMOS))})


def filas_base(cache, dias, sig):
    """Una fila por (serie, fecha, h, caja) con precio, ganadora y p de cada modelo."""
    out = []
    for (serie, fecha), d in dias.items():
        ev = cache["eventos"].get(f"{serie}|{fecha}", {})
        if "cajas" not in ev:
            continue
        for h in HORIZONTES:
            if h == 1 and serie.startswith("lowest"):
                continue
            pm = {}
            for m in MODELOS:
                s = sig.get((m, h, serie, fecha))
                if (m, h) in d and s:
                    pm[m] = s
            if len(pm) < len(MODELOS):
                continue                 # los dos modelos sobre los mismos dias
            ps = [c["p"].get(str(h)) for c in ev["cajas"]]
            suma = None if None in ps else sum(ps)
            for c in ev["cajas"]:
                p = c["p"].get(str(h))
                if p is None:
                    continue
                try:
                    probs = {m: p_caja(c["caja"], d[(m, h)], pm[m], d["en_f"]) for m in MODELOS}
                except Exception:
                    continue
                out.append({"serie": serie, "fecha": fecha, "h": h, "caja": c["caja"], "precio": p, "y": c["gano"],
                            "suma": suma, **{f"p_{m}": probs[m] for m in MODELOS}})
    return out


def lam(fs, m):
    def ll(l):
        s = 0.0
        for f in fs:
            q = min(max(f["precio"] + l * (f[f"p_{m}"] - f["precio"]), 1e-3), 1 - 1e-3)
            s += math.log(q if f["y"] else 1 - q)
        return s
    ls = [i / 40 for i in range(-20, 61)]
    v = {l: ll(l) for l in ls}
    best = max(ls, key=v.get)
    ok = [l for l in ls if v[best] - v[l] <= 1.92]
    return best, min(ok), max(ok)


def puntajes(fs, clave):
    br = sum((f[clave] - f["y"]) ** 2 for f in fs) / len(fs)
    lg = -sum(math.log(min(max(f[clave] if f["y"] else 1 - f[clave], 1e-3), 1)) for f in fs) / len(fs)
    return br, lg


def operar(fs, m, umbral, costo):
    """costo(p_hist, lado) -> precio pagado. Devuelve ops [(fecha, gasto, resultado)]."""
    ops = []
    for f in fs:
        p = f[f"p_{m}"]
        cy = costo(f["precio"], "Yes")
        cn = costo(f["precio"], "No")
        if PRECIO_MIN <= cy <= PRECIO_MAX and p - cy >= umbral:
            ops.append((f["fecha"], ACCIONES * cy, ACCIONES * ((1 - cy) if f["y"] else -cy), f, "Yes", cy))
        if PRECIO_MIN <= cn <= PRECIO_MAX and (1 - p) - cn >= umbral:
            ops.append((f["fecha"], ACCIONES * cn, ACCIONES * ((1 - cn) if not f["y"] else -cn), f, "No", cn))
    return ops


def resumen_ops(ops, semilla=1):
    if not ops:
        return {"n": 0}
    gasto = sum(o[1] for o in ops)
    gan = sum(o[2] for o in ops)
    por_dia = defaultdict(lambda: [0.0, 0.0])
    for o in ops:
        por_dia[o[0]][0] += o[1]
        por_dia[o[0]][1] += o[2]
    ds = list(por_dia.values())
    rnd = random.Random(semilla)
    neg = 0
    for _ in range(REMUESTREOS):
        g = r = 0.0
        for _ in ds:
            x = ds[rnd.randrange(len(ds))]
            g += x[0]
            r += x[1]
        neg += r < 0
    return {"n": len(ops), "dias": len(ds), "gasto": round(gasto, 2), "ganancia": round(gan, 2),
            "roi": round(gan / gasto, 4), "p_neg": round(neg / REMUESTREOS, 3),
            "acierto": round(sum(o[2] > 0 for o in ops) / len(ops), 3)}


def cuentas(fs, corte, medido):
    """Medidas por horizonte, criterio de REGLAS.md y la lista de operaciones (umbral principal)."""
    por_h, todas_ops = {}, []
    for h in HORIZONTES:
        fh = [f for f in fs if f["h"] == h]
        if not fh:
            continue
        r = {"cajas": len(fh), "dias": len({(f["serie"], f["fecha"]) for f in fh}),
             "puntaje": {"mercado": puntajes(fh, "precio"), **{m: puntajes(fh, f"p_{m}") for m in MODELOS}},
             "lambda": {m: lam(fh, m) for m in MODELOS}, "ops": {}}
        for m in MODELOS:
            for u in UMBRALES:
                ops = operar(fh, m, u, medido)
                if u == UMBRALES[0]:
                    todas_ops += [(m, h) + o for o in ops]
                r["ops"][f"{m}|{u}|medido"] = resumen_ops(ops)
                for k in ("highest", "lowest"):
                    r["ops"][f"{m}|{u}|medido|{k}"] = resumen_ops([o for o in ops if o[3]["serie"].startswith(k)])
                r["ops"][f"{m}|{u}|medido|1a mitad"] = resumen_ops([o for o in ops if o[0] < corte])
                r["ops"][f"{m}|{u}|medido|2a mitad"] = resumen_ops([o for o in ops if o[0] >= corte])
                for c in COSTOS_FIJOS:
                    fijo = lambda p, lado, c=c: (p if lado == "Yes" else 1 - p) + c
                    r["ops"][f"{m}|{u}|fijo {int(c * 100)}c"] = resumen_ops(operar(fh, m, u, fijo))
        por_h[h] = r
    crit = None
    r2 = por_h.get(2)
    if r2:
        o = r2["ops"]["Promedio|0.1|medido"]
        l = r2["lambda"]["Promedio"]
        m1, m2 = r2["ops"]["Promedio|0.1|medido|1a mitad"], r2["ops"]["Promedio|0.1|medido|2a mitad"]
        crit = {"roi_pos_y_p_neg_<5%": bool(o.get("n") and o["roi"] > 0 and o["p_neg"] < 0.05),
                "lambda_sin_0": l[1] > 0,
                "dos_mitades_pos": bool(m1.get("n") and m2.get("n") and m1["roi"] > 0 and m2["roi"] > 0)}
        crit["hay_ventaja"] = all(crit.values())
    return por_h, crit, todas_ops


def analizar():
    cache = cargar_cache()
    dias = leer_dias()
    sig = sigmas(dias)
    cy, cn, ncal = costos_medidos(cache)

    def medido(p, lado):
        c = (cy if lado == "Yes" else cn)[tramo(p)]
        c = 0.02 if c is None else c          # tramo sin fotos (no deberia pasar)
        return (p if lado == "Yes" else 1 - p) + c

    fs = filas_base(cache, dias, sig)
    fechas = sorted({f["fecha"] for f in fs})
    corte = fechas[len(fechas) // 2] if fechas else ""
    res = {"costo_yes": cy, "costo_no": cn, "n_calibracion": ncal, "filas": len(fs),
           "eventos": sum("cajas" in v for v in cache["eventos"].values()), "corte_mitades": corte}
    res["por_h"], res["criterio"], todas_ops = cuentas(fs, corte, medido)
    # AGREGADO DESPUES de ver resultados: solo momentos en que los precios de las cajas del evento suman
    # entre SUMA_MIN y SUMA_MAX (si suman 2-4, el "precio" es el medio de un libro vacio, no se puede operar)
    sano = [f for f in fs if f["suma"] is not None and SUMA_MIN <= f["suma"] <= SUMA_MAX]
    res["filas_sano"] = len(sano)
    res["por_h_sano"], res["criterio_sano"], _ = cuentas(sano, corte, medido)
    with open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False, default=str)
    with gzip.open(os.path.join(OUT, "ops.csv.gz"), "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["modelo", "h", "fecha", "serie", "caja", "lado", "costo", "precio_hist", "p_modelo", "gano", "resultado"])
        for m, h, fecha, gasto, resu, fl, lado, c in todas_ops:
            w.writerow([m, h, fecha, fl["serie"], fl["caja"], lado, round(c, 4), fl["precio"], round(fl[f"p_{m}"], 4),
                        fl["y"], round(resu, 3)])
    informe(res)
    log(f"{len(fs)} filas, {len(todas_ops)} ops")


def seccion(por_h, c, titulo):
    L = []
    if c:
        L += ["", titulo, "",
              f"- ROI > 0 y P(ROI<0) < 5 %: {'sí' if c['roi_pos_y_p_neg_<5%'] else 'no'}",
              f"- λ con intervalo sin 0: {'sí' if c['lambda_sin_0'] else 'no'}",
              f"- ROI positivo en las dos mitades: {'sí' if c['dos_mitades_pos'] else 'no'}",
              f"- **Hay ventaja: {'SÍ' if c['hay_ventaja'] else 'NO'}**"]
    for h, r in por_h.items():
        L += ["", f"## Horizonte {h} ({r['dias']} serie-días, {r['cajas']} cajas)", "",
              "| | Brier | log-score | λ (IC 95 %) |", "|---|---|---|---|",
              f"| Mercado | {r['puntaje']['mercado'][0]:.4f} | {r['puntaje']['mercado'][1]:.4f} | |"]
        for m in MODELOS:
            l = r["lambda"][m]
            L.append(f"| {m} | {r['puntaje'][m][0]:.4f} | {r['puntaje'][m][1]:.4f} | {l[0]:.2f} [{l[1]:.2f}, {l[2]:.2f}] |")
        L += ["", "| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for k, o in r["ops"].items():
            m, u, cc = k.split("|", 2)
            cc = cc.replace("|", ", ")
            if not o.get("n"):
                L.append(f"| {m} | {u} | {cc} | 0 | | | | | | |")
                continue
            L.append(f"| {m} | {u} | {cc} | {o['n']} | {o['dias']} | {o['acierto'] * 100:.0f}% | {o['gasto']:.0f} | "
                     f"{o['ganancia']:+.1f} | {o['roi'] * 100:+.1f}% | {o['p_neg'] * 100:.0f}% |")
    return L


def informe(res):
    L = ["# Promedio de 11 modelos contra precios históricos (backtest)", "",
         "Reglas fijadas antes de bajar precios: `historico/REGLAS.md`. Generado por `historico/backtest.py`.", "",
         f"Eventos con ganadora y precios: {res['eventos']}; filas (caja × horizonte): {res['filas']}.", "",
         "## Costo de ejecución medido (sobre el precio histórico)", "",
         "| Tramo | Comprar Yes (ask − hist) | Comprar No (hist − bid) | fotos |", "|---|---|---|---|"]
    for i, (a, b) in enumerate(TRAMOS):
        y, n = res["costo_yes"].get(i), res["costo_no"].get(i)
        L.append(f"| {int(a * 100)}-{int(min(b, 1) * 100)} ¢ | {'' if y is None else f'{y * 100:+.1f} ¢'} | "
                 f"{'' if n is None else f'{n * 100:+.1f} ¢'} | {res['n_calibracion'].get(i, 0)} |")
    L += seccion(res["por_h"], res["criterio"], "## Veredicto (criterio fijado antes, h = 2, Promedio, costo medido, umbral 10)")
    L += ["", "---", "", "# Agregado después de ver resultados: solo precios con libro de verdad", "",
          f"Las cajas de un evento deberían sumar ~1. En muchas mínimas (y a 3 días) sumaban 2-4: el precio histórico era el "
          f"medio de un libro casi vacío (ej. bid 1 ¢ / ask 66 ¢ → 33,5 ¢), que no se puede operar. Acá quedan solo los "
          f"momentos en que las cajas del evento suman entre {SUMA_MIN} y {SUMA_MAX} ({res['filas_sano']} filas)."]
    L += seccion(res["por_h_sano"], res["criterio_sano"], "## Veredicto con libro de verdad (misma regla)")
    with open(os.path.join(OUT, "informe.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if modo in ("bajar", "todo"):
        bajar()
    if modo in ("analizar", "todo"):
        analizar()

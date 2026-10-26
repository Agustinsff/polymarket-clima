"""
INVESTIGACION (sin operar): version maker de la prueba B de las corridas. Ver corridas/REGLA_MAKER.md.

Parte de las mismas senales que analizar.py dejo en corridas/ops.csv.gz (evento, caja, W, precio en W) y
simula, con las operaciones reales de rivales/datos/ (rama investigacion-rivales), una orden de compra
que espera en el libro en vez de pagar el spread. Escribe corridas/informe_maker.md y corridas/ops_maker.csv.gz.

Uso: python corridas/maker.py CARPETA_RIVALES_DATOS
"""

import glob
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
from estaciones import leer_caja  # noqa: E402

RIV = sys.argv[1]
VIDA = 3 * 3600          # la orden de compra vale 3 h
SALIDA_H = 6             # salida principal: W + 6 h
SALIDA = []


def p(s=""):
    SALIDA.append(s)


def tabla(cab, filas):
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for f in filas:
        p("| " + " | ".join(str(x) for x in f) + " |")
    p("")


def leer(nombre, **kw):
    partes = []
    for ruta in sorted(glob.glob(os.path.join(RIV, nombre + "_*.csv.gz"))):
        try:
            partes.append(pd.read_csv(ruta, **kw))
        except Exception as ex:
            print(f"aviso: {ruta}: {ex}", file=sys.stderr)
    return pd.concat(partes, ignore_index=True)


# ---------------------------------------------------------------------------
# senales ya seleccionadas por analizar.py
# ---------------------------------------------------------------------------
O0 = pd.read_csv(os.path.join(CARPETA, "ops.csv.gz"))
O0["W"] = O0.W.astype(np.int64)

# ---------------------------------------------------------------------------
# cajas: el mismo orden de cajas que analizar.py, para pasar de indice a condition_id
# ---------------------------------------------------------------------------
pr = leer("precios", dtype={"condition_id": str})
pr = pr.dropna().drop_duplicates(["condition_id", "t"]).sort_values(["condition_id", "t"])
cj = leer("eventos", dtype=str).drop_duplicates("condition_id")
cj = cj[cj.tipo.isin(["highest", "lowest"]) & cj.condition_id.isin(set(pr.condition_id))].copy()
cj["evento_id"] = cj.evento_id.astype(int)
lh = [leer_caja(c) for c in cj.caja]
cj["lo"] = [x[0] for x in lh]
cj["hi"] = [x[1] for x in lh]

CIDS, FINAL = {}, {}
for eid, g in cj.groupby("evento_id"):
    inter = g[g.lo.notna() & g.hi.notna()]
    if len(inter) == 0:
        continue
    w = float(np.median(inter.hi - inter.lo + 1))
    centros = []
    for r in g.itertuples():
        if pd.notna(r.lo) and pd.notna(r.hi):
            c = (r.lo + r.hi) / 2
        elif pd.isna(r.lo):
            c = r.hi - (w - 1) / 2 - w
        else:
            c = r.lo + (w - 1) / 2 + w
        centros.append(c)
    orden = np.argsort(centros)
    CIDS[eid] = list(g.condition_id.values[orden])
    for cid, fin in zip(g.condition_id, g.precio_final_si):
        try:
            FINAL[cid] = float(fin)
        except (TypeError, ValueError):
            pass

SERIES = {cid: (g.t.values.astype(np.int64), g.p.values.astype(float)) for cid, g in pr.groupby("condition_id")}
del pr


def precio(cid, t):
    """Ultimo precio por minuto en los 30 min anteriores a t (o None)."""
    s = SERIES.get(cid)
    if s is None:
        return None
    tm, pv = s
    i = np.searchsorted(tm, t, side="right") - 1
    if i < 0 or t - tm[i] > 1800:
        return None
    return float(pv[i])


# ---------------------------------------------------------------------------
# operaciones reales: lado del taker y precio visto como Si
# ---------------------------------------------------------------------------
op = leer("trades", dtype={"condition_id": str, "asset": str},
          usecols=["condition_id", "asset", "side", "price", "size", "timestamp", "tx", "wallet"])
op = op.drop_duplicates(["tx", "asset", "side", "size", "price", "wallet"])
op = op[op.condition_id.isin(set(cj.condition_id))]
si_de = dict(zip(cj.condition_id, cj.token_si))
op["es_si"] = op.asset == op.condition_id.map(si_de)
op["p_si"] = np.where(op.es_si, op.price, 1 - op.price)
op["compra_si"] = (op.es_si & (op.side == "BUY")) | (~op.es_si & (op.side == "SELL"))
OPS = {cid: (g.timestamp.values.astype(np.int64), g.p_si.values, g.compra_si.values)
       for cid, g in op.sort_values("timestamp").groupby("condition_id")}
del op


def mediana_ops(cid, t0, t1, compra):
    s = OPS.get(cid)
    if s is None:
        return None
    tm, pv, cs = s
    a, b = np.searchsorted(tm, t0), np.searchsorted(tm, t1, side="right")
    x = pv[a:b][cs[a:b] == compra]
    return float(np.median(x)) if len(x) else None


def llenado_compra(cid, B, t0, t1, estricto=True):
    """Primer momento en [t0, t1] en que un taker vendio Si por debajo de B (o None)."""
    s = OPS.get(cid)
    if s is None:
        return None
    tm, pv, cs = s
    a, b = np.searchsorted(tm, t0), np.searchsorted(tm, t1, side="right")
    m = (~cs[a:b]) & ((pv[a:b] < B - 1e-9) if estricto else (pv[a:b] <= B + 1e-9))
    return int(tm[a:b][m][0]) if m.any() else None


def llenado_venta(cid, A, t0, t1):
    """Primer momento en [t0, t1] en que un taker compro Si por encima de A (o None)."""
    s = OPS.get(cid)
    if s is None:
        return None
    tm, pv, cs = s
    a, b = np.searchsorted(tm, t0), np.searchsorted(tm, t1, side="right")
    m = cs[a:b] & (pv[a:b] > A + 1e-9)
    return int(tm[a:b][m][0]) if m.any() else None


def venta_taker(cid, X):
    px = precio(cid, X)
    if px is None:
        return None
    mv = mediana_ops(cid, X - 900, X + 900, False)
    v = min(px - 0.01, mv) if mv is not None else px - 0.01
    return max(v, 0.0)


# ---------------------------------------------------------------------------
# simulacion
# ---------------------------------------------------------------------------
filas = []
for r in O0.itertuples():
    cids = CIDS.get(int(r.evento))
    if cids is None or not (0 <= int(r.caja) < len(cids)):
        continue
    cid = cids[int(r.caja)]
    W = int(r.W)
    f = dict(modelo=r.modelo, corrida=r.corrida, evento=int(r.evento), tipo=r.tipo, ciudad=r.ciudad, fecha=r.fecha,
             W=W, db=r.db, caja=int(r.caja), p_W=r.p_W, cid=cid)
    # salidas comunes (taker) a W+3 y W+6
    v3, v6 = venta_taker(cid, W + 3 * 3600), venta_taker(cid, W + 6 * 3600)
    f["venta_3"], f["venta_6"] = v3, v6
    p6 = precio(cid, W + 6 * 3600)
    f["subio_6"] = (p6 - r.p_W) / r.p_W if p6 is not None else np.nan
    f["final"] = FINAL.get(cid, np.nan)
    # taker con las mismas senales (igual que REGLA.md pero salida a 6 h tambien)
    mc = mediana_ops(cid, W, W + 900, True)
    compra_t = max(r.p_W + 0.01, mc) if mc is not None else r.p_W + 0.01
    f["compra_taker"] = compra_t
    f["rt_3"] = (v3 - compra_t) / compra_t if v3 is not None else np.nan
    f["rt_6"] = (v6 - compra_t) / compra_t if v6 is not None else np.nan
    # maker: tres precios de orden
    for nom, desc in (("m1", 0.01), ("m0", 0.0), ("m2", 0.02)):
        B = round(r.p_W - desc, 2)
        tl = llenado_compra(cid, B, W, W + VIDA) if B > 0 else None
        f[f"{nom}_B"] = B
        f[f"{nom}_lleno"] = tl is not None
        f[f"{nom}_t_lleno"] = (tl - W) / 3600 if tl is not None else np.nan
        if tl is None:
            for k in ("r3", "r6", "rf3", "rmk", "rfin"):
                f[f"{nom}_{k}"] = np.nan
            continue
        f[f"{nom}_r6"] = (v6 - B) / B if v6 is not None else np.nan
        f[f"{nom}_r3"] = (v3 - B) / B if v3 is not None else np.nan
        vf = venta_taker(cid, tl + 3 * 3600)
        f[f"{nom}_rf3"] = (vf - B) / B if vf is not None else np.nan
        # salida maker: orden de venta a precio(W+6h)+1c, 3 h; si no, taker a W+9h
        if p6 is not None:
            A = round(p6 + 0.01, 2)
            tv = llenado_venta(cid, A, W + 6 * 3600, W + 9 * 3600)
            vm = A if tv is not None else venta_taker(cid, W + 9 * 3600)
            f[f"{nom}_salida_maker"] = tv is not None
        else:
            vm = None
        f[f"{nom}_rmk"] = (vm - B) / B if vm is not None else np.nan
        fin = FINAL.get(cid)
        f[f"{nom}_rfin"] = (fin - B) / B if fin is not None else np.nan
    # llenado "no estricto" (precio igual a B tambien llena), solo informativo
    B = round(r.p_W - 0.01, 2)
    f["m1_lleno_laxo"] = llenado_compra(cid, B, W, W + VIDA, estricto=False) is not None if B > 0 else False
    filas.append(f)

M = pd.DataFrame(filas)
M.to_csv(os.path.join(CARPETA, "ops_maker.csv.gz"), index=False)


def media_cluster(r, g):
    r = np.asarray(r, dtype=float)
    m = ~np.isnan(r)
    r, g = r[m], np.asarray(g)[m]
    if len(r) < 2:
        return np.nan, np.nan, len(r)
    d = pd.DataFrame({"r": r, "g": g}).groupby("g").r.agg(["sum", "count"])
    mu = r.mean()
    G = len(d)
    se = np.sqrt(((d["sum"] - mu * d["count"]) ** 2).sum() * G / max(G - 1, 1)) / len(r)
    return mu, se, len(r)


def fmt(mu, se, n):
    if n == 0 or np.isnan(mu):
        return "-", "-", 0
    return f"{100 * mu:+.1f}%", (f"{mu / se:+.1f}" if se > 0 else "-"), n


# ---------------------------------------------------------------------------
# informe
# ---------------------------------------------------------------------------
M["mitad"] = np.where(pd.to_datetime(M.fecha) <= pd.to_datetime(M.fecha).median(), 1, 2)
M["tramo"] = pd.cut(M.p_W, [0, 0.20, 0.40, 0.61], labels=["5–20 ¢", "20–40 ¢", "40–60 ¢"])

p("# Versión maker de la regla de las corridas. Resultados\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ} con la regla fija de `REGLA_MAKER.md`. "
  f"{len(M)} señales (las mismas de la prueba B de `REGLA.md`), {M.evento.nunique()} eventos, "
  f"{M.fecha.min()} a {M.fecha.max()}.\n")

p("## Tasa de llenado (orden de compra que vale 3 h)\n")
fil = []
for nom, desc in (("m1", "precio en W − 1 ¢ (principal)"), ("m0", "precio en W"), ("m2", "precio en W − 2 ¢")):
    ll = M[f"{nom}_lleno"]
    fil.append([desc, f"{ll.mean():.0%}", f"{M[ll][f'{nom}_t_lleno'].median():.2f} h" if ll.any() else "-"])
fil.append(["precio en W − 1 ¢, contando también operaciones justo a nuestro precio", f"{M.m1_lleno_laxo.mean():.0%}", ""])
tabla(["orden", "se llena", "mediana del tiempo hasta llenarse"], fil)
fil = []
for tr, g in M.groupby("tramo", observed=True):
    fil.append([tr, len(g), f"{g.m1_lleno.mean():.0%}"])
for mo, g in M.groupby("modelo"):
    fil.append([mo, len(g), f"{g.m1_lleno.mean():.0%}"])
tabla(["tramo / modelo", "señales", "se llena (principal)"], fil)

p("## Resultado por operación\n")
p("Ganancia = (venta − compra) / compra. t = media / error estándar agrupado por evento. Las filas taker usan las "
  "mismas señales y la misma salida, cambiando sólo la entrada.\n")
fil = []
for nom, desc in (("m1", "maker, W − 1 ¢"), ("m0", "maker, W"), ("m2", "maker, W − 2 ¢")):
    g = M[M[f"{nom}_lleno"]]
    for col, sal in (("r6", "taker a W + 6 h (principal)"), ("r3", "taker a W + 3 h"),
                     ("rf3", "taker 3 h después del llenado"), ("rmk", "maker a W + 6 h + 1 ¢ (si no, taker a 9 h)"),
                     ("rfin", "quedarse hasta la resolución")):
        mu, se, n = media_cluster(g[f"{nom}_{col}"].values, g.evento.values)
        a, b, n = fmt(mu, se, n)
        m1 = g[g.mitad == 1][f"{nom}_{col}"].mean()
        m2 = g[g.mitad == 2][f"{nom}_{col}"].mean()
        fil.append([desc, sal, n, a, b, f"{100 * m1:+.1f}%" if not np.isnan(m1) else "-",
                    f"{100 * m2:+.1f}%" if not np.isnan(m2) else "-"])
for col, sal in (("rt_6", "taker a W + 6 h"), ("rt_3", "taker a W + 3 h")):
    mu, se, n = media_cluster(M[col].values, M.evento.values)
    a, b, n = fmt(mu, se, n)
    fil.append(["taker (compra en W)", sal, n, a, b, f"{100 * M[M.mitad == 1][col].mean():+.1f}%",
                f"{100 * M[M.mitad == 2][col].mean():+.1f}%"])
tabla(["entrada", "salida", "operaciones", "ganancia media", "t", "1ª mitad", "2ª mitad"], fil)

p("## Selección adversa: ¿qué pasó con las órdenes que no se llenaron?\n")
p("Movimiento del precio de la caja de W a W + 6 h (sin costos), según si la orden principal se llenó o no.\n")
fil = []
for nom, g in (("se llenó", M[M.m1_lleno]), ("no se llenó", M[~M.m1_lleno])):
    mu, se, n = media_cluster(g.subio_6.values, g.evento.values)
    a, b, n = fmt(mu, se, n)
    fil.append([nom, n, a, b, f"{100 * g.p_W.mean():.1f} ¢", f"{100 * g.final.mean():.1f} ¢"])
tabla(["orden principal", "señales", "precio W → W+6 h", "t", "precio en W", "pago final medio"], fil)

p("## Por tramo de precio y modelo (entrada principal, salida principal)\n")
fil = []
g1 = M[M.m1_lleno]
for k, g in list(g1.groupby("tramo", observed=True)) + list(g1.groupby("modelo")):
    mu, se, n = media_cluster(g.m1_r6.values, g.evento.values)
    a, b, n = fmt(mu, se, n)
    fil.append([k, n, a, b])
tabla(["tramo / modelo", "operaciones", "ganancia media", "t"], fil)

mu, se, n = media_cluster(g1.m1_r6.values, g1.evento.values)
m1, m2 = g1[g1.mitad == 1].m1_r6.mean(), g1[g1.mitad == 2].m1_r6.mean()
ll = M.m1_lleno.mean()
ok1 = n >= 150 and mu >= 0.02 and se > 0 and mu / se >= 2
ok2 = m1 > 0 and m2 > 0
ok3 = ll >= 0.30
p("## Criterio de éxito\n")
p(f"1. ≥ +2 % por operación llenada, t ≥ 2, ≥ 150 llenadas: **{'sí' if ok1 else 'no'}** "
  f"({100 * mu:+.1f}%, t {mu / se:+.1f} , {n} ops).")
p(f"2. Positiva en las dos mitades: **{'sí' if ok2 else 'no'}** ({100 * m1:+.1f}% / {100 * m2:+.1f}%).")
p(f"3. Tasa de llenado ≥ 30 %: **{'sí' if ok3 else 'no'}** ({ll:.0%}).\n")

with open(os.path.join(CARPETA, "informe_maker.md"), "w") as f:
    f.write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

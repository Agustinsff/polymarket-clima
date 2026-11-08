"""
Pronóstico propio como filtro maker (regla: propio_maker/REGLA.md). Escribe propio_maker/informe.md.
Uso: python propio_maker/analizar.py RUTA/probs_cajas.csv.gz RUTA/maker/datos/llenados.csv
"""
import os
import sys

import numpy as np
import pandas as pd

PROBS, LL = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(3)
H0, H1 = pd.Timestamp("2026-11-02 22:25", tz="UTC").timestamp(), pd.Timestamp("2026-11-07 23:20", tz="UTC").timestamp()
L = []
p = lambda s="": L.append(s)

pr = pd.read_csv(PROBS)
pr["t_mod"] = pd.to_datetime(pr.momento_utc, utc=True).astype("int64") // 10**9
pr = pr.sort_values("t_mod").drop_duplicates("condition_id", keep="first")[["condition_id", "t_mod", "p_modelo", "fecha", "serie"]]
ll = pd.read_csv(LL, sep=";")
ll = ll[(ll.grupo == "clima") & (ll.precio_nuestro >= 0.03) & (ll.precio_nuestro <= 0.97)]
ll = ll[(ll.ts_foto < H0) | (ll.ts_foto >= H1)]
ll = ll.merge(pr, left_on="cid", right_on="condition_id", how="inner")
ll = ll[(ll.ts_foto >= ll.t_mod) & ll.gano.notna()].copy()
ll["signo"] = np.where(ll.lado == "compra", 1, -1)
ll["pnl"] = ll.signo * (ll.gano - ll.precio_nuestro) * ll.acciones + ll.reembolso
ll["acuerdo"] = np.where(ll.lado == "compra", ll.p_modelo > ll.precio_nuestro, ll.p_modelo < ll.precio_nuestro)

p(f"# Pronóstico propio como filtro maker (corte {pd.Timestamp.now('UTC'):%Y-%m-%d %H:%M} UTC)")
p()
p(f"Regla fija: `propio_maker/REGLA.md`. Llenados simulados resueltos sobre cajas con probabilidad del modelo (prueba B, "
  f"día anterior), posteriores a esa probabilidad y fuera del hueco 2-nov 22:25Z → 7-nov 23:20Z: {len(ll):,} llenados, "
  f"{ll.acciones.sum():,.0f} acciones, {ll.fecha.nunique()} fechas de evento, {ll.serie_x.nunique()} series.")
p()
fechas = ll.fecha.unique()
p("| orden | grupo | llenados | acciones | resultado ¢/acción (con reembolso) | intervalo 95 % |")
p("|---|---|---|---|---|---|")
res = {}
for d in (1, 2):
    x = ll[ll.dist_c == d]
    agg = x.groupby(["fecha", "acuerdo"]).agg(pnl=("pnl", "sum"), acc=("acciones", "sum")).unstack(fill_value=0).reindex(fechas, fill_value=0)
    P1, A1 = agg[("pnl", True)].values, agg[("acc", True)].values
    P0, A0 = agg[("pnl", False)].values, agg[("acc", False)].values
    W = np.vstack([np.ones(len(fechas))] + [np.bincount(rng.integers(0, len(fechas), len(fechas)), minlength=len(fechas)) for _ in range(2000)])
    de = (W @ P1) / (W @ A1) * 100
    en = (W @ P0) / (W @ A0) * 100
    to = (W @ (P0 + P1)) / (W @ (A0 + A1)) * 100
    for nom, v, n, a in (("de acuerdo", de, x.acuerdo.sum(), A1.sum()), ("en desacuerdo", en, (~x.acuerdo).sum(), A0.sum()),
                         ("todas", to, len(x), A0.sum() + A1.sum())):
        p(f"| {d} ¢ | {nom} | {n:,} | {a:,.0f} | {v[0]:+.2f} | [{np.percentile(v[1:], 2.5):+.2f}, {np.percentile(v[1:], 97.5):+.2f}] |")
    res[d] = (de[0] - to[0], np.percentile(de[1:] - to[1:], [2.5, 97.5]), de[0] - en[0], (de[1:] - en[1:] <= 0).mean())
p()
for d in (1, 2):
    r = res[d]
    p(f"- Orden a {d} ¢: de acuerdo − todas = {r[0]:+.2f} ¢/acción [{r[1][0]:+.2f}, {r[1][1]:+.2f}]; "
      f"de acuerdo − en desacuerdo = {r[2]:+.2f} ¢, P(≤0) = {r[3]:.3f}.")
r = res[2]
sirve = r[0] >= 1 and r[3] < 0.05
p()
p(f"**Veredicto según la regla: {'SIRVE como filtro' if sirve else 'NO SIRVE como filtro'}** (pide, a 2 ¢, ≥ +1 ¢ sobre todas y "
  "P < 5 % contra en desacuerdo).")
p()
p("Límites: llenados simulados (cuenta prudente del medidor), una sola foto del modelo por caja (día anterior), "
  "y pocas fechas de evento.")
with open(os.path.join(AQUI, "informe.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")
print("\n".join(L))

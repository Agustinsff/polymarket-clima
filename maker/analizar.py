"""
Analisis del medidor maker (ver maker/REGLA.md). Lee maker/datos/ y escribe maker/informe_datos.md.
No necesita Polymarket: corre en cualquier lado.  Uso: python maker/analizar.py
"""

import glob
import gzip
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "informe_datos.md")
TAM = 100
L = []


def p(s=""):
    L.append(s)


def tabla(df, cols, fmt):
    p("| " + " | ".join(cols) + " |")
    p("|" + "---|" * len(cols))
    for _, r in df.iterrows():
        p("| " + " | ".join(fmt[c](r[c]) if c in fmt else str(r[c]) for c in cols) + " |")
    p()


f0 = lambda x: f"{x:.0f}"
f1 = lambda x: f"{x:.1f}"
f2 = lambda x: f"{x:.2f}"
pc = lambda x: f"{x * 100:+.1f} %"
s = lambda x: str(x)

# ---------------------------------------------------------------- fotos
fotos = pd.concat([pd.read_csv(f, sep=";", compression="gzip") for f in sorted(glob.glob(os.path.join(C, "fotos_*.csv.gz")))],
                  ignore_index=True)
fotos = fotos[(fotos.medio >= 0.03) & (fotos.medio <= 0.97)].copy()
fotos["dia"] = pd.to_datetime(fotos.ts, unit="s").dt.strftime("%Y-%m-%d")
fotos["vivo"] = fotos.horas_hasta_fin > 0
n_fotos = fotos.groupby("grupo").ts.nunique()
dias = fotos.dia.nunique()
desde, hasta = datetime.fromtimestamp(fotos.ts.min(), timezone.utc), datetime.fromtimestamp(fotos.ts.max(), timezone.utc)

p(f"# Medidor maker: datos al {hasta:%Y-%m-%d %H:%M} UTC")
p()
p(f"Fotos del libro cada 5 min desde {desde:%Y-%m-%d %H:%M} UTC: {fotos.ts.nunique()} fotos, {dias} días, "
  f"{len(fotos):,} cajas-foto con precio entre 3 y 97 ¢ (clima {int((fotos.grupo == 'clima').sum()):,}, "
  f"cripto {int((fotos.grupo == 'cripto').sum()):,}). Regla fija: maker/REGLA.md.")
p()

# 1. pozos
p("## 1. Pozos de recompensa (lo que reparte Polymarket por día)")
p()
g = fotos[fotos.vivo].groupby(["grupo", "ts"]).agg(cajas=("cid", "nunique"), con_pozo=("pozo", lambda x: (x > 0).sum()),
                                                    pozo=("pozo", "sum")).groupby("grupo").mean().reset_index()
p("Promedio por foto (solo cajas cuyo evento todavía no terminó):")
p()
tabla(g, ["grupo", "cajas", "con_pozo", "pozo"], {"cajas": f0, "con_pozo": f0, "pozo": f0})
p("`pozo` = suma de US$/día que reparten las cajas vivas de ese grupo entre todos los makers.")
p()

# 2. recompensa estimada
p("## 2. Recompensa estimada si tuviéramos 100 acciones por lado en TODAS las cajas vivas")
p()
for d in (1, 2):
    col = f"rec_{d}c"
    por_foto = fotos[fotos.vivo].groupby(["grupo", "ts"])[col].sum().groupby("grupo").agg(["mean", "median", "min", "max"]).reset_index()
    p(f"**Orden a {d} ¢ del medio** (US$/día, suma de todas las cajas vivas; promedio, mediana, mín y máx de las fotos):")
    p()
    tabla(por_foto, ["grupo", "mean", "median", "min", "max"], {"mean": f1, "median": f1, "min": f1, "max": f1})
v = fotos[fotos.vivo & (fotos.pozo > 0)].copy()
v["solos"] = v.comp == 0
v["cap"] = TAM  # 100 acciones por lado ≈ US$ 100 de colateral por caja
r = v.groupby("grupo").agg(cajas_con_pozo=("cid", lambda x: x.nunique()), rec_media_caja=("rec_1c", "mean"),
                           pct_solos=("solos", "mean"), comp_mediana=("comp", "median")).reset_index()
p("Por caja con pozo (orden a 1 ¢): recompensa media por caja-día, % de fotos en que no hay ningún otro maker "
  "dentro del spread premiado (`solos`) y competencia mediana (puntaje de los demás):")
p()
tabla(r, ["grupo", "cajas_con_pozo", "rec_media_caja", "pct_solos", "comp_mediana"],
      {"rec_media_caja": f2, "pct_solos": pc, "comp_mediana": f0})
p(f"Capital: 100 acciones por lado inmovilizan ≈ US$ {TAM} por caja. Recompensa por US$ 100 de capital y día = "
  f"la columna `rec_media_caja`.")
p()
# por horas hasta el fin y hora local (clima, 1c)
cl = v[v.grupo == "clima"].copy()
cl["tramo"] = pd.cut(cl.horas_hasta_fin, [0, 6, 12, 24, 36, 48, 1000], labels=["0-6 h", "6-12 h", "12-24 h", "24-36 h", "36-48 h", ">48 h"])
t = cl.groupby("tramo", observed=True).agg(cajas_foto=("cid", "size"), rec=("rec_1c", "mean"), pozo=("pozo", "mean"),
                                           solos=("solos", "mean")).reset_index()
p("Clima, por horas hasta el cierre del evento (orden a 1 ¢, por caja con pozo):")
p()
tabla(t, ["tramo", "cajas_foto", "pozo", "rec", "solos"], {"rec": f2, "pozo": f1, "solos": pc})
cl["hl"] = pd.cut(cl.hora_local, [-1, 5, 11, 17, 23], labels=["0-5 h", "6-11 h", "12-17 h", "18-23 h"])
t = cl.groupby("hl", observed=True).agg(cajas_foto=("cid", "size"), rec=("rec_1c", "mean"), solos=("solos", "mean")).reset_index()
p("Clima, por hora local de la ciudad:")
p()
tabla(t, ["hl", "cajas_foto", "rec", "solos"], {"rec": f2, "solos": pc})
t = cl.groupby("serie").agg(cajas_foto=("cid", "size"), rec=("rec_1c", "mean"), pozo=("pozo", "mean"), solos=("solos", "mean")).reset_index()
t = t.sort_values("rec", ascending=False).head(12)
p("Clima, las 12 series con más recompensa por caja (orden a 1 ¢):")
p()
tabla(t, ["serie", "cajas_foto", "pozo", "rec", "solos"], {"rec": f2, "pozo": f1, "solos": pc})

# ---------------------------------------------------------------- llenados
ll = pd.read_csv(os.path.join(C, "llenados.csv"), sep=";")
ll = ll[(ll.medio_foto >= 0.03) & (ll.medio_foto <= 0.97)].copy()
ll["dia"] = pd.to_datetime(ll.ts, unit="s").dt.strftime("%Y-%m-%d")
ll["signo"] = np.where(ll.lado == "compra", 1, -1)      # compra = largo del Yes
ll["costo"] = ll.signo * ll.precio_nuestro * ll.acciones
# marca a mercado: medio de la caja a +5/+30/+60 min (primera foto después)
fm = fotos[["cid", "ts", "medio"]].sort_values("ts")
for m in (5, 30, 60):
    q = ll[["cid", "ts"]].copy()
    q["t"] = q.ts + m * 60
    q = q.sort_values("t")
    j = pd.merge_asof(q, fm.rename(columns={"ts": "t", "medio": f"medio_{m}"}), on="t", by="cid", direction="forward",
                      tolerance=20 * 60)
    ll[f"medio_{m}"] = j[f"medio_{m}"].values
    ll[f"pnl_{m}"] = ll.signo * (ll[f"medio_{m}"] - ll.precio_nuestro) * ll.acciones
ll["pnl_res"] = np.where(ll.gano.isna(), np.nan, ll.signo * (ll.gano.fillna(0) - ll.precio_nuestro) * ll.acciones)
ll["pnl_res_pct"] = ll.pnl_res / (ll.precio_nuestro * ll.acciones).where(ll.signo > 0, (1 - ll.precio_nuestro) * ll.acciones)
res = ll[ll.pnl_res.notna()]

p("## 3. Llenados simulados (alguien operó a peor precio que nuestra orden)")
p()
p(f"{len(ll):,} llenados en {dias} días; {len(res):,} ya resueltos. Por grupo y distancia de la orden, por día de medición:")
p()
t = ll.groupby(["grupo", "dist_c"]).agg(llenados=("ts", "size"), acciones=("acciones", "sum"), reembolso=("reembolso", "sum"),
                                        pnl_5=("pnl_5", "sum"), pnl_60=("pnl_60", "sum")).reset_index()
t2 = res.groupby(["grupo", "dist_c"]).agg(resueltos=("ts", "size"), acc_res=("acciones", "sum"), pnl_res=("pnl_res", "sum")).reset_index()
t = t.merge(t2, on=["grupo", "dist_c"], how="left")
for c in ("llenados", "acciones", "reembolso", "pnl_5", "pnl_60", "pnl_res", "acc_res"):
    t[c + "_d"] = t[c] / dias
t["pnl_res_acc"] = t.pnl_res / t.acc_res * 100
t["pnl_60_acc"] = t.pnl_60 / t.acciones * 100
tabla(t, ["grupo", "dist_c", "llenados_d", "acciones_d", "reembolso_d", "pnl_5_d", "pnl_60_d", "pnl_res_d", "pnl_60_acc", "pnl_res_acc"],
      {"llenados_d": f0, "acciones_d": f0, "reembolso_d": f2, "pnl_5_d": f1, "pnl_60_d": f1, "pnl_res_d": f1,
       "pnl_60_acc": f2, "pnl_res_acc": f2})
p("`pnl_60_d` = US$/día que vale lo llenado 60 min después (precio medio del libro) menos lo que pagamos; "
  "`pnl_res_d` = lo mismo a la resolución, solo de los ya resueltos (`_acc` = centavos por acción).")
p()
# t de student del pnl por resolucion por llenado (clima 1c)
for gr in ("clima", "cripto"):
    for d in (1, 2):
        x = res[(res.grupo == gr) & (res.dist_c == d)].pnl_res_pct.dropna()
        if len(x) > 10:
            tt = x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
            p(f"- {gr}, orden a {d} ¢: resultado por llenado {x.mean() * 100:+.1f} % del capital de esa orden (t = {tt:.1f}, n = {len(x):,}).")
p()
# por lado y por precio
res1 = res[(res.grupo == "clima") & (res.dist_c == 1)].copy()
res1["tramo_p"] = pd.cut(res1.precio_nuestro, [0, 0.1, 0.3, 0.7, 0.9, 1], labels=["3-10 ¢", "10-30 ¢", "30-70 ¢", "70-90 ¢", "90-97 ¢"])
t = res1.groupby(["lado", "tramo_p"], observed=True).agg(n=("ts", "size"), acc=("acciones", "sum"), pnl=("pnl_res", "sum"),
                                                         pnl_pct=("pnl_res_pct", "mean")).reset_index()
t["pnl_acc"] = t.pnl / t.acc * 100
p("Clima, orden a 1 ¢, resueltos, por lado y precio de nuestra orden:")
p()
tabla(t, ["lado", "tramo_p", "n", "acc", "pnl", "pnl_acc", "pnl_pct"], {"acc": f0, "pnl": f1, "pnl_acc": f2, "pnl_pct": pc})

# ---------------------------------------------------------------- neto
p("## 4. Neto diario (recompensa + reembolso + resultado de los llenados)")
p()
p("Con 100 acciones por lado en todas las cajas vivas con precio 3–97 ¢ (es lo que simula la regla), por día de medición:")
p()
filas = []
for gr in ("clima", "cripto"):
    for d in (1, 2):
        rec = fotos[fotos.vivo & (fotos.grupo == gr)].groupby("ts")[f"rec_{d}c"].sum().mean()
        sub = ll[(ll.grupo == gr) & (ll.dist_c == d)]
        subr = res[(res.grupo == gr) & (res.dist_c == d)]
        reemb = sub.reembolso.sum() / dias
        pnl60 = sub.pnl_60.sum() / dias
        # resultado a la resolucion escalado: pnl por accion resuelta x acciones llenadas por dia
        pnl_res_acc = subr.pnl_res.sum() / subr.acciones.sum() if subr.acciones.sum() else np.nan
        pnlres = pnl_res_acc * sub.acciones.sum() / dias
        cajas = fotos[fotos.vivo & (fotos.grupo == gr)].groupby("ts").cid.nunique().mean()
        filas.append({"grupo": gr, "dist_c": d, "recompensa": rec, "reembolso": reemb, "llenados_60min": pnl60,
                      "llenados_resol": pnlres, "neto_60": rec + reemb + pnl60, "neto_resol": rec + reemb + pnlres,
                      "cajas": cajas, "capital": cajas * TAM})
t = pd.DataFrame(filas)
tabla(t, ["grupo", "dist_c", "recompensa", "reembolso", "llenados_60min", "llenados_resol", "neto_60", "neto_resol", "cajas", "capital"],
      {"recompensa": f1, "reembolso": f2, "llenados_60min": f1, "llenados_resol": f1, "neto_60": f1, "neto_resol": f1,
       "cajas": f0, "capital": f0})
p("US$/día. `capital` = colateral inmovilizado (≈ US$ 100 por caja). `neto_resol` usa el resultado por acción de los "
  "llenados ya resueltos aplicado a todas las acciones llenadas.")
p()
# neto por dia (serie) clima 1c
p("Clima, orden a 1 ¢, día por día (recompensa estimada, llenados a 60 min, neto a 60 min):")
p()
rd = fotos[fotos.vivo & (fotos.grupo == "clima")].groupby(["dia", "ts"]).rec_1c.sum().groupby("dia").mean()
ld = ll[(ll.grupo == "clima") & (ll.dist_c == 1)].groupby("dia").agg(acc=("acciones", "sum"), pnl60=("pnl_60", "sum"), reemb=("reembolso", "sum"))
t = pd.concat([rd.rename("recompensa"), ld], axis=1).fillna(0).reset_index()
t["neto_60"] = t.recompensa + t.reemb + t.pnl60
tabla(t, ["dia", "recompensa", "acc", "reemb", "pnl60", "neto_60"], {"recompensa": f1, "acc": f0, "reemb": f2, "pnl60": f1, "neto_60": f1})
x = t.neto_60
if len(x) > 2:
    p(f"Neto a 60 min: {x.mean():+.1f} US$/día, t = {x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):.1f} con {len(x)} días.")
p()

# cajas con pozo y sin llenados: donde la recompensa viene "gratis"?
p("## 5. ¿Dónde conviene? Recompensa menos llenados por caja-día (clima, 1 ¢, a 60 min)")
p()
rc = v[v.grupo == "clima"].groupby(["serie", "evento", "cid"]).agg(rec=("rec_1c", "mean"), fotos=("ts", "size")).reset_index()
rc["dias_caja"] = rc.fotos / 288
lc = ll[(ll.grupo == "clima") & (ll.dist_c == 1)].groupby("cid").agg(pnl60=("pnl_60", "sum"), reemb=("reembolso", "sum"), acc=("acciones", "sum")).reset_index()
rc = rc.merge(lc, on="cid", how="left").fillna({"pnl60": 0, "reemb": 0, "acc": 0})
rc["neto"] = rc.rec * rc.dias_caja + rc.reemb + rc.pnl60
t = rc.groupby("serie").agg(cajas=("cid", "size"), rec=("rec", "mean"), neto_caja=("neto", "mean"), dias=("dias_caja", "mean")).reset_index()
t["neto_dia"] = t.neto_caja / t.dias
t = t.sort_values("neto_dia", ascending=False)
p("Mejores y peores series (neto por caja y día):")
p()
tabla(pd.concat([t.head(8), t.tail(5)]), ["serie", "cajas", "rec", "neto_dia"], {"rec": f2, "neto_dia": f2})
pos = (t.neto_dia > 0).sum()
p(f"{pos} de {len(t)} series con neto positivo por caja-día.")
p()

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("\n".join(L))

# ---------------------------------------------------------------- por spread del libro
p("## 6. Por ancho del libro (spread real bid-ask al momento de poner la orden), clima")
p()
p("Las órdenes a 1 ¢ del medio en un libro de 40 ¢ de ancho quedan muy adentro: el medio no es el precio justo. "
  "Esto separa los libros apretados (donde el medio sí vale algo) de los anchos.")
p()
fotos["spread_c"] = (fotos.ask - fotos.bid) * 100
fotos["tramo_s"] = pd.cut(fotos.spread_c, [0, 2, 5, 10, 20, 100], labels=["≤2 ¢", "2-5 ¢", "5-10 ¢", "10-20 ¢", ">20 ¢"])
def punt(v, s_):
    return np.where((s_ >= 0) & (s_ < v) & (v > 0), ((v - s_) / v.where(v > 0, 1)) ** 2, 0.0)


for d in (1, 2):
    # recompensa "pesimista": los rivales copian nuestra orden (la competencia suma otro tanto como lo nuestro)
    tam = np.maximum(TAM, fotos.tam_min)
    nuestro = np.minimum(punt(fotos.spread_max, fotos.medio - fotos[f"nbid_{d}c"]),
                         punt(fotos.spread_max, fotos[f"nask_{d}c"] - fotos.medio)) * tam
    comp = pd.to_numeric(fotos.comp, errors="coerce").fillna(0)
    fotos[f"pes_{d}c"] = np.where((fotos.pozo > 0) & (nuestro > 0), fotos.pozo * nuestro / (2 * nuestro + comp), 0.0)
vc = fotos[fotos.vivo & (fotos.grupo == "clima")]
key = fotos[["cid", "ts", "tramo_s", "spread_c"]].rename(columns={"ts": "ts_foto"})
llc = ll[(ll.grupo == "clima")].merge(key, on=["cid", "ts_foto"], how="left")
for d in (1, 2):
    filas = []
    for tr in vc.tramo_s.cat.categories:
        sub = vc[vc.tramo_s == tr]
        rec = sub.groupby("ts")[f"rec_{d}c"].sum().reindex(vc.ts.unique(), fill_value=0).mean()
        pes = sub.groupby("ts")[f"pes_{d}c"].sum().reindex(vc.ts.unique(), fill_value=0).mean()
        cajas = sub.groupby("ts").cid.nunique().reindex(vc.ts.unique(), fill_value=0).mean()
        f = llc[(llc.tramo_s == tr) & (llc.dist_c == d)]
        fr = f[f.pnl_res.notna()]
        pnl_acc = fr.pnl_res.sum() / fr.acciones.sum() if fr.acciones.sum() else np.nan
        pnlres = pnl_acc * f.acciones.sum() / dias
        filas.append({"spread": str(tr), "cajas": cajas, "recompensa": rec, "acciones_d": f.acciones.sum() / dias,
                      "pnl_res_acc": pnl_acc * 100, "llenados_resol": pnlres, "reemb": f.reembolso.sum() / dias,
                      "neto": rec + pnlres + f.reembolso.sum() / dias, "capital": cajas * TAM,
                      "rec_pes": pes, "neto_pes": pes + pnlres + f.reembolso.sum() / dias})
    t = pd.DataFrame(filas)
    t["neto_por_100"] = t.neto / t.cajas
    p(f"**Orden a {d} ¢** (US$/día):")
    p()
    tabla(t, ["spread", "cajas", "capital", "recompensa", "rec_pes", "acciones_d", "pnl_res_acc", "llenados_resol", "reemb", "neto", "neto_pes", "neto_por_100"],
          {"cajas": f0, "capital": f0, "recompensa": f1, "rec_pes": f1, "acciones_d": f0, "pnl_res_acc": f2, "llenados_resol": f1,
           "reemb": f2, "neto": f1, "neto_pes": f1, "neto_por_100": f2})
p("`rec_pes` / `neto_pes` = recompensa y neto si los otros makers copian nuestra orden (la competencia suma otro tanto "
  "como lo nuestro): es lo que pasa cuando los bots rivales se acomodan. `neto_por_100` = neto diario (optimista) por cada US$ 100 de capital (una caja). Spread mediano del libro en clima: "
  f"{vc.spread_c.median():.1f} ¢; {(vc.spread_c <= 2).mean() * 100:.0f} % de las cajas-foto con spread ≤ 2 ¢.")
p()

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

# ---------------------------------------------------------------- dia por dia, libros apretados, pesimista
p("## 7. Día por día: clima, libros con spread ≤ 5 ¢, orden a 2 ¢, recompensa pesimista")
p()
ap = vc[vc.spread_c <= 5]
f = llc[(llc.spread_c <= 5) & (llc.dist_c == 2)]
fr = f[f.pnl_res.notna()]
pnl_acc = fr.pnl_res.sum() / fr.acciones.sum()
rd = ap.groupby(["dia", "ts"]).pes_2c.sum().groupby("dia").mean()
cd = ap.groupby(["dia", "ts"]).cid.nunique().groupby("dia").mean()
fd = f.groupby("dia").agg(acc=("acciones", "sum"), reemb=("reembolso", "sum"))
t = pd.concat([rd.rename("rec_pes"), cd.rename("cajas"), fd], axis=1).fillna(0).reset_index()
t["llenados_resol"] = t.acc * pnl_acc
t["neto_pes"] = t.rec_pes + t.reemb + t.llenados_resol
t["por_100"] = t.neto_pes / t.cajas
tabla(t, ["dia", "cajas", "rec_pes", "acc", "reemb", "llenados_resol", "neto_pes", "por_100"],
      {"cajas": f0, "rec_pes": f1, "acc": f0, "reemb": f2, "llenados_resol": f1, "neto_pes": f1, "por_100": f2})
x = t.por_100
p(f"Neto pesimista por US$ 100 de capital: {x.mean():+.2f} US$/día, t = {x.mean() / (x.std(ddof=1) / np.sqrt(len(x))):.1f} "
  f"con {len(x)} días (el resultado de los llenados usa el promedio por acción de todos los resueltos, {pnl_acc * 100:.2f} ¢).")
p()
p("Lo que NO está en estos números: que Polymarket mide cada minuto y nosotros cada 5 (recompensa optimista); que los "
  "rivales pueden apretar más que 'copiarnos'; que las fotos son del libro visible (no se ven las órdenes que entran y "
  "salen entre fotos); gas y el día que una ciudad se dispute. Lo único que lo confirma es cobrar de verdad.")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

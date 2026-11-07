"""
Efecto de la comisión nueva en temperatura (regla: comision/REGLA.md).
Lee las fotos y llenados del medidor maker (rama medidor-maker) y escribe comision/informe.md.
Uso: python comision/analizar.py RUTA/maker/datos
"""
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

C = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "informe.md")
TAM = 100
FOTOS_DIA = 288
rng = np.random.default_rng(1)
L = []
p = lambda s="": L.append(s)
MES = {"october": 10, "november": 11}


def fecha_evento(slug):
    m = re.search(r"-on-([a-z]+)-(\d+)-(\d{4})$", slug)
    return pd.Timestamp(int(m.group(3)), MES[m.group(1)], int(m.group(2))) if m and m.group(1) in MES else pd.NaT


cols = ["ts", "grupo", "serie", "evento", "cid", "horas_hasta_fin", "tasa", "pozo", "spread_max", "tam_min", "medio",
        "bid", "ask", "comp", "nbid_2c", "nask_2c"]
fotos = pd.concat([pd.read_csv(f, sep=";", compression="gzip", usecols=cols) for f in sorted(glob.glob(os.path.join(C, "fotos_*.csv.gz")))],
                  ignore_index=True)
fotos = fotos[(fotos.medio >= 0.03) & (fotos.medio <= 0.97) & (fotos.horas_hasta_fin > 0)].copy()
fotos["spread_c"] = (fotos.ask - fotos.bid) * 100
fotos["comp"] = pd.to_numeric(fotos.comp, errors="coerce").fillna(0)
fotos["tramo"] = pd.cut(fotos.horas_hasta_fin, [0, 12, 24, 36, 48], labels=["0-12 h", "12-24 h", "24-36 h", "36-48 h"])
cr = fotos[fotos.grupo == "cripto"].copy()
cl = fotos[fotos.grupo == "clima"].copy()
cl["fecha"] = cl.evento.map(fecha_evento)
cl = cl[cl.fecha >= "2026-10-26"]
T0 = pd.Timestamp("2026-11-01 04:37", tz="UTC").timestamp()  # primera foto con tasa 0,05: 04:40Z; última con 0: 04:35Z
cl["con"] = cl.ts >= T0
cl["tipo"] = cl.serie.str.split("|").str[0]
cl["ciudad"] = cl.serie.str.split("|").str[1]
cl = cl[cl.tramo.notna()]
incoh = ((cl.tasa > 0) != cl.con).mean()
cl["u"] = list(zip(cl.fecha, cl.con))
# Hueco de llenados: Polymarket retiró data-api v1 (/trades) y el medidor no registró llenados del 2-nov 22:25Z al
# 7-nov ~23:20Z (arreglado en medidor-maker 1c72d4b4). Esas fotos no cuentan como exposición en las secciones 3 y 4.
HUECO = (pd.Timestamp("2026-11-02 22:30", tz="UTC").timestamp(), pd.Timestamp("2026-11-07 23:20", tz="UTC").timestamp())
cl["hueco"] = (cl.ts >= HUECO[0]) & (cl.ts < HUECO[1])


# puntaje pesimista a 2 ¢ (misma cuenta que maker/analizar.py, sección 6-7)
def punt(v, s_):
    return np.where((s_ >= 0) & (s_ < v) & (v > 0), ((v - s_) / v.where(v > 0, 1)) ** 2, 0.0)


tam = np.maximum(TAM, cl.tam_min)
nuestro = np.minimum(punt(cl.spread_max, cl.medio - cl.nbid_2c), punt(cl.spread_max, cl.nask_2c - cl.medio)) * tam
cl["pes_2c"] = np.where((cl.pozo > 0) & (nuestro > 0), cl.pozo * nuestro / (2 * nuestro + cl.comp), 0.0)

ll = pd.read_csv(os.path.join(C, "llenados.csv"), sep=";")
ll = ll[(ll.grupo == "clima") & (ll.medio_foto >= 0.03) & (ll.medio_foto <= 0.97)].copy()
ll["signo"] = np.where(ll.lado == "compra", 1, -1)
ll["pnl_res"] = np.where(ll.gano.isna(), np.nan, ll.signo * (ll.gano.fillna(0) - ll.precio_nuestro) * ll.acciones)
key = cl[["cid", "ts", "spread_c", "tramo", "fecha", "con", "tipo", "ciudad", "u"]].rename(columns={"ts": "ts_foto"})
ll = ll.merge(key, on=["cid", "ts_foto"], how="inner")

fechas_sin = sorted(set(cl[~cl.con].u))
fechas_con = sorted(set(cl[cl.con].u))
NB = 2000

# celdas por fecha de evento (el bootstrap remuestrea fechas, no filas)
celda = cl.groupby(["u", "tipo", "ciudad", "tramo"], observed=True).agg(
    spread=("spread_c", "median"), comp=("comp", "median"), pozo=("pozo", "mean"), n=("cid", "size")).reset_index()


def muestras():
    yield fechas_sin, fechas_con
    for _ in range(NB):
        yield [fechas_sin[i] for i in rng.integers(0, len(fechas_sin), len(fechas_sin))], [fechas_con[i] for i in rng.integers(0, len(fechas_con), len(fechas_con))]


def dif_ciudad(col, filtro):
    c = filtro(celda)
    # por ciudad y fecha: promedio de los tramos elegidos
    cf = c.groupby(["tipo", "ciudad", "u"])[col].mean().unstack(["tipo", "ciudad"])  # fecha x ciudad
    vals = []
    for fs, fc in muestras():
        d = cf.reindex(fc).mean() - cf.reindex(fs).mean()
        vals.append(d.dropna().mean())
    lo, hi = np.nanpercentile(vals[1:], [2.5, 97.5])
    return vals[0], lo, hi


def boot_sumas(tabla_fecha, fun):
    """tabla_fecha: DataFrame indexado por fecha con columnas sumables; fun(sumas_sin, sumas_con) -> número."""
    vals = []
    for fs, fc in muestras():
        vals.append(fun(tabla_fecha.reindex(fs).fillna(0).sum(), tabla_fecha.reindex(fc).fillna(0).sum()))
    lo, hi = np.nanpercentile(vals[1:], [2.5, 97.5])
    return vals[0], lo, hi


fmt = lambda e: f"{e[0]:+.2f} [{e[1]:+.2f}, {e[2]:+.2f}]"
hoy = pd.Timestamp.now("UTC")
p(f"# Efecto de la comisión nueva en temperatura (corte {hoy:%Y-%m-%d %H:%M} UTC)")
p()
p("Regla fija: `comision/REGLA.md`. Datos: medidor maker (fotos cada 5 min, llenados simulados). "
  "La comisión se prendió para todas las cajas abiertas a la vez, el 1-nov-2026 a las 04:37 UTC (última foto con tasa 0: "
  "04:35Z; primera con 0,05: 04:40Z). Sin comisión = fotos antes de esa hora; con = después. "
  f"Fechas de evento: {len(fechas_sin)} sin y {len(fechas_con)} con (los eventos del 31-oct al 2-nov tienen fotos en los dos lados; "
  "los últimos todavía sin cerrar). "
  f"Cajas-foto: {(~cl.con).sum():,} sin / {cl.con.sum():,} con. Chequeo: en {incoh * 100:.1f} % de las cajas-foto la tasa "
  "no coincide con la fecha del evento.")
p()
p("Diferencias = con comisión − sin comisión, emparejadas por ciudad y tipo; entre corchetes el intervalo del 95 % "
  "(bootstrap por fecha de evento). Spread, competencia y pozo: valor de cada fecha (mediana de sus cajas-foto), promediado por ciudad.")
p()

# 1. spread
p("## 1. Spread del libro (¢, mediana por caja-foto)")
p()
p("| tipo | tramo | sin | con | diferencia por ciudad |")
p("|---|---|---|---|---|")
res_spread = {}
for tipo in ("highest", "lowest"):
    for tr in cl.tramo.cat.categories:
        filt = lambda d, tipo=tipo, tr=tr: d[(d.tipo == tipo) & (d.tramo == tr)]
        sub = filt(cl)
        if sub.con.sum() < 50 or (~sub.con).sum() < 50:
            continue
        e = dif_ciudad("spread", filt)
        res_spread[(tipo, tr)] = e
        p(f"| {'máximas' if tipo == 'highest' else 'mínimas'} | {tr} | {sub[~sub.con].spread_c.median():.1f} | "
          f"{sub[sub.con].spread_c.median():.1f} | {fmt(e)} |")
p()
corte = T0
cr_d = cr[cr.ts >= corte].spread_c.median() - cr[cr.ts < corte].spread_c.median()
p(f"Control cripto (comisión igual todo el período): spread mediano {cr[cr.ts < corte].spread_c.median():.1f} ¢ antes del "
  f"1-nov 04:37Z y {cr[cr.ts >= corte].spread_c.median():.1f} ¢ después (diferencia {cr_d:+.1f} ¢).")
p()
p("Cajas apretadas (spread ≤ 5 ¢), proporción de cajas-foto:")
p()
for tipo in ("highest", "lowest"):
    s = cl[cl.tipo == tipo]
    p(f"- {'máximas' if tipo == 'highest' else 'mínimas'}: sin {(s[~s.con].spread_c <= 5).mean() * 100:.0f} %, "
      f"con {(s[s.con].spread_c <= 5).mean() * 100:.0f} %.")
p()

# 2. competencia y pozo
p("## 2. Competencia y pozo (máximas, 12–48 h)")
p()
m = lambda d: d[(d.tipo == "highest") & d.tramo.isin(["12-24 h", "24-36 h", "36-48 h"])]
s = m(cl)
e_comp = dif_ciudad("comp", m)
e_pozo = dif_ciudad("pozo", m)
p(f"- Puntaje de rivales en la zona de recompensa (mediana): sin {s[~s.con].comp.median():.0f}, con {s[s.con].comp.median():.0f}; "
  f"diferencia por ciudad {fmt(e_comp)}.")
p(f"- Pozo por caja (US$/día): sin {s[~s.con].pozo.mean():.1f}, con {s[s.con].pozo.mean():.1f}; diferencia por ciudad {fmt(e_pozo)}. "
  f"Cajas con pozo: sin {(s[~s.con].pozo > 0).mean() * 100:.0f} %, con {(s[s.con].pozo > 0).mean() * 100:.0f} %.")
pz = cl.groupby(["con", "fecha"]).apply(lambda d: d.groupby("ts").pozo.sum().mean()).reset_index(name="pozo")
p("- Pozo total por fecha de evento (promedio por foto, todas las cajas vivas):")
p()
p("| fecha | comisión | pozo US$/día |")
p("|---|---|---|")
for _, r in pz.sort_values("fecha").iterrows():
    p(f"| {r.fecha:%d-%b} | {'sí' if r.con else 'no'} | {r.pozo:,.0f} |")
p()


# 3. llenados
p("## 3. Llenados de la orden simulada (máximas y mínimas, todos los tramos)")
p()
lc = ll[ll.con]
p(f"Ojo: el medidor no registró llenados del 2-nov 22:25Z al 7-nov 23:20Z (Polymarket retiró la API vieja de operaciones). "
  f"Esas fotos se sacan de la exposición. Llenados con comisión: del 1-nov 04:37Z en adelante fuera del hueco "
  f"({pd.to_datetime(lc.ts_foto.min(), unit='s'):%d-%b %H:%M} a {pd.to_datetime(lc.ts_foto.max(), unit='s'):%d-%b %H:%M} UTC, "
  f"{lc.acciones.sum():,.0f} acciones).")
p()
p("| orden | grupo | acciones llenadas por caja-día | resultado a la resolución ¢/acción | reembolso ¢/acción | neto ¢/acción | acciones resueltas |")
p("|---|---|---|---|---|---|---|")
for d in (1, 2):
    for con in (False, True):
        f = ll[(ll.dist_c == d) & (ll.con == con)]
        fr = f[f.pnl_res.notna()]
        exp = cl[(cl.con == con) & ~cl.hueco].shape[0] / FOTOS_DIA
        acc_dia = f.acciones.sum() / exp
        pr = fr.pnl_res.sum() / fr.acciones.sum() * 100 if fr.acciones.sum() else np.nan
        rb = f.reembolso.sum() / f.acciones.sum() * 100
        p(f"| {d} ¢ | {'con' if con else 'sin'} | {acc_dia:.1f} | {pr:+.2f} | {rb:.2f} | {pr + rb:+.2f} | {fr.acciones.sum():,.0f} |")
p()


r1 = ll[(ll.dist_c == 1) & ll.pnl_res.notna()].groupby("u").agg(pnl=("pnl_res", "sum"), acc=("acciones", "sum"))
e_ll = boot_sumas(r1, lambda a, b: (b.pnl / b.acc - a.pnl / a.acc) * 100)
p(f"Diferencia del resultado por acción (orden a 1 ¢): {fmt(e_ll)} ¢.")
p()


# 4. neto maker en cajas apretadas
ap = cl[(cl.spread_c <= 5) & ~cl.hueco]
f2 = ll[(ll.dist_c == 2) & (ll.spread_c <= 5)]
tf = pd.concat([ap.groupby("u").agg(fotos=("cid", "size"), pes=("pes_2c", "sum")),
                f2.groupby("u").agg(acc=("acciones", "sum"), reemb=("reembolso", "sum")),
                f2[f2.pnl_res.notna()].groupby("u").agg(pnl=("pnl_res", "sum"), acc_res=("acciones", "sum"))], axis=1).fillna(0)


def neto(sm):
    rec = sm.pes / sm.fotos  # pes_2c ya es US$/día (parte del pozo diario)
    acc = sm.acc / sm.fotos * FOTOS_DIA
    pnl = sm.pnl / sm.acc_res * acc if sm.acc_res else np.nan
    reemb = sm.reemb / sm.fotos * FOTOS_DIA
    return rec, acc, pnl, reemb, rec + pnl + reemb


p("## 4. Neto maker por US$ 100 de capital y día (cajas con spread ≤ 5 ¢, orden a 2 ¢, recompensa pesimista)")
p()
p("| grupo | recompensa | acciones llenadas | resultado llenados | reembolso | neto |")
p("|---|---|---|---|---|---|")
for nom, fs in (("sin", fechas_sin), ("con", fechas_con)):
    r = neto(tf.reindex(fs).fillna(0).sum())
    p(f"| {nom} comisión | {r[0]:.2f} | {r[1]:.1f} | {r[2]:+.2f} | {r[3]:.2f} | {r[4]:+.2f} |")
p()
e_net = boot_sumas(tf, lambda a, b: neto(b)[4] - neto(a)[4])
p(f"Diferencia del neto (con − sin): {fmt(e_net)} US$/día por US$ 100. Las fechas con comisión más recientes todavía no "
  "resolvieron, así que el resultado de sus llenados sale de las que sí cerraron.")
p()
p("Límites: pocos días con comisión y sin repetir, la recompensa estimada es optimista (fotos cada 5 min), y los llenados "
  "son simulados. Ver `comision/REGLA.md`.")
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")
print("\n".join(L))

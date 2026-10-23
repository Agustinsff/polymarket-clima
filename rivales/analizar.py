"""
Analisis de rivales (lee lo que bajo rivales/bajar.py en rivales/datos/, no se conecta a nada).
Escribe rivales/informe_datos.md con las tablas y rivales/billeteras.csv.

Comision: hoy.py anota tasa 0.0 para los mercados de temperatura (feeSchedule de gamma), asi que el PnL va sin
comision. Si algun dia cobran, el PnL de los que compran caro (>=90c) casi no cambia (p*(1-p) es chico ahi).

Uso: python rivales/analizar.py
"""

import glob
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
from estaciones import TZ  # noqa: E402

SALIDA = []


def p(*a):
    SALIDA.append(" ".join(str(x) for x in a))


def leer(nombre, **kw):
    partes = []
    for ruta in sorted(glob.glob(os.path.join(CARPETA, "datos", nombre + "_*.csv.gz"))):
        try:
            partes.append(pd.read_csv(ruta, **kw))
        except Exception as ex:   # tramo cortado por el tiempo limite
            print(f"aviso: {ruta}: {ex}", file=sys.stderr)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def tabla(cab, filas):
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for f in filas:
        p("| " + " | ".join(str(x) for x in f) + " |")
    p("")


def usd(x):
    return f"{x:,.0f}".replace(",", ".")


def pct(a, b):
    return f"{100 * a / b:+.1f}%" if b else "-"


# ---------------------------------------------------------------------------
# cajas
# ---------------------------------------------------------------------------
cj = leer("eventos", dtype=str).drop_duplicates("condition_id")
cj = cj[cj.precio_final_si.isin(["0", "1"])].copy()


def inicio_dia(r):
    tz = ZoneInfo(TZ.get(r.ciudad, "UTC"))
    d = datetime.fromisoformat(r.fecha)
    return datetime(d.year, d.month, d.day, tzinfo=tz).astimezone(timezone.utc).timestamp()


cj["ini"] = [inicio_dia(r) for r in cj.itertuples()]
cj["gano_si"] = cj.precio_final_si == "1"
CJ = cj.set_index("condition_id")

# ---------------------------------------------------------------------------
# operaciones
# ---------------------------------------------------------------------------
op = leer("trades", dtype={"condition_id": str, "wallet": str, "name": str, "pseudonym": str, "tx": str, "asset": str})
op = op.drop_duplicates(["tx", "asset", "side", "size", "price", "wallet"])
op = op[op.condition_id.isin(CJ.index)].copy()
op = op.join(CJ[["ini", "gano_si", "ciudad", "slug", "tipo", "fecha", "caja"]], on="condition_id")
op["gana"] = np.where(op.outcome_index == 0, op.gano_si, ~op.gano_si)
op["usd"] = op.price * op["size"]
op["pnl"] = np.where(op.side == "BUY", op["size"] * (op.gana - op.price), op["size"] * (op.price - op.gana))
op["h_rel"] = (op.timestamp - op.ini) / 3600
op["fase"] = np.select([op.h_rel < 0, op.h_rel < 24], ["antes", "durante"], "despues")
op["nombre"] = op.name.fillna(op.pseudonym).fillna("")
op["hora_utc"] = (op.timestamp % 86400) // 3600
op = op.sort_values("timestamp")

t0 = datetime.fromtimestamp(op.timestamp.min(), timezone.utc)
t1 = datetime.fromtimestamp(op.timestamp.max(), timezone.utc)
p("# Rivales en mercados de temperatura: datos\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ}. {cj.slug.nunique()} eventos cerrados "
  f"({cj.fecha.min()} a {cj.fecha.max()}), {len(cj)} cajas, {len(op)} operaciones (lado taker) del {t0:%d-%b} al {t1:%d-%b}. "
  f"Volumen taker US$ {usd(op.usd.sum())}.\n")
p("PnL = lo que gana o pierde el que toma la orden si se queda hasta la resolución (sin comisión: en temperatura la tasa es 0). "
  "No vemos al market maker (el otro lado de cada operación): lo que pierden los takers lo gana él.\n")

# --- 1. donde esta la plata ---------------------------------------------------
p("## 1. Dónde está la plata\n")
fil = []
for fase, nom in (("antes", "antes del día (pronóstico)"), ("durante", "durante el día"),
                  ("despues", "después del día (esperando resolución)")):
    x = op[op.fase == fase]
    fil.append([nom, len(x), usd(x.usd.sum()), usd(x.pnl.sum()), pct(x.pnl.sum(), x.usd.sum())])
tabla(["fase", "operaciones", "volumen US$", "PnL takers US$", "PnL/volumen"], fil)

fil = []
for a, b in [(0, 10), (10, 100), (100, 500), (500, 2000), (2000, 1e12)]:
    x = op[(op.usd >= a) & (op.usd < b)]
    xb = x[x.price < 0.9]
    fil.append([f"{usd(a)}–{usd(b) if b < 1e11 else '+'}", len(x), usd(x.usd.sum()), usd(x.pnl.sum()), pct(x.pnl.sum(), x.usd.sum()),
                pct(xb.pnl.sum(), xb.usd.sum()), f"{100 * (x.fase == 'antes').mean():.0f}%"])
tabla(["tamaño (US$)", "operaciones", "volumen", "PnL", "PnL/volumen", "PnL/vol. sin las de ≥90¢", "% antes del día"], fil)

p("Compras por precio pagado (¿el precio dice la verdad?):\n")
fil = []
cb = op[op.side == "BUY"]
for a, b in [(0, .05), (.05, .2), (.2, .5), (.5, .8), (.8, .95), (.95, .99), (.99, 1.01)]:
    for fase in ("antes", "durante"):
        x = cb[(cb.price >= a) & (cb.price < b) & (cb.fase == fase)]
        if len(x):
            fil.append([f"{a:.2f}–{min(b, 1):.2f}", fase, len(x), usd(x.usd.sum()), pct(x.pnl.sum(), x.usd.sum()),
                        f"{100 * x.price.mean():.1f}%", f"{100 * x.gana.mean():.1f}%"])
tabla(["precio", "fase", "compras", "volumen", "PnL/volumen", "precio medio", "ganaron"], fil)

# --- 2. billeteras ----------------------------------------------------------------
p("## 2. Billeteras\n")
porev = op.groupby(["wallet", "slug"]).pnl.sum().reset_index()
ev = porev.groupby("wallet").pnl.agg(eventos="count", ev_mean="mean", ev_std="std",
                                      ev_pos=lambda s: (s > 0).mean())
ev["t"] = ev.ev_mean / (ev.ev_std / np.sqrt(ev.eventos))
g = op.groupby("wallet")
B = pd.DataFrame({
    "nombre": g.nombre.last(), "ops": g.size(), "volumen": g.usd.sum(), "pnl": g.pnl.sum(),
    "precio_med": g.price.median(), "caro": g.price.apply(lambda s: (s >= .9).mean()),
    "h_rel_med": g.h_rel.median(),
    "antes": op[op.fase == "antes"].groupby("wallet").usd.sum(),
    "durante": op[op.fase == "durante"].groupby("wallet").usd.sum(),
    "despues": op[op.fase == "despues"].groupby("wallet").usd.sum(),
    "ciudades": g.ciudad.nunique(),
    "dias": g.timestamp.apply(lambda s: s.floordiv(86400).nunique()),
}).fillna({"antes": 0, "durante": 0, "despues": 0}).join(ev)
for c in ("antes", "durante", "despues"):
    B[c] = B[c] / B.volumen
B["roi"] = B.pnl / B.volumen
top_c = op.groupby(["wallet", "ciudad"]).usd.sum().reset_index().sort_values("usd").drop_duplicates("wallet", keep="last").set_index("wallet")
B["ciudad_top"] = top_c.ciudad
B.sort_values("pnl", ascending=False).to_csv(os.path.join(CARPETA, "billeteras.csv"))

orden = B.sort_values("volumen", ascending=False)
n50 = int((orden.volumen.cumsum() < B.volumen.sum() / 2).sum()) + 1
p(f"{len(B)} billeteras distintas. Las {n50} más grandes hacen la mitad del volumen taker. "
  f"Las que ganan plata en total: {(B.pnl > 0).sum()} ({100 * (B.pnl > 0).mean():.0f}%).\n")

CAB = ["nombre", "billetera", "eventos", "días", "volumen", "PnL", "PnL/vol", "eventos +", "t",
       "% antes/durante/después", "precio mediano", "% a ≥90¢", "hora mediana vs inicio del día", "ciudades", "ciudad principal"]


def filas(df):
    out = []
    for w, r in df.iterrows():
        out.append([str(r.nombre)[:18] or w[:10], w[:8], int(r.eventos), int(r.dias), usd(r.volumen), usd(r.pnl),
                    f"{100 * r.roi:+.1f}%", f"{100 * r.ev_pos:.0f}%", f"{r.t:.1f}" if pd.notna(r.t) else "-",
                    f"{100 * r.antes:.0f}/{100 * r.durante:.0f}/{100 * r.despues:.0f}", f"{r.precio_med:.2f}",
                    f"{100 * r.caro:.0f}%", f"{r.h_rel_med:+.0f}", int(r.ciudades), r.ciudad_top])
    return out


MIN_EV = 30
grandes = B[B.eventos >= MIN_EV]
p(f"### Las 30 que más ganaron (mínimo {MIN_EV} eventos)\n")
tabla(CAB, filas(grandes.sort_values("pnl", ascending=False).head(30)))
p(f"### Las 15 que más perdieron (mínimo {MIN_EV} eventos)\n")
tabla(CAB, filas(grandes.sort_values("pnl").head(15)))
p("### Las 15 de más volumen\n")
tabla(CAB, filas(orden.head(15)))
p("t = PnL medio por evento dividido por su error estándar (más de 3 = ganan de forma constante, no por suerte). "
  "Hora mediana vs inicio del día: horas desde la medianoche local del día que se mide (negativo = el día anterior; "
  "+24 o más = después de que terminó el día).\n")

# ganadoras constantes por estilo
gan = B[(B.eventos >= MIN_EV) & (B.t >= 3) & (B.pnl > 0)].copy()
gan["estilo"] = np.select(
    [gan.antes >= .6, (gan.caro >= .5) & (gan.antes < .6), gan.durante + gan.despues >= .6],
    ["pronóstico (antes del día)", "cosecha (compra ≥90¢ en el día)", "durante el día (<90¢)"], "mixto")
p(f"### Ganadoras constantes (≥{MIN_EV} eventos y t ≥ 3): {len(gan)} billeteras, PnL total US$ {usd(gan.pnl.sum())}\n")
fil = []
for est, x in gan.groupby("estilo"):
    fil.append([est, len(x), usd(x.volumen.sum()), usd(x.pnl.sum()), pct(x.pnl.sum(), x.volumen.sum()),
                ", ".join(str(n)[:16] for n in x.sort_values("pnl", ascending=False).nombre.head(5))])
tabla(["estilo", "billeteras", "volumen", "PnL", "PnL/vol", "las principales"], fil)
GW = set(gan.index)

# --- cuando entran las ganadoras -----------------------------------------------
p("### ¿Cuándo entran? (volumen por hora UTC)\n")
p("Sólo operaciones **antes del día** (o sea, apuestas de pronóstico). Columnas: todas las billeteras, las ganadoras "
  "constantes de estilo pronóstico, y el PnL/volumen de todos los takers en esa hora.\n")
pre = op[op.fase == "antes"]
gpro = set(gan[gan.estilo.str.startswith("pronóstico")].index)
vt = pre.groupby("hora_utc").usd.sum()
vg = pre[pre.wallet.isin(gpro)].groupby("hora_utc").usd.sum()
pn = pre.groupby("hora_utc").pnl.sum()
fil = []
for h in range(24):
    a, b = vt.get(h, 0), vg.get(h, 0)
    fil.append([f"{h:02d}", f"{100 * a / vt.sum():.1f}%", f"{100 * b / max(1, vg.sum()):.1f}%", "█" * round(100 * b / max(1, vg.sum())),
                pct(pn.get(h, 0), a)])
tabla(["hora UTC", "% vol. todos", "% vol. ganadoras pronóstico", "", "PnL/vol todos"], fil)

p("Cuánto antes del día operan (horas antes de la medianoche local del día que se mide):\n")
fil = []
for a, b in [(-60, -36), (-36, -24), (-24, -12), (-12, -6), (-6, 0)]:
    x = pre[(pre.h_rel >= a) & (pre.h_rel < b)]
    xg = x[x.wallet.isin(gpro)]
    fil.append([f"{-b} a {-a} h", usd(x.usd.sum()), pct(x.pnl.sum(), x.usd.sum()), usd(xg.usd.sum()), pct(xg.pnl.sum(), xg.usd.sum())])
tabla(["antelación", "volumen todos", "PnL/vol todos", "volumen ganadoras", "PnL/vol ganadoras"], fil)

# minuto de la hora durante el dia (bots de METAR)
p("### ¿A qué minuto de la hora operan durante el día? (UTC)\n")
p("Los METAR de rutina salen a la hora en punto (o :20/:50, o :30 según la estación) y tardan unos minutos en publicarse. "
  "Un pico pegado a esos minutos es señal de bots de velocidad.\n")
dur = op[op.fase != "antes"].copy()
dur["m5"] = (dur.timestamp % 3600) // 300 * 5
gcos = set(gan[gan.estilo.str.startswith(("cosecha", "durante"))].index)
ma = dur.groupby("m5").usd.sum()
mg = dur[dur.wallet.isin(gcos)].groupby("m5").usd.sum()
fil = [[f":{m:02d}", f"{100 * ma.get(m, 0) / ma.sum():.1f}%", f"{100 * mg.get(m, 0) / max(1, mg.sum()):.1f}%",
        "█" * round(100 * mg.get(m, 0) / max(1, mg.sum()))] for m in range(0, 60, 5)]
tabla(["minuto", "% vol. todos", "% vol. ganadoras del día", ""], fil)

# --- 3. operaciones grandes -----------------------------------------------------
p("## 3. Las operaciones grandes\n")
UMB = 1000
gr = op[op.usd >= UMB]
p(f"{len(gr)} operaciones de US$ {UMB} o más ({usd(gr.usd.sum())} de volumen, {100 * gr.usd.sum() / op.usd.sum():.0f}% del total), "
  f"de {gr.wallet.nunique()} billeteras. PnL: {usd(gr.pnl.sum())} ({pct(gr.pnl.sum(), gr.usd.sum())}).\n")
fil = []
for fase in ("antes", "durante", "despues"):
    for caro in (False, True):
        x = gr[(gr.fase == fase) & ((gr.price >= .9) == caro)]
        if len(x):
            fil.append([fase, "≥90¢" if caro else "<90¢", len(x), usd(x.usd.sum()), pct(x.pnl.sum(), x.usd.sum()),
                        f"{100 * x.gana.mean():.0f}%", f"{100 * x.price.mean():.0f}¢"])
tabla(["fase", "precio", "operaciones", "volumen", "PnL/vol", "ganaron", "precio medio"], fil)
p("Las 25 más grandes de menos de 90¢ (apuestas de verdad, no cosecha):\n")
fil = []
for r in gr[gr.price < .9].sort_values("usd", ascending=False).head(25).itertuples():
    fil.append([datetime.fromtimestamp(r.timestamp, timezone.utc).strftime("%d-%b %H:%M"), r.ciudad, r.tipo[:4], r.fecha[5:],
                r.caja, r.side, "Sí" if r.outcome_index == 0 else "No", f"{r.price:.3f}", usd(r.usd), usd(r.pnl),
                f"{r.h_rel:+.1f}", str(r.nombre)[:16]])
tabla(["hora UTC", "ciudad", "tipo", "fecha", "caja", "lado", "token", "precio", "US$", "PnL", "h vs inicio día", "quién"], fil)

# ---------------------------------------------------------------------------
# 4 y 5. precios por minuto
# ---------------------------------------------------------------------------
pr = leer("precios", dtype={"condition_id": str})
if len(pr):
    pr = pr[pr.condition_id.isin(CJ.index)].drop_duplicates(["condition_id", "t"]).sort_values(["condition_id", "t"])
    pr["ini"] = pr.condition_id.map(CJ.ini)
    p("## 4. ¿Cuándo se mueve el precio? (cajas que todavía no empezaron su día)\n")
    d = pr.groupby("condition_id")
    pr["dp"] = d.p.diff().abs()
    pr["dt"] = d.t.diff()
    m = pr[(pr.t < pr.ini - 3600) & (pr.dt <= 600) & pr.dp.notna()]
    m = m.assign(b5=(m.t % 86400) // 300)
    mov = m.groupby("b5").dp.sum()
    vol = pre[pre.h_rel < -1].groupby((pre.timestamp % 86400) // 300).usd.sum()
    dias = m.t.floordiv(86400).nunique()
    p(f"{pr.condition_id.nunique()} cajas con historia de precio por minuto, {dias} días. Suma de |cambio de precio| por hora UTC, "
      "sólo cajas cuyo día local empieza en más de 1 h. Si 24 horas pesaran igual, cada una tendría 4,2%.\n")
    fil = []
    for h in range(24):
        a = mov[(mov.index >= h * 12) & (mov.index < h * 12 + 12)].sum()
        b = vol[(vol.index >= h * 12) & (vol.index < h * 12 + 12)].sum()
        fil.append([f"{h:02d}", f"{100 * a / mov.sum():.1f}%", "█" * round(100 * a / mov.sum()), f"{100 * b / vol.sum():.1f}%"])
    tabla(["hora UTC", "% del movimiento", "", "% del volumen"], fil)
    top = mov.sort_values(ascending=False).head(15)
    p("Los 15 tramos de 5 min con más movimiento (media de un tramo = 0,35%): " + ", ".join(
        f"{b * 5 // 60:02d}:{b * 5 % 60:02d} ({100 * top[b] / mov.sum():.2f}%)" for b in sorted(top.index)) + "\n")

    # 5. estudio de eventos
    p("## 5. ¿Qué tan rápido se mueve el precio después de cada corrida?\n")
    p("Horas aproximadas en que cada corrida aparece en las fuentes gratis (UTC): GFS 00/06/12/18Z a las 03:30/09:30/15:30/21:30; "
      "ECMWF 00/12Z a las ~06:40/18:40 (06/18Z a las ~12:40/00:40). Para cada ventana W y cada caja del día siguiente "
      "(su día local empieza en más de 6 h, precio entre 3 y 97¢) se mide |precio(W+k) − precio(W)| y se compara con lo mismo "
      "en el mismo mercado 3 h antes (control). Exceso = lo que se movió de más.\n")
    VENT = [("GFS 00Z", 210), ("ECMWF 00Z", 400), ("GFS 06Z", 570), ("ECMWF 06Z", 760), ("GFS 12Z", 930),
            ("ECMWF 12Z", 1120), ("GFS 18Z", 1290), ("ECMWF 18Z", 40)]
    KS = [10, 20, 30, 60, 90, 120, 180]
    series = {cid: (g.t.values // 60, g.p.values, g.ini.iloc[0]) for cid, g in pr.groupby("condition_id")}

    def precio_en(tm, pv, q):
        i = np.searchsorted(tm, q, side="right") - 1
        ok = (i >= 0) & (q - tm[np.maximum(i, 0)] < 30)
        return np.where(ok, pv[np.maximum(i, 0)], np.nan)

    def estudio(wmin, desfase=0):
        acc = {k: [] for k in KS}
        ctl = {k: [] for k in KS}
        for tm, pv, ini in series.values():
            dias_ = np.arange(tm[0] // 1440, tm[-1] // 1440 + 1)
            W = dias_ * 1440 + wmin + desfase
            W = W[(W * 60 <= ini - 6 * 3600) & (W - 180 >= tm[0]) & (W + 180 <= tm[-1])]
            if not len(W):
                continue
            a, ac = precio_en(tm, pv, W), precio_en(tm, pv, W - 180)
            ok = (a > .03) & (a < .97) & ~np.isnan(ac)
            for k in KS:
                acc[k].append(np.abs(precio_en(tm, pv, W[ok] + k) - a[ok]))
                ctl[k].append(np.abs(precio_en(tm, pv, W[ok] - 180 + k) - ac[ok]))
        r = {}
        for k in KS:
            x, c = np.concatenate(acc[k]) if acc[k] else np.array([]), np.concatenate(ctl[k]) if ctl[k] else np.array([])
            x, c = x[~np.isnan(x)], c[~np.isnan(c)]
            r[k] = (np.mean(x) * 100 if len(x) else np.nan, np.mean(c) * 100 if len(c) else np.nan, len(x))
        return r

    fil = []
    for nom, wm in VENT:
        r = estudio(wm)
        ex = {k: r[k][0] - r[k][1] for k in KS}
        base = ex[180] if ex[180] > 0.05 else None
        fil.append([nom, f"{wm // 60:02d}:{wm % 60:02d}", r[180][2], f"{r[180][0]:.2f}", f"{r[180][1]:.2f}", f"{ex[180]:+.2f}"] +
                   [f"{100 * ex[k] / base:.0f}%" if base else "-" for k in (10, 20, 30, 60, 120)])
    tabla(["corrida", "W (UTC)", "casos", "mov. 3h después (pts)", "control (pts)", "exceso", "a 10 min", "20 min", "30 min",
           "60 min", "120 min"], fil)
    p("'a X min' = qué parte del exceso de 3 h ya había ocurrido X minutos después de W.\n")

    # barrido: cada hora en punto como W, para ver donde esta la informacion de verdad
    p("Barrido: cuánto se mueve el precio en la hora siguiente a cada media hora del día (dónde aparece información nueva):\n")
    fil = []
    for wm in range(0, 1440, 30):
        r = estudio(wm)
        fil.append([f"{wm // 60:02d}:{wm % 60:02d}", f"{r[60][0]:.2f}", "█" * round(r[60][0] * 10), r[60][2]])
    tabla(["W (UTC)", "mov. medio en los 60 min siguientes (pts)", "", "casos"], fil)

with open(os.path.join(CARPETA, "informe_datos.md"), "w") as f:
    f.write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

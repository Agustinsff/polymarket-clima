"""
INVESTIGACION (sin operar): ¿el precio de las cajas absorbe tarde las corridas de GFS/ECMWF? Ver corridas/REGLA.md.

Lee corridas/datos/ (de bajar.py) y los datos de Polymarket de rivales/datos/ (rama investigacion-rivales;
pasar la carpeta como argumento). Escribe corridas/informe.md, corridas/senales.csv.gz y corridas/ops.csv.gz.

Uso: python corridas/analizar.py CARPETA_RIVALES_DATOS
"""

import glob
import os
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
from estaciones import TZ, leer_caja  # noqa: E402

RIV = sys.argv[1]
TASA = 0.0   # tasa real de comision en temperatura (pronostico_ops.csv desde el 23-oct: 0.0)
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
# cajas y eventos (solo los tramos con precio por minuto)
# ---------------------------------------------------------------------------
pr = leer("precios", dtype={"condition_id": str})
pr = pr.dropna().drop_duplicates(["condition_id", "t"]).sort_values(["condition_id", "t"])
cj = leer("eventos", dtype=str).drop_duplicates("condition_id")
cj = cj[cj.tipo.isin(["highest", "lowest"]) & cj.condition_id.isin(set(pr.condition_id))].copy()


def est_de(u):
    u = u if isinstance(u, str) else ""
    for pat in (r"ids=([A-Z0-9]{4})", r"site=([a-z0-9]{4})", r"wunderground\.com/history/daily/[a-z]{2}/[^/\s]+/([A-Z0-9]{4})"):
        m = re.search(pat, u, re.I)
        if m:
            return m.group(1).upper()
    if "weather.gov.hk" in u or "Observatory" in u:
        return "HKO"
    return None


cj["est"] = cj.fuente.map(est_de)
# si un evento no trae la estacion en la fuente, la mas comun de esa ciudad
comun = cj.dropna(subset=["est"]).groupby("ciudad").est.agg(lambda s: s.value_counts().index[0])
cj["est"] = cj.est.fillna(cj.ciudad.map(comun))
cj = cj.dropna(subset=["est"])


def inicio_dia(r):
    tz = ZoneInfo(TZ.get(r.ciudad, "UTC"))
    d = datetime.fromisoformat(r.fecha)
    a = datetime(d.year, d.month, d.day, tzinfo=tz)
    b = datetime.fromordinal(d.toordinal() + 1).replace(tzinfo=tz)
    return a.astimezone(timezone.utc).timestamp(), b.astimezone(timezone.utc).timestamp()


ini_fin = [inicio_dia(r) for r in cj.itertuples()]
cj["ini"] = [a for a, _ in ini_fin]
cj["fin_dia"] = [b for _, b in ini_fin]
lh = [leer_caja(c) for c in cj.caja]
cj["lo"] = [x[0] for x in lh]
cj["hi"] = [x[1] for x in lh]
cj["en_f"] = [x[2] for x in lh]

EVENTOS = {}
for eid, g in cj.groupby("evento_id"):
    inter = g[g.lo.notna() & g.hi.notna()]
    if len(inter) == 0:
        continue
    w = float(np.median(inter.hi - inter.lo + 1))
    centros = []
    for r in g.itertuples():
        if pd.notna(r.lo) and pd.notna(r.hi):
            c = (r.lo + r.hi) / 2
        elif pd.isna(r.lo):        # "X o menos": un ancho mas alla del borde
            c = r.hi - (w - 1) / 2 - w
        else:                      # "X o mas"
            c = r.lo + (w - 1) / 2 + w
        centros.append(c)
    orden = np.argsort(centros)
    g0 = g.iloc[0]
    EVENTOS[eid] = dict(cids=list(g.condition_id.values[orden]), centros=np.array(centros)[orden] / w, ancho=w,
                        tipo=g0.tipo, ciudad=g0.ciudad, fecha=g0.fecha, est=g0.est, en_f=bool(g.en_f.any()),
                        ini=g0.ini, fin_dia=g0.fin_dia, si=dict(zip(g.condition_id, g.token_si)),
                        no=dict(zip(g.condition_id, g.token_no)))

SERIES = {cid: (g.t.values.astype(np.int64), g.p.values.astype(float)) for cid, g in pr.groupby("condition_id")}


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


def precios_evento(ev, t):
    ps = [precio(c, t) for c in ev["cids"]]
    return None if any(x is None for x in ps) else np.array(ps)


def media(ev, ps):
    return float((ps / ps.sum() * ev["centros"]).sum())


# ---------------------------------------------------------------------------
# operaciones (para el precio ejecutable)
# ---------------------------------------------------------------------------
op = leer("trades", dtype={"condition_id": str, "asset": str},
          usecols=["condition_id", "asset", "side", "price", "size", "timestamp", "tx", "wallet"])
op = op.drop_duplicates(["tx", "asset", "side", "size", "price", "wallet"])
op = op[op.condition_id.isin(set(cj.condition_id))]
si_de = dict(zip(cj.condition_id, cj.token_si))
op["es_si"] = op.asset == op.condition_id.map(si_de)
# precio del Si visto por el taker: compra Si (o vende No) = paga el ask; vende Si (o compra No) = cobra el bid
op["p_si"] = np.where(op.es_si, op.price, 1 - op.price)
op["compra_si"] = (op.es_si & (op.side == "BUY")) | (~op.es_si & (op.side == "SELL"))
OPS = {cid: (g.timestamp.values.astype(np.int64), g.p_si.values, g.compra_si.values)
       for cid, g in op.sort_values("timestamp").groupby("condition_id")}


def mediana_ops(cid, t0, t1, compra):
    s = OPS.get(cid)
    if s is None:
        return None
    tm, pv, cs = s
    a, b = np.searchsorted(tm, t0), np.searchsorted(tm, t1, side="right")
    x = pv[a:b][cs[a:b] == compra]
    return float(np.median(x)) if len(x) else None


# ---------------------------------------------------------------------------
# pronosticos por corrida
# ---------------------------------------------------------------------------
pn = pd.read_csv(os.path.join(CARPETA, "datos", "pronos.csv.gz"))
def segundos(x, **kw):
    return (pd.to_datetime(x, utc=True, **kw) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)


pn["run_ts"] = segundos(pn.corrida, format="%Y-%m-%dT%H")
pn["valido"] = pn.run_ts + pn.paso_h * 3600
PRON = {k: (g.valido.values, g.temp_c.values) for k, g in pn.groupby(["modelo", "run_ts", "estacion"])}
dp = pd.read_csv(os.path.join(CARPETA, "datos", "disponible.csv.gz"))
dp["run_ts"] = segundos(dp.corrida, format="%Y-%m-%dT%H")
dp["lm"] = segundos(dp.last_modified)
DISP = {k: (g.paso_h.values, g.lm.values) for k, g in dp.groupby(["modelo", "run_ts"])}
NECESITA = {"gfs": 24, "ecmwf": 8}


def extremo(modelo, run, ev):
    s = PRON.get((modelo, run, ev["est"]))
    if s is None:
        return None
    va, te = s
    m = (va >= ev["ini"]) & (va < ev["fin_dia"])
    if m.sum() < NECESITA[modelo]:
        return None
    v = te[m].max() if ev["tipo"] == "highest" else te[m].min()
    return v * 9 / 5 + 32 if ev["en_f"] else v


def disponible(modelo, run, ev):
    s = DISP.get((modelo, run))
    if s is None:
        return None
    pasos, lm = s
    lo, hi = (ev["ini"] - run) / 3600, (ev["fin_dia"] - run) / 3600
    m = (pasos >= lo - 3) & (pasos <= hi + 3)
    return int(lm[m].max()) + 600 if m.any() else None


# ---------------------------------------------------------------------------
# senales
# ---------------------------------------------------------------------------
filas, ops = [], []
runs = sorted(set(pn.run_ts))
for modelo in ("gfs", "ecmwf"):
    for run in runs:
        for eid, ev in EVENTOS.items():
            if not (ev["ini"] - run < 4 * 86400 and ev["ini"] > run):
                continue
            W = disponible(modelo, run, ev)
            if W is None or not (6 * 3600 <= ev["ini"] - W <= 48 * 3600):
                continue
            a, b = extremo(modelo, run, ev), extremo(modelo, run - 6 * 3600, ev)
            if a is None or b is None:
                continue
            db = (a - b) / ev["ancho"]
            pw = precios_evento(ev, W)
            if pw is None or not (0.90 <= pw.sum() <= 1.15):
                continue
            f = dict(modelo=modelo, corrida=datetime.fromtimestamp(run, timezone.utc).strftime("%Y-%m-%dT%H"),
                     evento=eid, tipo=ev["tipo"], ciudad=ev["ciudad"], fecha=ev["fecha"], W=W,
                     h_antes=(ev["ini"] - W) / 3600, db=db, E_W=media(ev, pw), suma=pw.sum())
            pr3 = precios_evento(ev, run + 3 * 3600)
            f["E_pre"] = media(ev, pr3) if pr3 is not None else np.nan
            for h in (1, 3, 6):
                ph = precios_evento(ev, W + h * 3600)
                f[f"E_{h}"] = media(ev, ph) if ph is not None else np.nan
            filas.append(f)
            # prueba B
            if abs(db) < 0.5:
                continue
            k = int(np.argmax(pw)) + (1 if db > 0 else -1)
            if not (0 <= k < len(pw)) or not (0.05 <= pw[k] <= 0.60):
                continue
            cid = ev["cids"][k]
            mc = mediana_ops(cid, W, W + 900, True)
            compra = max(pw[k] + 0.01, mc) if mc is not None else pw[k] + 0.01
            o = dict(modelo=modelo, corrida=f["corrida"], evento=eid, tipo=ev["tipo"], ciudad=ev["ciudad"],
                     fecha=ev["fecha"], W=W, db=db, caja=k, p_W=pw[k], compra=compra, ops_compra=mc is not None)
            for h in (1, 3, 6):
                X = W + h * 3600
                px = precio(cid, X)
                if px is None:
                    o[f"r_{h}"] = np.nan
                    continue
                mv = mediana_ops(cid, X - 900, X + 900, False)
                venta = min(px - 0.01, mv) if mv is not None else px - 0.01
                venta = max(venta, 0.0)
                com = TASA * compra * (1 - compra) + TASA * venta * (1 - venta)
                o[f"r_{h}"] = (venta - compra - com) / compra
                o[f"ops_venta_{h}"] = mv is not None
            ops.append(o)

S = pd.DataFrame(filas)
O = pd.DataFrame(ops)
S.to_csv(os.path.join(CARPETA, "senales.csv.gz"), index=False)
O.to_csv(os.path.join(CARPETA, "ops.csv.gz"), index=False)


def ols_cluster(x, y, g):
    """y = a + b x; devuelve b, error estandar agrupado por g, n."""
    m = ~(np.isnan(x) | np.isnan(y))
    x, y, g = x[m], y[m], np.asarray(g)[m]
    X = np.column_stack([np.ones_like(x), x])
    XtX = np.linalg.inv(X.T @ X)
    beta = XtX @ X.T @ y
    u = y - X @ beta
    meat = np.zeros((2, 2))
    for k in np.unique(g):
        s = (X[g == k] * u[g == k, None]).sum(0)
        meat += np.outer(s, s)
    G = len(np.unique(g))
    V = XtX @ meat @ XtX * G / max(G - 1, 1)
    return beta[1], np.sqrt(V[1, 1]), len(x)


def media_cluster(r, g):
    m = ~np.isnan(r)
    r, g = r[m], np.asarray(g)[m]
    if len(r) < 2:
        return np.nan, np.nan, len(r)
    d = pd.DataFrame({"r": r, "g": g}).groupby("g").r.agg(["sum", "count"])
    mu = r.mean()
    G = len(d)
    se = np.sqrt(((d["sum"] - mu * d["count"]) ** 2).sum() * G / max(G - 1, 1)) / len(r)
    return mu, se, len(r)


# ---------------------------------------------------------------------------
# informe
# ---------------------------------------------------------------------------
p("# ¿El precio absorbe tarde las corridas de GFS/ECMWF? Resultados\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ} con la regla fija de `REGLA.md`. "
  f"{len(EVENTOS)} eventos con precio por minuto ({min(e['fecha'] for e in EVENTOS.values())} a "
  f"{max(e['fecha'] for e in EVENTOS.values())}), {len(runs)} corridas por modelo, "
  f"{len(S)} señales (modelo × corrida × evento) que pasan los filtros.\n")

p("## Hora en que cada corrida aparece en AWS (mediana, horas después de la hora de la corrida)\n")
fil = []
for mo in ("gfs", "ecmwf"):
    x = dp[dp.modelo == mo]
    for hh in ("00", "06", "12", "18"):
        y = x[x.corrida.str.endswith(hh)]
        if len(y):
            ult = y.groupby("run_ts").lm.max() - y.groupby("run_ts").run_ts.first()
            fil.append([mo, hh + "Z", f"{np.median(ult) / 3600:.2f}"])
tabla(["modelo", "corrida", "h hasta el último paso"], fil)

p("## Prueba A: ¿el precio se mueve tarde hacia donde fue la corrida?\n")
p("E = media del mercado en anchos de caja. Pendiente β de ΔE sobre Δb (cambio del pronóstico entre corridas, en "
  "anchos de caja); t = β / error estándar agrupado por evento. β = 1 sería que el mercado copia el cambio entero.\n")
fil = []
for mo in ("gfs", "ecmwf", "ambos"):
    s = S if mo == "ambos" else S[S.modelo == mo]
    if not len(s):
        continue
    for nom, y in (("antes de W (desde corrida+3 h)", s.E_W - s.E_pre), ("W → W+1 h", s.E_1 - s.E_W),
                   ("W → W+3 h", s.E_3 - s.E_W), ("W → W+6 h", s.E_6 - s.E_W)):
        b, se, n = ols_cluster(s.db.values, y.values, s.evento.values)
        fil.append([mo, nom, n, f"{b:+.3f}", f"{b / se:+.1f}" if se > 0 else "-"])
tabla(["modelo", "tramo", "señales", "β", "t"], fil)
p(f"Δb típico: mediana |Δb| = {S.db.abs().median():.2f}; |Δb| ≥ 0,5 en {(S.db.abs() >= 0.5).mean():.0%} de las señales.\n")

fil = []
for tipo in ("highest", "lowest"):
    s = S[S.tipo == tipo]
    b, se, n = ols_cluster(s.db.values, (s.E_3 - s.E_W).values, s.evento.values)
    b0, se0, _ = ols_cluster(s.db.values, (s.E_W - s.E_pre).values, s.evento.values)
    fil.append([tipo, n, f"{b0:+.3f} (t {b0 / se0:+.1f})", f"{b:+.3f} (t {b / se:+.1f})"])
tabla(["tipo", "señales", "β antes de W", "β W → W+3 h"], fil)

p("## Prueba B: comprar la caja vecina hacia donde fue la corrida\n")
if len(O):
    O["mitad"] = np.where(pd.to_datetime(O.fecha) <= pd.to_datetime(O.fecha).median(), 1, 2)
    fil = []
    for h in (1, 3, 6):
        for mo in ("ambos", "gfs", "ecmwf"):
            o = O if mo == "ambos" else O[O.modelo == mo]
            mu, se, n = media_cluster(o[f"r_{h}"].values, o.evento.values)
            m1 = o[o.mitad == 1][f"r_{h}"].mean()
            m2 = o[o.mitad == 2][f"r_{h}"].mean()
            fil.append([f"{h} h", mo, n, f"{100 * mu:+.1f}%", f"{mu / se:+.1f}" if se > 0 else "-",
                        f"{100 * m1:+.1f}%", f"{100 * m2:+.1f}%"])
    tabla(["salida", "modelo", "operaciones", "ganancia media", "t", "1ª mitad", "2ª mitad"], fil)
    p(f"Precio de compra con operaciones reales en la ventana: {O.ops_compra.mean():.0%}; de venta a 3 h: "
      f"{O.get('ops_venta_3', pd.Series(dtype=bool)).mean():.0%} (el resto, precio ± 1 ¢). "
      f"Compra media {100 * O.compra.mean():.1f} ¢ vs precio en W {100 * O.p_W.mean():.1f} ¢.\n")
    # sin costos: para separar 'no se mueve' de 'se mueve pero no paga el spread'
    sc = []
    for r in O.itertuples():
        x = precio(EVENTOS[r.evento]["cids"][r.caja], r.W + 3 * 3600)
        sc.append((x - r.p_W) / r.p_W if x is not None else np.nan)
    mu, se, n = media_cluster(np.array(sc), O.evento.values)
    p(f"La misma prueba sin costos (precio en W contra precio a W+3 h): {100 * mu:+.1f}% (t {mu / se:+.1f}, {n} ops).\n")

    ba, sea, _ = ols_cluster(S.db.values, (S.E_3 - S.E_W).values, S.evento.values)
    ok_a = ba > 0 and ba / sea >= 3
    mu, se, n = media_cluster(O.r_3.values, O.evento.values)
    m1, m2 = O[O.mitad == 1].r_3.mean(), O[O.mitad == 2].r_3.mean()
    ok_b = mu >= 0.02 and mu / se >= 2 and n >= 150 and m1 > 0 and m2 > 0
    p("## Criterio de éxito\n")
    p(f"1. Prueba A, β a 3 h > 0 con t ≥ 3: **{'sí' if ok_a else 'no'}** (β {ba:+.3f}, t {ba / sea:+.1f}).")
    p(f"2. Prueba B a 3 h ≥ +2 %, t ≥ 2, ≥ 150 ops, + en las dos mitades: **{'sí' if ok_b else 'no'}** "
      f"({100 * mu:+.1f}%, t {mu / se:+.1f}, {n} ops, mitades {100 * m1:+.1f}% / {100 * m2:+.1f}%).\n")

with open(os.path.join(CARPETA, "informe.md"), "w") as f:
    f.write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

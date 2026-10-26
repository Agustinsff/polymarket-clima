"""
CON QUE INFORMACION ELIGEN LAS GANADORAS: ¿sus apuestas coinciden con el pronostico de los modelos (antes del dia)
o con la maxima/minima ya registrada (durante el dia)? Y si eso da una regla mecanica.
Reglas en informacion/REGLAS.md, fijadas antes de correr esto. No opera nada.

Uso: python informacion/analisis.py CARPETA_RIVALES METAR_IEM_CSV_GZ
  CARPETA_RIVALES: rivales/datos/ de la rama investigacion-rivales
  METAR_IEM_CSV_GZ: velocidad/datos/metar_iem.csv.gz de la rama investigacion-velocidad
Escribe informacion/informe.md.
"""

import glob
import math
import os
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, RAIZ)
from estaciones import TZ  # noqa: E402

DATOS, METAR = sys.argv[1], sys.argv[2]

# --- reglas (REGLAS.md) -------------------------------------------------------
P_MIN, P_MAX = 0.05, 0.90
MIN_EVENTOS, MIN_T, MIN_ROI = 20, 2.5, 0.03       # ganadoras, igual que ganadoras/
MIN_PREVIOS = 5
RETRASO_METAR = 600
LECTURA_PUNTOS = 0.10
DECISION_ANTES, DECISION_DURANTE = [-24, -12, -6], [0, 3, 6, 9, 12]
UMBRAL = 0.10
APUESTA, DESLIZ, VENTANA = 10.0, 0.01, 120 * 60
PASA_ROI = 0.03

SALIDA = []


def p(*a):
    SALIDA.append(" ".join(str(x) for x in a))


def tabla(cab, filas):
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for f in filas:
        p("| " + " | ".join(str(x) for x in f) + " |")
    p("")


def f(x, d=1):
    return "-" if pd.isna(x) else f"{100 * x:+.{d}f}%"


def n_(x):
    return f"{x:,.0f}".replace(",", ".")


def leer(nombre, **kw):
    partes = [pd.read_csv(r, **kw) for r in sorted(glob.glob(os.path.join(DATOS, nombre + "_*.csv.gz")))]
    return pd.concat(partes, ignore_index=True)


_erf = np.frompyfunc(math.erf, 1, 1)


def Phi(x):
    x = np.asarray(x, dtype=float)
    out = np.where(np.isposinf(x), 1.0, np.where(np.isneginf(x), 0.0, 0.0))
    fin = np.isfinite(x)
    out[fin] = 0.5 * (1 + _erf(x[fin] / math.sqrt(2)).astype(float))
    return out


# --- cajas -------------------------------------------------------------------
def limites(caja):
    """(lo, hi) en °C de la caja: la temperatura final cae en ella si lo <= T < hi."""
    c = caja.replace("−", "-")
    en_f = "°F" in c
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", c)]
    if "below" in c:
        lo, hi = -np.inf, nums[0] + 0.5
    elif "higher" in c or "above" in c:
        lo, hi = nums[0] - 0.5, np.inf
    elif len(nums) == 2:
        lo, hi = nums[0] - 0.5, nums[1] + 0.5
    else:
        lo, hi = nums[0] - 0.5, nums[0] + 0.5
    if en_f:
        lo, hi = (lo - 32) / 1.8, (hi - 32) / 1.8
    return lo, hi


cj = leer("eventos", dtype=str).drop_duplicates("condition_id")
cj = cj[cj.precio_final_si.isin(["0", "1"])].copy()


def inicio_dia(r):
    d = datetime.fromisoformat(r.fecha)
    return datetime(d.year, d.month, d.day, tzinfo=ZoneInfo(TZ.get(r.ciudad, "UTC"))).timestamp()


cj["ini"] = [inicio_dia(r) for r in cj.itertuples()]
cj["gano_si"] = cj.precio_final_si == "1"
cj[["lo", "hi"]] = [limites(c) for c in cj.caja]
cj["es_max"] = cj.tipo.str.startswith("high")
cj["eeuu"] = cj.caja.str.contains("°F")
FECHAS = sorted(cj.fecha.unique())
CORTE = FECHAS[len(FECHAS) // 2]
cj["mitad"] = np.where(cj.fecha < CORTE, "desc", "prueba")

# --- pronóstico (Promedio corregido) y σ con días previos ------------------------
md = pd.read_csv(os.path.join(RAIZ, "modelos", "dias.csv.gz"), sep=";")
md = md[(md.modelo == "Promedio") & md["corr"].notna()].copy()
md[["tipo", "ciudad"]] = md.serie.str.split("|", expand=True)
md = md.sort_values("fecha")
md["err"] = md.real - md["corr"]
md["sigma"] = md.groupby(["serie", "horizonte"]).err.transform(
    lambda s: s.shift(1).expanding(MIN_PREVIOS).std())
md = md.dropna(subset=["sigma"])
PRON = md.set_index(["tipo", "ciudad", "fecha", "horizonte"])[["corr", "sigma", "icao"]]
ICAO = md.drop_duplicates("ciudad").set_index("ciudad").icao.to_dict()

# --- METAR -------------------------------------------------------------------
mt = pd.read_csv(METAR)


def temp(raw):
    m = re.search(r"\sT([01])(\d{3})([01])(\d{3})", raw)
    if m:
        return (-1 if m.group(1) == "1" else 1) * int(m.group(2)) / 10
    m = re.search(r"\s(M?\d{2})/(M?\d{2})?\s", raw)
    if m:
        return -int(m.group(1)[1:]) if m.group(1).startswith("M") else int(m.group(1))
    return np.nan


mt["t"] = [temp(r) for r in mt.raw]
mt["ts"] = (pd.to_datetime(mt.valid_utc, utc=True) - pd.Timestamp(0, tz="UTC")).dt.total_seconds()
mt = mt.dropna(subset=["t"]).sort_values("ts")
OBS = {k: (g.ts.to_numpy(), g.t.to_numpy()) for k, g in mt.groupby("icao")}


def extremo_hasta(icao, ini, t, es_max):
    if icao not in OBS:
        return np.nan
    ts, tt = OBS[icao]
    a, b = np.searchsorted(ts, ini), np.searchsorted(ts, t - RETRASO_METAR)
    if b <= a:
        return np.nan
    return tt[a:b].max() if es_max else tt[a:b].min()


def prob_si(lo, hi, mu, s, m, es_max, durante):
    """P(final en [lo, hi)) con T ~ N(mu, s); durante el día final = max(m, T) o min(m, T)."""
    pt = lambda x: Phi((x - mu) / s)  # noqa: E731  P(T < x)
    caja = pt(hi) - pt(lo)
    if not durante:
        return caja
    m = np.asarray(m, dtype=float)
    if es_max:
        return np.where(hi <= m, 0.0, np.where(lo <= m, pt(hi), caja))
    return np.where(lo > m, 0.0, np.where(m < hi, 1 - pt(lo), caja))


def prob_vec(df, t_col):
    """Agrega p_si a un DataFrame con columnas de caja, fecha, h_rel y el instante t_col."""
    df = df.copy()
    df["horizonte"] = np.where(df.h_rel < -24, 2, 1)
    df["tipo_s"] = np.where(df.es_max, "highest", "lowest")
    k = pd.MultiIndex.from_arrays([df.tipo_s, df.ciudad, df.fecha, df.horizonte])
    pr = PRON.reindex(k)
    df["mu"], df["sigma"] = pr["corr"].to_numpy(), pr["sigma"].to_numpy()
    df["durante"] = df.h_rel >= 0
    df["m"] = [extremo_hasta(ICAO.get(c), i, t, e) if d else np.nan
               for c, i, t, e, d in zip(df.ciudad, df.ini, df[t_col], df.es_max, df.durante)]
    ok = df.mu.notna() & (~df.durante | df.m.notna())
    df = df[ok].copy()
    ps = np.empty(len(df))
    for (e, d), idx in df.groupby(["es_max", "durante"]).groups.items():
        x = df.loc[idx]
        ps[df.index.get_indexer(idx)] = prob_si(x.lo.to_numpy(), x.hi.to_numpy(), x.mu.to_numpy(),
                                                x.sigma.to_numpy(), x.m.to_numpy(), e, d)
    df["p_si"] = ps
    return df


# --- operaciones --------------------------------------------------------------
CJ = cj.set_index("condition_id")
op = leer("trades", dtype={"condition_id": str, "wallet": str, "name": str, "pseudonym": str, "tx": str, "asset": str})
op = op.drop_duplicates(["tx", "asset", "side", "size", "price", "wallet"])
op = op[op.condition_id.isin(CJ.index)].copy()
op = op.join(CJ[["ini", "gano_si", "slug", "fecha", "ciudad", "lo", "hi", "es_max", "eeuu", "mitad"]],
             on="condition_id")
op["lado_i"] = np.where(op.side == "BUY", op.outcome_index, 1 - op.outcome_index).astype(int)
op["lado"] = np.where(op.lado_i == 0, "Si", "No")
op["q"] = np.where(op.side == "BUY", op.price, 1 - op.price)
op["p_tr"] = np.where(op.outcome_index == 0, op.price, 1 - op.price)
op["gana"] = np.where(op.lado_i == 0, op.gano_si, ~op.gano_si).astype(float)
op["usd"] = op["size"] * op.q
op["pnl"] = op["size"] * (op.gana - op.q)
op["h_rel"] = (op.timestamp - op.ini) / 3600
op = op.sort_values("timestamp").reset_index(drop=True)

ap = op[(op.q >= P_MIN) & (op.q < P_MAX) & (op.h_rel < 24)]
d = ap[ap.mitad == "desc"]
ev = d.groupby(["wallet", "slug"]).agg(pnl=("pnl", "sum"), usd=("usd", "sum"))
w = ev.groupby("wallet").agg(n=("pnl", "size"), m=("pnl", "mean"), s=("pnl", "std"), pnl=("pnl", "sum"),
                             usd=("usd", "sum"))
w["t"] = w.m / (w.s / np.sqrt(w.n))
w["roi"] = w.pnl / w.usd
GAN = set(w[(w.n >= MIN_EVENTOS) & (w.t >= MIN_T) & (w.roi >= MIN_ROI)].index)

pr = ap[ap.mitad == "prueba"].copy()
pr["grupo"] = np.where(pr.wallet.isin(GAN), "ganadoras", "resto")
n_total = len(pr)
pr = prob_vec(pr, "timestamp")
pr["p_lado"] = np.where(pr.lado == "Si", pr.p_si, 1 - pr.p_si)
pr["ventaja"] = pr.p_lado - pr.q
pr["fase"] = np.where(pr.durante, "durante", "antes")

# =============================================================================
p("# ¿Con qué información eligen las ganadoras?\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ} con las reglas de `informacion/REGLAS.md` (fijadas antes). "
  f"{len(GAN)} ganadoras elegidas con los eventos del {FECHAS[0]} al día anterior a {CORTE}; todo se mide en "
  f"{CORTE} a {FECHAS[-1]}. Con pronóstico y METAR disponibles: {n_(len(pr))} de {n_(n_total)} apuestas.\n")

p("## 1. ¿Apuestan a favor del modelo?\n")
p("\"A favor\" = el modelo le da a ese lado más probabilidad que el precio pagado. Antes del día: promedio de 11 "
  "modelos corregido. Durante el día: lo mismo, pero sabiendo la máxima/mínima registrada hasta 10 min antes.\n")
fil = []
res = {}
for fase in ("antes", "durante"):
    for gr in ("ganadoras", "resto"):
        x = pr[(pr.fase == fase) & (pr.grupo == gr)]
        a, c = x[x.ventaja > 0], x[x.ventaja <= 0]
        fav = a.usd.sum() / x.usd.sum()
        res[(fase, gr)] = fav
        fil.append([fase, gr, n_(len(x)), f"{100 * fav:.0f}%", f"{100 * (x.ventaja * x.usd).sum() / x.usd.sum():+.1f} pts",
                    f(x.pnl.sum() / x.usd.sum()), f(a.pnl.sum() / a.usd.sum()), f(c.pnl.sum() / c.usd.sum())])
tabla(["fase", "grupo", "apuestas", "% vol a favor del modelo", "ventaja media", "PnL/vol", "PnL/vol a favor",
       "PnL/vol en contra"], fil)
for fase in ("antes", "durante"):
    dif = res[(fase, "ganadoras")] - res[(fase, "resto")]
    p(f"- {fase} del día: ganadoras {100 * res[(fase, 'ganadoras')]:.0f}% vs resto {100 * res[(fase, 'resto')]:.0f}% "
      f"a favor ({100 * dif:+.0f} puntos) → **{'usan esta información' if dif >= LECTURA_PUNTOS else 'no se explica con esta información'}**.")
p("")

p("Ganadoras por país (las cajas en °F son las de EE.UU.):\n")
fil = []
for fase in ("antes", "durante"):
    for us in (True, False):
        x = pr[(pr.fase == fase) & (pr.grupo == "ganadoras") & (pr.eeuu == us)]
        y = pr[(pr.fase == fase) & (pr.grupo == "resto") & (pr.eeuu == us)]
        fil.append([fase, "EE.UU." if us else "resto del mundo", n_(len(x)), f(x.pnl.sum() / x.usd.sum()),
                    f"{100 * x[x.ventaja > 0].usd.sum() / x.usd.sum():.0f}%",
                    f"{100 * y[y.ventaja > 0].usd.sum() / y.usd.sum():.0f}%"])
tabla(["fase", "país", "apuestas ganadoras", "PnL/vol ganadoras", "% a favor (ganadoras)", "% a favor (resto)"], fil)

# =============================================================================
CINTA = {}
for (cid, lado), g in op.groupby(["condition_id", "lado"], sort=False):
    CINTA[(cid, lado)] = (g.timestamp.to_numpy(), g.q.to_numpy())

fotos = []
for slug, g in op.groupby("slug", sort=False):
    c0 = g.iloc[0]
    for T in DECISION_ANTES + DECISION_DURANTE:
        t = c0.ini + T * 3600
        x = g[g.timestamp < t]
        if x.empty:
            continue
        last = x.groupby("condition_id").p_tr.last()
        for cid, ps in last.items():
            fotos.append((cid, T, t, ps))
F = pd.DataFrame(fotos, columns=["condition_id", "T", "t", "precio_si"])
F = F.join(CJ[["ini", "slug", "fecha", "ciudad", "lo", "hi", "es_max", "gano_si", "mitad"]], on="condition_id")
F["h_rel"] = F["T"].astype(float)
F = prob_vec(F, "t")
filas = []
for r in F.itertuples():
    for lado, q, pl in (("Si", r.precio_si, r.p_si), ("No", 1 - r.precio_si, 1 - r.p_si)):
        if not (P_MIN <= q < P_MAX) or pl - q < UMBRAL:
            continue
        ts, qs = CINTA.get((r.condition_id, lado), (np.array([]), np.array([])))
        i = np.searchsorted(ts, r.t)
        if i >= len(ts) or ts[i] >= r.t + VENTANA:
            continue
        e = min(qs[i] + DESLIZ, 0.99)
        gana = float(r.gano_si if lado == "Si" else not r.gano_si)
        filas.append((r.slug, r.fecha, r.mitad, "durante" if r.durante else "antes", e, APUESTA / e * (gana - e)))
R = pd.DataFrame(filas, columns=["slug", "fecha", "mitad", "fase", "e", "pnl"])
R["usd"] = APUESTA


def boot(x, pct, semilla=1):
    ev = x.groupby("slug").agg(pnl=("pnl", "sum"), usd=("usd", "sum"))
    rng = np.random.default_rng(semilla)
    idx = rng.integers(0, len(ev), (4000, len(ev)))
    return np.percentile(ev.pnl.to_numpy()[idx].sum(1) / ev.usd.to_numpy()[idx].sum(1), [pct, 100 - pct])


p("## 2. Regla mecánica: comprar cuando el modelo ve ≥ 10 puntos de ventaja\n")
p(f"Fotos en {', '.join(f'{t:+d} h' for t in DECISION_ANTES + DECISION_DURANTE)} respecto del inicio del día local; "
  "entrada a la primera operación real de ese lado dentro de 120 min, +1 ¢; US$10 por compra.\n")
fil, alguna = [], False
fechas_p = sorted(R[R.mitad == "prueba"].fecha.unique())
med = fechas_p[len(fechas_p) // 2] if fechas_p else None
for fase in ("antes", "durante"):
    xd, xp = R[(R.fase == fase) & (R.mitad == "desc")], R[(R.fase == fase) & (R.mitad == "prueba")]
    rd = xd.pnl.sum() / xd.usd.sum() if len(xd) else np.nan
    rp = xp.pnl.sum() / xp.usd.sum() if len(xp) else np.nan
    lo, hi = boot(xp, 2.5) if xp.slug.nunique() > 1 else (np.nan, np.nan)
    a, b = xp[xp.fecha < med], xp[xp.fecha >= med]
    ra = a.pnl.sum() / a.usd.sum() if len(a) else np.nan
    rb = b.pnl.sum() / b.usd.sum() if len(b) else np.nan
    pasa = rp >= PASA_ROI and lo > 0 and ra > 0 and rb > 0
    alguna |= bool(pasa)
    fil.append([fase, f"{f(rd)} ({len(xd)})", f"**{f(rp)}** ({len(xp)})", f"{f(lo)} a {f(hi)}", f"{f(ra)} / {f(rb)}",
                "**PASA**" if pasa else "no"])
tabla(["fase", "descubrimiento (compras)", "prueba (compras)", "intervalo 95%", "mitades de la prueba", "veredicto"], fil)
p(f"**Veredicto de la regla: {'PASA' if alguna else 'no pasa'}.**\n")

open(os.path.join(CARPETA, "informe.md"), "w").write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

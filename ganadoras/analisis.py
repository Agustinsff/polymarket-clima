"""
QUE HACEN DISTINTO LAS BILLETERAS GANADORAS, y si eso se puede convertir en una regla mecanica.
Las reglas estan en ganadoras/REGLAS.md y se fijaron antes de correr esto. No opera nada.

Lee los datos crudos de la investigacion de rivales (rama investigacion-rivales, rivales/datos/) y escribe
ganadoras/informe.md.

Uso: python ganadoras/analisis.py CARPETA_DATOS
"""

import glob
import itertools
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
from estaciones import TZ  # noqa: E402

DATOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(CARPETA), "rivales", "datos")

# --- reglas (REGLAS.md) -------------------------------------------------------
P_MIN, P_MAX = 0.05, 0.90
MIN_EVENTOS, MIN_T, MIN_ROI = 20, 2.5, 0.03
MOMENTOS = [-np.inf, -24, -12, -6, 0, 6, 12, 24]
MOMENTOS_NOM = ["<-24", "-24a-12", "-12a-6", "-6a0", "0a6", "6a12", "12a24"]
PRECIOS = [0.05, 0.15, 0.30, 0.50, 0.70, 0.90]
PRECIOS_NOM = ["05-15", "15-30", "30-50", "50-70", "70-90"]
DECISION = [-36, -24, -12, -6, 0, 6, 12]
APUESTA, DESLIZ, VENTANA = 10.0, 0.01, 120 * 60
CAND_MIN_EVENTOS, CAND_MIN_ROI, CAND_MIN_T, CAND_MAX = 150, 0.03, 2.0, 5
PASA_ROI, PASA_PCT = 0.03, 2  # límite inferior del intervalo de 98 %
RASGOS = ["momento", "precio", "tipo", "lado", "puesto", "punta", "region"]

SALIDA = []


def p(*a):
    SALIDA.append(" ".join(str(x) for x in a))


def tabla(cab, filas):
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for f in filas:
        p("| " + " | ".join(str(x) for x in f) + " |")
    p("")


def n_(x):
    return f"{x:,.0f}".replace(",", ".")


def f(x, d=1):
    return "-" if pd.isna(x) else f"{100 * x:+.{d}f}%"


def leer(nombre, **kw):
    partes = [pd.read_csv(r, **kw) for r in sorted(glob.glob(os.path.join(DATOS, nombre + "_*.csv.gz")))]
    return pd.concat(partes, ignore_index=True)


def region(ciudad):
    z = TZ.get(ciudad, "UTC")
    if z.startswith("America"):
        return "America"
    if z.startswith(("Europe", "Africa")):
        return "Europa-Africa"
    return "Asia-Oceania"


# --- cajas y operaciones (igual que seguir/backtest.py) -------------------------
cj = leer("eventos", dtype=str).drop_duplicates("condition_id")
cj = cj[cj.precio_final_si.isin(["0", "1"])].copy()


def inicio_dia(r):
    d = datetime.fromisoformat(r.fecha)
    return datetime(d.year, d.month, d.day, tzinfo=ZoneInfo(TZ.get(r.ciudad, "UTC"))).timestamp()


cj["ini"] = [inicio_dia(r) for r in cj.itertuples()]
cj["gano_si"] = cj.precio_final_si == "1"
cj["tipo"] = np.where(cj.tipo.str.startswith("high"), "maxima", "minima")
cj["punta"] = np.where(cj.caja.str.contains("or below|or higher|or above", case=False), "punta", "medio")
cj["region"] = cj.ciudad.map(region)
FECHAS = sorted(cj.fecha.unique())
CORTE = FECHAS[len(FECHAS) // 2]
cj["mitad"] = np.where(cj.fecha < CORTE, "desc", "prueba")
CJ = cj.set_index("condition_id")

op = leer("trades", dtype={"condition_id": str, "wallet": str, "name": str, "pseudonym": str, "tx": str, "asset": str})
op = op.drop_duplicates(["tx", "asset", "side", "size", "price", "wallet"])
op = op[op.condition_id.isin(CJ.index)].copy()
op = op.join(CJ[["ini", "gano_si", "slug", "fecha", "ciudad", "tipo", "punta", "region", "mitad"]], on="condition_id")
op["lado_i"] = np.where(op.side == "BUY", op.outcome_index, 1 - op.outcome_index).astype(int)
op["lado"] = np.where(op.lado_i == 0, "Si", "No")
op["q"] = np.where(op.side == "BUY", op.price, 1 - op.price)
op["p_si"] = np.where(op.outcome_index == 0, op.price, 1 - op.price)
op["gana"] = np.where(op.lado_i == 0, op.gano_si, ~op.gano_si).astype(float)
op["usd"] = op["size"] * op.q
op["pnl"] = op["size"] * (op.gana - op.q)
op["h_rel"] = (op.timestamp - op.ini) / 3600
op["nombre"] = op.name.fillna(op.pseudonym).fillna("")
op = op.sort_values("timestamp").reset_index(drop=True)

# puesto de la caja (por último precio del Sí operado dentro del evento) en el momento de cada operación
puesto = np.zeros(len(op), dtype=int)
for slug, g in op.groupby("slug", sort=False):
    piv = pd.DataFrame({"t": np.arange(len(g)), "c": g.condition_id.to_numpy(), "p": g.p_si.to_numpy()})
    m = piv.pivot(index="t", columns="c", values="p").ffill()
    rk = m.rank(axis=1, ascending=False, method="first").to_numpy()
    col = {c: i for i, c in enumerate(m.columns)}
    puesto[g.index.to_numpy()] = rk[np.arange(len(g)), [col[c] for c in g.condition_id]]
op["puesto"] = np.minimum(puesto, 4).astype(int).astype(str)
op.loc[op.puesto == "4", "puesto"] = "4+"
op["momento"] = pd.cut(op.h_rel, MOMENTOS, labels=MOMENTOS_NOM, right=False).astype(str)
op["precio"] = pd.cut(op.q, PRECIOS, labels=PRECIOS_NOM, right=False).astype(str)

ap = op[(op.q >= P_MIN) & (op.q < P_MAX) & (op.h_rel < 24)].copy()
desc = ap[ap.mitad == "desc"]


def stats_eventos(x, col="pnl", vol="usd"):
    ev = x.groupby("slug").agg(pnl=(col, "sum"), usd=(vol, "sum"))
    n = len(ev)
    if n < 2 or ev.pnl.std() == 0:
        return n, np.nan, np.nan
    return n, ev.pnl.sum() / ev.usd.sum(), ev.pnl.mean() / (ev.pnl.std() / np.sqrt(n))


# =============================================================================
p("# Qué hacen distinto las billeteras ganadoras\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ} con las reglas de `ganadoras/REGLAS.md` (fijadas antes). "
  f"Descubrimiento: eventos del {FECHAS[0]} al día anterior a {CORTE}; prueba: {CORTE} a {FECHAS[-1]}. "
  f"Apuestas = compras entre 5 y 90 ¢ hasta el fin del día medido. Comisión 0.\n")

ev_w = desc.groupby(["wallet", "slug"]).agg(pnl=("pnl", "sum"), usd=("usd", "sum"))
w = ev_w.groupby("wallet").agg(n=("pnl", "size"), m=("pnl", "mean"), s=("pnl", "std"), pnl=("pnl", "sum"),
                               usd=("usd", "sum"))
w["t"] = w.m / (w.s / np.sqrt(w.n))
w["roi"] = w.pnl / w.usd
GAN = w[(w.n >= MIN_EVENTOS) & (w.t >= MIN_T) & (w.roi >= MIN_ROI)].index
desc = desc.assign(grupo=np.where(desc.wallet.isin(GAN), "ganadoras", "resto"))
g_desc = desc[desc.grupo == "ganadoras"]
p(f"Ganadoras (con el descubrimiento): **{len(GAN)}** billeteras, {n_(len(g_desc))} apuestas, "
  f"US$ {n_(g_desc.usd.sum())} de volumen, PnL/vol {f(g_desc.pnl.sum() / g_desc.usd.sum())}. "
  f"El resto: PnL/vol {f(desc[desc.grupo == 'resto'].pnl.sum() / desc[desc.grupo == 'resto'].usd.sum())}.\n")

g_prueba = ap[(ap.mitad == "prueba") & ap.wallet.isin(GAN)]
p(f"Las mismas ganadoras en la mitad de prueba (a su propio precio): PnL/vol "
  f"**{f(g_prueba.pnl.sum() / g_prueba.usd.sum())}** en {n_(len(g_prueba))} apuestas.\n")

p("## 1. En qué se diferencian (descubrimiento)\n")
p("Reparto del volumen y PnL/vol de cada grupo según cada rasgo.\n")
for r in RASGOS:
    fil = []
    tot = desc.groupby("grupo").usd.sum()
    orden = {"momento": MOMENTOS_NOM, "precio": PRECIOS_NOM}.get(r)
    for v, x in sorted(desc.groupby(r), key=lambda kv: orden.index(kv[0]) if orden else kv[0]):
        fila = [v]
        for gr in ("ganadoras", "resto"):
            y = x[x.grupo == gr]
            fila += [f"{100 * y.usd.sum() / tot[gr]:.0f}%", f(y.pnl.sum() / y.usd.sum()) if len(y) else "-"]
        fil.append(fila)
    p(f"**{r}**\n")
    tabla([r, "ganadoras: % vol", "ganadoras: PnL/vol", "resto: % vol", "resto: PnL/vol"], fil)

p("## 2. ¿Su ventaja es el lugar donde apuestan o lo que eligen adentro?\n")
celda = ["momento", "precio", "lado", "tipo"]
roi_celda = desc.groupby(celda).apply(lambda x: x.pnl.sum() / x.usd.sum())
gx = g_desc.join(roi_celda.rename("roi_celda"), on=celda)
esperado = (gx.usd * gx.roi_celda).sum()
real = g_desc.pnl.sum()
p(f"Si en cada celda (momento × precio × lado × tipo) las ganadoras hubieran ganado lo mismo que el promedio de "
  f"todos los takers de esa celda, habrían hecho **{f(esperado / g_desc.usd.sum())}** sobre su volumen. "
  f"Hicieron **{f(real / g_desc.usd.sum())}**. Lo que explica el lugar: "
  f"**{100 * esperado / real:.0f}%**; el resto es elección dentro de la celda (información propia).\n")

# =============================================================================
# regla mecánica: fotos en horarios fijos de decisión
CINTA = {}
for (cid, lado), g in op.groupby(["condition_id", "lado"], sort=False):
    CINTA[(cid, lado)] = (g.timestamp.to_numpy(), g.q.to_numpy())

filas = []
for slug, g in op.groupby("slug", sort=False):
    c0 = g.iloc[0]
    for T in DECISION:
        t = c0.ini + T * 3600
        x = g[g.timestamp < t]
        if x.empty:
            continue
        last = x.groupby("condition_id").p_si.last()
        rk = last.rank(ascending=False, method="first").astype(int)
        for cid, ps in last.items():
            for lado, q in (("Si", ps), ("No", 1 - ps)):
                if not (P_MIN <= q < P_MAX):
                    continue
                ts, qs = CINTA.get((cid, lado), (np.array([]), np.array([])))
                i = np.searchsorted(ts, t)
                if i >= len(ts) or ts[i] >= t + VENTANA:
                    continue
                e = min(qs[i] + DESLIZ, 0.99)
                b = CJ.loc[cid]
                gana = float(b.gano_si if lado == "Si" else not b.gano_si)
                filas.append((slug, b.fecha, b.mitad, str(T), q, lado, b.tipo, min(rk[cid], 4), b.punta, b.region, e,
                               APUESTA / e * (gana - e)))
R = pd.DataFrame(filas, columns=["slug", "fecha", "mitad", "momento", "q", "lado", "tipo", "puesto", "punta", "region",
                                 "e", "pnl"])
R["precio"] = pd.cut(R.q, PRECIOS, labels=PRECIOS_NOM, right=False).astype(str)
R["puesto"] = R.puesto.astype(str).replace("4", "4+")
R["usd"] = APUESTA
R["id"] = np.arange(len(R))

p("## 3. Reglas mecánicas (sin mirar quién opera)\n")
p(f"Fotos en {', '.join(f'{t:+d} h' for t in DECISION)} respecto del inicio del día local; compra de US$10 a la "
  f"primera operación real de ese lado dentro de 120 min, +1 ¢. {n_(len(R))} compras posibles.\n")
Rd, Rp = R[R.mitad == "desc"], R[R.mitad == "prueba"]
n, roi, t = stats_eventos(Rd)
p(f"Comprar **todo** (sin filtro) en descubrimiento: PnL/vol {f(roi)} (t {t:.1f}, {n} eventos).\n")

cands = []
for k in (1, 2):
    for rs in itertools.combinations(RASGOS, k):
        for vals, x in Rd.groupby(list(rs)):
            vals = vals if isinstance(vals, tuple) else (vals,)
            n, roi, t = stats_eventos(x)
            if n >= CAND_MIN_EVENTOS and roi >= CAND_MIN_ROI and t >= CAND_MIN_T:
                cands.append((t, roi, n, dict(zip(rs, vals)), set(x.id)))
cands.sort(key=lambda c: -c[0])
p(f"Celdas que cumplen en descubrimiento (≥{CAND_MIN_EVENTOS} eventos, ≥ +3 %, t ≥ 2): **{len(cands)}**.\n")
elegidas = []
for c in cands:
    if all(len(c[4] & e[4]) <= len(c[4]) / 2 for e in elegidas):
        elegidas.append(c)
    if len(elegidas) == CAND_MAX:
        break


def filtro(df, cond):
    m = np.ones(len(df), dtype=bool)
    for k, v in cond.items():
        m &= (df[k] == v).to_numpy()
    return df[m]


def boot(x, pct, semilla=1):
    ev = x.groupby("slug").agg(pnl=("pnl", "sum"), usd=("usd", "sum"))
    rng = np.random.default_rng(semilla)
    idx = rng.integers(0, len(ev), (4000, len(ev)))
    s, u = ev.pnl.to_numpy()[idx].sum(1), ev.usd.to_numpy()[idx].sum(1)
    return np.percentile(s / u, [pct, 100 - pct])


p("## 4. Prueba (mitad 2, una sola vez)\n")
fechas_p = sorted(Rp.fecha.unique())
med = fechas_p[len(fechas_p) // 2]
fil, alguna = [], False
for t_d, roi_d, n_d, cond, _ in elegidas:
    x = filtro(Rp, cond)
    n, roi, t = stats_eventos(x)
    lo, hi = boot(x, PASA_PCT) if n > 1 else (np.nan, np.nan)
    a, b = x[x.fecha < med], x[x.fecha >= med]
    ra = a.pnl.sum() / a.usd.sum() if len(a) else np.nan
    rb = b.pnl.sum() / b.usd.sum() if len(b) else np.nan
    pasa = roi >= PASA_ROI and lo > 0 and ra > 0 and rb > 0
    alguna |= pasa
    fil.append([" · ".join(f"{k}={v}" for k, v in cond.items()), f"{f(roi_d)} ({n_d})", f"**{f(roi)}** ({n})",
                f"{f(lo)} a {f(hi)}", f"{f(ra)} / {f(rb)}", "**PASA**" if pasa else "no"])
tabla(["regla", "descubrimiento (eventos)", "prueba (eventos)", "intervalo 98%", "mitades de la prueba", "veredicto"],
      fil)
n, roi, t = stats_eventos(Rp)
p(f"Referencia, comprar todo en prueba: {f(roi)}.\n")
p(f"**Veredicto: {'al menos una regla PASA' if alguna else 'ninguna regla pasa'}.**\n")

open(os.path.join(CARPETA, "informe.md"), "w").write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

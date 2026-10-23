"""
SEGUIR BILLETERAS GANADORAS: backtest fuera de muestra (walk-forward), sin operar nada.
Las reglas estan en seguir/REGLAS.md y se fijaron antes de correr esto.

Lee los datos crudos de la investigacion de rivales (rama investigacion-rivales, rivales/datos/) y escribe
seguir/informe.md.

Uso: python seguir/backtest.py CARPETA_DATOS
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

DATOS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(CARPETA), "rivales", "datos")

# --- reglas (REGLAS.md) -------------------------------------------------------
P_MIN, P_MAX = 0.05, 0.90
MIN_EVENTOS, MIN_T, MIN_ROI, MAX_BILLETERAS = 20, 2.5, 0.03, 50
DIAS_HISTORIA = 10
MIN_USD_SENAL = 20
APUESTA = 10.0
DESLIZ = 0.01
TOPE_PRECIO, TOPE_SOBRE_ELLOS = 0.95, 0.10
VENTANA = 120 * 60
LATENCIAS = [0, 1, 5, 15, 60]
L_PRINCIPAL = 15
AZAR_REPETICIONES = 20

SALIDA = []


def p(*a):
    SALIDA.append(" ".join(str(x) for x in a))


def tabla(cab, filas):
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for f in filas:
        p("| " + " | ".join(str(x) for x in f) + " |")
    p("")


def leer(nombre, **kw):
    partes = [pd.read_csv(r, **kw) for r in sorted(glob.glob(os.path.join(DATOS, nombre + "_*.csv.gz")))]
    return pd.concat(partes, ignore_index=True)


# --- cajas y operaciones (igual que rivales/analizar.py) -------------------------
cj = leer("eventos", dtype=str).drop_duplicates("condition_id")
cj = cj[cj.precio_final_si.isin(["0", "1"])].copy()


def inicio_dia(r):
    d = datetime.fromisoformat(r.fecha)
    return datetime(d.year, d.month, d.day, tzinfo=ZoneInfo(TZ.get(r.ciudad, "UTC"))).timestamp()


cj["ini"] = [inicio_dia(r) for r in cj.itertuples()]
cj["gano_si"] = cj.precio_final_si == "1"
cj["dia_fecha"] = (pd.to_datetime(cj.fecha).astype("int64") // 86_400_000_000_000).astype(int)
CJ = cj.set_index("condition_id")

op = leer("trades", dtype={"condition_id": str, "wallet": str, "name": str, "pseudonym": str, "tx": str, "asset": str})
op = op.drop_duplicates(["tx", "asset", "side", "size", "price", "wallet"])
op = op[op.condition_id.isin(CJ.index)].copy()
op = op.join(CJ[["ini", "gano_si", "slug", "dia_fecha", "ciudad"]], on="condition_id")
# todo pasado a "compra del lado X a precio q": vender el lado k a p es comprar el otro lado a 1-p
op["lado"] = np.where(op.side == "BUY", op.outcome_index, 1 - op.outcome_index).astype(int)
op["q"] = np.where(op.side == "BUY", op.price, 1 - op.price)
op["gana"] = np.where(op.lado == 0, op.gano_si, ~op.gano_si).astype(float)
op["usd"] = op["size"] * op.q
op["pnl"] = op["size"] * (op.gana - op.q)
op["h_rel"] = (op.timestamp - op.ini) / 3600
op["dia"] = (op.timestamp // 86400).astype(int)
op["nombre"] = op.name.fillna(op.pseudonym).fillna("")
op = op.sort_values("timestamp").reset_index(drop=True)
op["apuesta"] = (op.q >= P_MIN) & (op.q <= P_MAX) & (op.h_rel < 24)

# cinta por caja y lado, para buscar a que precio entro otro despues de la senal
CINTA = {}
for (cid, lado), g in op.groupby(["condition_id", "lado"], sort=False):
    CINTA[(cid, lado)] = (g.timestamp.to_numpy(), g.q.to_numpy(), g.wallet.to_numpy())

ap = op[op.apuesta]
dias = sorted(op.dia.unique())
dias_prueba = [d for d in dias if d >= dias[0] + DIAS_HISTORIA]


def stats_billeteras(hist):
    ev = hist.groupby(["wallet", "slug"]).agg(pnl=("pnl", "sum"), usd=("usd", "sum"))
    w = ev.groupby("wallet").agg(n=("pnl", "size"), m=("pnl", "mean"), s=("pnl", "std"), pnl=("pnl", "sum"),
                                 usd=("usd", "sum"))
    w["t"] = w.m / (w.s / np.sqrt(w.n))
    w["roi"] = w.pnl / w.usd
    return w[w.n >= MIN_EVENTOS]


ELEGIDAS, ELEGIBLES = {}, {}
for d in dias_prueba:
    hist = ap[(ap.dia_fecha <= d - 2) & (ap.timestamp < d * 86400)]
    w = stats_billeteras(hist)
    ELEGIBLES[d] = w.index.to_numpy()
    ELEGIDAS[d] = w[(w.t >= MIN_T) & (w.roi >= MIN_ROI)].sort_values("t", ascending=False).head(MAX_BILLETERAS).index


def senales(elegidas_por_dia):
    out = []
    for d in dias_prueba:
        x = ap[(ap.dia == d) & ap.wallet.isin(elegidas_por_dia[d]) & (ap.usd >= MIN_USD_SENAL)]
        out.append(x.drop_duplicates(["wallet", "condition_id", "lado"]))
    return pd.concat(out)


def copiar(sen, L):
    filas = []
    for s in sen.itertuples():
        ts, qs, ws = CINTA[(s.condition_id, s.lado)]
        if L == 0:
            e = s.q + DESLIZ
        else:
            i = np.searchsorted(ts, s.timestamp + L * 60)
            e = None
            while i < len(ts) and ts[i] < s.timestamp + L * 60 + VENTANA:
                if ws[i] != s.wallet:
                    e = qs[i] + DESLIZ
                    break
                i += 1
            if e is None:
                continue
        if e > TOPE_PRECIO or e > s.q + TOPE_SOBRE_ELLOS:
            continue
        filas.append((s.dia, s.slug, s.wallet, s.nombre, s.ciudad, s.q, e, s.gana, s.h_rel))
    c = pd.DataFrame(filas, columns=["dia", "slug", "wallet", "nombre", "ciudad", "q_ellos", "e", "gana", "h_rel"])
    c["pnl"] = APUESTA / c.e * (c.gana - c.e)
    return c


def resumen(c, boot=True, semilla=1):
    if len(c) == 0:
        return dict(n=0, roi=np.nan, lo=np.nan, hi=np.nan, t_dia=np.nan, pnl=0)
    vol = APUESTA * len(c)
    roi = c.pnl.sum() / vol
    lo = hi = np.nan
    if boot:
        ev = c.groupby("slug").pnl.agg(["sum", "size"])
        rng = np.random.default_rng(semilla)
        idx = rng.integers(0, len(ev), (2000, len(ev)))
        s, n = ev["sum"].to_numpy()[idx].sum(1), ev["size"].to_numpy()[idx].sum(1)
        lo, hi = np.percentile(s / (APUESTA * n), [5, 95])
    pd_ = c.groupby("dia").pnl.sum().reindex(dias_prueba, fill_value=0)
    t_dia = pd_.mean() / (pd_.std() / np.sqrt(len(pd_))) if pd_.std() > 0 else np.nan
    return dict(n=len(c), roi=roi, lo=lo, hi=hi, t_dia=t_dia, pnl=c.pnl.sum())


def f(x, d=1):
    return "-" if pd.isna(x) else f"{100 * x:+.{d}f}%"


# =============================================================================
fd = lambda d: datetime.fromtimestamp(d * 86400, timezone.utc).strftime("%d-%b")  # noqa: E731
p("# Seguir billeteras ganadoras: backtest fuera de muestra\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ} con las reglas de `seguir/REGLAS.md` (fijadas antes). "
  f"Historia desde {fd(dias[0])}; días de prueba {fd(dias_prueba[0])} a {fd(dias_prueba[-1])} ({len(dias_prueba)} días). "
  f"Copia de US$10 por señal, +1¢ sobre el precio que consiguió otro, comisión 0.\n")
n_eleg = [len(ELEGIDAS[d]) for d in dias_prueba]
p(f"Billeteras elegidas por día: mínimo {min(n_eleg)}, mediana {int(np.median(n_eleg))}, máximo {max(n_eleg)} "
  f"(de {int(np.median([len(ELEGIBLES[d]) for d in dias_prueba]))} con ≥{MIN_EVENTOS} eventos).\n")

SEN = senales(ELEGIDAS)
p(f"Señales: {len(SEN)} ({len(SEN) / len(dias_prueba):.0f} por día), de {SEN.wallet.nunique()} billeteras.\n")

p("## 1. ¿Seguirlas habría ganado? (según cuánto tardamos en copiar)\n")
fil, COP = [], {}
for L in LATENCIAS:
    c = copiar(SEN, L)
    COP[L] = c
    r = resumen(c)
    deriva = (c.e - DESLIZ - c.q_ellos).mean() if L else 0.0
    fil.append([f"{L} min" + (" **(principal)**" if L == L_PRINCIPAL else ""), r["n"], f"{100 * r['n'] / len(SEN):.0f}%",
                f"{100 * deriva:+.1f}¢", f"{r['pnl']:+.0f}", f"**{f(r['roi'])}**", f"{f(r['lo'])} a {f(r['hi'])}",
                f"{r['t_dia']:.1f}"])
tabla(["latencia", "copias", "llenadas", "precio vs el de ellos", "PnL US$", "PnL/vol", "intervalo 90%", "t por día"], fil)
p("L = 0 es su propio precio +1¢: el techo teórico (ganarías lo que ellos si copiaras al instante y sin moverles el precio).\n")

rp = resumen(COP[L_PRINCIPAL])
pasa = rp["roi"] >= 0.02 and rp["lo"] > 0
p(f"**Veredicto con la regla fijada (L = {L_PRINCIPAL} min): {'PASA' if pasa else 'NO PASA'}** "
  f"(PnL/vol {f(rp['roi'])}, límite inferior {f(rp['lo'])}; hacía falta ≥ +2% y > 0).\n")

p("## 2. Controles\n")
mitad = dias_prueba[len(dias_prueba) // 2]
fil = []
for nom, cond in (("1ª mitad de los días de prueba", lambda c: c.dia < mitad), ("2ª mitad", lambda c: c.dia >= mitad),
                  ("sólo antes del día (pronóstico)", lambda c: c.h_rel < 0),
                  ("sólo durante el día", lambda c: c.h_rel >= 0)):
    fil.append([nom] + [f(resumen(COP[L][cond(COP[L])], boot=False)["roi"]) + f" ({cond(COP[L]).sum()})"
                        for L in LATENCIAS])
tabla(["subconjunto"] + [f"L={L}" for L in LATENCIAS], fil)

p("Copiando billeteras **al azar** (misma cantidad por día, entre las que tienen ≥20 eventos, sin mirar si ganan); "
  f"{AZAR_REPETICIONES} sorteos:\n")
fil = []
rng = np.random.default_rng(7)
res_azar = {L: [] for L in LATENCIAS}
for k in range(AZAR_REPETICIONES):
    eleg = {d: rng.choice(ELEGIBLES[d], size=min(len(ELEGIDAS[d]), len(ELEGIBLES[d])), replace=False)
            for d in dias_prueba}
    s = senales(eleg)
    for L in (0, L_PRINCIPAL):
        res_azar[L].append(resumen(copiar(s, L), boot=False)["roi"])
for L in (0, L_PRINCIPAL):
    v = np.array(res_azar[L])
    fil.append([f"{L} min", f(np.mean(v)), f"{f(np.min(v))} a {f(np.max(v))}", f(resumen(COP[L], boot=False)["roi"])])
tabla(["latencia", "azar: PnL/vol medio", "azar: rango", "elegidas"], fil)

p(f"## 3. Por billetera (L = {L_PRINCIPAL} min, las de más copias)\n")
c = COP[L_PRINCIPAL]
g = c.groupby("wallet").agg(nombre=("nombre", "first"), copias=("pnl", "size"), pnl=("pnl", "sum"),
                            deriva=("e", "mean"), q=("q_ellos", "mean"))
g["roi"] = g.pnl / (APUESTA * g.copias)
fil = [[r.nombre or w[:8], r.copias, f"{r.pnl:+.0f}", f(r.roi), f"{100 * (r.deriva - DESLIZ - r.q):+.1f}¢"]
       for w, r in g.sort_values("copias", ascending=False).head(20).iterrows()]
tabla(["billetera", "copias", "PnL US$", "PnL/vol", "precio vs el de ellos"], fil)

# =============================================================================
p("## 4. Velocidad: ¿queda algo para el que ve el METAR a los ~4 min?\n")
p("Operaciones durante el día medido, entre 5¢ y 90¢ (las que apuestan a algo que todavía no está decidido), "
  "según el minuto de la hora UTC en que entraron. La mayoría de las estaciones informa a la hora en punto; "
  "algunas a :20/:50 o :30, eso mezcla un poco los tramos.\n")
du = op[(op.h_rel >= 0) & (op.h_rel < 24) & (op.q >= P_MIN) & (op.q <= P_MAX)]
mi = (du.timestamp % 3600) // 60
fil = []
for a, b in ((0, 2), (2, 5), (5, 10), (10, 30), (30, 60)):
    x = du[(mi >= a) & (mi < b)]
    fil.append([f":{a:02d}–:{b - 1:02d}", len(x), f"{x.usd.sum():,.0f}".replace(",", "."), f(x.pnl.sum() / x.usd.sum())])
tabla(["minuto", "operaciones", "volumen US$", "PnL/vol"], fil)

p("Lo mismo, pero copiando como en la sección 1: si alguien compra entre 5¢ y 90¢ en :00–:04, ¿a qué precio "
  "se consigue lo mismo unos minutos después y cuánto deja?\n")
pr = du[(mi < 5) & (du.usd >= MIN_USD_SENAL)]
pr = pr.assign(hora=pr.timestamp // 3600).drop_duplicates(["condition_id", "lado", "hora"])
fil = []
for L in (0, 2, 4, 6, 10):
    c = copiar(pr, L)
    r = resumen(c, boot=False)
    fil.append([f"{L} min", r["n"], f"{100 * ((c.e - DESLIZ - c.q_ellos).mean() if L else 0):+.1f}¢", f(r["roi"])])
tabla(["latencia", "copias", "precio vs el primero", "PnL/vol"], fil)

open(os.path.join(CARPETA, "informe.md"), "w").write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

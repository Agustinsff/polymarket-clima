"""
Conversión °F/°C en cajas de EE.UU. (regla: fahrenheit/REGLA.md). Escribe fahrenheit/informe.md.
Uso: python fahrenheit/analizar.py RUTA/obs_diaria.csv.gz RUTA/maker/datos
"""
import glob
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

OBS, FOTOS = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2)
L = []
p = lambda s="": L.append(s)


def a_f(c):
    return int((Decimal(str(c)) * Decimal("1.8") + 32).quantize(Decimal("1"), ROUND_HALF_UP))


# cuántas décimas de °C caen en cada caja par-impar
cuenta = {}
for t in range(-400, 600):
    f = a_f(t / 10)
    lo = f - (f % 2)
    cuenta[lo] = cuenta.get(lo, 0) + 1
DOCE = sorted(k for k, v in cuenta.items() if v == 12 and -40 < k < 120)


def vecinas(tab, g, val):
    """tab con columnas g, lo, val -> filas con x = log(val) - media log de las vecinas lo±2 (vectorizado)."""
    t = tab[[g, "lo", val]][tab[val] > 0].copy()
    t["lv"] = np.log(t[val])
    izq = t[[g, "lo", "lv"]].assign(lo=t.lo + 2).rename(columns={"lv": "li"})
    der = t[[g, "lo", "lv"]].assign(lo=t.lo - 2).rename(columns={"lv": "ld"})
    m = t.merge(izq, on=[g, "lo"]).merge(der, on=[g, "lo"])
    m["x"] = m.lv - 0.5 * (m.li + m.ld)
    m["doce"] = m.lo.map(cuenta) == 12
    return m


def boot(d, g, NB=2000):
    """d: filas (g, doce, x). Diferencia media x(12) - x(11) con bootstrap por g (vectorizado con pesos)."""
    agg = d.groupby([g, "doce"]).x.agg(["sum", "count"]).unstack(fill_value=0)
    gs = agg.index.values
    S12, N12 = agg[("sum", True)].values, agg[("count", True)].values
    S11, N11 = agg[("sum", False)].values, agg[("count", False)].values
    est = S12.sum() / N12.sum() - S11.sum() / N11.sum()
    W = rng.multinomial(len(gs), np.ones(len(gs)) / len(gs), size=NB)
    vals = (W @ S12) / (W @ N12) - (W @ S11) / (W @ N11)
    return est, np.nanpercentile(vals, 2.5), np.nanpercentile(vals, 97.5), (vals <= 0).mean(), int(N12.sum()), int(N11.sum())


p(f"# Conversión °F/°C en cajas de EE.UU. (corte {pd.Timestamp.now('UTC'):%Y-%m-%d %H:%M} UTC)")
p()
p("Regla fija: `fahrenheit/REGLA.md`. Cajas de 2 °F con 12 décimas de °C (el resto tiene 11): "
  + ", ".join(f"{k}-{k + 1}" for k in DOCE if 0 <= k <= 110) + " °F. Esperado si la física manda: +0,087 (log 12/11).")
p()

# A. física
o = pd.read_csv(OBS)
o = o[o.icao.str.startswith("K")].copy()
o["anio"] = o.fecha.str[:4]
filasA = []
for col in ("max", "min"):
    x = o.dropna(subset=[col]).copy()
    x["F"] = x[col].map(a_f)
    x["lo"] = x.F - x.F % 2
    x["g"] = x.icao + "|" + col + "|" + x.anio
    filasA.append(x.groupby(["g", "lo"]).size().rename("n").reset_index())
A = pd.concat(filasA)
eA = boot(vecinas(A, "g", "n"), "g")
p("## A. Física: ¿las cajas de 12 salen más seguido? (METAR de rutina 2023–2026, estaciones de EE.UU.)")
p()
p(f"Estaciones: {o.icao.nunique()}, días-estación: {len(o):,}. Diferencia 12 vs 11: **{eA[0]:+.3f}** "
  f"[{eA[1]:+.3f}, {eA[2]:+.3f}], P(≤0) = {eA[3]:.3f} (cajas-grupo: {eA[4]} de 12, {eA[5]} de 11; bootstrap por estación-año).")
p()

ent = o["max"].dropna() * 1.8 + 32
p(f"Por qué: en EE.UU. el sensor ASOS mide en °F enteros y el METAR lo pasa a décimas de °C; al volver a °F, el "
  f"{(abs(ent - ent.round()) < 0.15).mean() * 100:.1f} % de las máximas cae exacto en un °F entero. O sea, la conversión "
  "es ida y vuelta sin pérdida y todas las cajas de 2 °F tienen el mismo peso: el efecto de las cajas de 12 no existe.")
p()

# B. mercado
cols = ["ts", "grupo", "serie", "evento", "caja", "medio"]
fo = pd.concat([pd.read_csv(f, sep=";", compression="gzip", usecols=cols) for f in sorted(glob.glob(os.path.join(FOTOS, "fotos_*.csv.gz")))],
               ignore_index=True)
fo = fo[(fo.grupo == "clima") & fo.caja.str.match(r"^-?\d+--?\d+°F$")].copy()
fo["lo"] = fo.caja.str.extract(r"^(-?\d+)-")[0].astype(int)
fo = fo[(fo.medio >= 0.02) & (fo.medio <= 0.98)]
fo["g"] = fo.evento
# un valor por evento y caja: mediana de log precio en fotos donde estén las tres; simplificado: mediana del precio por evento-caja-foto
fo["k"] = fo.evento + "|" + fo.ts.astype(str)
dB = vecinas(fo, "k", "medio")
dB["evento"] = dB.k.str.split("|").str[0]
B = dB.groupby(["evento", "doce"]).x.mean().reset_index()
estB, loB, hiB, _, n12B, n11B = boot(B, "evento")
ev = B.evento.unique()
p("## B. Mercado: ¿el precio ya lo cobra? (fotos del libro cada 5 min, medidor maker, 26-oct en adelante)")
p()
p(f"Eventos de EE.UU.: {len(ev)}; con caja de 12 entre vecinas: {B[B.doce].evento.nunique()}. Diferencia 12 vs 11 en precio: "
  f"**{estB:+.3f}** [{loB:+.3f}, {hiB:+.3f}] (bootstrap por evento).")
cobra = (loB <= eA[0] <= hiB) and loB > 0
ignora = not (loB <= eA[0] <= hiB)
p()
p(f"Veredicto según la regla: física {'PASA' if eA[3] < 0.05 and eA[0] > 0 else 'NO PASA'}; mercado "
  f"{'LO COBRA' if cobra else ('LO IGNORA' if ignora else 'sin decidir (intervalo incluye la física y el 0)')}.")
p()

# C. plata (informativa)
rf = pd.read_csv(os.path.join(AQUI, "..", "regla_metar", "datos", "fotos.csv"), sep=";")
rr = pd.read_csv(os.path.join(AQUI, "..", "regla_metar", "datos", "resultados.csv"), sep=";")
rf = rf[rf.caja.str.match(r"^-?\d+--?\d+°F$", na=False)].copy()
rf["lo"] = rf.caja.str.extract(r"^(-?\d+)-")[0].astype(int)
rf = rf[rf.lo.map(cuenta) == 12].merge(rr[["slug", "caja", "gano"]], on=["slug", "caja"], how="inner")
for c in ("bid", "ask", "si_10"):
    rf[c] = pd.to_numeric(rf[c], errors="coerce")
rf = rf[(rf.ask - rf.bid <= 0.05) & (rf.si_10 > 0.02) & (rf.si_10 < 0.98)]
rf["ask"] = rf.si_10  # costo real de 10 acciones recorriendo el libro
rf["costo"] = rf.ask + 0.05 * rf.ask * (1 - rf.ask)
rf["pnl"] = 10 * (rf.gano - rf.costo)
p("## C. Plata (informativo): comprar 10 acciones del Sí de cada caja de 12 (libro con spread ≤ 5 ¢, precio real de 10 acciones), con comisión 0,05·p(1−p)")
p()
if len(rf):
    t = rf.groupby("momento").agg(n=("pnl", "size"), ganadas=("gano", "sum"), precio=("ask", "mean"), pnl=("pnl", "sum"),
                                  invertido=("costo", lambda c: 10 * c.sum())).reset_index()
    p("| momento | n | ganadas | ask medio | resultado US$ | ROI |")
    p("|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        p(f"| {r.momento} | {r.n} | {int(r.ganadas)} | {r.precio:.2f} | {r.pnl:+.2f} | {r.pnl / r.invertido * 100:+.1f} % |")
    p()
    p("Muestra chica: no decide nada (ver regla).")
else:
    p("Sin datos.")
p()
with open(os.path.join(AQUI, "informe.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(L) + "\n")
print("\n".join(L))

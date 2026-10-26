"""
Analisis de los mercados de clima lentos con la regla fija de otros_clima/REGLA.md.
Lee otros_clima/datos/ (lo que bajaron bajar.py y fuentes.py) y escribe otros_clima/informe_datos.md.

Uso: python otros_clima/analizar.py
"""

import calendar
import json
import os
import re

import numpy as np
import pandas as pd
from scipy.stats import norm

CARPETA = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(CARPETA, "datos")
MESES = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MESES.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
SALIDA = []
RNG = np.random.default_rng(1)


def p(*a):
    SALIDA.append(" ".join(str(x) for x in a))


def familia(t):
    t = t.lower()
    if "temperature increase" in t or "heat increase" in t:
        return "anomalia_mes"
    if "hottest" in t:
        return "mes_mas_caluroso"
    if "precipitation" in t or "rain" in t:
        return "lluvia"
    if "snow" in t:
        return "nieve"
    if "tornado" in t:
        return "tornados"
    if "storm" in t or "hurricane" in t:
        return "huracanes"
    if "sea ice" in t:
        return "hielo"
    return None


def fin_periodo(ev, inicio, fam):
    """F: fin del periodo medido (UTC). None si no se puede leer del titulo."""
    t = ev.lower()
    y0 = inicio.year
    if fam == "hielo":
        return pd.Timestamp(f"{y0}-10-01" if "min" in t else f"{y0}-04-01", tz="UTC")
    if fam == "huracanes" and "season" in t:
        return pd.Timestamp(f"{y0}-12-01", tz="UTC")
    m = re.search(r"\(?([a-z]+)\.? (\d{1,2})\s*[-–]\s*(?:([a-z]+)\.? )?(\d{1,2})\)?", t)
    if m and m.group(1) in MESES and fam == "nieve":
        mes = MESES[m.group(3)] if m.group(3) in MESES else MESES[m.group(1)]
        yy = y0 + (1 if mes < inicio.month - 6 else 0)
        return pd.Timestamp(yy, mes, int(m.group(4)), tz="UTC") + pd.Timedelta(days=1, hours=5)
    ym = re.search(r"(20\d\d)", t)
    for w in re.findall(r"[a-z]+", t):
        if w in MESES and w not in ("may",) or (w == "may" and re.search(r"\bmay\b", t) and fam != "nieve"):
            mes = MESES[w]
            yy = int(ym.group(1)) if ym else (y0 + (1 if mes < inicio.month - 6 else 0))
            return pd.Timestamp(yy, mes, calendar.monthrange(yy, mes)[1], tz="UTC") + pd.Timedelta(days=1, hours=5)
    if ym and ("year" in t or re.search(r"in 20\d\d\?", t)):
        return pd.Timestamp(int(ym.group(1)) + 1, 1, 1, 5, tz="UTC")
    return None


def tasa(c):
    try:
        return float(json.loads(c).get("rate", 0))
    except Exception:
        return 0.0


def cargar():
    m = pd.read_csv(os.path.join(DATOS, "mercados.csv.gz"), low_memory=False)
    m = m[(m.cerrado == True) & m.condition_id.notna()].copy()  # noqa: E712
    m["fam"] = m.evento.fillna("").map(familia)
    m = m[m.fam.notna()].copy()
    m["inicio"] = pd.to_datetime(m.inicio, utc=True, format="mixed", errors="coerce")
    m["C"] = pd.to_datetime(m.cerrado_hora, utc=True, format="mixed", errors="coerce")
    m["F"] = [fin_periodo(e, i, f) if pd.notna(i) else None for e, i, f in zip(m.evento, m.inicio, m.fam)]
    m["gano"] = pd.to_numeric(m.precio_final_si, errors="coerce") > 0.5
    m["tasa"] = m.comision.map(tasa)
    t = pd.read_csv(os.path.join(DATOS, "trades.csv.gz"))
    t["t"] = pd.to_datetime(t.timestamp, unit="s", utc=True)
    # precio de comprar el Si: compras de Si a p, o ventas de No a q (equivale a comprar Si a 1-q)
    t["p_si"] = np.where(t.outcome_index == 0, t.price, 1 - t.price)
    t["compra_si"] = ((t.outcome_index == 0) & (t.side == "BUY")) | ((t.outcome_index == 1) & (t.side == "SELL"))
    t["usd"] = t.price * t["size"]
    return m, t


def precio(tm, H, lado):
    """precio medio de ejecucion de comprar `lado` (si/no) en la hora anterior a H"""
    v = tm[(tm.t >= H - pd.Timedelta(hours=1)) & (tm.t < H)]
    if lado == "si":
        v = v[v.compra_si]
        return np.average(v.p_si, weights=v["size"]) if len(v) else None
    v = v[~v.compra_si]
    return np.average(1 - v.p_si, weights=v["size"]) if len(v) else None


def roi(ops):
    if not ops:
        return None, None, 0
    d = pd.DataFrame(ops, columns=["evento", "costo", "pago"])
    r = (d.pago.sum() - d.costo.sum()) / d.costo.sum()
    ev = d.groupby("evento")[["costo", "pago"]].sum()
    bs = []
    for _ in range(2000):
        s = ev.sample(len(ev), replace=True, random_state=RNG.integers(1e9))
        bs.append((s.pago.sum() - s.costo.sum()) / s.costo.sum())
    return r, float(np.mean(np.array(bs) < 0)), len(d)


def modelo_era5():
    """prob. de cada mes segun ERA5 (REGLA.md punto 3): devuelve {Period: (media, sd)}"""
    g = pd.read_csv(os.path.join(DATOS, "fuentes", "gistemp_glb.csv"), skiprows=1, na_values=["***", "****"])
    g = g.melt(id_vars="Year", value_vars=list(calendar.month_abbr)[1:], var_name="mes", value_name="gis").dropna()
    g["m"] = pd.to_datetime(g.Year.astype(str) + g.mes, format="%Y%b").dt.to_period("M")
    e = pd.read_csv(os.path.join(DATOS, "fuentes", "era5_diario_2t.csv"), comment="#", header=None,
                    names=["d", "t", "c", "a", "st"])
    e["d"] = pd.to_datetime(e.d, errors="coerce", format="%Y-%m-%d")
    e = e.dropna(subset=["d"])
    e["a"] = pd.to_numeric(e.a, errors="coerce")
    era = e.groupby(e.d.dt.to_period("M")).a.mean()
    x = g.set_index("m")[["gis"]].join(era.rename("era"), how="outer").sort_index().loc["1995-01":]
    x["mo"] = x.index.month
    out = {}
    for i in range(120, len(x)):
        if pd.isna(x.era.iloc[i]):
            continue
        tr = x.iloc[i - 120:i].dropna()
        dif = tr.gis - tr.era
        off = dif.groupby(tr.mo).mean()
        rec = (dif - dif.groupby(tr.mo).transform("mean")).iloc[-12:].mean()
        out[x.index[i]] = (x.era.iloc[i] + off[x.mo.iloc[i]] + rec, 0.045)
    return out


def caja_rango(txt):
    """(lo, hi) en grados de la caja de anomalia; None si no se lee"""
    s = (txt or "").replace("º", "").replace("°", "").replace("C", "").replace("pt", ".").replace("–", "-")
    n = [float(v) for v in re.findall(r"\d+\.\d+", s)]
    if len(n) >= 2:
        return n[0] - 0.005, n[1] + 0.005
    if len(n) == 1 and (">" in s or "more" in s.lower() or "above" in s.lower() or "greater" in s.lower()):
        return n[0] + 0.005, 9
    if len(n) == 1 and ("<" in s or "less" in s.lower() or "below" in s.lower()):
        return -9, n[0] - 0.005
    return None


def main():
    m, t = cargar()
    tg = dict(tuple(t.groupby("mercado_id")))
    p("# Mercados de clima lentos: resultados con la regla fija (REGLA.md)\n")
    p(f"Mercados cerrados en las familias: {len(m)} ({m.evento_id.nunique()} eventos); "
      f"con F leído: {m.F.notna().sum()}; con operaciones bajadas: {m.mercado_id.isin(tg).sum()}.\n")
    p("## Volumen por familia y año (US$ miles)\n")
    m["anio"] = m.C.dt.year
    v = m.pivot_table(index="fam", columns="anio", values="volumen", aggfunc="sum").fillna(0) / 1e3
    p(v.round(0).to_markdown())
    p("\nEventos por familia y año:\n")
    p(m.drop_duplicates("evento_id").pivot_table(index="fam", columns="anio", values="evento_id", aggfunc="count")
      .fillna(0).astype(int).to_markdown())

    m = m[m.F.notna() & m.C.notna()].copy()
    m["H1"] = m.F - pd.Timedelta(days=7)
    m["H2"] = m.F
    m["H3"] = m.F + (m.C - m.F) / 2
    filas = []
    for r in m.itertuples():
        tm = tg.get(r.mercado_id)
        if tm is None:
            continue
        for h in ("H1", "H2", "H3"):
            H = getattr(r, h)
            if h == "H3" and r.C <= r.F:
                continue
            ps, pn = precio(tm, H, "si"), precio(tm, H, "no")
            filas.append(dict(fam=r.fam, evento=r.evento_id, mercado=r.mercado_id, caja=r.caja or r.pregunta, h=h,
                              gano=r.gano, tasa=r.tasa, p_si=ps, p_no=pn,
                              ref=tm[tm.t < H].sort_values("t").p_si.iloc[-1] if (tm.t < H).any() else None))
    d = pd.DataFrame(filas)
    p("\n## 1. Calibración (precio de referencia = última operación antes de H)\n")
    d["bin"] = pd.cut(d.ref, [0, .05, .2, .5, .8, .95, 1.0001], right=False,
                      labels=["0-5", "5-20", "20-50", "50-80", "80-95", "95-100"])
    for h in ("H1", "H2", "H3"):
        x = d[(d.h == h) & d.ref.notna()]
        tab = x.groupby(["fam", "bin"], observed=True).agg(n=("gano", "size"), precio=("ref", "mean"), gano=("gano", "mean"))
        p(f"\n### {h}\n")
        p(tab.round(3).to_markdown())

    p("\n## 2. Reglas mecánicas (precio de ejecución de la hora previa + comisión + 1 ¢)\n")
    p("| regla | momento | familia | ops | ROI | P(ROI<0) |\n|---|---|---|---|---|---|")
    def costo(px, tasa_):
        px = min(px + 0.01, 0.999)
        return px + tasa_ * px * (1 - px)
    for h in ("H1", "H2", "H3"):
        x = d[d.h == h]
        for fam in sorted(x.fam.unique()) + ["TODAS"]:
            y = x if fam == "TODAS" else x[x.fam == fam]
            reglas = {"a fav Si": [], "b No 5-30": [], "c Si 5-30": []}
            for ev, g in y.groupby("evento"):
                gg = g[g.ref.notna()]
                if len(gg) >= 2:
                    f = gg.loc[gg.ref.idxmax()]
                    if f.p_si is not None and not pd.isna(f.p_si):
                        reglas["a fav Si"].append((ev, costo(f.p_si, f.tasa), float(f.gano)))
                for q in gg.itertuples():
                    if 0.05 <= q.ref <= 0.30:
                        if q.p_no is not None and not pd.isna(q.p_no):
                            reglas["b No 5-30"].append((ev, costo(q.p_no, q.tasa), float(not q.gano)))
                        if q.p_si is not None and not pd.isna(q.p_si):
                            reglas["c Si 5-30"].append((ev, costo(q.p_si, q.tasa), float(q.gano)))
            for k, ops in reglas.items():
                r_, pn_, n_ = roi(ops)
                if n_:
                    p(f"| {k} | {h} | {fam} | {n_} | {r_:+.1%} | {pn_:.2f} |")

    p("\n## 3. Anomalía global: modelo ERA5 en H3 (comprar si prob − precio ≥ 0,10)\n")
    mod = modelo_era5()
    ops, filas3 = [], []
    for r in m[(m.fam == "anomalia_mes")].itertuples():
        per = (r.F - pd.Timedelta(days=2)).to_period("M")
        rg = caja_rango(r.caja or r.pregunta)
        if per not in mod or rg is None:
            continue
        mu, sd = mod[per]
        pr = norm.cdf(rg[1], mu, sd) - norm.cdf(rg[0], mu, sd)
        tm = tg.get(r.mercado_id)
        if tm is None:
            continue
        ps = precio(tm, r.H3, "si")
        pn = precio(tm, r.H3, "no")
        filas3.append((r.evento_id, str(per), r.caja, round(pr, 3), ps, r.gano))
        if ps is not None and pr - ps >= 0.10:
            ops.append((r.evento_id, costo(ps, r.tasa), float(r.gano)))
        if pn is not None and (1 - pr) - pn >= 0.10:
            ops.append((r.evento_id, costo(pn, r.tasa), float(not r.gano)))
    r_, pn_, n_ = roi(ops)
    p(f"Cajas con modelo y precio: {sum(1 for f in filas3 if f[4] is not None)} de {len(filas3)}; operaciones: {n_}; "
      + (f"ROI {r_:+.1%}, P(ROI<0) {pn_:.2f}" if n_ else "sin operaciones"))
    f3 = pd.DataFrame(filas3, columns=["evento", "mes", "caja", "prob_era5", "precio_H3", "gano"])
    if len(f3):
        z = f3.dropna(subset=["precio_H3"])
        p(f"\nBrier en H3 (cajas con precio): modelo {((z.prob_era5 - z.gano) ** 2).mean():.4f}, "
          f"mercado {((z.precio_H3 - z.gano) ** 2).mean():.4f}, n={len(z)}")

    p("\n## 4. Cosecha después de F: precio de la caja ganadora y dinero operado por debajo de 95 ¢\n")
    p("| familia | eventos | mediana F+1d | F+3d | F+7d | US$ comprados <95 ¢ después de F | por evento |\n|---|---|---|---|---|---|---|")
    for fam, g in m[m.gano].groupby("fam"):
        a, b, c, usd, nev = [], [], [], 0.0, 0
        for r in g.itertuples():
            tm = tg.get(r.mercado_id)
            if tm is None or r.C <= r.F:
                continue
            nev += 1
            for lst, dd in ((a, 1), (b, 3), (c, 7)):
                H = r.F + pd.Timedelta(days=dd)
                if H < r.C and (tm.t < H).any():
                    lst.append(tm[tm.t < H].sort_values("t").p_si.iloc[-1])
            w = tm[(tm.t > r.F) & tm.compra_si & (tm.p_si < 0.95)]
            usd += (w.p_si * w["size"]).sum()
        med = lambda l: f"{np.median(l):.2f}" if l else "–"  # noqa: E731
        p(f"| {fam} | {nev} | {med(a)} | {med(b)} | {med(c)} | {usd:,.0f} | {usd / max(nev, 1):,.0f} |")

    with open(os.path.join(CARPETA, "informe_datos.md"), "w") as f:
        f.write("\n".join(SALIDA) + "\n")
    print("\n".join(SALIDA))


if __name__ == "__main__":
    main()

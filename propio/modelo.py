"""
PRONOSTICO PROPIO - PASO 2: EL MODELO POR ESTACION (reglas en propio/REGLAS.md, fijadas el 3-nov-2026).

Para cada estacion, serie (max/min), horizonte (1 o 2 dias) y dia D, arma una distribucion normal
(media, desvio) de la temperatura real usando SOLO lo que se sabia al pronosticar: pronosticos de
modelos para D hechos h dias antes y observaciones hasta D-h-1.

Candidatos (cerrados en REGLAS.md):
  M0       promedio de modelos, cada uno menos su sesgo de los ultimos 30 dias; desvio = error
           cuadratico medio de los ultimos 30 dias del propio M0 (fuera de muestra).
  M1       EMOS: media = a + suma w_m * f_m (ridge hacia pesos iguales), desvio^2 = c + d * dispersion^2;
           entrenado con los ultimos 120 dias + la misma epoca (+-45 dias) de los anios anteriores.
  M1-EEUU  M1 sumando NBM (NBS) y MOS de GFS como entradas, solo estaciones de EE.UU.

Parametros fijados el 4-nov-2026 ANTES de correr nada: LAMBDA=20, minimo 40 dias de entrenamiento,
desvio minimo 0,4 °C, modelos con >=80 % de datos en la ventana.

Uso: python propio/modelo.py --datos DIR   (DIR = copia de la rama propio-datos)
Salida: propio/resultados_modelo.md y DIR/predicciones.csv.gz (para el paso 3).
"""

import argparse
import csv
import gzip
import math
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
import json  # noqa: E402

EST = json.load(open(os.path.join(AQUI, "estaciones.json"), encoding="utf-8"))

HORIZONTES = [1, 2]
LAMBDA = 20.0
MIN_ENTRENAR = 40
SD_MIN = 0.4
VENTANA = 120
EPOCA = 45
COBERTURA = 0.8
SEL_DESDE, SEL_HASTA = date(2025, 10, 1), date(2026, 9, 30)   # periodo para elegir metodo
EVAL_DESDE = date(2024, 9, 1)                                   # antes no hay con que entrenar


def leer(ruta):
    with gzip.open(ruta, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f2c(f):
    return (float(f) - 32) * 5 / 9


# ---------------------------------------------------------------------------
# DATOS

def cargar(datos):
    obs = {}
    for f in leer(os.path.join(datos, "obs_diaria.csv.gz")):
        if f["max"] not in ("", "None") and f["min"] not in ("", "None"):
            obs[(f["icao"], f["fecha"])] = (float(f["max"]), float(f["min"]))
    pron = defaultdict(dict)       # (icao, fecha, h) -> {modelo: (max, min)}
    for icao in EST:
        ruta = os.path.join(datos, "pron", f"{icao}.csv.gz")
        if not os.path.exists(ruta):
            continue
        for f in leer(ruta):
            h = int(f["h"])
            if h in HORIZONTES:
                pron[(icao, f["fecha"], h)][f["modelo"]] = (float(f["max"]), float(f["min"]))
    mos = defaultdict(dict)        # (icao, fecha, h) -> {"MOS_NBS": (max, min), ...}
    for icao in EST:
        ruta = os.path.join(datos, "mos", f"{icao}.csv.gz")
        if os.path.exists(ruta):
            cargar_mos(icao, leer(ruta), mos)
    return obs, pron, mos


def cargar_mos(icao, filas, mos):
    """MOS/NBM: n_x con hora de validez 00Z = maxima del dia anterior (local EE.UU.), 12Z = minima
    de ese dia. Para el horizonte h se usa la corrida mas nueva con al menos 24*h horas de anticipacion
    a esa hora de validez (misma idea que 'previous_day h' de Open-Meteo)."""
    mejor = {}   # (modelo, fecha, serie, h) -> (runtime, valor)
    for f in filas:
        if f["modelo"] not in ("NBS", "GFS"):
            continue
        ft = datetime.strptime(f["ftime"], "%Y-%m-%d %H:%M:%S")
        rt = datetime.strptime(f["runtime"], "%Y-%m-%d %H:%M:%S")
        if ft.hour == 0:
            serie, fecha = 0, (ft - timedelta(days=1)).date()
        elif ft.hour == 12:
            serie, fecha = 1, ft.date()
        else:
            continue
        horas = (ft - rt).total_seconds() / 3600
        for h in HORIZONTES:
            if horas >= 24 * h:
                k = (f["modelo"], fecha.isoformat(), serie, h)
                if k not in mejor or rt > mejor[k][0]:
                    mejor[k] = (rt, f2c(f["n_x"]))
    tmp = defaultdict(dict)
    for (modelo, fecha, serie, h), (_, v) in mejor.items():
        tmp[(fecha, h, modelo)][serie] = v
    for (fecha, h, modelo), d in tmp.items():
        if 0 in d and 1 in d:
            mos[(icao, fecha, h)]["MOS_" + modelo] = (d[0], d[1])


# ---------------------------------------------------------------------------
# METODOS

def crps_normal(mu, sd, y):
    z = (y - mu) / sd
    pdf = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
    cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return sd * (z * (2 * cdf - 1) + 2 * pdf - 1 / math.sqrt(math.pi))


def ventana(ords, d_ord, h):
    """Indices de entrenamiento: ultimos VENTANA dias conocidos + misma epoca de anios anteriores."""
    tope = d_ord - h - 1
    sel = (ords <= tope) & (ords > tope - VENTANA)
    for k in (1, 2, 3):
        c = d_ord - 365 * k
        sel |= (ords <= tope) & (np.abs(ords - c) <= EPOCA)
    return np.nonzero(sel)[0]


def emos(F, y, idx, hoy_f, cols_hoy):
    """Ajusta M1 con las filas idx y predice para hoy. None si no alcanza."""
    usar = [j for j in cols_hoy if np.mean(~np.isnan(F[idx, j])) >= COBERTURA]
    if len(usar) < 2:
        return None
    X = F[np.ix_(idx, usar)]
    ok = ~np.isnan(X).any(axis=1)
    X, yy = X[ok], y[idx][ok]
    n, k = X.shape
    if n < MIN_ENTRENAR:
        return None
    xm, ym = X.mean(axis=0), yy.mean()
    Xc = X - xm
    w = np.linalg.solve(Xc.T @ Xc + LAMBDA * np.eye(k), Xc.T @ (yy - ym) + LAMBDA * np.full(k, 1 / k))
    a = ym - xm @ w
    r2 = (yy - a - X @ w) ** 2 * n / max(n - k - 1, 1)
    s2 = X.var(axis=1)
    A = np.column_stack([np.ones(n), s2])
    c, d = np.linalg.lstsq(A, r2, rcond=None)[0]
    c, d = max(c, 0.0), max(d, 0.0)
    if c == 0 and d == 0:
        c = r2.mean()
    x = hoy_f[usar]
    mu = a + x @ w
    sd = math.sqrt(max(c + d * x.var(), SD_MIN ** 2))
    return mu, sd


def correr(obs, pron, mos):
    salida = []
    for icao, info in EST.items():
        for serie_i, serie in enumerate(("max", "min")):
            if serie not in info["series"]:
                continue
            for h in HORIZONTES:
                fechas = sorted({f for (i, f, hh) in pron if i == icao and hh == h and (icao, f) in obs})
                if len(fechas) < MIN_ENTRENAR:
                    continue
                modelos = sorted({m for f in fechas for m in pron[(icao, f, h)]})
                extra = sorted({m for f in fechas for m in mos.get((icao, f, h), {})})
                cols = modelos + extra
                F = np.full((len(fechas), len(cols)), np.nan)
                for i, f in enumerate(fechas):
                    fuente = dict(pron[(icao, f, h)])
                    fuente.update(mos.get((icao, f, h), {}))
                    for j, m in enumerate(cols):
                        if m in fuente:
                            F[i, j] = fuente[m][serie_i]
                y = np.array([obs[(icao, f)][serie_i] for f in fechas])
                ords = np.array([date.fromisoformat(f).toordinal() for f in fechas])
                nm = len(modelos)
                errs0 = []       # (ord, error) de M0, para su desvio fuera de muestra
                for i, f in enumerate(fechas):
                    d = date.fromisoformat(f)
                    if d < EVAL_DESDE - timedelta(days=60):
                        continue
                    hoy = F[i]
                    cols_hoy = [j for j in range(nm) if not np.isnan(hoy[j])]
                    if len(cols_hoy) < 2:
                        continue
                    tope = ords[i] - h - 1
                    # M0
                    rec = (ords <= tope) & (ords > tope - 30)
                    corr = []
                    for j in cols_hoy:
                        e = F[rec, j] - y[rec]
                        e = e[~np.isnan(e)]
                        if len(e) >= 10:
                            corr.append(hoy[j] - e.mean())
                    m0 = None
                    if len(corr) >= 2:
                        mu0 = float(np.mean(corr))
                        prev = [e for (o, e) in errs0 if tope - 30 < o <= tope]
                        sd0 = math.sqrt(np.mean(np.square(prev))) if len(prev) >= 10 else None
                        errs0.append((ords[i], y[i] - mu0))
                        if sd0:
                            m0 = (mu0, max(sd0, SD_MIN))
                    idx = ventana(ords, ords[i], h)
                    m1 = emos(F, y, idx, hoy, cols_hoy)
                    cols_us = cols_hoy + [j for j in range(nm, len(cols)) if not np.isnan(hoy[j])]
                    m1u = emos(F, y, idx, hoy, cols_us) if len(cols_us) > len(cols_hoy) else None
                    if d < EVAL_DESDE:
                        continue
                    salida.append({"icao": icao, "serie": serie, "h": h, "fecha": f, "real": y[i],
                                   "M0": m0, "M1": m1, "M1-EEUU": m1u})
    return salida


# ---------------------------------------------------------------------------
# PROBABILIDAD POR CAJA (para el paso 3)

def prob_caja(mu, sd, lo, hi, en_f, entero):
    """P(la temperatura resuelta cae en la caja [lo, hi] (grados enteros de Polymarket, en la unidad
    del mercado; None = abierta). Polymarket redondea .5 hacia arriba; en °F convierte antes.
    Si el METAR solo trae enteros (entero=True) la caja k va de k-0,5 a k+0,5 en °C igual."""
    def cdf(x):
        return 0.5 * (1 + math.erf((x - mu) / (sd * math.sqrt(2))))

    def a_c(v):
        return (v - 32) * 5 / 9 if en_f else v
    b_lo = -math.inf if lo is None else a_c(lo - 0.5)
    b_hi = math.inf if hi is None else a_c(hi + 0.5)
    return max(0.0, (1 if b_hi == math.inf else cdf(b_hi)) - (0 if b_lo == -math.inf else cdf(b_lo)))


# ---------------------------------------------------------------------------
# INFORME

def informe(filas, datos):
    def tabla(sub, metodos):
        comunes = [f for f in sub if all(f[m] for m in metodos)]
        out = {}
        for m in metodos:
            c = [crps_normal(f[m][0], f[m][1], f["real"]) for f in comunes]
            a = [abs(f["real"] - f[m][0]) for f in comunes]
            out[m] = (len(comunes), float(np.mean(c)) if c else None, float(np.mean(a)) if a else None)
        return out

    sel = [f for f in filas if SEL_DESDE.isoformat() <= f["fecha"] <= SEL_HASTA.isoformat()]
    dias = sorted({f["fecha"] for f in sel})
    lineas = ["# Pronóstico propio: elección del método (paso 2)", "",
              f"Generado {datetime.utcnow():%Y-%m-%d %H:%M} UTC. Período de elección "
              f"{SEL_DESDE} a {SEL_HASTA} (reglas en REGLAS.md); días con datos: "
              f"{dias[0] if dias else '-'} a {dias[-1] if dias else '-'} ({len(dias)}).", "",
              "CRPS = error de la distribución completa (°C, menor es mejor). EMA = error medio absoluto "
              "de la media. Todos los métodos se miden sobre los mismos días.", ""]
    todos = tabla(sel, ["M0", "M1"])
    lineas += ["## Todas las estaciones", "", "| Método | Casos | CRPS | EMA |", "|---|---|---|---|"]
    for m, (n, c, a) in todos.items():
        lineas.append(f"| {m} | {n} | {c:.3f} | {a:.3f} |" if c else f"| {m} | {n} | - | - |")
    for h in HORIZONTES:
        t = tabla([f for f in sel if f["h"] == h], ["M0", "M1"])
        lineas.append("")
        lineas.append(f"Horizonte {h}: " + ", ".join(f"{m} {c:.3f}" for m, (n, c, a) in t.items() if c))
    us = [f for f in sel if f["icao"].startswith("K")]
    tus = tabla(us, ["M0", "M1", "M1-EEUU"])
    lineas += ["", "## EE.UU. (con NBM y MOS)", "", "| Método | Casos | CRPS | EMA |", "|---|---|---|---|"]
    for m, (n, c, a) in tus.items():
        lineas.append(f"| {m} | {n} | {c:.3f} | {a:.3f} |" if c else f"| {m} | {n} | - | - |")
    # regla de eleccion
    lineas += ["", "## Elección (regla fija)", ""]
    c0, c1 = todos["M0"][1], todos["M1"][1]
    if c0 and c1:
        gana = "M1" if c1 <= 0.98 * c0 else "M0"
        lineas.append(f"M1 vs M0: {100 * (1 - c1 / c0):+.1f} % de CRPS → se usa **{gana}** "
                      "(M1 tiene que ganar por 2 % o más).")
        cu, c1u = tus["M1"][1], tus["M1-EEUU"][1]
        if gana == "M1" and cu and c1u:
            lineas.append(f"En EE.UU., M1-EEUU vs M1: {100 * (1 - c1u / cu):+.1f} % → "
                          f"{'se usa M1-EEUU' if c1u <= 0.98 * cu else 'se usa M1'} en EE.UU.")
    if len(dias) < 300:
        lineas += ["", f"**Provisorio**: faltan datos del período de elección ({len(dias)} de 365 días)."]
    open(os.path.join(AQUI, "resultados_modelo.md"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    with gzip.open(os.path.join(datos, "predicciones.csv.gz"), "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["icao", "serie", "h", "fecha", "real", "m0_mu", "m0_sd", "m1_mu", "m1_sd", "m1u_mu", "m1u_sd"])
        for f in filas:
            fila = [f["icao"], f["serie"], f["h"], f["fecha"], f["real"]]
            for m in ("M0", "M1", "M1-EEUU"):
                fila += [round(f[m][0], 3), round(f[m][1], 3)] if f[m] else ["", ""]
            w.writerow(fila)
    print("\n".join(lineas))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", required=True)
    a = ap.parse_args()
    obs, pron, mos = cargar(a.datos)
    filas = correr(obs, pron, mos)
    informe(filas, a.datos)


if __name__ == "__main__":
    main()

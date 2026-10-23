"""
INVESTIGACION (sin operar): cuando un METAR mata una caja, ¿cuanto tardan los demas en llevarse la plata
y cuanto queda para el que llega 10 s, 1 min o 5 min despues?

Entrada (bajar con git, no estan en main):
  rivales/datos/eventos_*.csv.gz y trades_*.csv.gz  (rama investigacion-rivales)
  velocidad/datos/metar_awc.csv.gz y metar_iem.csv.gz (rama investigacion-velocidad)
Salida: velocidad/informe_historia.md y velocidad/muertes_historia.csv

Uso: python velocidad/analizar.py CARPETA_RIVALES CARPETA_VELOCIDAD
"""

import glob
import math
import os
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))
from estaciones import TZ, leer_caja, redondear  # noqa: E402
from estaciones_vel import CIUDAD_ESTACION  # noqa: E402

TRAMOS = [(-3600, -600), (-600, -120), (-120, 0), (0, 30), (30, 60), (60, 120), (120, 180), (180, 300),
          (300, 600), (600, 1800), (1800, 3600), (3600, 4 * 3600)]


def temp_raw(raw):
    """Temperatura en °C de un METAR crudo: grupo T (decimas) si esta, si no la del cuerpo."""
    g = re.search(r"\bT([01])(\d{3})[01]\d{3}\b", raw)
    if g:
        return (-1 if g.group(1) == "1" else 1) * int(g.group(2)) / 10
    g = re.search(r"\s(M?\d{2})/(M?\d{2})?\s", raw + " ")
    if g:
        return int(g.group(1).replace("M", "-"))
    return None


def metars(carpeta):
    """DataFrame icao, obs (epoch), recibido (epoch o NaN), especial (bool), c."""
    filas = []
    f_awc = os.path.join(carpeta, "metar_awc.csv.gz")
    if os.path.exists(f_awc):
        a = pd.read_csv(f_awc, dtype=str)
        for r in a.itertuples():
            c = temp_raw(r.raw or "")
            if c is None:
                continue
            rec = pd.Timestamp(r.receipt_time).timestamp() if isinstance(r.receipt_time, str) and r.receipt_time else math.nan
            filas.append((r.icao, int(float(r.obs_epoch)), rec, (r.tipo == "SPECI") or r.raw.startswith("SPECI"), c, "awc"))
    f_iem = os.path.join(carpeta, "metar_iem.csv.gz")
    if os.path.exists(f_iem):
        b = pd.read_csv(f_iem, dtype=str).dropna()
        for r in b.itertuples():
            c = temp_raw(r.raw)
            if c is None:
                continue
            t = datetime.strptime(r.valid_utc, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp()
            filas.append((r.icao, int(t), math.nan, r.raw.startswith("SPECI"), c, "iem"))
    m = pd.DataFrame(filas, columns=["icao", "obs", "recibido", "especial", "c", "fuente"])
    # mismo reporte en las dos fuentes: queda el de aviationweather (trae hora de publicacion)
    m = m.sort_values(["icao", "obs", "fuente"]).drop_duplicates(["icao", "obs"], keep="first")
    # los SPECI de IEM no vienen marcados: los de rutina caen siempre en el mismo minuto de la hora
    minuto = m.assign(mm=(m.obs // 60) % 60)
    modal = minuto[minuto.fuente == "awc"].groupby("icao").mm.agg(lambda s: set(s.value_counts().index[:2]))
    def es_esp(r):
        if r.fuente == "awc":
            return r.especial
        mods = modal.get(r.icao)
        return bool(mods) and ((r.obs // 60) % 60) not in mods
    m["especial"] = [es_esp(r) for r in m.itertuples()]
    return m


def muertes(ev, met, solo_rutina):
    """Una fila por caja que perdio y que algun reporte del dia mato: cuando (obs) y con que reporte."""
    out = []
    por_est = {k: g.sort_values("obs") for k, g in met.groupby("icao")}
    for (slug, ciudad, tipo, fecha), g in ev.groupby(["slug", "ciudad", "tipo", "fecha"]):
        icao = CIUDAD_ESTACION.get(ciudad)
        if not icao or icao not in por_est or ciudad not in TZ:
            continue
        tz = ZoneInfo(TZ[ciudad])
        d = datetime.strptime(fecha, "%Y-%m-%d")
        t0 = datetime(d.year, d.month, d.day, tzinfo=tz).timestamp()
        o = por_est[icao]
        o = o[(o.obs >= t0) & (o.obs < t0 + 86400)]
        if solo_rutina:
            o = o[~o.especial]
        if len(o) < 12:
            continue
        for r in g.itertuples():
            if r.precio_final_si != "0":
                continue
            try:
                lo, hi, en_f = leer_caja(r.caja)
            except Exception:
                continue
            v = [redondear(c, en_f) for c in o.c]
            idx = None
            if tipo == "highest" and hi is not None:
                idx = next((i for i, x in enumerate(v) if x > hi), None)
            elif tipo == "lowest" and lo is not None:
                idx = next((i for i, x in enumerate(v) if x < lo), None)
            if idx is None:
                continue
            k = o.iloc[idx]
            # ¿la mato este reporte o ya venia muerta de antes? (siempre es el primero que la supera)
            out.append({"condition_id": r.condition_id, "slug": slug, "ciudad": ciudad, "icao": icao, "tipo": tipo,
                        "fecha": fecha, "caja": r.caja, "obs": int(k.obs), "recibido": k.recibido,
                        "especial": bool(k.especial), "valor": v[idx], "hora_local": datetime.fromtimestamp(k.obs, tz).hour,
                        "n_reporte": idx})
    return pd.DataFrame(out)


def analizar(dir_riv, dir_vel, salida):
    ev = pd.concat([pd.read_csv(f, dtype=str) for f in sorted(glob.glob(os.path.join(dir_riv, "eventos_*.csv.gz")))])
    ev = ev.drop_duplicates("condition_id")
    cols = ["condition_id", "outcome_index", "side", "price", "size", "timestamp", "wallet", "name"]
    tr = pd.concat([pd.read_csv(f, usecols=cols, dtype={"condition_id": str, "wallet": str, "name": str})
                    for f in sorted(glob.glob(os.path.join(dir_riv, "trades_*.csv.gz")))]).drop_duplicates()
    met = metars(dir_vel)
    mu = muertes(ev, met, solo_rutina=False)
    mu = mu[mu.n_reporte > 0]   # si ya la mataba el primer reporte del dia, no hubo carrera
    # operaciones que apuestan a que la caja murio: comprar No o vender Si. y = precio equivalente del Si
    tr = tr[tr.condition_id.isin(mu.condition_id)].copy()
    tr["muerte"] = ((tr.outcome_index == 1) & (tr.side == "BUY")) | ((tr.outcome_index == 0) & (tr.side == "SELL"))
    tr["y"] = tr.price.where(tr.outcome_index == 0, 1 - tr.price)
    tr["ganancia"] = tr["y"] * tr["size"]   # si el Si vale 0, el que apuesta a la muerte gana y por accion
    tr = tr.merge(mu[["condition_id", "obs", "recibido"]], on="condition_id")
    tr["d"] = tr.timestamp - tr.obs
    tr["d_pub"] = tr.timestamp - tr.recibido
    return ev, tr, mu, met


if __name__ == "__main__":
    analizar(sys.argv[1], sys.argv[2], os.path.join(AQUI, "informe_historia.md"))

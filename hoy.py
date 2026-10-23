"""
PRONOSTICO DEL MISMO DIA en todas las ciudades (en papel, no usa plata).

Las billeteras que ganan comprando "colas baratas" operan sobre todo el mismo
dia a la tarde: ya saben cuanto marco la estacion y solo tienen que estimar
cuanto puede subir (o bajar) en lo que queda del dia. Esto hace lo mismo:

  1. Lee los METAR de hoy de la estacion oficial: el extremo hasta ahora (O).
  2. Toma el ensemble de Open-Meteo para las horas que FALTAN del dia, corregido
     por cuanto se esta equivocando el modelo ahora mismo (ultima observacion).
  3. Resultado final = max(O, lo que falta) para la maxima (min para la minima).
     Con eso calcula la probabilidad de cada caja, contando el redondeo.
  4. Anota todo en hoy.csv y las operaciones simuladas en hoy_ops.csv
     (mismas reglas que pronostico.py: taker, maker y colas).

Momentos fijos (hora local de cada ciudad), decididos ANTES de ver resultados:
  maxima: 12:00 y 15:00     minima: 09:00
Cada momento se registra una sola vez por dia (ventana de 60 min).
Lo corre el reloj cada 15 minutos.

Uso: python hoy.py
"""

import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pronostico as P
from estaciones import TZ, SIN_METAR, leer_caja, redondear, temp_metar

MOMENTOS = {"highest": [12, 15], "lowest": [9]}
VENTANA_MIN = 60
TAU_H = 6.0          # el error actual del modelo se va "olvidando" con este ritmo (horas)
SESGO_HORARIO = {"highest": 0.3, "lowest": -0.2}   # el extremo real cae entre horas (°C)
SIGMA = 0.8          # incertidumbre extra de cada escenario (°C)

COLS = ["momento_utc", "serie", "fecha", "icao", "hora_local", "caja", "condition_id", "p_modelo", "bid", "ask",
        "extremo_obs", "ultima_obs", "error_modelo_ahora", "centro_resto", "n_escenarios", "calibrada"]


def metars(icaos):
    datos = {}
    lista = sorted(icaos)
    for i in range(0, len(lista), 40):
        j = P.S.get("https://aviationweather.gov/api/data/metar",
                    params={"ids": ",".join(lista[i:i + 40]), "format": "json", "hours": 30}, timeout=30).json()
        for x in j:
            c = temp_metar(x)
            if c is not None and x.get("obsTime"):
                datos.setdefault(x["icaoId"], {})[int(x["obsTime"])] = c
    return datos


def ensemble_hoy(lat, lon, tz, fecha):
    r = P.S.get(P.ENS, params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m", "models": P.MODELOS,
                               "timezone": tz, "start_date": fecha.isoformat(), "end_date": fecha.isoformat()},
                timeout=40)
    r.raise_for_status()
    h = r.json()["hourly"]
    horas = [datetime.fromisoformat(t).replace(tzinfo=ZoneInfo(tz)).timestamp() for t in h["time"]]
    miembros = [v for k, v in h.items() if k.startswith("temperature_2m") and sum(x is not None for x in v) >= 20]
    return horas, miembros


def interpolar(horas, valores, ts):
    for i in range(len(horas) - 1):
        if horas[i] <= ts <= horas[i + 1] and valores[i] is not None and valores[i + 1] is not None:
            f = (ts - horas[i]) / (horas[i + 1] - horas[i])
            return valores[i] * (1 - f) + valores[i + 1] * f
    return None


def main():
    est = P.cargar(P.F_EST, {})
    hechas = est.setdefault("hoy_hechas", {})
    ahora = datetime.now(timezone.utc)
    evs = P.eventos_abiertos()
    toca = []
    for e in evs:
        tz = ZoneInfo(TZ[e["ciudad"]])
        local = ahora.astimezone(tz)
        if e["fecha"] != local.date() or e["icao"] in SIN_METAR:
            continue
        for h in MOMENTOS[e["tipo"]]:
            k = f"{e['tipo']}|{e['ciudad']}|{e['fecha']}|{h}"
            minutos = (local.hour - h) * 60 + local.minute
            if 0 <= minutos < VENTANA_MIN and k not in hechas:
                toca.append((e, h, k))
    if not toca:
        print("Nada que registrar ahora")
        return
    sta = P.coordenadas({e["icao"] for e, h, k in toca})
    obs = metars({e["icao"] for e, h, k in toca})
    filas, ops, pend = [], [], []
    for e, h, k in toca:
        serie = f"{e['tipo']}|{e['ciudad']}"
        tzs = TZ[e["ciudad"]]
        tz = ZoneInfo(tzs)
        inicio = datetime(e["fecha"].year, e["fecha"].month, e["fecha"].day, tzinfo=tz).timestamp()
        o = sorted((t, c) for t, c in obs.get(e["icao"], {}).items() if t >= inicio)
        if len(o) < 3 or e["icao"] not in sta:
            continue
        try:
            horas, miembros = ensemble_hoy(sta[e["icao"]]["lat"], sta[e["icao"]]["lon"], tzs, e["fecha"])
            time.sleep(0.5)
        except Exception as ex:
            P.log(f"open-meteo fallo {serie}: {ex}")
            continue
        t_ult, c_ult = o[-1]
        alta = e["tipo"] == "highest"
        centros, errores = [], []
        for v in miembros:
            m_ahora = interpolar(horas, v, t_ult)
            if m_ahora is None:
                continue
            delta = c_ult - m_ahora
            resto = [x + delta * math.exp(-(t - t_ult) / 3600 / TAU_H)
                     for t, x in zip(horas, v) if t > t_ult and x is not None]
            if not resto:
                continue
            errores.append(delta)
            centros.append((max(resto) if alta else min(resto)) + SESGO_HORARIO[e["tipo"]])
        if len(centros) < 10:
            continue
        hechas[k] = ahora.strftime("%Y-%m-%d %H:%M")
        for m in e["markets"]:
            if m.get("closed"):
                continue
            try:
                lo, hi, en_f = leer_caja(m["groupItemTitle"])
            except Exception:
                continue
            u = (lambda c: c * 9 / 5 + 32) if en_f else (lambda c: c)
            s = SIGMA * (1.8 if en_f else 1.0)
            O = (max if alta else min)(redondear(c, en_f) for t, c in o)
            cs = [u(c) for c in centros]

            def p_hasta(kk):     # maxima: P(resultado <= kk)
                if kk is None:
                    return 1.0
                return 0.0 if O > kk else sum(P.ncdf((kk + 0.5 - c) / s) for c in cs) / len(cs)

            def p_desde(kk):     # minima: P(resultado >= kk)
                if kk is None:
                    return 1.0
                return 0.0 if O < kk else sum(1 - P.ncdf((kk - 0.5 - c) / s) for c in cs) / len(cs)

            if alta:
                p = p_hasta(hi) - (0.0 if lo is None else p_hasta(lo - 1))
            else:
                p = p_desde(lo) - (0.0 if hi is None else p_desde(hi + 1))
            p = min(max(p, 0.0), 1.0)
            try:
                token = json.loads(m["clobTokenIds"])[0]
            except Exception:
                continue
            filas.append([ahora.strftime("%Y-%m-%d %H:%M"), serie, e["fecha"].isoformat(), e["icao"], h,
                          m["groupItemTitle"], m["conditionId"], round(p, 4), None, None, O, round(u(c_ult), 1),
                          round(sum(errores) / len(errores), 2), round(sum(cs) / len(cs), 2), len(cs), 0])
            muerta = (hi is not None and O > hi) if alta else (lo is not None and O < lo)
            pend.append((filas[-1], token, p, muerta, [ahora.strftime("%Y-%m-%d %H:%M:%S"), serie, e["fecha"].isoformat(),
                                                       m["groupItemTitle"], m["conditionId"]], e["fin"] or ""))
    # operaciones simuladas: mismas reglas que pronostico.py, con el libro real de cada caja
    libs = P.libros([t for _, t, *_ in pend])
    for fila, token, p, muerta, base, fin in pend:
        lib = libs.get(token)
        if lib is None:
            continue
        fila[8] = lib[0][0][0] if lib[0] else None     # mejor bid
        fila[9] = lib[1][0][0] if lib[1] else None     # mejor ask
        for lado, modo, precio in P.operaciones(p, lib, muerta):
            ops.append(base + [lado, modo, precio, round(p, 4), 0, P.ACCIONES, fin])
    # limpiar marcas viejas
    viejo = (ahora - timedelta(days=3)).strftime("%Y-%m-%d")
    est["hoy_hechas"] = {k: v for k, v in hechas.items() if v >= viejo}
    est.setdefault("desde_libro", ahora.strftime("%Y-%m-%d %H:%M:%S"))
    P.guardar(P.F_EST, est)
    P.agregar(P.F_HOY, COLS, filas)
    P.agregar(P.F_HOY_OPS, P.COLS_OPS, ops)
    P.log(f"hoy: {len(toca)} momentos, {len(filas)} cajas, {len(ops)} operaciones simuladas")


if __name__ == "__main__":
    main()

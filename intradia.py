"""
Backtest INTRADIA: operar el mismo dia, usando lo que la estacion ya midio.

Idea: a las 13:00, si la estacion ya marco 19°C, la pregunta es
"¿cuanto mas va a subir?". Eso se puede estimar mirando todos los dias
pasados: a esa hora, con una diferencia parecida entre lo ya medido y lo
que decia el pronostico, ¿cuantos grados mas subio despues?

Para cada dia y cada hora (10 a 16 hs):
  1. Maxima medida hasta esa hora (METAR, archivo de la Univ. de Iowa).
  2. Precio de cada caja 15 minutos despues de esa hora (Polymarket),
     para dar tiempo a que el dato de la estacion se publique.
  3. Probabilidad del modelo "nowcast", aprendido SOLO con dias anteriores.
  4. Se compara con la caja que gano y se simulan operaciones.

Tambien cuenta las "cajas muertas": cajas que ya no pueden ganar porque la
estacion ya marco mas que eso, pero que el mercado todavia cotiza.

Necesita historial_sesgo.csv (calcular_sesgo.bat).
La primera vez tarda bastante (baja precios cada 10 minutos de cientos de dias);
despues usa intradia_cache.json y metar_cache.json.

Uso:
  python intradia.py
"""

import csv
import io
import json
import math
import os
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import requests

from monitor import CIUDADES, GAMMA_API, leer_caja, slug_evento
from backtest import leer_historial, MODELOS

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = os.path.dirname(os.path.abspath(__file__))
CACHE_PRECIOS = os.path.join(CARPETA, "intradia_cache.json")
CACHE_METAR = os.path.join(CARPETA, "metar_cache.json")
ARCHIVO_DETALLE = os.path.join(CARPETA, "intradia_detalle.csv")
CLOB_HISTORY = "https://clob.polymarket.com/prices-history"
IEM_API = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
CODIGOS = {"Buenos Aires": "SAEZ", "Sao Paulo": "SBGR"}

HORAS = [10, 11, 12, 13, 14, 15, 16]   # hora local de decision
DEMORA_MIN = 15                        # minutos despues de la hora para operar
UTC_OFFSET = -3                        # Buenos Aires y Sao Paulo
COSTO = 0.01                           # 1 centavo por accion
UMBRALES = [0.05, 0.10, 0.15, 0.20]
MIN_DIAS_ENTRENAMIENTO = 60

_local = threading.local()


def http():
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
    return _local.s


def guardar_json(ruta, datos):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f)
    os.replace(tmp, ruta)


def cargar_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# DATOS DE LA ESTACION
# ---------------------------------------------------------------------------

def bajar_metar(ciudad, desde, hasta):
    """{dia: [[minuto_del_dia, temp], ...]} en hora local."""
    fin = hasta + timedelta(days=1)
    r = http().get(IEM_API, params={
        "station": CODIGOS[ciudad["nombre"]], "data": "tmpc",
        "year1": desde.year, "month1": desde.month, "day1": desde.day,
        "year2": fin.year, "month2": fin.month, "day2": fin.day,
        "tz": ciudad["zona_horaria"], "format": "onlycomma", "latlon": "no",
        "missing": "M", "report_type": [3, 4],
    }, timeout=180)
    r.raise_for_status()
    por_dia = defaultdict(list)
    for fila in csv.DictReader(io.StringIO(r.text)):
        t = fila.get("tmpc")
        if t in (None, "", "M"):
            continue
        dia, hora = fila["valid"].split(" ")
        hh, mm = hora.split(":")
        por_dia[dia].append([int(hh) * 60 + int(mm), float(t)])
    return dict(por_dia)


def metar_de_todos(historial):
    cache = cargar_json(CACHE_METAR)
    ciudades = {c["nombre"]: c for c in CIUDADES}
    for nombre, dias in historial.items():
        if nombre not in ciudades:
            continue
        if cache.get(nombre) and max(cache[nombre]) >= max(dias):
            continue
        print(f"Bajando observaciones horarias de {nombre}...")
        desde = date.fromisoformat(min(dias))
        hasta = date.fromisoformat(max(dias))
        cache[nombre] = bajar_metar(ciudades[nombre], desde, hasta)
        guardar_json(CACHE_METAR, cache)
    return cache


# ---------------------------------------------------------------------------
# PRECIOS DEL MERCADO DURANTE EL DIA
# ---------------------------------------------------------------------------

def precios_del_dia(ciudad, dia):
    r = http().get(GAMMA_API, params={"slug": slug_evento(ciudad, dia)}, timeout=30)
    r.raise_for_status()
    eventos = r.json()
    if not eventos:
        return None
    inicio = datetime(dia.year, dia.month, dia.day, HORAS[0] - UTC_OFFSET, 0, tzinfo=timezone.utc)
    fin = datetime(dia.year, dia.month, dia.day, HORAS[-1] - UTC_OFFSET + 1, 0, tzinfo=timezone.utc)
    cajas = []
    hay_ganadora = False
    for m in eventos[0].get("markets", []):
        try:
            rango = leer_caja(m["groupItemTitle"])
            token = json.loads(m["clobTokenIds"])[0]
        except (KeyError, ValueError, IndexError):
            continue
        precios = json.loads(m.get("outcomePrices") or "[]")
        gano = bool(m.get("closed") and precios and float(precios[0]) >= 0.99)
        hay_ganadora |= gano
        h = http().get(CLOB_HISTORY, params={
            "market": token, "startTs": int(inicio.timestamp()) - 1800,
            "endTs": int(fin.timestamp()), "fidelity": 10,
        }, timeout=30)
        h.raise_for_status()
        serie = [[p["t"], p["p"]] for p in h.json().get("history", [])]
        cajas.append({"titulo": m["groupItemTitle"], "rango": list(rango),
                      "gano": gano, "serie": serie})
    if not hay_ganadora:
        return "pendiente"
    return cajas


def precios_de_todos(historial, metar):
    cache = cargar_json(CACHE_PRECIOS)
    ciudades = {c["nombre"]: c for c in CIUDADES}
    tareas = [(n, d) for n, dias in historial.items() for d in dias
              if n in ciudades and f"{n}|{d}" not in cache and d in metar.get(n, {})]
    if tareas:
        print(f"Bajando precios intradia de Polymarket ({len(tareas)} dias)... "
              "la primera vez puede tardar 10-20 minutos.")
    errores = 0

    def trabajo(t):
        n, d = t
        try:
            return t, precios_del_dia(ciudades[n], date.fromisoformat(d))
        except Exception as e:
            return t, ("error", str(e))

    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, ((n, d), res) in enumerate(pool.map(trabajo, tareas), 1):
            if isinstance(res, tuple):
                errores += 1
            elif res != "pendiente":
                cache[f"{n}|{d}"] = res
            if i % 50 == 0:
                print(f"  {i}/{len(tareas)}")
                guardar_json(CACHE_PRECIOS, cache)
    guardar_json(CACHE_PRECIOS, cache)
    if errores:
        print(f"  Atencion: {errores} dias dieron error. Volve a correrlo para completarlos.")
    return cache


def precio_en(serie, ts):
    """Primer precio registrado en o despues de ts (dentro de 30 minutos)."""
    for t, p in serie:
        if ts <= t <= ts + 1800:
            return p
    return None


# ---------------------------------------------------------------------------
# MODELO NOWCAST
# ---------------------------------------------------------------------------

def maxima_hasta(obs, minuto):
    vals = [t for m, t in obs if m <= minuto]
    return round(max(vals)) if vals else None


def maxima_final(obs):
    return round(max(t for _, t in obs)) if len(obs) >= 18 else None


def armar_casos(historial, metar):
    """Para cada ciudad, dia y hora: maxima hasta esa hora, 'brecha' con el
    pronostico corregido, y cuanto subio despues (para entrenar)."""
    casos = defaultdict(dict)
    for nombre, dias in historial.items():
        obs_ciudad = metar.get(nombre, {})
        orden = sorted(dias)
        for i, dia in enumerate(orden):
            obs = obs_ciudad.get(dia)
            if not obs:
                continue
            final = maxima_final(obs)
            p = dias[dia]
            if final is None or any(p[m] is None for m in MODELOS):
                continue
            # sesgo movil (60 dias previos) del pronostico promedio
            previos = []
            for d2 in orden[max(0, i - 60):i]:
                q = dias[d2]
                if q["real"] is not None and all(q[m] is not None for m in MODELOS):
                    previos.append(q["real"] - sum(q[m] for m in MODELOS) / len(MODELOS))
            if len(previos) < 30:
                continue
            pron = sum(p[m] for m in MODELOS) / len(MODELOS) + sum(previos) / len(previos)
            por_hora = {}
            for h in HORAS:
                hasta = maxima_hasta(obs, h * 60)
                if hasta is None:
                    continue
                por_hora[h] = {"hasta": hasta, "brecha": pron - hasta, "sube": final - hasta}
            casos[nombre][dia] = {"final": final, "horas": por_hora}
    return casos


def distribucion_subida(entrenamiento, hora, brecha):
    """Distribucion de 'cuantos grados mas sube' en dias pasados parecidos."""
    for ancho in (0.75, 1.5, 3.0, 99):
        subidas = [c["horas"][hora]["sube"] for c in entrenamiento
                   if hora in c["horas"] and abs(c["horas"][hora]["brecha"] - brecha) <= ancho]
        if len(subidas) >= 25:
            break
    if not subidas:
        return None
    conteo = defaultdict(float)
    for s in subidas:
        conteo[s] += 1
    total = len(subidas) + 1.0
    # un poquito de suavizado para no dar 0% a nada
    return {k: v / total for k, v in conteo.items()}, 1.0 / total


def prob_caja(dist, hasta, rango):
    probs, resto = dist
    bajo = -math.inf if rango[0] is None else rango[0]
    alto = math.inf if rango[1] is None else rango[1]
    if alto < hasta:
        return 0.0                         # caja muerta: ya se supero
    p = sum(v for s, v in probs.items() if bajo <= hasta + s <= alto)
    return p + resto * (0.5 if bajo <= hasta + 1 <= alto else 0.0)


# ---------------------------------------------------------------------------
# PRINCIPAL
# ---------------------------------------------------------------------------

def main():
    if not os.path.exists(os.path.join(CARPETA, "historial_sesgo.csv")):
        print("Falta historial_sesgo.csv: corre primero calcular_sesgo.bat")
        return
    historial = leer_historial()
    metar = metar_de_todos(historial)
    precios = precios_de_todos(historial, metar)
    casos = armar_casos(historial, metar)

    filas = []
    muertas = defaultdict(list)
    for nombre, por_dia in casos.items():
        orden = sorted(por_dia)
        for i, dia in enumerate(orden):
            cajas = precios.get(f"{nombre}|{dia}")
            if not cajas or i < MIN_DIAS_ENTRENAMIENTO:
                continue
            entrenamiento = [por_dia[d] for d in orden[:i]]
            d = date.fromisoformat(dia)
            for h, info in por_dia[dia]["horas"].items():
                ts = int(datetime(d.year, d.month, d.day, h - UTC_OFFSET, DEMORA_MIN,
                                  tzinfo=timezone.utc).timestamp())
                dist = distribucion_subida(entrenamiento, h, info["brecha"])
                if not dist:
                    continue
                for c in cajas:
                    p = precio_en(c["serie"], ts)
                    if p is None:
                        continue
                    alto = math.inf if c["rango"][1] is None else c["rango"][1]
                    if alto < info["hasta"]:
                        muertas[(nombre, h)].append(p)
                        continue
                    filas.append({
                        "ciudad": nombre, "dia": dia, "hora": h, "caja": c["titulo"],
                        "precio": p, "modelo": prob_caja(dist, info["hasta"], c["rango"]),
                        "gano": 1 if c["gano"] else 0, "hasta": info["hasta"],
                    })

    if not filas:
        print("No hay datos suficientes para el backtest intradia.")
        return

    with open(ARCHIVO_DETALLE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ciudad", "dia", "hora", "maxima_hasta_ahora", "caja", "precio", "prob_modelo", "gano"])
        for r in filas:
            w.writerow([r["ciudad"], r["dia"], r["hora"], r["hasta"], r["caja"],
                        str(r["precio"]).replace(".", ","),
                        str(round(r["modelo"], 4)).replace(".", ","), r["gano"]])

    for nombre in sorted({r["ciudad"] for r in filas}):
        reporte(nombre, [r for r in filas if r["ciudad"] == nombre], muertas)
    print(f"\nDetalle: {ARCHIVO_DETALLE}")
    print("Pegale esta salida a Claude para interpretarla.")


def simular(filas, umbral):
    n = gan = 0
    costo = res = 0.0
    for r in filas:
        if not (0.02 <= r["precio"] <= 0.98):
            continue
        dif = r["modelo"] - r["precio"]
        if dif >= umbral:
            pago, cobro = r["precio"] + COSTO, r["gano"]
        elif -dif >= umbral:
            pago, cobro = 1 - r["precio"] + COSTO, 1 - r["gano"]
        else:
            continue
        n += 1
        gan += cobro
        costo += pago
        res += cobro - pago
    return n, gan, costo, res


def reporte(nombre, filas, muertas):
    dias = sorted({r["dia"] for r in filas})
    print(f"\n=== {nombre}: {len(dias)} dias ({dias[0]} a {dias[-1]}) ===")

    # Cajas muertas que el mercado seguia cotizando
    print("  Cajas ya imposibles que el mercado seguia cotizando (precio > 1 centavo):")
    linea = "  "
    for h in HORAS:
        ps = muertas.get((nombre, h), [])
        caras = [p for p in ps if p > 0.01]
        linea += f"{h}hs: {len(caras)}/{len(ps)}  "
    print(linea)

    print(f"\n  {'Hora':<6}{'Brier mercado':>15}{'Brier modelo':>14}")
    for h in HORAS:
        sub = [r for r in filas if r["hora"] == h]
        if not sub:
            continue
        por_dia_m = defaultdict(float)
        por_dia_o = defaultdict(float)
        for r in sub:
            por_dia_m[r["dia"]] += (r["precio"] - r["gano"]) ** 2
            por_dia_o[r["dia"]] += (r["modelo"] - r["gano"]) ** 2
        print(f"  {f'{h}hs':<6}{sum(por_dia_m.values()) / len(por_dia_m):>15.3f}"
              f"{sum(por_dia_o.values()) / len(por_dia_o):>14.3f}")

    print("\n  Calibracion del mercado durante el dia (cuando dice X%, ¿cuanto pasa?):")
    for lo, hi in [(.02, .1), (.1, .25), (.25, .5), (.5, .75), (.75, .9), (.9, .98)]:
        g = [r for r in filas if lo <= r["precio"] < hi]
        o = [r for r in filas if lo <= r["modelo"] < hi]
        txt_m = f"{sum(r['gano'] for r in g) / len(g) * 100:4.0f}% de {len(g):<5}" if g else "      -      "
        txt_o = f"{sum(r['gano'] for r in o) / len(o) * 100:4.0f}% de {len(o):<5}" if o else "      -      "
        print(f"  {f'{lo*100:.0f}-{hi*100:.0f}%':<8} mercado {txt_m}  modelo {txt_o}")

    print(f"\n  Simulacion (precios entre 2 y 98 centavos, costo {COSTO*100:.0f} centavo):")
    print(f"  {'Hora':<6}" + "".join(f"{f'+{u*100:.0f} pts':>20}" for u in UMBRALES))
    for h in HORAS:
        sub = [r for r in filas if r["hora"] == h]
        linea = f"  {f'{h}hs':<6}"
        for u in UMBRALES:
            n, g, c, res = simular(sub, u)
            linea += f"{(f'{n} op, {res/c*100:+.1f}%' if n else '-'):>20}"
        print(linea)
    mitad = dias[len(dias) // 2]
    for etiqueta, sub in (("1ra mitad", [r for r in filas if r["dia"] < mitad]),
                          ("2da mitad", [r for r in filas if r["dia"] >= mitad])):
        n, g, c, res = simular(sub, 0.10)
        if n:
            print(f"  {etiqueta}, todas las horas, +10 pts: {n} op, ${res:+.2f} ({res/c*100:+.1f}%)")


if __name__ == "__main__":
    main()

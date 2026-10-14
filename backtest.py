"""
Backtest: como le habria ido al modelo contra el mercado en los meses pasados.

Para cada dia pasado y cada ciudad:
  1. Toma el precio de cada caja en Polymarket la TARDE ANTERIOR (15:00 hora local),
     que es mas o menos cuando corre el monitor.
  2. Calcula la probabilidad del modelo con el pronostico del dia anterior
     (historial_sesgo.csv) y una calibracion que usa SOLO los 60 dias previos
     (para no "hacer trampa" mirando el futuro).
  3. Compara los dos con la caja que gano de verdad.
  4. Simula operaciones: comprar "Yes" cuando el modelo ve la caja mas probable
     que el precio, o comprar "No" cuando la ve menos probable, si la
     diferencia supera un umbral.

Necesita haber corrido antes sesgo.py (usa historial_sesgo.csv).
La primera vez tarda varios minutos (baja miles de precios); despues usa
backtest_cache.json y es casi instantaneo.

Uso:
  python backtest.py
"""

import csv
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_HISTORIAL = os.path.join(CARPETA, "historial_sesgo.csv")
ARCHIVO_CACHE = os.path.join(CARPETA, "backtest_cache.json")
ARCHIVO_DETALLE = os.path.join(CARPETA, "backtest_detalle.csv")
CLOB_HISTORY = "https://clob.polymarket.com/prices-history"

HORA_FOTO_UTC = 18          # 15:00 en Buenos Aires / Sao Paulo, el dia anterior
VENTANA_CALIBRACION = 60    # dias previos usados para calcular sesgo y error
MINIMO_CALIBRACION = 40
COSTO_POR_ACCION = 0.01     # 1 centavo por accion: spread / deslizamiento estimado
UMBRALES = [0.05, 0.08, 0.12, 0.15]
MODELOS = ["gfs_seamless", "ecmwf_ifs025"]

_sesion = threading.local()


def http():
    if not hasattr(_sesion, "s"):
        _sesion.s = requests.Session()
    return _sesion.s


# ---------------------------------------------------------------------------
# DATOS
# ---------------------------------------------------------------------------

def numero(t):
    t = (t or "").strip()
    return float(t.replace(",", ".")) if t else None


def leer_historial():
    """{ciudad: {dia: {"real": x, "gfs_seamless": y, "ecmwf_ifs025": z}}}"""
    datos = defaultdict(dict)
    with open(ARCHIVO_HISTORIAL, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            datos[fila["ciudad"]][fila["dia"]] = {
                "real": numero(fila["maxima_real"]),
                **{m: numero(fila[f"pron_{m}"]) for m in MODELOS},
            }
    return datos


def mercado_del_dia(ciudad, dia):
    """Precios de la tarde anterior y caja ganadora. None si no hubo mercado."""
    r = http().get(GAMMA_API, params={"slug": slug_evento(ciudad, dia)}, timeout=30)
    r.raise_for_status()
    eventos = r.json()
    if not eventos:
        return None
    foto = datetime(dia.year, dia.month, dia.day, HORA_FOTO_UTC, tzinfo=timezone.utc) - timedelta(days=1)
    ts = int(foto.timestamp())
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
            "market": token, "startTs": ts - 8 * 3600, "endTs": ts, "fidelity": 60,
        }, timeout=30)
        h.raise_for_status()
        historia = h.json().get("history", [])
        precio = historia[-1]["p"] if historia else None
        cajas.append({"titulo": m["groupItemTitle"], "rango": list(rango),
                      "precio": precio, "gano": gano})
    if not hay_ganadora:
        return "pendiente"
    return cajas


def bajar_mercados(historial):
    cache = {}
    if os.path.exists(ARCHIVO_CACHE):
        with open(ARCHIVO_CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    ciudades = {c["nombre"]: c for c in CIUDADES}
    tareas = [(nombre, dia) for nombre, dias in historial.items() for dia in dias
              if nombre in ciudades and f"{nombre}|{dia}" not in cache]
    if tareas:
        print(f"Bajando precios historicos de Polymarket ({len(tareas)} dias)... "
              "puede tardar unos minutos la primera vez.")
    hechos = 0
    errores = 0
    lock = threading.Lock()

    def trabajo(t):
        nombre, dia = t
        try:
            res = mercado_del_dia(ciudades[nombre], date.fromisoformat(dia))
        except Exception as e:
            return t, ("error", str(e))
        return t, res

    with ThreadPoolExecutor(max_workers=6) as pool:
        for (nombre, dia), res in pool.map(trabajo, tareas):
            hechos += 1
            with lock:
                if isinstance(res, tuple):          # error de red: reintentar la proxima vez
                    errores += 1
                elif res == "pendiente":            # todavia sin resolver: no guardar
                    pass
                else:
                    cache[f"{nombre}|{dia}"] = res  # lista de cajas, o None si no hubo mercado
            if hechos % 50 == 0:
                print(f"  {hechos}/{len(tareas)}")
                with open(ARCHIVO_CACHE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
    with open(ARCHIVO_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    if errores:
        print(f"  Atencion: {errores} dias dieron error de conexion. Volve a correrlo para completarlos.")
    return cache


# ---------------------------------------------------------------------------
# MODELO (solo con informacion disponible ese dia)
# ---------------------------------------------------------------------------

def Phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def calibracion_movil(hist_ciudad, dia):
    d = date.fromisoformat(dia)
    previos = [hist_ciudad[(d - timedelta(days=k)).isoformat()]
               for k in range(1, VENTANA_CALIBRACION + 1)
               if (d - timedelta(days=k)).isoformat() in hist_ciudad]
    if len(previos) < MINIMO_CALIBRACION:
        return None
    calib = {}
    for m in MODELOS:
        errores = [p["real"] - p[m] for p in previos if p[m] is not None and p["real"] is not None]
        media = sum(errores) / len(errores)
        sd = math.sqrt(sum((e - media) ** 2 for e in errores) / (len(errores) - 1))
        calib[m] = (media, max(sd, 0.6))
    return calib


def prob_modelo(pron, calib, rango):
    bajo = -math.inf if rango[0] is None else rango[0] - 0.5
    alto = math.inf if rango[1] is None else rango[1] + 0.5
    pesos = {m: 1 / calib[m][1] ** 2 for m in MODELOS}
    total = sum(pesos.values())
    p = 0.0
    for m in MODELOS:
        sesgo, sd = calib[m]
        c = pron[m] + sesgo
        pa = 1.0 if alto == math.inf else Phi((alto - c) / sd)
        pb = 0.0 if bajo == -math.inf else Phi((bajo - c) / sd)
        p += pesos[m] / total * (pa - pb)
    return p


# ---------------------------------------------------------------------------
# ANALISIS
# ---------------------------------------------------------------------------

def main():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        print("Falta historial_sesgo.csv: corre primero calcular_sesgo.bat")
        return
    historial = leer_historial()
    cache = bajar_mercados(historial)

    filas = []   # una por caja y dia
    for nombre, dias in historial.items():
        for dia in sorted(dias):
            cajas = cache.get(f"{nombre}|{dia}")
            if not cajas:
                continue
            pron = dias[dia]
            if any(pron[m] is None for m in MODELOS):
                continue
            calib = calibracion_movil(dias, dia)
            if not calib:
                continue
            precios = [c["precio"] for c in cajas if c["precio"] is not None]
            if len(precios) < len(cajas) - 1 or not (0.85 <= sum(precios) <= 1.2):
                continue  # mercado sin precios razonables a esa hora
            for c in cajas:
                if c["precio"] is None:
                    continue
                filas.append({
                    "ciudad": nombre, "dia": dia, "caja": c["titulo"],
                    "precio": c["precio"], "gano": 1 if c["gano"] else 0,
                    "modelo": prob_modelo(pron, calib, c["rango"]),
                })

    if not filas:
        print("No hay dias con mercado + pronostico para comparar.")
        return

    with open(ARCHIVO_DETALLE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ciudad", "dia", "caja", "precio_tarde_anterior", "prob_modelo", "gano"])
        for r in filas:
            w.writerow([r["ciudad"], r["dia"], r["caja"], str(r["precio"]).replace(".", ","),
                        str(round(r["modelo"], 4)).replace(".", ","), r["gano"]])

    for nombre in sorted({r["ciudad"] for r in filas}):
        reporte(nombre, [r for r in filas if r["ciudad"] == nombre])
    print(f"\nDetalle caja por caja: {ARCHIVO_DETALLE}")
    print("Pegale esta salida a Claude para interpretarla.")


def brier(filas, clave):
    por_dia = defaultdict(float)
    for r in filas:
        por_dia[r["dia"]] += (r[clave] - r["gano"]) ** 2
    return sum(por_dia.values()) / len(por_dia)


def simular(filas, umbral):
    n = ganadas = 0
    costo = ganancia = 0.0
    for r in filas:
        dif = r["modelo"] - r["precio"]
        if dif >= umbral and r["precio"] + COSTO_POR_ACCION < 1:          # comprar Yes
            pago = r["precio"] + COSTO_POR_ACCION
            cobro = r["gano"]
        elif -dif >= umbral and (1 - r["precio"]) + COSTO_POR_ACCION < 1:  # comprar No
            pago = (1 - r["precio"]) + COSTO_POR_ACCION
            cobro = 1 - r["gano"]
        else:
            continue
        n += 1
        ganadas += cobro
        costo += pago
        ganancia += cobro - pago
    return n, ganadas, costo, ganancia


def reporte(nombre, filas):
    dias = sorted({r["dia"] for r in filas})
    print(f"\n=== {nombre}: {len(dias)} dias ({dias[0]} a {dias[-1]}) ===")

    print(f"  Puntaje Brier (mas bajo = mejor):  mercado {brier(filas, 'precio'):.3f}"
          f"   modelo {brier(filas, 'modelo'):.3f}")

    # Quien acerto la caja favorita
    acierto_m = acierto_o = 0
    for d in dias:
        del_dia = [r for r in filas if r["dia"] == d]
        acierto_m += max(del_dia, key=lambda r: r["precio"])["gano"]
        acierto_o += max(del_dia, key=lambda r: r["modelo"])["gano"]
    print(f"  Su caja favorita gano:             mercado {acierto_m}/{len(dias)}"
          f"   modelo {acierto_o}/{len(dias)}")

    # Calibracion: cuando dicen X%, pasa X%?
    print("\n  Cuando dicen... ¿cuantas veces pasa de verdad?")
    print(f"  {'Rango':<10}{'Mercado':>18}{'Modelo':>18}")
    for lo, hi in [(0, .05), (.05, .15), (.15, .25), (.25, .35), (.35, .5), (.5, 1.01)]:
        linea = f"  {f'{lo*100:.0f}-{min(hi,1)*100:.0f}%':<10}"
        for clave in ("precio", "modelo"):
            grupo = [r for r in filas if lo <= r[clave] < hi]
            if grupo:
                real = sum(r["gano"] for r in grupo) / len(grupo)
                linea += f"{real*100:>9.0f}% de {len(grupo):<5}"
            else:
                linea += f"{'-':>18}"
        print(linea)

    # Simulacion de operaciones
    print(f"\n  Simulacion (1 accion por senal, costo {COSTO_POR_ACCION*100:.0f} centavo):")
    print(f"  {'Umbral':<8}{'Operac.':>8}{'Ganadas':>9}{'Invertido':>11}{'Resultado':>11}{'Retorno':>9}")
    for u in UMBRALES:
        n, g, c, res = simular(filas, u)
        if n:
            print(f"  {f'+{u*100:.0f} pts':<8}{n:>8}{g:>9}{f'${c:,.2f}':>11}{f'${res:+,.2f}':>11}{res/c*100:>8.1f}%")
        else:
            print(f"  {f'+{u*100:.0f} pts':<8}{'0':>8}")

    # Estabilidad: primera mitad vs segunda mitad
    mitad = dias[len(dias) // 2]
    for etiqueta, sub in (("1ra mitad", [r for r in filas if r["dia"] < mitad]),
                          ("2da mitad", [r for r in filas if r["dia"] >= mitad])):
        n, g, c, res = simular(sub, 0.08)
        if n:
            print(f"  {etiqueta} (+8 pts): {n} operaciones, resultado ${res:+.2f} ({res/c*100:+.1f}%)")


if __name__ == "__main__":
    main()

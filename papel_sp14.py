"""
PRUEBA EN PAPEL hacia adelante: "Sao Paulo a las 14 hs".

Regla FIJADA DE ANTEMANO (13-oct-2026). No se cambia durante la prueba:
  - Ciudad: Sao Paulo (estacion Guarulhos, SBGR).
  - Momento: 14:15 hora local, usando lo medido por la estacion hasta las 14:00.
  - Modelo: el "nowcast" de intradia.py, CONGELADO (entrenado solo con datos
    hasta el dia en que se armo el backtest). No se reentrena.
  - Senal: diferencia de 10 puntos o mas entre modelo y precio.
  - Ejecucion: al precio REAL del libro de ordenes (lo que costaria comprar
    10 acciones de Yes o de No en ese momento), solo si el precio esta entre
    2 y 98 centavos.
  - Duracion: ~30 dias. Despues se evalua UNA vez.

No compra nada: solo anota lo que habria hecho y, dias despues, si gano o perdio.

Archivos:
  papel_libro.csv        -> foto del libro de todas las cajas cada dia
  papel_operaciones.csv  -> operaciones simuladas y su resultado

Uso:
  python papel_sp14.py           -> registra hoy (si son entre 14:10 y 14:59)
                                    y liquida los dias anteriores
  python papel_sp14.py resumen   -> solo liquida y muestra el resumen
"""

import csv
import json
import os
import sys
from datetime import date, datetime, timedelta

import requests

from estaciones import tasa_de
from monitor import CIUDADES, GAMMA_API, leer_caja, slug_evento
from backtest import leer_historial, MODELOS
from intradia import (armar_casos, bajar_metar, cargar_json, distribucion_subida,
                      maxima_hasta, prob_caja, CACHE_METAR)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_LIBRO = os.path.join(CARPETA, "papel_libro.csv")
ARCHIVO_OPS = os.path.join(CARPETA, "papel_operaciones.csv")
BOOK_API = "https://clob.polymarket.com/book"
PREVIOUS_RUNS_API = "https://previous-runs-api.open-meteo.com/v1/forecast"

CIUDAD = next(c for c in CIUDADES if c["nombre"] == "Sao Paulo")
HORA = 14
UMBRAL = 0.10
ACCIONES = 10
PRECIO_MIN, PRECIO_MAX = 0.02, 0.98
VENTANA_MIN, VENTANA_MAX = (14, 10), (14, 59)

COLS_OPS = ["fecha", "caja", "lado", "prob_modelo", "precio_medio", "acciones",
            "costo", "maxima_hasta_14", "ganadora", "resultado", "tasa_comision"]   # comision: RESUMEN.md


# ---------------------------------------------------------------------------
# MODELO CONGELADO
# ---------------------------------------------------------------------------

def preparar_modelo():
    historial = leer_historial()
    metar = cargar_json(CACHE_METAR)
    if CIUDAD["nombre"] not in metar:
        raise SystemExit("Falta metar_cache.json: corre primero intradia.bat")
    casos = armar_casos(historial, metar)[CIUDAD["nombre"]]
    entrenamiento = list(casos.values())
    # sesgo: ultimos 60 dias del historial (congelado)
    dias = historial[CIUDAD["nombre"]]
    ultimos = sorted(dias)[-60:]
    errores = [dias[d]["real"] - sum(dias[d][m] for m in MODELOS) / len(MODELOS)
               for d in ultimos if dias[d]["real"] is not None
               and all(dias[d][m] is not None for m in MODELOS)]
    sesgo = sum(errores) / len(errores)
    return entrenamiento, sesgo


def pronostico_de_ayer_para_hoy(hoy):
    r = requests.get(PREVIOUS_RUNS_API, params={
        "latitude": CIUDAD["lat"], "longitude": CIUDAD["lon"],
        "hourly": "temperature_2m_previous_day1", "models": ",".join(MODELOS),
        "timezone": CIUDAD["zona_horaria"],
        "start_date": hoy.isoformat(), "end_date": hoy.isoformat(),
    }, timeout=30)
    r.raise_for_status()
    h = r.json()["hourly"]
    maximos = []
    for m in MODELOS:
        vals = [v for v in h.get(f"temperature_2m_previous_day1_{m}", []) if v is not None]
        if len(vals) < 20:
            raise RuntimeError(f"Pronostico incompleto de {m}")
        maximos.append(max(vals))
    return sum(maximos) / len(maximos)


# ---------------------------------------------------------------------------
# LIBRO DE ORDENES
# ---------------------------------------------------------------------------

def libro(token):
    r = requests.get(BOOK_API, params={"token_id": token}, timeout=20)
    r.raise_for_status()
    b = r.json()
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
    return bids, asks


def costo_de_comprar(asks, cantidad):
    """Precio medio de comprar 'cantidad' acciones recorriendo el libro."""
    falta, total = cantidad, 0.0
    for precio, tam in asks:
        toma = min(falta, tam)
        total += toma * precio
        falta -= toma
        if falta <= 1e-9:
            return total / cantidad
    return None  # no hay suficiente liquidez


# ---------------------------------------------------------------------------
# ARCHIVOS
# ---------------------------------------------------------------------------

def num(x):
    return "" if x is None else str(round(x, 4)).replace(".", ",")


def leer_ops():
    if not os.path.exists(ARCHIVO_OPS):
        return []
    with open(ARCHIVO_OPS, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def escribir_ops(ops):
    with open(ARCHIVO_OPS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS_OPS, delimiter=";")
        w.writeheader()
        w.writerows(ops)


def ya_registrado(hoy):
    if not os.path.exists(ARCHIVO_LIBRO):
        return False
    with open(ARCHIVO_LIBRO, encoding="utf-8-sig") as f:
        return any(linea.startswith(hoy.isoformat()) for linea in f)


# ---------------------------------------------------------------------------
# REGISTRAR HOY
# ---------------------------------------------------------------------------

def registrar_hoy():
    ahora = datetime.now()
    hoy = ahora.date()
    if not (VENTANA_MIN <= (ahora.hour, ahora.minute) <= VENTANA_MAX):
        print(f"Son las {ahora:%H:%M}: la regla solo registra entre 14:10 y 14:59. Hoy no se anota nada.")
        return
    if ya_registrado(hoy):
        print("Hoy ya quedo registrado. No se repite.")
        return

    entrenamiento, sesgo = preparar_modelo()
    pron = pronostico_de_ayer_para_hoy(hoy) + sesgo
    obs = bajar_metar(CIUDAD, hoy, hoy).get(hoy.isoformat(), [])
    hasta = maxima_hasta(obs, HORA * 60)
    if hasta is None:
        print("No hay mediciones de la estacion todavia. No se anota nada.")
        return
    dist = distribucion_subida(entrenamiento, HORA, pron - hasta)

    r = requests.get(GAMMA_API, params={"slug": slug_evento(CIUDAD, hoy)}, timeout=30)
    r.raise_for_status()
    eventos = r.json()
    if not eventos:
        print("No hay mercado de hoy para Sao Paulo.")
        return

    print(f"\n=== Prueba en papel SP 14hs | {hoy} {ahora:%H:%M} ===")
    print(f"Estacion hasta las 14:00: {hasta}°C | pronostico corregido: {pron:.1f}°C\n")
    print(f"  {'Caja':<16}{'Modelo':>7}{'Yes compra':>11}{'Yes venta':>10}{'No compra':>10}   Operacion")

    nuevo = not os.path.exists(ARCHIVO_LIBRO)
    ops = leer_ops()
    with open(ARCHIVO_LIBRO, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(["fecha", "hora", "caja", "maxima_hasta_14", "pron_corregido",
                        "prob_modelo", "yes_mejor_compra", "yes_mejor_venta", "no_mejor_compra",
                        "yes_costo_10", "no_costo_10"])
        for m in eventos[0].get("markets", []):
            try:
                rango = leer_caja(m["groupItemTitle"])
                yes_tok, no_tok = json.loads(m["clobTokenIds"])
            except (KeyError, ValueError):
                continue
            prob = prob_caja(dist, hasta, rango)
            yes_bids, yes_asks = libro(yes_tok)
            _, no_asks = libro(no_tok)
            yes_ask = yes_asks[0][0] if yes_asks else None
            yes_bid = yes_bids[0][0] if yes_bids else None
            no_ask = no_asks[0][0] if no_asks else None
            yes_10 = costo_de_comprar(yes_asks, ACCIONES)
            no_10 = costo_de_comprar(no_asks, ACCIONES)
            w.writerow([hoy.isoformat(), f"{ahora:%H:%M}", m["groupItemTitle"], hasta, num(pron),
                        num(prob), num(yes_ask), num(yes_bid), num(no_ask), num(yes_10), num(no_10)])

            op = ""
            muerta = rango[1] is not None and rango[1] < hasta  # ya imposible: igual que en el backtest, no se opera
            if muerta:
                lado = None
            elif yes_10 is not None and PRECIO_MIN <= yes_10 <= PRECIO_MAX and prob - yes_10 >= UMBRAL:
                lado, precio = "Yes", yes_10
            elif no_10 is not None and PRECIO_MIN <= no_10 <= PRECIO_MAX and (1 - prob) - no_10 >= UMBRAL:
                lado, precio = "No", no_10
            else:
                lado = None
            if lado:
                ops.append({"fecha": hoy.isoformat(), "caja": m["groupItemTitle"], "lado": lado,
                            "prob_modelo": num(prob), "precio_medio": num(precio),
                            "acciones": ACCIONES, "costo": num(precio * ACCIONES),
                            "maxima_hasta_14": hasta, "ganadora": "", "resultado": "", "tasa_comision": num(tasa_de(m))})
                op = f"<- compraria {ACCIONES} {lado} a {precio*100:.1f}¢"
            fmt = lambda x: "  -" if x is None else f"{x*100:.1f}¢"
            print(f"  {m['groupItemTitle']:<16}{prob*100:>6.0f}%{fmt(yes_ask):>11}{fmt(yes_bid):>10}"
                  f"{fmt(no_ask):>10}   {op}")
    escribir_ops(ops)


# ---------------------------------------------------------------------------
# LIQUIDAR Y RESUMIR
# ---------------------------------------------------------------------------

def liquidar_y_resumir():
    ops = leer_ops()
    hoy = date.today()
    ganadoras = {}
    for op in ops:
        if op["resultado"] or date.fromisoformat(op["fecha"]) >= hoy:
            continue
        f = op["fecha"]
        if f not in ganadoras:
            r = requests.get(GAMMA_API, params={"slug": slug_evento(CIUDAD, date.fromisoformat(f))}, timeout=30)
            r.raise_for_status()
            ganadoras[f] = None
            for m in (r.json() or [{}])[0].get("markets", []):
                precios = json.loads(m.get("outcomePrices") or "[]")
                if m.get("closed") and precios and float(precios[0]) >= 0.99:
                    ganadoras[f] = m["groupItemTitle"]
        g = ganadoras[f]
        if not g:
            continue
        acerto = (op["caja"] == g) == (op["lado"] == "Yes")
        costo = float(op["costo"].replace(",", "."))
        cobro = int(op["acciones"]) if acerto else 0
        op["ganadora"] = g
        op["resultado"] = num(cobro - costo)
    escribir_ops(ops)

    cerradas = [o for o in ops if o["resultado"]]
    dias = sorted({o["fecha"] for o in ops})
    print(f"\n=== Resumen prueba SP 14hs ===")
    print(f"Dias con operaciones: {len(dias)} | operaciones: {len(ops)} | ya liquidadas: {len(cerradas)}")
    if cerradas:
        invertido = sum(float(o["costo"].replace(",", ".")) for o in cerradas)
        resultado = sum(float(o["resultado"].replace(",", ".")) for o in cerradas)
        ganadas = sum(1 for o in cerradas if float(o["resultado"].replace(",", ".")) > 0)
        print(f"Ganadas: {ganadas}/{len(cerradas)} | invertido ${invertido:.2f} | "
              f"resultado ${resultado:+.2f} ({resultado / invertido * 100:+.1f}%)")
        print("El backtest decia +13% aprox. Con menos de ~100 operaciones, esto es todavia muy ruidoso.")


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() != "resumen":
        try:
            registrar_hoy()
        except Exception as e:
            print(f"Error registrando hoy: {e}")
    try:
        liquidar_y_resumir()
    except Exception as e:
        print(f"Error liquidando: {e}")


if __name__ == "__main__":
    main()

"""
Monitor de mercados de temperatura en Polymarket (SOLO OBSERVA, no apuesta).

Que hace:
  1. Busca el mercado "Highest temperature in <ciudad> on <fecha>?" de Polymarket.
  2. Lee el precio de cada caja de temperatura (17°C, 18°C, ...).
  3. Baja el pronostico "ensemble" gratuito de Open-Meteo (GFS + ECMWF, ~80 escenarios).
  4. Calcula que probabilidad le da el pronostico a cada caja.
  5. Muestra la comparacion en pantalla y la guarda en registro.csv.

Uso:
  python monitor.py            -> mercados de MANANA
  python monitor.py hoy        -> mercados de HOY
  python monitor.py 2026-10-20 -> una fecha concreta
"""

import csv
import json
import math
import os
import sys
from datetime import date, datetime, timedelta

import requests

# En la consola de Windows, para que se vean bien los "°" y acentos
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# CONFIGURACION (lo unico que quizas quieras tocar)
# ---------------------------------------------------------------------------

CIUDADES = [
    {
        "nombre": "Buenos Aires",
        "slug": "buenos-aires",
        "estacion": "Ezeiza (SAEZ)",
        "lat": -34.8222,
        "lon": -58.5358,
        "zona_horaria": "America/Argentina/Buenos_Aires",
    },
    {
        "nombre": "Sao Paulo",
        "slug": "sao-paulo",
        "estacion": "Guarulhos (SBGR)",
        "lat": -23.4356,
        "lon": -46.4731,
        "zona_horaria": "America/Sao_Paulo",
    },
]

# Modelos de pronostico a combinar (todos gratis en Open-Meteo)
MODELOS = "gfs025,ecmwf_ifs025"

# Incertidumbre extra (en °C) que sumamos a cada escenario. Los ensembles suelen
# ser "demasiado seguros" y la estacion mide en grados enteros. 1.0 es un punto
# de partida razonable; lo ajustaremos con los resultados reales.
SIGMA_EXTRA = 1.0

# Cuanta diferencia minima (en puntos de probabilidad) marcamos como "senal"
UMBRAL_SENAL = 0.08

CARPETA = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_REGISTRO = os.path.join(CARPETA, "registro.csv")
ARCHIVO_CALIBRACION = os.path.join(CARPETA, "calibracion.json")

GAMMA_API = "https://gamma-api.polymarket.com/events"
ENSEMBLE_API = "https://ensemble-api.open-meteo.com/v1/ensemble"

MESES_EN = ["january", "february", "march", "april", "may", "june", "july",
            "august", "september", "october", "november", "december"]


# ---------------------------------------------------------------------------
# POLYMARKET
# ---------------------------------------------------------------------------

def slug_evento(ciudad, fecha):
    return f"highest-temperature-in-{ciudad['slug']}-on-{MESES_EN[fecha.month - 1]}-{fecha.day}-{fecha.year}"


def leer_caja(titulo):
    """'19°C' -> (19, 19); '14°C or below' -> (None, 14); '24°C or higher' -> (24, None)."""
    t = titulo.replace("°C", "").replace("°", "").strip().lower()
    if "or below" in t:
        return (None, int(t.replace("or below", "").strip()))
    if "or higher" in t or "or above" in t:
        return (int(t.replace("or higher", "").replace("or above", "").strip()), None)
    if "-" in t[1:]:  # rango tipo "18-19"
        a, b = t.rsplit("-", 1)
        return (int(a), int(b))
    n = int(t)
    return (n, n)


def a_numero(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def buscar_mercado(ciudad, fecha):
    r = requests.get(GAMMA_API, params={"slug": slug_evento(ciudad, fecha)}, timeout=20)
    r.raise_for_status()
    eventos = r.json()
    if not eventos:
        return None
    evento = eventos[0]
    cajas = []
    for m in evento.get("markets", []):
        try:
            rango = leer_caja(m["groupItemTitle"])
        except (KeyError, ValueError):
            continue
        precios = json.loads(m.get("outcomePrices") or "[]")
        cajas.append({
            "titulo": m["groupItemTitle"],
            "rango": rango,
            "precio": a_numero(precios[0]) if precios else None,
            "compra": a_numero(m.get("bestAsk")),   # lo que pagas si compras "Yes"
            "venta": a_numero(m.get("bestBid")),    # lo que recibes si vendes "Yes"
            "cerrado": m.get("closed", False),
        })
    cajas.sort(key=lambda c: c["rango"][0] if c["rango"][0] is not None else -999)
    return {
        "titulo": evento.get("title", ""),
        "fuente": evento.get("resolutionSource", ""),
        "volumen": a_numero(evento.get("volume")) or 0,
        "cajas": cajas,
    }


# ---------------------------------------------------------------------------
# PRONOSTICO
# ---------------------------------------------------------------------------

def familia(clave):
    clave = clave.lower()
    if "ecmwf" in clave:
        return "ecmwf"
    if "gfs" in clave:
        return "gfs"
    return "otro"


def maximas_del_ensemble(ciudad, fecha):
    """Lista de (familia de modelo, temperatura maxima del dia) para cada escenario."""
    r = requests.get(ENSEMBLE_API, params={
        "latitude": ciudad["lat"],
        "longitude": ciudad["lon"],
        "hourly": "temperature_2m",
        "models": MODELOS,
        "timezone": ciudad["zona_horaria"],
        "forecast_days": 7,
    }, timeout=30)
    r.raise_for_status()
    horario = r.json()["hourly"]
    horas = horario["time"]
    indices = [i for i, h in enumerate(horas) if h.startswith(fecha.isoformat())]
    if not indices:
        return []
    maximas = []
    for clave, valores in horario.items():
        if not clave.startswith("temperature_2m"):
            continue
        del_dia = [valores[i] for i in indices if valores[i] is not None]
        if len(del_dia) >= 20:  # dia (casi) completo
            maximas.append((familia(clave), max(del_dia)))
    return maximas


def normal_acumulada(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def cargar_calibracion():
    try:
        with open(ARCHIVO_CALIBRACION, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def escenarios_calibrados(ciudad, fecha, maximas, calibracion):
    """
    Convierte los escenarios del ensemble en (centro, sigma, peso):
      - centro: maxima del escenario + sesgo de la estacion para ese modelo
                (+ medio ajuste por mes, porque el dato mensual es mas ruidoso)
      - sigma : lo que falta para que la incertidumbre total sea igual al
                error tipico historico de ese modelo
      - peso  : los modelos que historicamente erraron menos pesan mas
    Sin calibracion.json se usa lo de antes: sin sesgo y sigma SIGMA_EXTRA.
    """
    calib = calibracion.get(ciudad["nombre"])
    if not calib:
        n = len(maximas)
        return [(t, SIGMA_EXTRA, 1.0 / n) for _, t in maximas], False

    nombres = {"gfs": "gfs_seamless", "ecmwf": "ecmwf_ifs025"}
    ajuste_mes = 0.5 * (calib.get("sesgo_por_mes", {}).get(str(fecha.month), calib["sesgo"]) - calib["sesgo"])

    grupos = {}
    for fam, t in maximas:
        grupos.setdefault(fam, []).append(t)

    escenarios = []
    pesos_fam = {}
    for fam, temps in grupos.items():
        datos = calib.get("por_modelo", {}).get(nombres.get(fam, ""), None)
        sesgo = (datos or {}).get("sesgo", calib["sesgo"]) + ajuste_mes
        error = (datos or {}).get("desvio", calib["error_tipico"])
        media = sum(temps) / len(temps)
        dispersion = math.sqrt(sum((t - media) ** 2 for t in temps) / max(len(temps) - 1, 1))
        sigma = math.sqrt(max(error ** 2 - dispersion ** 2, 0.5 ** 2))
        pesos_fam[fam] = 1.0 / error ** 2
        for t in temps:
            escenarios.append((fam, t + sesgo, sigma))

    total_peso = sum(pesos_fam.values())
    resultado = []
    for fam, centro, sigma in escenarios:
        peso = (pesos_fam[fam] / total_peso) / len(grupos[fam])
        resultado.append((centro, sigma, peso))
    return resultado, True


def probabilidad_caja(escenarios, rango):
    """La estacion informa grados enteros: la caja 19°C cubre de 18.5 a 19.5."""
    bajo = -math.inf if rango[0] is None else rango[0] - 0.5
    alto = math.inf if rango[1] is None else rango[1] + 0.5
    total = 0.0
    for centro, sigma, peso in escenarios:
        p_alto = 1.0 if alto == math.inf else normal_acumulada((alto - centro) / sigma)
        p_bajo = 0.0 if bajo == -math.inf else normal_acumulada((bajo - centro) / sigma)
        total += peso * (p_alto - p_bajo)
    return total


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------

def fecha_objetivo():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "hoy":
            return date.today()
        return date.fromisoformat(arg)
    return date.today() + timedelta(days=1)


def pct(x):
    return "  -  " if x is None else f"{x * 100:4.0f}%"


def guardar(filas):
    nuevo = not os.path.exists(ARCHIVO_REGISTRO)
    with open(ARCHIVO_REGISTRO, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(["momento", "ciudad", "fecha_mercado", "caja", "precio_mercado",
                        "compra_yes", "venta_yes", "prob_modelo", "ventaja_compra",
                        "media_modelo", "n_escenarios"])
        # Excel en espanol usa coma decimal
        for fila in filas:
            w.writerow([str(x).replace(".", ",") if isinstance(x, float) else
                        ("" if x is None else x) for x in fila])


def main():
    fecha = fecha_objetivo()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n=== Monitor de clima | mercados del {fecha} | {ahora} ===")
    print("(Solo observacion: no se compra nada)\n")

    calibracion = cargar_calibracion()
    filas = []
    for ciudad in CIUDADES:
        print(f"--- {ciudad['nombre']} · estacion {ciudad['estacion']} ---")
        try:
            mercado = buscar_mercado(ciudad, fecha)
        except Exception as e:
            print(f"  No pude leer Polymarket: {e}\n")
            continue
        if not mercado or not mercado["cajas"]:
            print(f"  No hay mercado para esa fecha ({slug_evento(ciudad, fecha)}).\n")
            continue

        try:
            maximas = maximas_del_ensemble(ciudad, fecha)
        except Exception as e:
            print(f"  No pude leer el pronostico: {e}\n")
            continue
        if not maximas:
            print("  El pronostico no cubre esa fecha.\n")
            continue

        escenarios, calibrado = escenarios_calibrados(ciudad, fecha, maximas, calibracion)
        media = sum(c * p for c, _, p in escenarios)
        temps = [t for _, t in maximas]
        print(f"  Volumen: ${mercado['volumen']:,.0f} | Fuente oficial: {mercado['fuente']}")
        print(f"  Pronostico: maxima esperada {media:.1f}°C "
              f"(escenarios de {min(temps):.1f} a {max(temps):.1f}, {len(temps)} en total) | "
              f"{'calibrado con historial' if calibrado else 'SIN calibrar'}\n")
        print(f"  {'Caja':<16}{'Mercado':>8}{'Compra':>8}{'Modelo':>8}   Senal")

        for c in mercado["cajas"]:
            prob = probabilidad_caja(escenarios, c["rango"])
            senal = ""
            if c["compra"] is not None and prob - c["compra"] >= UMBRAL_SENAL:
                senal = f"<- modelo mas alto (+{(prob - c['compra']) * 100:.0f} pts)"
            elif c["venta"] is not None and c["venta"] - prob >= UMBRAL_SENAL:
                senal = f"<- mercado mas alto (+{(c['venta'] - prob) * 100:.0f} pts)"
            print(f"  {c['titulo']:<16}{pct(c['precio']):>8}{pct(c['compra']):>8}{pct(prob):>8}   {senal}")

            filas.append([
                ahora, ciudad["nombre"], fecha.isoformat(), c["titulo"],
                c["precio"], c["compra"], c["venta"], round(prob, 4),
                None if c["compra"] is None else round(prob - c["compra"], 4),
                round(media, 2), len(temps),
            ])
        print()

    if filas:
        guardar(filas)
        print(f"Guardado en {ARCHIVO_REGISTRO}")
    print("\nRecordatorio: una 'senal' NO es una recomendacion. Primero medimos varias "
          "semanas si el modelo acierta mas que el mercado.")


if __name__ == "__main__":
    main()

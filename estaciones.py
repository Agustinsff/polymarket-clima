"""
Datos compartidos por todos los bots: zona horaria de cada ciudad, estaciones
excluidas, como leer el nombre de una caja y PECULIARIDADES de cada estacion
(ver PECULIARIDADES y el informe estaciones_informe.md).
"""

import re

TZ = {"london": "Europe/London", "paris": "Europe/Paris", "ankara": "Europe/Istanbul", "munich": "Europe/Berlin",
      "shanghai": "Asia/Shanghai", "milan": "Europe/Rome", "madrid": "Europe/Madrid", "warsaw": "Europe/Warsaw",
      "chongqing": "Asia/Shanghai", "wuhan": "Asia/Shanghai", "shenzhen": "Asia/Shanghai", "amsterdam": "Europe/Amsterdam",
      "helsinki": "Europe/Helsinki", "jeddah": "Asia/Riyadh", "lucknow": "Asia/Kolkata", "singapore": "Asia/Singapore",
      "kuala-lumpur": "Asia/Kuala_Lumpur", "cape-town": "Africa/Johannesburg", "karachi": "Asia/Karachi",
      "manila": "Asia/Manila", "nyc": "America/New_York", "dallas": "America/Chicago", "atlanta": "America/New_York",
      "miami": "America/New_York", "chicago": "America/Chicago", "austin": "America/Chicago", "denver": "America/Denver",
      "houston": "America/Chicago", "seattle": "America/Los_Angeles", "los-angeles": "America/Los_Angeles",
      "san-francisco": "America/Los_Angeles", "sao-paulo": "America/Sao_Paulo",
      "buenos-aires": "America/Argentina/Buenos_Aires", "toronto": "America/Toronto", "mexico-city": "America/Mexico_City",
      "panama-city": "America/Panama", "seoul": "Asia/Seoul", "wellington": "Pacific/Auckland", "tokyo": "Asia/Tokyo",
      "beijing": "Asia/Shanghai", "chengdu": "Asia/Shanghai", "busan": "Asia/Seoul", "guangzhou": "Asia/Shanghai",
      "qingdao": "Asia/Shanghai"}

# Estaciones donde el METAR no coincidio con la resolucion oficial (ver PECULIARIDADES)
EXCLUIR = {"LFPB", "VILK", "KBKF"}

# Analisis del 20-oct-2026 (1148 mercados del 6 al 19-oct, ver estaciones_informe.md):
# el maximo/minimo de los METAR cayo en la caja ganadora 1142 veces de 1148.
# Estas son las 6 veces que NO (en todas, el METAR marco 1-2 grados de mas).
PECULIARIDADES = {
    "KBKF": "Denver: 2 de 13 dias el METAR dio 1-2 °F mas que la caja ganadora (13 y 14-oct). Excluida del cosechador.",
    "LFPB": "Paris: 07-oct METAR 19, gano 18. Excluida del cosechador.",
    "VILK": "Lucknow: 13-oct METAR 33, gano 32. Excluida del cosechador.",
    "KORD": "Chicago: 16-oct METAR 58 °F, gano 56-57. Vigilar.",
    "KMIA": "Miami (minima): 17-oct METAR 76 °F, gano 74-75. Vigilar.",
    "FACT": "Ciudad del Cabo: 18-oct un METAR suelto de 19 °C con tormenta; resolucion en disputa.",
}


def fee(p):
    """Comision del que toma la orden (taker), por accion."""
    return 0.05 * p * (1 - p)


def leer_caja(t):
    """'19°C' -> (19, 19, False); '60-61°F' -> (60, 61, True); '15°C or below' -> (None, 15, False)."""
    f = "°F" in t
    t = re.sub(r"°[CF]", "", t).strip().lower()
    if "or below" in t:
        return None, int(t.replace("or below", "")), f
    if "or higher" in t or "or above" in t:
        return int(re.sub(r"or (higher|above)", "", t)), None, f
    m = re.match(r"^(-?\d+)-(-?\d+)$", t)
    if m:
        return int(m.group(1)), int(m.group(2)), f
    return int(t), int(t), f


def centro_caja(t):
    """Temperatura 'representativa' de una caja ganadora (en sus unidades)."""
    try:
        lo, hi, _ = leer_caja(t)
    except Exception:
        return None
    if lo is None:
        return hi
    if hi is None:
        return lo
    return (lo + hi) / 2

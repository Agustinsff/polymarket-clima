"""
Guardia METAR "fina" del bot maker (8-nov-2026, pedido de Agus): el dia del evento, si la temperatura ya observada
en la estacion dejo una caja DECIDIDA, el bot deja de cotizarla (la suelta). Solo cajas decididas con certeza:
  - maximas: la maxima observada hasta ahora ya supero la caja (la caja "17°C" o "17°C or below" ya no puede ganar),
    o ya alcanzo una caja "N or higher" (gano seguro: el No esta muerto);
  - minimas: al reves (la minima observada ya quedo por debajo de la caja, o ya alcanzo una "N or below").
Una caja donde la observada APENAS llego al valor de la caja (Chengdu 17 °C el 8-nov) NO esta decidida: puede subir.
Regla de resolucion de Polymarket (regla_metar/REGLA.md): solo reportes de rutina (METAR, no SPECI), grupo T en
decimas si esta, .5 hacia arriba, °F convertido. Estaciones: propio/estaciones.json (ciudad -> ICAO, zona horaria,
°F). Ciudades sin estacion conocida: sin guardia (se avisa en el log una vez).
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

AWC = "https://aviationweather.gov/api/data/metar"
F_ESTACIONES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "propio", "estaciones.json")
MESES = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                         "september", "october", "november", "december"])}


def cargar_estaciones(ruta=F_ESTACIONES):
    """ciudad (como en el slug del evento) -> {icao, tz, en_f}."""
    with open(ruta, encoding="utf-8") as f:
        e = json.load(f)
    return {v["ciudad"]: {"icao": k, "tz": v["tz"], "en_f": bool(v.get("en_f"))} for k, v in e.items() if k != "HKO"}


def evento_de(slug):
    """'highest-temperature-in-tel-aviv-on-november-8-2026' -> ('max', 'tel-aviv', date(2026, 11, 8)); None si no."""
    m = re.match(r"(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})$", slug or "")
    if not m or m.group(3) not in MESES:
        return None
    serie = "max" if m.group(1) == "highest" else "min"
    return serie, m.group(2), datetime(int(m.group(5)), MESES[m.group(3)], int(m.group(4))).date()


def caja_de(titulo):
    """'17°C' -> ('exacta', 17, 'C'); '35°C or below' -> ('hasta', 35, 'C'); '36°F or higher' -> ('desde', 36, 'F')."""
    m = re.match(r"\s*(-?\d+)\s*°\s*([CF])\s*(or below|or higher)?\s*$", titulo or "")
    if not m:
        return None
    tipo = {"or below": "hasta", "or higher": "desde", None: "exacta"}[m.group(3)]
    return tipo, int(m.group(1)), m.group(2)


def redondear_pm(x):
    """Redondeo de Polymarket: .5 hacia arriba (tambien en negativos: -0,5 -> 0)."""
    return int((x + 0.5) // 1)


def temp_reporte(rep):
    """Temperatura en decimas de °C del reporte (grupo T si esta, si no el campo temp). None si no hay."""
    raw = rep.get("rawOb") or ""
    m = re.search(r"\bT(\d)(\d{3})(\d)(\d{3})\b", raw)
    if m:
        t = int(m.group(2)) / 10
        return -t if m.group(1) == "1" else t
    t = rep.get("temp")
    return float(t) if t is not None else None


def temps_del_dia(reportes, fecha, tz, en_f):
    """Temperaturas resueltas (enteras, °C o °F segun el mercado) de los reportes de RUTINA del dia local `fecha`."""
    zona = ZoneInfo(tz)
    out = []
    for r in reportes:
        if (r.get("metarType") or "METAR") != "METAR":
            continue
        try:
            cuando = datetime.fromtimestamp(int(r["obsTime"]), timezone.utc).astimezone(zona).date()
        except (KeyError, TypeError, ValueError):
            continue
        if cuando != fecha:
            continue
        t = temp_reporte(r)
        if t is None:
            continue
        out.append(redondear_pm(t * 9 / 5 + 32 if en_f else t))
    return out


def decidida(serie, caja, temps):
    """Motivo si la caja ya quedo decidida por lo observado; None si sigue abierta o no hay datos."""
    c = caja_de(caja)
    if not c or not temps:
        return None
    tipo, n, _ = c
    if serie == "max":
        obs = max(temps)
        if tipo in ("exacta", "hasta") and obs > n:
            return f"maxima observada {obs} > {caja}: el Si ya no puede ganar"
        if tipo == "desde" and obs >= n:
            return f"maxima observada {obs} >= {caja}: el Si ya gano"
    else:
        obs = min(temps)
        if tipo in ("exacta", "desde") and obs < n:
            return f"minima observada {obs} < {caja}: el Si ya no puede ganar"
        if tipo == "hasta" and obs <= n:
            return f"minima observada {obs} <= {caja}: el Si ya gano"
    return None


class Guardia:
    """Consulta los METAR de la estacion (cache 10 min) y dice si una caja esta decidida."""
    def __init__(self, estaciones=None, buscar=None, cache_seg=600, log=print):
        self.est = estaciones if estaciones is not None else cargar_estaciones()
        self.buscar = buscar or self._awc
        self.cache_seg, self.log = cache_seg, log
        self.cache = {}                                   # icao -> (momento, reportes)
        self.sin_estacion = set()

    @staticmethod
    def _awc(icao):
        r = requests.get(AWC, params={"ids": icao, "format": "json", "hours": 30}, timeout=30)
        r.raise_for_status()
        return r.json() or []

    def reportes(self, icao, ahora):
        c = self.cache.get(icao)
        if c and ahora - c[0] < self.cache_seg:
            return c[1]
        reps = self.buscar(icao)
        self.cache[icao] = (ahora, reps)
        return reps

    def motivo(self, evento_slug, caja, ahora=None):
        """Motivo (texto) si la caja ya esta decidida por la temperatura observada; None si no (o sin datos)."""
        ev = evento_de(evento_slug)
        if not ev:
            return None
        serie, ciudad, fecha = ev
        e = self.est.get(ciudad)
        if not e:
            if ciudad not in self.sin_estacion:
                self.sin_estacion.add(ciudad)
                self.log(f"guardia METAR: sin estacion para {ciudad}, esa ciudad va sin guardia")
            return None
        ahora = ahora if ahora is not None else time.time()
        # solo tiene sentido el dia del evento (hora local) o despues
        if datetime.fromtimestamp(ahora, timezone.utc).astimezone(ZoneInfo(e["tz"])).date() < fecha:
            return None
        try:
            reps = self.reportes(e["icao"], ahora)
        except Exception as ex:                           # noqa: BLE001
            self.log(f"guardia METAR: no se pudo leer {e['icao']}: {ex!r}; sigo sin guardia en {ciudad}")
            return None
        return decidida(serie, caja, temps_del_dia(reps, fecha, e["tz"], e["en_f"]))

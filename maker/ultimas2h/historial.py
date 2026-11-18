"""Complemento de la medicion "ultimas 2 horas" (REGLA.md): con el historial publico de precios del CLOB, en eventos de
temperatura ya resueltos, mira cuantas cajas siguen con precio entre 0,10 y 0,90 en las ultimas 2 h del dia local, cuanto
se mueve el precio por hora ahi y cuanto se mueve en las 22 h anteriores. No hay libro ni competencia en este historial:
solo precio. Uso: python maker/ultimas2h/historial.py 2026-11-13 2026-11-17  (fechas de los eventos)."""
import json
import os
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))
from estaciones import TZ  # noqa: E402
import requests  # noqa: E402

S = requests.Session()
MESES = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november",
         "december"]
d0, d1 = (date.fromisoformat(x) for x in sys.argv[1:3])


def evento(tipo, ciudad, d):
    slug = f"{tipo}-temperature-in-{ciudad}-on-{MESES[d.month - 1]}-{d.day}-{d.year}"
    try:
        r = S.get("https://gamma-api.polymarket.com/events", params={"slug": slug}, timeout=30).json()
        return (ciudad, d, r[0]) if r else None
    except Exception:            # noqa: BLE001
        return None


def historia(token, a, b):
    r = S.get("https://clob.polymarket.com/prices-history", params={"market": token, "startTs": a, "endTs": b,
                                                                    "fidelity": 5}, timeout=30).json()
    return [(int(x["t"]), float(x["p"])) for x in r.get("history", [])]


pedidos = [(t, c, d0 + timedelta(days=i)) for t in ("highest", "lowest") for c in TZ for i in range((d1 - d0).days + 1)]
with ThreadPoolExecutor(8) as ex:
    evs = [e for e in ex.map(lambda p: evento(*p), pedidos) if e]
cajas = []
for ciudad, d, e in evs:
    fin = datetime(d.year, d.month, d.day, tzinfo=ZoneInfo(TZ[ciudad])) + timedelta(days=1)   # medianoche local
    for mk in e.get("markets", []):
        if mk.get("clobTokenIds"):
            cajas.append({"evento": e["slug"], "caja": mk.get("groupItemTitle"), "token": json.loads(mk["clobTokenIds"])[0],
                          "fin": int(fin.timestamp())})


def medir(c):
    try:
        h = historia(c["token"], c["fin"] - 24 * 3600, c["fin"])
    except Exception:            # noqa: BLE001
        return None
    if len(h) < 20:
        return None
    ult = [p for t, p in h if t >= c["fin"] - 7200]
    ant = [p for t, p in h if t < c["fin"] - 7200]

    def mov(serie):              # |cambio| en 1 h (12 puntos de 5 min)
        return [abs(serie[i] - serie[i - 12]) for i in range(12, len(serie))]
    return dict(c, medio_ult=statistics.mean(ult) if ult else None, mov_ult=mov(ult), mov_ant=mov(ant),
                mitad_ult=bool(ult) and all(0.10 <= p <= 0.90 for p in ult[:3]))


with ThreadPoolExecutor(8) as ex:
    res = [r for r in ex.map(medir, cajas) if r]
dias = (d1 - d0).days + 1
vivas = [r for r in res if r["mitad_ult"]]
mov_u = [x for r in vivas for x in r["mov_ult"]]
mov_a = [x for r in vivas for x in r["mov_ant"]]
lin = ["", "## Complemento con el historial de precios (eventos del " + f"{d0:%d}-{d1:%d-%m-%Y})", "",
       f"- Eventos leídos: {len(evs)} ({len(res)} cajas con historial).",
       f"- Cajas que al empezar las últimas 2 h del día local seguían con precio entre 0,10 y 0,90: {len(vivas)} "
       f"({len(vivas) / dias:.1f} por día entre todas las ciudades; {100 * len(vivas) / max(len(res), 1):.1f} % de las cajas).",
       f"- En esas cajas, movimiento medio del precio en 1 h: últimas 2 h {100 * statistics.mean(mov_u) if mov_u else float('nan'):.2f} ¢ "
       f"({100 * sum(x >= 0.06 for x in mov_u) / max(len(mov_u), 1):.0f} % de las horas con 6 ¢ o más) contra "
       f"{100 * statistics.mean(mov_a) if mov_a else float('nan'):.2f} ¢ en las 22 h anteriores "
       f"({100 * sum(x >= 0.06 for x in mov_a) / max(len(mov_a), 1):.0f} %).", ""]
print("\n".join(lin))
with open(os.path.join(AQUI, "informe.md"), "a", encoding="utf-8") as f:
    f.write("\n".join(lin) + "\n")

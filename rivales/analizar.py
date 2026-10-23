"""
Analisis de rivales (lee lo que bajo rivales/bajar.py, no se conecta a nada).
Escribe rivales/informe_datos.md con las tablas y rivales/billeteras.csv.

Uso: python rivales/analizar.py
"""

import csv
import gzip
import math
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(CARPETA))
from estaciones import TZ, fee  # noqa: E402

SALIDA = []


def p(*a):
    SALIDA.append(" ".join(str(x) for x in a))


def leer(nombre):
    with gzip.open(os.path.join(CARPETA, nombre), "rt", newline="") as f:
        yield from csv.DictReader(f)


def tabla(cab, filas):
    p("| " + " | ".join(cab) + " |")
    p("|" + "---|" * len(cab))
    for f in filas:
        p("| " + " | ".join(str(x) for x in f) + " |")
    p("")


def usd(x):
    return f"{x:,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
# cajas
# ---------------------------------------------------------------------------
CAJAS = {}
for r in leer("eventos.csv.gz"):
    if r["precio_final_si"] not in ("0", "1"):
        continue
    tz = ZoneInfo(TZ.get(r["ciudad"], "UTC"))
    d = datetime.fromisoformat(r["fecha"])
    ini = datetime(d.year, d.month, d.day, tzinfo=tz).astimezone(timezone.utc).timestamp()
    CAJAS[r["condition_id"]] = {**r, "gano_si": r["precio_final_si"] == "1", "ini": ini, "fin_dia": ini + 86400,
                                "fee_on": r["fee"] == "True", "tz": tz}

# ---------------------------------------------------------------------------
# operaciones
# ---------------------------------------------------------------------------
OPS = []
for r in leer("trades.csv.gz"):
    c = CAJAS.get(r["condition_id"])
    if not c:
        continue
    pr, sz, t = float(r["price"]), float(r["size"]), int(r["timestamp"])
    oi = int(r["outcome_index"])
    gana_tok = c["gano_si"] if oi == 0 else not c["gano_si"]
    pago = 1.0 if gana_tok else 0.0
    com = fee(pr) * sz if c["fee_on"] else 0.0
    pnl = (sz * (pago - pr) if r["side"] == "BUY" else sz * (pr - pago)) - com
    if t < c["ini"]:
        fase = "antes"
    elif t < c["fin_dia"]:
        fase = "durante"
    else:
        fase = "despues"
    OPS.append({"cid": r["condition_id"], "w": r["wallet"], "name": r["name"] or r["pseudonym"], "side": r["side"],
                "pr": pr, "sz": sz, "usd": pr * sz, "t": t, "pnl": pnl, "fase": fase, "gana": gana_tok,
                "p_si": pr if oi == 0 else 1 - pr, "ev": c["slug"], "ciudad": c["ciudad"], "c": c})
OPS.sort(key=lambda o: o["t"])
if not OPS:
    sys.exit("sin operaciones")
t0 = datetime.fromtimestamp(OPS[0]["t"], timezone.utc)
t1 = datetime.fromtimestamp(OPS[-1]["t"], timezone.utc)
evs = {c["slug"] for c in CAJAS.values()}
p(f"# Rivales en mercados de temperatura: datos\n")
p(f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%MZ}. {len(evs)} eventos cerrados, {len(CAJAS)} cajas, "
  f"{len(OPS)} operaciones (lado taker) del {t0:%d-%b} al {t1:%d-%b}. Volumen taker US$ {usd(sum(o['usd'] for o in OPS))}.\n")
p("PnL = lo que gana o pierde el que toma la orden si se queda hasta la resolución, con comisión. "
  "No vemos al market maker (el otro lado de cada operación).\n")

# --- volumen por fase y por tamano -------------------------------------------
p("## 1. Dónde está la plata\n")
fil = []
for fase, nom in (("antes", "antes del día (pronóstico)"), ("durante", "durante el día"), ("despues", "después del día (esperando resolución)")):
    xs = [o for o in OPS if o["fase"] == fase]
    v = sum(o["usd"] for o in xs)
    pn = sum(o["pnl"] for o in xs)
    fil.append([nom, len(xs), usd(v), usd(pn), f"{100 * pn / v:+.1f}%" if v else "-"])
tabla(["fase", "operaciones", "volumen US$", "PnL takers US$", "PnL/volumen"], fil)

fil = []
tramos = [(0, 10), (10, 100), (100, 500), (500, 2000), (2000, 1e12)]
for a, b in tramos:
    xs = [o for o in OPS if a <= o["usd"] < b]
    v = sum(o["usd"] for o in xs)
    pn = sum(o["pnl"] for o in xs)
    fil.append([f"{usd(a)}–{usd(b) if b < 1e11 else '+'}", len(xs), usd(v), usd(pn), f"{100 * pn / v:+.1f}%" if v else "-",
                f"{100 * sum(o['fase'] == 'antes' for o in xs) / max(1, len(xs)):.0f}%"])
tabla(["tamaño (US$)", "operaciones", "volumen", "PnL", "PnL/volumen", "% antes del día"], fil)

# por precio del token comprado
fil = []
for a, b in [(0, .05), (.05, .2), (.2, .5), (.5, .8), (.8, .95), (.95, 1.01)]:
    xs = [o for o in OPS if o["side"] == "BUY" and a <= o["pr"] < b]
    v = sum(o["usd"] for o in xs)
    pn = sum(o["pnl"] for o in xs)
    gan = sum(o["gana"] for o in xs) / max(1, len(xs))
    pm = sum(o["pr"] for o in xs) / max(1, len(xs))
    fil.append([f"{a:.2f}–{min(b, 1):.2f}", len(xs), usd(v), f"{100 * pn / v:+.1f}%" if v else "-", f"{100 * pm:.1f}%", f"{100 * gan:.1f}%"])
p("Compras por precio pagado (¿el precio dice la verdad?):\n")
tabla(["precio", "compras", "volumen", "PnL/volumen", "precio medio", "ganaron"], fil)

# --- billeteras ---------------------------------------------------------------
p("## 2. Billeteras\n")
B = defaultdict(lambda: {"n": 0, "usd": 0.0, "pnl": 0.0, "ev": defaultdict(float), "fases": defaultdict(float),
                         "minutos": [], "precios": [], "nombre": "", "ciudades": defaultdict(float), "horas_ini": []})
for o in OPS:
    b = B[o["w"]]
    b["n"] += 1
    b["usd"] += o["usd"]
    b["pnl"] += o["pnl"]
    b["ev"][o["ev"]] += o["pnl"]
    b["fases"][o["fase"]] += o["usd"]
    b["minutos"].append(datetime.fromtimestamp(o["t"], timezone.utc).minute)
    b["precios"].append(o["pr"])
    b["nombre"] = o["name"]
    b["ciudades"][o["ciudad"]] += o["usd"]
    b["horas_ini"].append((o["t"] - o["c"]["ini"]) / 3600)


def tstat(xs):
    if len(xs) < 3:
        return 0.0
    s = st.pstdev(xs)
    return st.mean(xs) / (s / math.sqrt(len(xs))) if s > 0 else 0.0


def resumen_b(w, b):
    evp = list(b["ev"].values())
    tot = b["usd"] or 1
    ciudad = max(b["ciudades"], key=b["ciudades"].get)
    return {"billetera": w, "nombre": b["nombre"], "ops": b["n"], "eventos": len(evp), "volumen": round(b["usd"]),
            "pnl": round(b["pnl"]), "roi": b["pnl"] / tot, "ev_ganados": sum(x > 0 for x in evp) / max(1, len(evp)),
            "t": tstat(evp), "antes": b["fases"]["antes"] / tot, "durante": b["fases"]["durante"] / tot,
            "despues": b["fases"]["despues"] / tot, "precio_med": st.median(b["precios"]),
            "caro": sum(x >= .9 for x in b["precios"]) / b["n"], "hora_rel_med": st.median(b["horas_ini"]),
            "ciudad_top": f"{ciudad} {100 * b['ciudades'][ciudad] / tot:.0f}%"}


RES = [resumen_b(w, b) for w, b in B.items()]
with open(os.path.join(CARPETA, "billeteras.csv"), "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(RES[0]))
    wr.writeheader()
    for r in sorted(RES, key=lambda r: -r["pnl"]):
        wr.writerow(r)

vol_tot = sum(r["volumen"] for r in RES)
orden = sorted(RES, key=lambda r: -r["volumen"])
acum = 0
for i, r in enumerate(orden):
    acum += r["volumen"]
    if acum >= vol_tot / 2:
        break
p(f"{len(RES)} billeteras distintas. Las {i + 1} más grandes hacen la mitad del volumen taker.\n")


def fila_b(r):
    return [r["nombre"][:18] or r["billetera"][:10], r["billetera"][:8], r["eventos"], usd(r["volumen"]), usd(r["pnl"]),
            f"{100 * r['roi']:+.1f}%", f"{100 * r['ev_ganados']:.0f}%", f"{r['t']:.1f}",
            f"{100 * r['antes']:.0f}/{100 * r['durante']:.0f}/{100 * r['despues']:.0f}", f"{r['precio_med']:.2f}",
            f"{100 * r['caro']:.0f}%", f"{r['hora_rel_med']:+.0f}", r["ciudad_top"]]


CAB = ["nombre", "billetera", "eventos", "volumen", "PnL", "PnL/vol", "eventos +", "t", "% antes/durante/después",
       "precio mediano", "% a ≥90¢", "hora mediana vs inicio del día", "ciudad principal"]
p("### Las 25 que más ganaron (mínimo 10 eventos)\n")
tabla(CAB, [fila_b(r) for r in sorted([r for r in RES if r["eventos"] >= 10], key=lambda r: -r["pnl"])[:25]])
p("### Las 15 que más perdieron (mínimo 10 eventos)\n")
tabla(CAB, [fila_b(r) for r in sorted([r for r in RES if r["eventos"] >= 10], key=lambda r: r["pnl"])[:15]])
p("### Las 15 de más volumen\n")
tabla(CAB, [fila_b(r) for r in orden[:15]])
p("t = PnL medio por evento dividido por su error (más de 2 o 3 = ganan de forma constante, no por suerte). "
  "Hora mediana vs inicio del día: horas desde la medianoche local del día que se mide (negativo = el día anterior).\n")

# estilo de las ganadoras
gan = [r for r in RES if r["eventos"] >= 10 and r["t"] >= 2 and r["pnl"] > 0]
p(f"**Ganadoras constantes** (≥10 eventos, t ≥ 2): {len(gan)} billeteras, PnL total US$ {usd(sum(r['pnl'] for r in gan))}. "
  f"De su volumen: {100 * sum(r['antes'] * r['volumen'] for r in gan) / max(1, sum(r['volumen'] for r in gan)):.0f}% antes del día, "
  f"{100 * sum(r['durante'] * r['volumen'] for r in gan) / max(1, sum(r['volumen'] for r in gan)):.0f}% durante, "
  f"{100 * sum(r['despues'] * r['volumen'] for r in gan) / max(1, sum(r['volumen'] for r in gan)):.0f}% después.\n")

# minuto de la hora de las ganadoras (bots de METAR)
p("### ¿A qué minuto de la hora operan las ganadoras constantes? (UTC)\n")
mins = defaultdict(int)
mins_all = defaultdict(int)
gw = {r["billetera"] for r in gan}
for o in OPS:
    m = datetime.fromtimestamp(o["t"], timezone.utc).minute // 5 * 5
    mins_all[m] += 1
    if o["w"] in gw:
        mins[m] += 1
na, ng = max(1, sum(mins_all.values())), max(1, sum(mins.values()))
tabla(["minuto", "% ops ganadoras", "% ops de todos"], [[f":{m:02d}", f"{100 * mins[m] / ng:.1f}%", f"{100 * mins_all[m] / na:.1f}%"] for m in range(0, 60, 5)])

# operaciones grandes
p("## 3. Las 30 operaciones más grandes\n")
fil = []
for o in sorted(OPS, key=lambda o: -o["usd"])[:30]:
    c = o["c"]
    fil.append([datetime.fromtimestamp(o["t"], timezone.utc).strftime("%d-%b %H:%M"), c["ciudad"], c["tipo"][:4], c["fecha"][5:],
                c["caja"], o["side"], "Sí" if (o["p_si"] == o["pr"]) else "No", f"{o['pr']:.3f}", usd(o["usd"]), usd(o["pnl"]),
                f"{(o['t'] - c['ini']) / 3600:+.1f}", o["name"][:16]])
tabla(["hora UTC", "ciudad", "tipo", "fecha", "caja", "lado", "token", "precio", "US$", "PnL", "h vs inicio día", "quién"], fil)

# ---------------------------------------------------------------------------
# 4. movimiento de precio por hora del dia UTC (cajas del dia siguiente)
# ---------------------------------------------------------------------------
p("## 4. ¿Cuándo se mueve el precio? (cajas que todavía no empezaron su día)\n")
SER = defaultdict(list)
try:
    for r in leer("precios.csv.gz"):
        if r["condition_id"] in CAJAS:
            SER[r["condition_id"]].append((int(r["t"]), float(r["p"])))
except FileNotFoundError:
    pass
mov = defaultdict(float)
cnt = defaultdict(int)
dias = set()
for cid, s in SER.items():
    c = CAJAS[cid]
    s.sort()
    for (ta, pa), (tb, pb) in zip(s, s[1:]):
        if tb >= c["ini"] - 3600 or tb - ta > 600:
            continue
        b = (tb % 86400) // 300
        mov[b] += abs(pb - pa)
        dias.add(tb // 86400)
for o in OPS:
    if o["fase"] == "antes" and o["t"] < o["c"]["ini"] - 3600:
        cnt[(o["t"] % 86400) // 300] += o["usd"]
nd = max(1, len(dias))
tot_m = sum(mov.values()) or 1
tot_v = sum(cnt.values()) or 1
p(f"{len(SER)} cajas con historia de precio por minuto, {nd} días. Suma de |cambio de precio| (puntos) por hora UTC, "
  "sólo cajas cuyo día local empieza en más de 1 h. Volumen = operaciones taker en esas cajas.\n")
fil = []
for h in range(24):
    m = sum(mov[b] for b in range(h * 12, h * 12 + 12))
    v = sum(cnt[b] for b in range(h * 12, h * 12 + 12))
    fil.append([f"{h:02d}", f"{100 * m / tot_m:.1f}%", "█" * round(100 * m / tot_m), f"{100 * v / tot_v:.1f}%"])
tabla(["hora UTC", "% del movimiento", "", "% del volumen"], fil)
top = sorted(mov, key=lambda b: -mov[b])[:15]
p("Los 15 tramos de 5 min con más movimiento: " + ", ".join(
    f"{b * 5 // 60:02d}:{b * 5 % 60:02d} ({100 * mov[b] / tot_m:.1f}%)" for b in sorted(top)) + "\n")

# ---------------------------------------------------------------------------
# 5. reaccion a las corridas de los modelos
# ---------------------------------------------------------------------------
p("## 5. ¿Qué tan rápido se mueve el precio después de cada corrida?\n")
p("Horas aproximadas en que cada corrida empieza a estar disponible gratis (UTC): GFS 00/06/12/18Z a las 03:30/09:30/15:30/21:30; "
  "ECMWF 00/12Z a las ~06:40/18:40. Para cada ventana y cada caja del día siguiente (su día local empieza en más de 6 h), "
  "se mide |precio(W+k) − precio(W)| y se compara con lo mismo 3 h antes (control). El 'exceso' es lo que se movió por la corrida.\n")


def serie_minuto(s):
    d = {}
    for t, x in s:
        d[t // 60] = x
    return d


MIN = {cid: serie_minuto(s) for cid, s in SER.items()}


def precio_en(d, m, atras=30):
    for k in range(atras):
        if m - k in d:
            return d[m - k]
    return None


VENT = [("GFS 00Z", 3 * 60 + 30), ("ECMWF 00Z", 6 * 60 + 40), ("GFS 06Z", 9 * 60 + 30), ("GFS 12Z", 15 * 60 + 30),
        ("ECMWF 12Z", 18 * 60 + 40), ("GFS 18Z", 21 * 60 + 30)]
KS = [10, 20, 30, 45, 60, 90, 120, 180]


def estudio(wmin):
    sumas = {k: [0.0, 0.0, 0] for k in KS}
    for cid, d in MIN.items():
        c = CAJAS[cid]
        if not d:
            continue
        m0, m1 = min(d), max(d)
        dia = m0 // 1440
        while dia * 1440 <= m1:
            W = dia * 1440 + wmin
            dia += 1
            if W * 60 > c["ini"] - 6 * 3600 or W - 180 < m0 or W + 180 > m1:
                continue
            a, ac = precio_en(d, W), precio_en(d, W - 180)
            if a is None or ac is None or not (0.03 < a < 0.97):
                continue
            for k in KS:
                b, bc = precio_en(d, W + k), precio_en(d, W - 180 + k)
                if b is None or bc is None:
                    continue
                sumas[k][0] += abs(b - a)
                sumas[k][1] += abs(bc - ac)
                sumas[k][2] += 1
    return sumas


fil = []
for nom, wm in VENT:
    s = estudio(wm)
    n = s[180][2]
    if not n:
        continue
    ex = {k: (s[k][0] - s[k][1]) / max(1, s[k][2]) * 100 for k in KS}
    base = ex[180] if ex[180] > 0 else None
    fil.append([nom, f"{wm // 60:02d}:{wm % 60:02d}", n, f"{100 * s[180][0] / n:.2f}", f"{100 * s[180][1] / n:.2f}",
                f"{ex[180]:+.2f}"] + [f"{100 * ex[k] / base:.0f}%" if base else "-" for k in (10, 20, 30, 60, 120)])
tabla(["corrida", "W (UTC)", "casos", "mov. 3h después (pts)", "control (pts)", "exceso", "a 10 min", "20 min", "30 min", "60 min", "120 min"], fil)
p("Columnas 'a X min': qué parte del exceso de 3 h ya ocurrió a los X minutos de W.\n")

with open(os.path.join(CARPETA, "informe_datos.md"), "w") as f:
    f.write("\n".join(SALIDA) + "\n")
print("\n".join(SALIDA))

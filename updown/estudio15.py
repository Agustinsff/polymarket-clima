"""Favorito tardio en 15 min (regla en updown/REGLA_15M.md): baja 60 dias de BTC/ETH 15 min y analiza.
Uso (en Actions, paso.txt = estudio15): python updown/estudio15.py   -> updown/resultados_15m.md
Con ANALIZAR_SOLO=1 no baja nada (sirve para correrlo sin red sobre lo ya bajado)."""
import gzip
import json
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA)
SERIES15 = {"btc-up-or-down-15m": "BTC", "eth-up-or-down-15m": "ETH"}
LO, HI, ACC = 0.70, 0.90, 10
out = []


def p(*a):
    out.append(" ".join(str(x) for x in a))


def cargar(serie):
    ruta = os.path.join(CARPETA, "datos", serie + ".json.gz")
    if not os.path.exists(ruta):
        return {}
    with gzip.open(ruta, "rt", encoding="utf-8") as f:
        return json.load(f)


def precio_antes(h, t, max_viejo):
    xs = [pp for ts, pp in h if t - max_viejo <= ts <= t]
    return xs[-1] if xs else None


def ops(mercados, seg_antes, costo, lo=LO, hi=HI):
    """[(activo, dia, neto, puesto, gano, precio)] del favorito a seg_antes del cierre."""
    res = []
    for v in mercados:
        if v.get("gano_up") not in (0, 1):
            continue
        pu = precio_antes(v["h"], v["fin"] - seg_antes, v["ventana"] / 10)
        if pu is None:
            continue
        lado_up = pu >= 0.5
        s = pu if lado_up else 1 - pu
        if not lo <= s < hi:
            continue
        pr = min(s + costo, 0.999)
        gana = (v["gano_up"] == 1) == lado_up
        tasa = v.get("tasa") if v.get("tasa") is not None else 0.07
        neto = ACC * ((1 if gana else 0) - pr) - ACC * tasa * pr * (1 - pr)
        dia = datetime.fromtimestamp(v["ini"], timezone.utc).strftime("%Y-%m-%d")
        res.append((v["activo"], dia, neto, ACC * pr, int(gana), s))
    return res


def boot(res, n=2000):
    bl = defaultdict(float)
    for a, d, neto, *_ in res:
        bl[(a, d)] += neto
    v = list(bl.values())
    if len(v) < 2:
        return float("nan")
    rnd = random.Random(7)
    return sum(sum(rnd.choice(v) for _ in v) <= 0 for _ in range(n)) / n


def linea(res):
    if not res:
        return "0 ops"
    neto, puesto = sum(r[2] for r in res), sum(r[3] for r in res)
    gan = sum(r[4] for r in res) / len(res)
    pm = sum(r[5] for r in res) / len(res)
    return (f"{len(res)} ops, ganó {100 * gan:.1f} % (precio medio {100 * pm:.1f} ¢), neto US$ {neto:+.1f}, "
            f"ROI {100 * neto / puesto:+.2f} %, P(≤0) {boot(res):.3f}")


def analizar():
    m15 = [v for s in SERIES15 for v in cargar(s).values()]
    m1h = [v for s in ("btc-up-or-down-hourly", "eth-up-or-down-hourly") for v in cargar(s).values()]
    dias = sorted({datetime.fromtimestamp(v["ini"], timezone.utc).strftime("%Y-%m-%d") for v in m15})
    p(f"# Favorito tardío en 15 min (regla en REGLA_15M.md) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z", "")
    p(f"Mercados 15 min con ganador: BTC {sum(v['activo'] == 'BTC' and v.get('gano_up') in (0, 1) for v in m15)}, "
      f"ETH {sum(v['activo'] == 'ETH' and v.get('gano_up') in (0, 1) for v in m15)}; días {dias[0] if dias else '–'} a {dias[-1] if dias else '–'}.", "")
    p("## Control (1 h, 6 min antes, 1 ¢): debe dar ~545 ops y +4,8 %")
    p("- " + linea(ops(m1h, 360, 0.01)), "")
    p("## Regla principal: 15 min, 90 s antes, 70–90 ¢, comisión + 1 ¢")
    r = ops(m15, 90, 0.01)
    p("- Todo: " + linea(r))
    mitad = dias[len(dias) // 2] if dias else ""
    r1, r2 = [x for x in r if x[1] < mitad], [x for x in r if x[1] >= mitad]
    p("- Primera mitad: " + linea(r1))
    p("- Segunda mitad: " + linea(r2))
    rb, re_ = [x for x in r if x[0] == "BTC"], [x for x in r if x[0] == "ETH"]
    p("- BTC: " + linea(rb))
    p("- ETH: " + linea(re_))
    roi = lambda rs: sum(x[2] for x in rs) / sum(x[3] for x in rs) if rs else 0
    pasa = bool(r) and roi(r) > 0 and boot(r) < 0.05 and roi(r1) > 0 and roi(r2) > 0 and roi(rb) > 0 and roi(re_) > 0
    p("", f"**Veredicto con la regla fija: {'PASA' if pasa else 'NO PASA'}.**", "")
    p("## Se informa además (no decide)")
    p("| momento | costo extra | resultado |", "|---|---|---|")
    for seg, nom in ((360, "6 min"), (240, "4 min"), (180, "3 min"), (90, "90 s")):
        for c in (0.0, 0.01, 0.02):
            p(f"| {nom} | {int(100 * c)} ¢ | {linea(ops(m15, seg, c))} |")
    p("", "Calibración del lado favorito (sin costos): cuánto gana de verdad vs el precio.", "")
    p("| momento | tramo | ops | precio medio | ganó |", "|---|---|---|---|---|")
    for seg, nom in ((360, "6 min"), (180, "3 min"), (90, "90 s")):
        for lo, hi in ((0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)):
            rr = ops(m15, seg, 0.0, lo, hi + (1e-9 if hi == 1.0 else 0))
            if rr:
                p(f"| {nom} | {int(100 * lo)}–{int(100 * hi)} ¢ | {len(rr)} | {100 * sum(x[5] for x in rr) / len(rr):.1f} ¢ | "
                  f"{100 * sum(x[4] for x in rr) / len(rr):.1f} % |")
    with open(os.path.join(CARPETA, "resultados_15m.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    if not os.environ.get("ANALIZAR_SOLO"):
        import bajar
        bajar.T0 = __import__("time").time()
        for serie, activo in SERIES15.items():
            bajar.bajar_serie(serie, activo, 900, 60, 1)
    analizar()

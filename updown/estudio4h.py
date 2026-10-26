"""Favorito tardio en 4 h y 1 dia (regla en updown/REGLA_4H1D.md). Usa lo ya bajado; no usa red.
Uso: python updown/estudio4h.py  -> updown/resultados_4h1d.md"""
import os
import sys
from datetime import datetime, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA)
from estudio15 import boot, cargar, linea, ops  # noqa: E402

out = []
p = lambda *a: out.extend(a)
roi = lambda rs: sum(x[2] for x in rs) / sum(x[3] for x in rs) if rs else 0
VENT = {"4 h": ("btc-up-or-down-4h", "eth-up-or-down-4h"), "1 día": ("btc-up-or-down-daily", "eth-up-or-down-daily")}


def ops6(ms, seg, costo, lo=0.70, hi=0.90):
    # el precio vale si es de los ultimos `seg` segundos como mucho 6 min (no 1/10 de la ventana, que en 1 dia son 2,4 h)
    return ops([dict(v, ventana=min(v["ventana"], 3600)) for v in ms], seg, costo, lo, hi)


def main():
    p(f"# Favorito tardío en 4 h y 1 día (regla en REGLA_4H1D.md) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z", "")
    m1h = [v for s in ("btc-up-or-down-hourly", "eth-up-or-down-hourly") for v in cargar(s).values()]
    p("## Control (1 h, 6 min antes, 1 ¢): debe dar 545 ops y +4,8 %", "- " + linea(ops(m1h, 360, 0.01)), "")
    for nombre, series in VENT.items():
        ms = [v for s in series for v in cargar(s).values()]
        dias = sorted({datetime.fromtimestamp(v["ini"], timezone.utc).strftime("%Y-%m-%d") for v in ms})
        r = ops6(ms, 360, 0.01)
        mitad = dias[len(dias) // 2]
        r1, r2 = [x for x in r if x[1] < mitad], [x for x in r if x[1] >= mitad]
        rb, re_ = [x for x in r if x[0] == "BTC"], [x for x in r if x[0] == "ETH"]
        p(f"## {nombre}: 6 min antes, 70–90 ¢, comisión + 1 ¢ ({len(ms)} mercados, {dias[0]} a {dias[-1]})",
          "- Todo: " + linea(r), "- Primera mitad: " + linea(r1), "- Segunda mitad: " + linea(r2),
          "- BTC: " + linea(rb), "- ETH: " + linea(re_))
        if len(r) < 40:
            ver = "SIN DATOS SUFICIENTES"
        else:
            ver = "PASA" if (roi(r) > 0 and boot(r) < 0.025 and roi(r1) > 0 and roi(r2) > 0 and roi(rb) > 0 and roi(re_) > 0) else "NO PASA"
        p("", f"**Veredicto {nombre}: {ver}.**", "", "| momento | costo extra | resultado |", "|---|---|---|")
        for seg, nom in ((600, "10 min"), (360, "6 min"), (180, "3 min")):
            for c in (0.0, 0.01, 0.02):
                p(f"| {nom} | {int(100 * c)} ¢ | {linea(ops6(ms, seg, c))} |")
        p("", "| 6 min, tramo | ops | precio medio | ganó |", "|---|---|---|---|")
        for lo, hi in ((0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)):
            rr = ops6(ms, 360, 0.0, lo, hi + (1e-9 if hi == 1.0 else 0))
            if rr:
                p(f"| {int(100 * lo)}–{int(100 * hi)} ¢ | {len(rr)} | {100 * sum(x[5] for x in rr) / len(rr):.1f} ¢ | "
                  f"{100 * sum(x[4] for x in rr) / len(rr):.1f} % |")
        p("")
    with open(os.path.join(CARPETA, "resultados_4h1d.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()

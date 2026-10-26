"""
FOTOS POR MINUTO del final de los Up/Down de 1 h (para elegir el minuto de entrada el 17-nov). NO opera.
Despues de la pasada del bot (minuto 54) saca una foto del libro de los dos lados en cada minuto hasta el 58.
Los resultados por minuto NO se miran hasta el 17-nov (regla en bot/SOMBRA_REGLA.md, seccion "minuto").

Uso: python bot/fotos_minuto.py            (fotos de esta hora; la corre el reloj)
     python bot/fotos_minuto.py analizar   (solo el 17-nov: ROI del favorito segun el minuto de entrada)
Archivo: bot/fotos_minuto.csv
"""
import csv
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA)
import mercado  # noqa: E402
from polybot import cargar_cfg  # noqa: E402

F = os.path.join(CARPETA, "fotos_minuto.csv")
COLS = ["momento_utc", "minuto", "activo", "condition_id", "lado", "bid", "ask", "p5", "p10", "tasa"]
ULTIMO = 58


def foto(cfg, ahora):
    filas = []
    for serie, activo in cfg["favorito"]["series"].items():
        for e in mercado.eventos_abiertos(serie):
            try:
                mins = mercado.minutos_al_cierre(e, ahora)
            except (KeyError, ValueError):
                continue
            mk = (e.get("markets") or [None])[0]
            if not 0.5 <= mins <= 8 or not mk or mk.get("closed"):
                continue
            for lado, tok in mercado.lados(mk):
                bids, asks = mercado.libro(tok)
                filas.append([ahora.strftime("%Y-%m-%d %H:%M:%S"), ahora.minute, activo, mk["conditionId"], lado,
                              bids[0][0] if bids else "", asks[0][0] if asks else "",
                              mercado.costo_compra(asks, 5) or "", mercado.costo_compra(asks, 10) or "",
                              mercado.tasa_comision(mk)])
    nuevo = not os.path.exists(F)
    with open(F, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(COLS)
        w.writerows(filas)
    return len(filas)


def fotos():
    cfg = cargar_cfg()
    while True:
        ahora = datetime.now(timezone.utc)
        if not cfg["favorito"]["minuto_objetivo"] <= ahora.minute <= ULTIMO:
            return
        try:
            n = foto(cfg, ahora)
            print(f"{ahora:%H:%M:%S}Z minuto {ahora.minute}: {n} libros")
        except Exception as ex:
            print(f"{ahora:%H:%M:%S}Z minuto {ahora.minute}: error {ex!r}")
        if ahora.minute >= ULTIMO:
            return
        sig = ahora.replace(second=5, microsecond=0).timestamp() + 60
        time.sleep(max(1, sig - time.time()))


def analizar():
    """ROI del favorito tardio (5 acciones, 70-90 c, comision + 1 c) segun el minuto de entrada."""
    with open(F, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    por = defaultdict(list)
    for r in filas:
        por[(r["condition_id"], r["minuto"])].append(r)
    ganador = {}
    res = defaultdict(list)
    for (cid, minuto), lados in sorted(por.items()):
        cal = [r for r in lados if r["p5"] and 0.70 <= float(r["p5"]) < 0.90]
        if len(cal) != 1:
            continue
        if cid not in ganador:
            try:
                ganador[cid] = mercado.ganador(cid)
            except Exception:
                ganador[cid] = None
        if ganador[cid] is None:
            continue
        r = cal[0]
        p, t = min(float(r["p5"]) + 0.01, 0.999), float(r["tasa"] or 0)
        neto = 5 * ((ganador[cid] == r["lado"]) - p) - 5 * t * p * (1 - p)
        res[int(minuto)].append((r["momento_utc"][:10], neto, 5 * p))
    for minuto in sorted(res):
        ops = res[minuto]
        dia = defaultdict(float)
        for d, n, _ in ops:
            dia[d] += n
        v = list(dia.values())
        rnd = random.Random(7)
        pboot = sum(sum(rnd.choice(v) for _ in v) <= 0 for _ in range(2000)) / 2000 if len(v) > 1 else float("nan")
        neto, puesto = sum(o[1] for o in ops), sum(o[2] for o in ops)
        print(f"minuto {minuto}: {len(ops)} ops, neto US$ {neto:+.2f}, ROI {100 * neto / puesto:+.2f} %, P(<=0) {pboot:.3f}")


if __name__ == "__main__":
    analizar() if len(sys.argv) > 1 and sys.argv[1] == "analizar" else fotos()

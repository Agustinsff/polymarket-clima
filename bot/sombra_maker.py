"""
SOMBRA MAKER del favorito tardio (regla en bot/SOMBRA_REGLA.md). NO pone ordenes.
Por cada senal del bot en papel imagina una compra 1 c abajo del precio visto, viva hasta el cierre, y mira con las
operaciones reales si se habria llenado. Compara contra comprar al precio de venta (taker) en los mismos mercados.

Uso: python bot/sombra_maker.py        (evalua los mercados ya cerrados y escribe bot/sombra_maker.md)
Archivos: bot/sombra_maker.csv
"""
import csv
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA)
import mercado  # noqa: E402

F_OPS = os.path.join(CARPETA, "ops_papel.csv")
F_SOM = os.path.join(CARPETA, "sombra_maker.csv")
F_RES = os.path.join(CARPETA, "sombra_maker.md")
TRADES = "https://data-api.polymarket.com/trades"
COLS = ["momento_utc", "activo", "evento", "condition_id", "lado", "acciones", "precio_visto", "tasa", "L",
        "llenadas", "gano", "pnl_maker", "pnl_taker"]


def leer(n):
    if not os.path.exists(n):
        return []
    with open(n, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def ts(txt):
    return datetime.strptime(txt, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def trades(cid, desde, hasta, m=mercado):
    """Operaciones taker del mercado entre desde y hasta: [(ts, outcome, side, precio, acciones)]."""
    out, offset = [], 0
    while offset < 5000:
        lote = m.S.get(TRADES, params={"market": cid, "limit": 500, "offset": offset, "takerOnly": "true"},
                       timeout=30).json() or []
        for t in lote:
            x = int(t.get("timestamp") or 0)
            if desde < x <= hasta:
                out.append((x, t.get("outcome"), t.get("side"), float(t.get("price") or 0), float(t.get("size") or 0)))
        if len(lote) < 500 or min(int(t.get("timestamp") or 0) for t in lote) <= desde:
            break
        offset += 500
    return sorted(out)


def llenado(trs, lado, L, acciones):
    """Acciones que se habrian llenado a L (prudente: solo ventas de nuestro lado a precio < L)."""
    resto = acciones
    for _, outcome, side, p, q in trs:
        if outcome != lado:                 # operaron el otro token: se pasa a nuestro lado
            p, side = 1 - p, ("SELL" if side == "BUY" else "BUY")
        if side == "SELL" and p < L - 1e-9:
            resto -= min(resto, q)
            if resto <= 0:
                break
    return acciones - resto


def evaluar(m=mercado, ahora=None):
    ahora = ahora or datetime.now(timezone.utc)
    hechos = {r["condition_id"] for r in leer(F_SOM)}
    primeras = {}
    for o in leer(F_OPS):
        if o.get("precio_visto") and o["condition_id"] not in primeras:
            primeras[o["condition_id"]] = o
    nuevas = []
    for cid, o in primeras.items():
        if cid in hechos:
            continue
        cierre = datetime.strptime(o["momento_utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) \
            + timedelta(minutes=float(o["min_al_cierre"]))
        if ahora < cierre + timedelta(minutes=5):
            continue
        try:
            g = m.ganador(cid)
            if g is None:
                continue
            trs = trades(cid, ts(o["momento_utc"]), cierre.timestamp(), m)
        except Exception as ex:
            print(f"{cid}: {ex!r}")
            continue
        q, pv, tasa = float(o["acciones"]), float(o["precio_visto"]), float(o["tasa"] or 0)
        L = round(pv - 0.01, 2)
        lle = llenado(trs, o["lado"], L, q)
        gano = int(g == o["lado"])
        nuevas.append([o["momento_utc"], o["activo"], o["evento"], cid, o["lado"], q, pv, tasa, L, lle, gano,
                       round(lle * (gano - L), 4), round(q * (gano - pv) - q * tasa * pv * (1 - pv), 4)])
    if nuevas:
        nuevo = not os.path.exists(F_SOM)
        with open(F_SOM, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            if nuevo:
                w.writerow(COLS)
            w.writerows(nuevas)
    return nuevas


def resumen():
    filas = leer(F_SOM)
    lin = [f"# Sombra maker del favorito tardío (regla en SOMBRA_REGLA.md) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z", ""]
    if not filas:
        lin.append("- Todavía no hay mercados cerrados para evaluar.")
    else:
        n = len(filas)
        llen = [r for r in filas if float(r["llenadas"]) > 0]
        completas = sum(float(r["llenadas"]) >= float(r["acciones"]) for r in filas)
        pm = sum(float(r["pnl_maker"]) for r in filas)
        pt = sum(float(r["pnl_taker"]) for r in filas)
        dif = defaultdict(float)
        for r in filas:
            dif[r["momento_utc"][:10]] += float(r["pnl_maker"]) - float(r["pnl_taker"])
        v = list(dif.values())
        rnd = random.Random(7)
        p = sum(sum(rnd.choice(v) for _ in v) <= 0 for _ in range(2000)) / 2000 if len(v) > 1 else float("nan")
        no_llen = [r for r in filas if float(r["llenadas"]) == 0]
        acierto = lambda rs: f"{100 * sum(int(r['gano']) for r in rs) / len(rs):.0f} %" if rs else "–"
        lin += [f"- Mercados: {n}; con algo llenado: {len(llen)} ({100 * len(llen) / n:.0f} %), completos: {completas}.",
                f"- Ganancia maker US$ {pm:+.2f} vs taker US$ {pt:+.2f} en los mismos mercados "
                f"(diferencia {pm - pt:+.2f}; {len(v)} días, P(maker ≤ taker) {p:.2f}).",
                f"- Aciertos del favorito: llenadas {acierto(llen)} vs no llenadas {acierto(no_llen)} "
                f"(si las llenadas aciertan mucho menos, hay selección adversa)."]
    with open(F_RES, "w", encoding="utf-8") as f:
        f.write("\n".join(lin) + "\n")
    print("\n".join(lin))


if __name__ == "__main__":
    evaluar()
    resumen()

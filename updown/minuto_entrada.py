"""ANALISIS ADELANTADO (2-nov, pedido por Agus): favorito tardio segun el minuto de entrada (53 de favorito/fotos.csv,
54-58 de bot/fotos_minuto.csv), con el ganador de TODOS los mercados fotografiados (no solo los operados), y calibracion
precio vs. acierto por tramo. Solo lee (raw de GitHub + clob). No toca reglas. Salida: updown/minuto_entrada.md"""
import csv, io, os, random, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAW = "https://raw.githubusercontent.com/Agustinsff/polymarket-clima/main/"
S = requests.Session(); S.headers["User-Agent"] = "polymarket-clima-updown/0.1 (investigacion personal)"
out = []
p = lambda *a: out.append(" ".join(str(x) for x in a))


def leer(ruta):
    return list(csv.DictReader(io.StringIO(S.get(RAW + ruta, timeout=40).text), delimiter=";"))


def ganador(cid):
    for i in range(3):
        try:
            r = S.get(f"https://clob.polymarket.com/markets/{cid}", timeout=20).json()
            if not r.get("closed"):
                return cid, None
            return cid, next((t["outcome"] for t in r.get("tokens", []) if t.get("winner")), None)
        except Exception:
            time.sleep(2)
    return cid, None


def main():
    fm = leer("bot/fotos_minuto.csv"); ff = leer("favorito/fotos.csv")
    por = defaultdict(list)
    for r in fm:
        por[(r["condition_id"], int(r["minuto"]))].append((r["momento_utc"], r["lado"], r["p5"], r["p10"], r["tasa"], r["activo"]))
    for r in ff:
        por[(r["condition_id"], 53)].append((r["momento_utc"], r["lado"], r["p10"], r["p10"], "0.07", r["activo"]))
    cids = sorted({c for c, _ in por})
    with ThreadPoolExecutor(8) as ex:
        gan = dict(ex.map(ganador, cids))
    gan = {k: v for k, v in gan.items() if v}
    p(f"# Favorito tardío según el minuto de entrada — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z\n")
    p(f"Análisis adelantado a pedido de Agus (2-nov). {len(cids)} mercados fotografiados, {len(gan)} con resultado. "
      "Minuto 53 = favorito/fotos.csv (10 acc.); 54–58 = bot/fotos_minuto.csv. Compra del lado a 70–90 ¢, comisión del mercado + 1 ¢.\n")
    for q, col in ((5, 2), (10, 3)):
        p(f"## {q} acciones\n\n| minuto | ops | ganó | % | precio medio | neto US$ | ROI | P(≤0) | días | BTC / ETH |\n|---|---|---|---|---|---|---|---|---|---|")
        for m in range(53, 59):
            ops = []
            for (cid, mm), lados in por.items():
                if mm != m or cid not in gan:
                    continue
                cal = [l for l in lados if l[col] and 0.70 <= float(l[col]) < 0.90]
                if len(cal) != 1:
                    continue
                l = cal[0]; pr = min(float(l[col]) + 0.01, 0.999); t = float(l[4] or 0); win = gan[cid] == l[1]
                ops.append((l[0][:10], q * (win - pr) - q * t * pr * (1 - pr), q * pr, win, float(l[col]), l[5]))
            if not ops:
                continue
            dia = defaultdict(float); act = defaultdict(float)
            for d, n, _, _, _, a in ops:
                dia[d] += n; act[a] += n
            v = list(dia.values()); rnd = random.Random(7)
            pb = sum(sum(rnd.choice(v) for _ in v) <= 0 for _ in range(2000)) / 2000 if len(v) > 1 else float("nan")
            neto = sum(o[1] for o in ops); puesto = sum(o[2] for o in ops); w = sum(o[3] for o in ops)
            p(f"| {m} | {len(ops)} | {w} | {100 * w / len(ops):.0f} % | {sum(o[4] for o in ops) / len(ops):.3f} | {neto:+.2f} | {100 * neto / puesto:+.1f} % | {pb:.2f} | {len(v)} | {act.get('BTC', 0):+.1f} / {act.get('ETH', 0):+.1f} |")
        p("")
    p("## Calibración en el minuto 54 (todos los lados con precio ≥ 50 ¢, 5 acciones)\n\n| tramo | fotos | ganó % | precio medio | ganó − precio |\n|---|---|---|---|---|")
    band = defaultdict(lambda: [0, 0, 0.0])
    for (cid, m), lados in por.items():
        if m != 54 or cid not in gan:
            continue
        for l in lados:
            if l[2] and float(l[2]) >= 0.5:
                pr = float(l[2]); b = band[min(int(pr * 20) / 20, 0.95)]; b[0] += 1; b[1] += gan[cid] == l[1]; b[2] += pr
    for b in sorted(band):
        n, w, s = band[b]
        p(f"| {b:.2f}–{b + .05:.2f} | {n} | {100 * w / n:.0f} % | {s / n:.3f} | {100 * (w / n - s / n):+.1f} pts |")
    with open(os.path.join(CARPETA, "minuto_entrada.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()

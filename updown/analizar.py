"""Paso 2: calibracion y reglas simples sobre lo bajado (REGLA.md). No usa red.
Uso: python updown/analizar.py  -> updown/resultados.md y updown/resumen.json"""
import glob, gzip, json, math, os, random
from collections import defaultdict
from datetime import datetime, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
MOMENTOS = (0.10, 0.25, 0.50, 0.75, 0.90)
TRAMOS = [(i / 10, (i + 1) / 10) for i in range(10)]
COSTOS = (0.0, 0.01, 0.02)
ACC = 10
REMUESTREOS = 2000
REGLAS = {"favorito>=70": ("fav", .70), "favorito>=80": ("fav", .80), "favorito>=90": ("fav", .90),
          "cola<=30": ("cola", .30), "cola<=20": ("cola", .20), "cola<=10": ("cola", .10), "cincuenta 45-55": ("cin", None)}
NOMBRE_V = {900: "15 min", 3600: "1 h", 14400: "4 h", 86400: "1 día"}
out = []


def p(*a):
    out.append(" ".join(str(x) for x in a))


def fee(pr, tasa):
    return tasa * pr * (1 - pr)


def precio_en(h, t, ventana):
    xs = [pp for ts, pp in h if t - ventana / 10 <= ts <= t]
    return xs[-1] if xs else None


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    r = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (c - r, c + r)


def cargar():
    filas = []    # (activo, ventana, slug, dia, momento, p_up, gano_up, tasa, fin)
    for f in sorted(glob.glob(os.path.join(CARPETA, "datos", "*.json.gz"))):
        for slug, v in json.load(gzip.open(f, "rt", encoding="utf-8")).items():
            if v["gano_up"] not in (0, 1):
                continue
            dia = datetime.fromtimestamp(v["ini"], timezone.utc).strftime("%Y-%m-%d")
            for m in MOMENTOS:
                pu = precio_en(v["h"], v["ini"] + m * v["ventana"], v["ventana"])
                if pu is None:
                    continue
                filas.append((v["activo"], v["ventana"], slug, dia, m, pu, v["gano_up"], v["tasa"] or 0.0, v["fin"]))
    return filas


def op(lado, pr, gano_up, tasa, costo):
    """Neto de comprar ACC acciones del lado a precio pr (+costo)."""
    pr = min(pr + costo, 0.999)
    gana = (gano_up == 1) == (lado == "Up")
    return ACC * ((1 - pr) if gana else -pr) - ACC * fee(pr, tasa), ACC * pr


def aplicar(regla, pu):
    tipo, u = REGLAS[regla]
    if tipo == "fav":
        return "Up" if pu >= u else "Down" if 1 - pu >= u else None
    if tipo == "cola":
        return "Up" if pu <= u else "Down" if 1 - pu <= u else None
    return "Up" if .45 <= pu <= .55 else None


def boot(bloques):
    v = list(bloques.values())
    if len(v) < 2:
        return float("nan")
    rnd = random.Random(7)
    return sum(sum(rnd.choice(v) for _ in v) <= 0 for _ in range(REMUESTREOS)) / REMUESTREOS


def main():
    filas = cargar()
    resumen = {"n_filas": len(filas), "reglas": []}
    p(f"# Up or Down de cripto: calibración y reglas simples ({len(filas)} fotos, generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z)\n")
    # deriva
    p("## Deriva (cuántas veces resolvió Up)\n\n| activo | ventana | mercados | Up | % |\n|---|---|---|---|---|")
    vistos = {}
    for a, v, slug, dia, m, pu, g, tasa, fin in filas:
        vistos[(a, v, slug)] = g
    for (a, v), xs in sorted(defaultdict(list, {k: [g for (a2, v2, s), g in vistos.items() if (a2, v2) == k] for k in {(a, v) for a, v, s in vistos}}).items()):
        p(f"| {a} | {NOMBRE_V[v]} | {len(xs)} | {sum(xs)} | {100 * sum(xs) / len(xs):.1f} |")
    # calibracion por momento y ventana (Up y Down juntos: una foto a precio q del lado X cuenta como q)
    p("\n## Calibración: precio del lado vs. cuántas veces ganó (Up y Down juntos, 95 % Wilson)\n")
    for v in sorted({f[1] for f in filas}):
        p(f"\n### Ventana {NOMBRE_V[v]}\n\n| momento | tramo | fotos | precio medio | ganó % | IC 95 % | ganó − precio (¢) |\n|---|---|---|---|---|---|---|")
        for m in MOMENTOS:
            cel = defaultdict(list)
            for a, vv, slug, dia, mm, pu, g, tasa, fin in filas:
                if vv != v or mm != m:
                    continue
                for lado, q, gana in (("Up", pu, g == 1), ("Down", 1 - pu, g == 0)):
                    for lo, hi in TRAMOS:
                        if lo <= q < hi or (hi == 1.0 and q == 1.0):
                            cel[(lo, hi)].append((q, gana)); break
            for (lo, hi), xs in sorted(cel.items()):
                if len(xs) < 20:
                    continue
                k = sum(g for q, g in xs); n = len(xs); qm = sum(q for q, g in xs) / n
                a_, b_ = wilson(k, n)
                p(f"| {int(m * 100)} % | {int(lo * 100)}–{int(hi * 100)} | {n} | {100 * qm:.1f} | {100 * k / n:.1f} | {100 * a_:.0f}–{100 * b_:.0f} | {100 * (k / n - qm):+.1f} |")
    # reglas
    p("\n## Reglas fijas (10 acciones por foto; comisión del mercado + costo extra 0/1/2 ¢)\n")
    p("ROI = neto / plata puesta. P(≤0) por bootstrap de bloques (activo, día). Mitades = primera/segunda mitad de fechas.\n")
    for v in sorted({f[1] for f in filas}):
        p(f"\n### Ventana {NOMBRE_V[v]}\n\n| regla | momento | ops | ROI 0 ¢ | ROI 1 ¢ | ROI 2 ¢ | P(≤0) 1 ¢ | mitades 1 ¢ | BTC / ETH 1 ¢ |\n|---|---|---|---|---|---|---|---|---|")
        for regla in REGLAS:
            for m in MOMENTOS:
                res = {c: [0.0, 0.0] for c in COSTOS}
                bl = defaultdict(float); mit = defaultdict(float); act = defaultdict(float)
                fechas = sorted({f[3] for f in filas if f[1] == v}); corte = fechas[len(fechas) // 2]
                n = 0
                for a, vv, slug, dia, mm, pu, g, tasa, fin in filas:
                    if vv != v or mm != m:
                        continue
                    lado = aplicar(regla, pu)
                    if lado is None:
                        continue
                    n += 1
                    for c in COSTOS:
                        neto, puesto = op(lado, pu if lado == "Up" else 1 - pu, g, tasa, c)
                        res[c][0] += neto; res[c][1] += puesto
                        if c == 0.01:
                            bl[(a, dia)] += neto; mit[dia >= corte] += neto; act[a] += neto
                if n < 20:
                    continue
                roi = {c: 100 * res[c][0] / res[c][1] for c in COSTOS}
                p0 = boot(bl)
                p(f"| {regla} | {int(m * 100)} % | {n} | {roi[0]:+.1f} % | {roi[.01]:+.1f} % | {roi[.02]:+.1f} % | {p0:.2f} | "
                  f"{mit[False]:+.0f} / {mit[True]:+.0f} | {act.get('BTC', 0):+.0f} / {act.get('ETH', 0):+.0f} |")
                resumen["reglas"].append({"ventana": v, "regla": regla, "momento": m, "ops": n, "roi": roi, "p0_1c": p0,
                                          "mitades": [mit[False], mit[True]], "btc": act.get("BTC", 0), "eth": act.get("ETH", 0),
                                          "pasa": roi[.01] > 0 and p0 < .05 and mit[False] > 0 and mit[True] > 0 and act.get("BTC", 0) > 0 and act.get("ETH", 0) > 0})
    pasan = [r for r in resumen["reglas"] if r["pasa"]]
    p(f"\n## Criterio de REGLA.md\n\nReglas que pasan (ROI>0 con 1 ¢, P(≤0)<5 %, dos mitades y BTC y ETH positivos): **{len(pasan)}** de {len(resumen['reglas'])}.")
    for r in pasan:
        p(f"- {NOMBRE_V[r['ventana']]} {r['regla']} al {int(r['momento'] * 100)} %: ROI {r['roi'][.01]:+.1f} %, {r['ops']} ops, P {r['p0_1c']:.3f}")
    # ---- agregado despues (26-oct 14:50Z), tras ver las tablas: el tramo 70-90 c tarde en la ventana ----
    p("\n## Agregado después de ver los datos: favorito tardío a 70–90 ¢ (no es regla fija; hay que probarlo en vivo)\n")
    p("| ventana | momento | tramo | ops | ganó % | ROI 0 ¢ | ROI 1 ¢ | ROI 2 ¢ | P(≤0) 1 ¢ | mitades 1 ¢ | BTC / ETH 1 ¢ |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for v in (3600, 14400):
        fechas = sorted({f[3] for f in filas if f[1] == v}); corte = fechas[len(fechas) // 2]
        for ms in ((0.75,), (0.90,), (0.75, 0.90)):
            for lo, hi in ((.70, .90), (.70, .80), (.80, .90)):
                res = {c: [0.0, 0.0] for c in COSTOS}; bl = defaultdict(float); act = defaultdict(float); mit = defaultdict(float); n = w = 0
                for a, vv, slug, dia, m, pu, g, tasa, fin in filas:
                    if vv != v or m not in ms:
                        continue
                    for lado, q, gana in (("Up", pu, g == 1), ("Down", 1 - pu, g == 0)):
                        if lo <= q < hi:
                            n += 1; w += gana
                            for c in COSTOS:
                                neto, puesto = op(lado, q, g, tasa, c); res[c][0] += neto; res[c][1] += puesto
                                if c == .01:
                                    bl[(a, dia)] += neto; act[a] += neto; mit[dia >= corte] += neto
                if n < 20:
                    continue
                roi = {c: 100 * res[c][0] / res[c][1] for c in COSTOS}
                p(f"| {NOMBRE_V[v]} | {'+'.join(str(int(m * 100)) for m in ms)} % | {int(lo * 100)}–{int(hi * 100)} | {n} | {100 * w / n:.1f} | {roi[0]:+.1f} % | {roi[.01]:+.1f} % | {roi[.02]:+.1f} % | {boot(bl):.3f} | {mit[False]:+.0f} / {mit[True]:+.0f} | {act.get('BTC', 0):+.0f} / {act.get('ETH', 0):+.0f} |")
    with open(os.path.join(CARPETA, "resultados.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    with open(os.path.join(CARPETA, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()

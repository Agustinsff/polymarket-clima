"""Desarma la prueba cripto en papel (regla en REGLA.md). Uso: python cripto_analisis/analizar.py"""
import csv, json, os, random, re, statistics as st
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
est = json.load(open(os.path.join(RAIZ, "cripto_estado.json")))
gan = est["ganadoras"]
ops = list(csv.DictReader(open(os.path.join(RAIZ, "cripto_ops.csv"), encoding="utf-8"), delimiter=";"))
MES = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}


def dia(ev):
    m = re.search(r"on-([a-z]+)-(\d+)-(\d{4})", ev)
    return f"{m.group(3)}-{MES[m.group(1)]:02d}-{int(m.group(2)):02d}"


def resultado(o, modo):
    y = gan[o["condition_id"]]
    p, q = float(o["precio"]), float(o["acciones"])
    if modo == "c":
        p = min(p + 0.01, 0.999)
    gana = (y == 1) == (o["lado"] == "Yes")
    tasa = float(o["tasa_comision"] or 0.05) if modo == "a" else 0.07
    return q * ((1 - p) if gana else -p) - q * tasa * p * (1 - p), gana


def tramo_precio(p):
    return "<10c" if p < .10 else "10-30c" if p < .30 else "30-70c" if p < .70 else "70-90c" if p < .90 else ">90c"


def tramo_borde(o):
    p, m = float(o["precio"]), float(o["p_modelo"])
    b = (m - p) if o["lado"] == "Yes" else ((1 - m) - p)
    return "5-10" if b < .10 else "10-20" if b < .20 else ">20"


def bloques_boot(filas, n=10000, semilla=1):
    bl = defaultdict(float)
    for o, r in filas:
        bl[(o["activo"], dia(o["evento"]))] += r
    v = list(bl.values())
    rnd = random.Random(semilla)
    tot = [sum(rnd.choice(v) for _ in v) for _ in range(n)]
    p0 = sum(t <= 0 for t in tot) / n
    t = st.mean(v) / (st.stdev(v) / len(v) ** .5) if len(v) > 1 and st.stdev(v) > 0 else float("nan")
    return bl, p0, t


def informe(nombre, sub, salida):
    salida.append(f"\n## {nombre}\n")
    for modo, txt in [("a", "comisión anotada"), ("b", "comisión real 0,07·p·(1−p)"), ("c", "real + 1 ¢ de deslizamiento")]:
        f = [(o, resultado(o, modo)[0]) for o in sub]
        inv = sum(float(o["precio"]) * float(o["acciones"]) for o in sub)
        bl, p0, t = bloques_boot(f)
        salida.append(f"- {txt}: {len(f)} ops, neto US$ {sum(r for _, r in f):+.2f} sobre US$ {inv:.2f} "
                      f"({100 * sum(r for _, r in f) / inv:+.1f} %), {len(bl)} bloques (activo×día), "
                      f"P(total≤0) bootstrap {p0:.2f}, t por bloques {t:.2f}")
    f = [(o, *resultado(o, "b")) for o in sub]
    for corte, clave in [("activo", lambda o: o["activo"]), ("tipo", lambda o: o["tipo"]),
                         ("activo y tipo", lambda o: o["activo"] + " " + o["tipo"]),
                         ("horizonte (h)", lambda o: int(o["horizonte"])), ("lado", lambda o: o["lado"]),
                         ("precio pagado", lambda o: tramo_precio(float(o["precio"]))),
                         ("borde del modelo (puntos)", tramo_borde),
                         ("día de cierre", lambda o: dia(o["evento"])),
                         ("activo y día", lambda o: o["activo"] + " " + dia(o["evento"])),
                         ("hora UTC de entrada", lambda o: f"{int(o['momento_utc'][11:13]) // 6 * 6:02d}-{int(o['momento_utc'][11:13]) // 6 * 6 + 5:02d}")]:
        g = defaultdict(list)
        for o, r, ok in f:
            g[clave(o)].append((r, ok, float(o["precio"])))
        salida.append(f"\n**Por {corte}** (comisión real)\n\n| | ops | ganadas | precio medio | neto US$ |\n|---|---|---|---|---|")
        for k in sorted(g):
            xs = g[k]
            salida.append(f"| {k} | {len(xs)} | {sum(x[1] for x in xs)} | {st.mean(x[2] for x in xs):.2f} | {sum(x[0] for x in xs):+.2f} |")
    # concentración: top ops
    top = sorted(f, key=lambda x: -x[1])[:5]
    salida.append("\n**Las 5 ops que más ganaron**\n")
    for o, r, ok in top:
        salida.append(f"- {o['activo']} {o['tipo']} {o['strike']} {o['lado']} a {float(o['precio']):.3f} "
                      f"(modelo {float(o['p_modelo']):.2f}) h{o['horizonte']} {dia(o['evento'])}: {r:+.2f}")
    sin = sum(r for _, r, _ in f) - sum(r for _, r, _ in top)
    salida.append(f"\nSin esas 5: neto {sin:+.2f}")


liq = [o for o in ops if o["condition_id"] in gan]
nuevo = [o for o in liq if o["momento_utc"] >= est["desde_libro"]]
viejo = [o for o in liq if o["momento_utc"] < est["desde_libro"]]
pend = [o for o in ops if o["condition_id"] not in gan]
out = [f"# Prueba cripto desarmada ({len(liq)} ops liquidadas, {len(pend)} abiertas; datos hasta "
       f"{max(o['momento_utc'] for o in ops)} UTC)"]
informe("Con precio del libro real (desde " + est["desde_libro"] + ")", nuevo, out)
informe("Antes, con 1er escalón (referencia)", viejo, out)
informe("Todo junto", liq, out)
texto = "\n".join(out) + "\n"
open(os.path.join(RAIZ, "cripto_analisis", "resultados.md"), "w", encoding="utf-8").write(texto)
print(texto)

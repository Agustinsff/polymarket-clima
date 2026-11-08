"""
PRONOSTICO PROPIO - PASO 3: VALIDACION CONTRA EL MERCADO (reglas fijas en propio/REGLAS.md).

  Prueba A (principal): maximas, foto de hoy.csv de las 9 h local del dia D, contra M1 con horizonte 1.
  Prueba B: maximas y minimas, ultima foto de pronostico.csv del dia anterior, contra M1 con horizonte 2.

Para cada evento (serie + fecha) con todas las cajas y puntos medios que suman 0,90-1,15:
  - Brier (suma sobre cajas) del modelo y del mercado (punto medio normalizado);
  - bootstrap por dias (10.000) de la diferencia;
  - compras como taker: 1 accion de cada caja con p_modelo - ask - comision >= 3 c, al ask de la foto,
    comision 0,05*p*(1-p) (la de temperatura desde el 1-nov-2026; pronostico.csv no anota la tasa).
Pasa si en A o en B: Brier del modelo >= 3 % menor, P(no mejor) < 2,5 % y ROI > 0.

Uso: python propio/validar.py --datos DIR   (DIR = copia de la rama propio-datos con predicciones.csv.gz)
Salida: propio/resultados_validacion.md y DIR/probs_cajas.csv.gz
"""

import argparse
import csv
import gzip
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
from estaciones import EXCLUIR, leer_caja, redondear  # noqa: E402
from modelo import prob_caja  # noqa: E402

DESDE = "2026-10-22"
METODO = "M1"          # elegido en el paso 2 (resultados_modelo.md, 8-nov-2026)
BORDE = 0.03
TASA = 0.05
MIN_DIAS, MIN_EVENTOS = 15, 300
BOOT = 10000


def leer_pred(datos):
    out = {}
    with gzip.open(os.path.join(datos, "predicciones.csv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["m1_mu"]:
                out[(r["icao"], r["serie"], int(r["h"]), r["fecha"])] = (float(r["m1_mu"]), float(r["m1_sd"]),
                                                                         float(r["real"]))
    return out


def fotos_A():
    """{(serie, fecha, momento): [filas]} de hoy.csv a las 9 h local, solo maximas."""
    g = defaultdict(list)
    with open(os.path.join(RAIZ, "hoy.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["hora_local"].strip() == "9" and r["serie"].startswith("highest|") and r["fecha"] >= DESDE:
                g[(r["serie"], r["fecha"], r["momento_utc"])].append(r)
    return elegir_una(g, ultima=False)


def fotos_B():
    g = defaultdict(list)
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            try:
                hh = float(r["horas_hasta"])
            except ValueError:
                continue
            if hh > 0 and r["fecha"] >= DESDE:
                g[(r["serie"], r["fecha"], r["momento_utc"])].append(r)
    return elegir_una(g, ultima=True)


def fotos_temprano():
    g = defaultdict(list)
    with open(os.path.join(RAIZ, "pronostico.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            try:
                hh = float(r["horas_hasta"])
            except ValueError:
                continue
            if hh > 0 and r["fecha"] >= DESDE:
                g[(r["serie"], r["fecha"], r["momento_utc"])].append(r)
    return elegir_una(g, ultima=False)


def fotos_12():
    g = defaultdict(list)
    with open(os.path.join(RAIZ, "hoy.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["hora_local"].strip() == "12" and r["serie"].startswith("highest|") and r["fecha"] >= DESDE:
                g[(r["serie"], r["fecha"], r["momento_utc"])].append(r)
    return elegir_una(g, ultima=False)


def elegir_una(g, ultima):
    """Una foto por evento: la ultima (B) o la primera (A, por si hubo dos a las 9 h)."""
    por_evento = defaultdict(list)
    for (serie, fecha, momento), filas in g.items():
        por_evento[(serie, fecha)].append((momento, filas))
    out = {}
    for k, v in por_evento.items():
        v.sort()
        out[k] = v[-1] if ultima else v[0]
    return out


def evaluar(fotos, h, pred, nombre, salida_probs):
    eventos = []
    descartes = defaultdict(int)
    for (serie, fecha), (momento, filas) in sorted(fotos.items()):
        icao = filas[0]["icao"]
        tipo = "max" if serie.startswith("highest") else "min"
        if icao in EXCLUIR:
            descartes["estacion excluida"] += 1
            continue
        p = pred.get((icao, tipo, h, fecha))
        if not p:
            descartes["sin pronostico propio o sin dato real"] += 1
            continue
        mu, sd, real = p
        cajas = []
        for r in filas:
            try:
                lo, hi, en_f = leer_caja(r["caja"])
                bid, ask = float(r["bid"] or 0), float(r["ask"] or 0)
            except (ValueError, TypeError):
                cajas = None
                break
            cajas.append((r, lo, hi, en_f, bid, ask))
        if not cajas or not any(c[1] is None for c in cajas) or not any(c[2] is None for c in cajas):
            descartes["faltan cajas"] += 1
            continue
        medios = [(b + a) / 2 if a > 0 else b for (_, _, _, _, b, a) in cajas]
        s = sum(medios)
        if not 0.90 <= s <= 1.15:
            descartes["libro incompleto (medios no suman ~1)"] += 1
            continue
        en_f = cajas[0][3]
        v = redondear(real, en_f)
        pm = [prob_caja(mu, sd, lo, hi, ef, False) for (_, lo, hi, ef, _, _) in cajas]
        sp = sum(pm) or 1
        pm = [x / sp for x in pm]
        gana = [1 if (lo is None or v >= lo) and (hi is None or v <= hi) else 0 for (_, lo, hi, _, _, _) in cajas]
        if sum(gana) != 1:
            descartes["no se pudo ubicar la caja ganadora"] += 1
            continue
        pk = [m / s for m in medios]
        bs_mod = sum((a - o) ** 2 for a, o in zip(pm, gana))
        bs_mer = sum((a - o) ** 2 for a, o in zip(pk, gana))
        compras = []
        for (r, lo, hi, ef, bid, ask), pmod, o in zip(cajas, pm, gana):
            com = TASA * ask * (1 - ask)
            if 0 < ask < 1 and pmod - ask - com >= BORDE:
                compras.append((ask + com, o))
            salida_probs.append([momento, serie, fecha, icao, h, r["caja"], r["condition_id"], round(pmod, 4),
                                 bid, ask, METODO, nombre])
        eventos.append({"dia": fecha, "serie": serie, "bs_mod": bs_mod, "bs_mer": bs_mer, "compras": compras})
    return eventos, descartes


def resumen(eventos, descartes, nombre, titulo):
    dias = sorted({e["dia"] for e in eventos})
    L = [f"## {titulo}", ""]
    if not eventos:
        return L + ["Sin eventos.", ""], False
    bm = sum(e["bs_mod"] for e in eventos) / len(eventos)
    bk = sum(e["bs_mer"] for e in eventos) / len(eventos)
    mejora = 1 - bm / bk
    por_dia = defaultdict(list)
    for e in eventos:
        por_dia[e["dia"]].append(e["bs_mod"] - e["bs_mer"])
    rnd = random.Random(1)
    lista = list(por_dia.values())
    no_mejor = 0
    for _ in range(BOOT):
        m = [rnd.choice(lista) for _ in lista]
        tot = sum(sum(x) for x in m) / sum(len(x) for x in m)
        no_mejor += tot >= 0
    p_no = no_mejor / BOOT
    comp = [c for e in eventos for c in e["compras"]]
    costo = sum(c for c, _ in comp)
    gan = sum(o - c for c, o in comp)
    roi = gan / costo if costo else 0.0
    suficiente = len(dias) >= MIN_DIAS and len(eventos) >= MIN_EVENTOS
    pasa = suficiente and mejora >= 0.03 and p_no < 0.025 and roi > 0
    L += [f"Días: {len(dias)} ({dias[0]} a {dias[-1]}); eventos: {len(eventos)}.", "",
          "| Medida | Modelo | Mercado |", "|---|---|---|",
          f"| Brier medio (menor es mejor) | {bm:.4f} | {bk:.4f} |", "",
          f"- Mejora del modelo sobre el mercado: **{100 * mejora:+.1f} %** (regla: ≥ +3 %).",
          f"- Probabilidad de que el modelo no sea mejor (bootstrap por días): **{100 * p_no:.1f} %** (regla: < 2,5 %).",
          f"- Compras como taker (borde ≥ 3 ¢, ask real, comisión 0,05·p·(1−p)): {len(comp)} compras, "
          f"ganan {sum(o for _, o in comp)}, costo US$ {costo:.2f}, resultado US$ {gan:+.2f}, "
          f"**ROI {100 * roi:+.1f} %** (regla: > 0).", ""]
    for serie in ("highest", "lowest"):
        sub = [e for e in eventos if e["serie"].startswith(serie)]
        if sub and len(sub) != len(eventos):
            b1 = sum(e["bs_mod"] for e in sub) / len(sub)
            b2 = sum(e["bs_mer"] for e in sub) / len(sub)
            L.append(f"- Solo {'máximas' if serie == 'highest' else 'mínimas'}: {len(sub)} eventos, "
                     f"modelo {b1:.4f} vs mercado {b2:.4f} ({100 * (1 - b1 / b2):+.1f} %).")
    if descartes:
        L.append("- Eventos descartados: " + ", ".join(f"{k} {v}" for k, v in sorted(descartes.items())) + ".")
    if not suficiente:
        L.append(f"- **No alcanza el mínimo** ({MIN_DIAS} días y {MIN_EVENTOS} eventos): no se decide con esta prueba.")
    L += ["", f"**Prueba {nombre}: {'PASA' if pasa else 'NO PASA'}.**", ""]
    return L, pasa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", required=True)
    a = ap.parse_args()
    pred = leer_pred(a.datos)
    probs = []
    ea, da = evaluar(fotos_A(), 1, pred, "A", probs)
    eb, db = evaluar(fotos_B(), 2, pred, "B", probs)
    la, pa = resumen(ea, da, "A", "Prueba A: máximas, mismo día a las 9 h local (horizonte 1)")
    lb, pb = resumen(eb, db, "B", "Prueba B: máximas y mínimas, día anterior (horizonte 2)")
    L = ["# Pronóstico propio: validación contra el mercado (paso 3)", "",
         f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con las reglas de REGLAS.md (fijadas el 3-nov-2026) "
         f"y el método {METODO} (elegido en resultados_modelo.md). Precio del mercado = punto medio "
         "normalizado de la foto; real = METAR de rutina con el redondeo de Polymarket.", ""] + la + lb
    veredicto = pa or pb
    if not ea:
        L += ["La prueba A no se pudo hacer: `hoy.csv` guarda las máximas a las 12 y 15 h local y las mínimas a "
              "las 9 h, no hay foto de máximas a las 9 h. Fue un error al escribir REGLAS.md.", ""]
    # Informativo (no decide): variantes que nos favorecen, para ver cuan lejos queda el modelo
    L += ["## Informativo (no decide)", "",
          "Variantes más generosas con el modelo, para medir la distancia:", ""]
    for titulo, fotos, h in (("B con horizonte 1 (puede usar corridas que a esa hora quizás no existían)", fotos_B(), 1),
                             ("B con la primera foto del día anterior, horizonte 2", fotos_temprano(), 2),
                             ("Máximas a las 12 h local del mismo día, horizonte 1", fotos_12(), 1)):
        ev, _ = evaluar(fotos, h, pred, "info", [])
        if ev:
            bm = sum(e["bs_mod"] for e in ev) / len(ev)
            bk = sum(e["bs_mer"] for e in ev) / len(ev)
            L.append(f"- {titulo}: {len(ev)} eventos, modelo {bm:.4f} vs mercado {bk:.4f} ({100 * (1 - bm / bk):+.1f} %).")
    L.append("")
    L += ["## Veredicto", "",
          ("**PASA**: sigue el paso 4 (papel 2–3 semanas con avisos ntfy)." if veredicto else
           "**NO PASA**: según la regla, se cierra acá sin prueba en papel."), ""]
    open(os.path.join(AQUI, "resultados_validacion.md"), "w", encoding="utf-8").write("\n".join(L))
    with gzip.open(os.path.join(a.datos, "probs_cajas.csv.gz"), "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["momento_utc", "serie", "fecha", "icao", "h", "caja", "condition_id", "p_modelo", "bid", "ask",
                    "metodo", "prueba"])
        w.writerows(probs)
    print("\n".join(L))


if __name__ == "__main__":
    main()

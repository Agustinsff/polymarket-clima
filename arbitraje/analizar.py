"""
Resume las fotos de arbitraje/medir.py segun arbitraje/REGLA.md.

Uso:
  python arbitraje/analizar.py [archivos .csv.gz ...]   (por defecto todos los de arbitraje/datos/)
  -> escribe arbitraje/informe_datos.md y arbitraje/resumen.json
"""

import csv
import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from statistics import median

CARPETA = os.path.dirname(os.path.abspath(__file__))
UMBRALES = [10, 60, 900]      # segundos: servidor rapido, 1 min, cron de 15 min


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))]


def leer(archivos):
    filas = []
    for a in archivos:
        with gzip.open(a, "rt") as f:
            for r in csv.DictReader(f):
                r["ts"] = float(r["ts"])
                filas.append(r)
    filas.sort(key=lambda r: r["ts"])
    return filas


def es_op(r, lado):
    g, q, mn = num(r[f"ganancia_{lado}"]), num(r[f"juegos_{lado}"]), num(r["min_orden"])
    return g is not None and q is not None and q >= mn and g >= 0.01


def main():
    archivos = sys.argv[1:] or sorted(glob.glob(os.path.join(CARPETA, "datos", "fotos_*.csv.gz")))
    filas = leer(archivos)
    if not filas:
        print("sin datos")
        return
    fotos_ts = sorted({r["ts"] for r in filas})
    pasos = [b - a for a, b in zip(fotos_ts, fotos_ts[1:]) if b - a < 120]
    paso = median(pasos) if pasos else 10
    horas = sum(pasos) / 3600 if pasos else 0

    por_ev = defaultdict(list)
    for r in filas:
        por_ev[(r["grupo"], r["aumentado"], r["slug"])].append(r)

    res = {"archivos": [os.path.basename(a) for a in archivos], "desde": fotos_ts[0], "hasta": fotos_ts[-1],
           "fotos": len(fotos_ts), "paso_mediano_s": paso, "horas": horas, "grupos": {}}
    episodios = []
    for (grupo, aum, slug), rs in por_ev.items():
        for lado in ("si", "no"):
            ep = None
            for r in rs:
                if es_op(r, lado):
                    if ep is None:
                        ep = {"grupo": grupo, "aum": aum, "slug": slug, "lado": lado, "inicio": r["ts"],
                              "gan_inicio": num(r[f"ganancia_{lado}"]), "gan_max": 0, "borde_c": num(r[f"borde_{lado}_c"]),
                              "juegos": num(r[f"juegos_{lado}"]), "fotos": 0, "n": int(r["n"])}
                    ep["fotos"] += 1
                    ep["gan_max"] = max(ep["gan_max"], num(r[f"ganancia_{lado}"]))
                    ep["ultimo"] = r["ts"]
                elif ep is not None:
                    ep["dur"], ep["cortado"] = r["ts"] - ep["inicio"], False
                    episodios.append(ep)
                    ep = None
            if ep is not None:       # el evento desaparecio o termino la medicion con la oportunidad abierta
                ep["dur"], ep["cortado"] = ep["ultimo"] - ep["inicio"] + paso, True
                episodios.append(ep)

    claves = sorted({(r["grupo"], r["aumentado"]) for r in filas})
    for grupo, aum in claves:
        nombre = grupo + (" (aumentado)" if aum == "1" else "")
        rs = [r for r in filas if r["grupo"] == grupo and r["aumentado"] == aum]
        g = {"eventos": len({r["slug"] for r in rs}), "filas": len(rs)}
        for lado in ("si", "no"):
            ops = [r for r in rs if es_op(r, lado)]
            bordes = [num(r[f"borde_{lado}_c"]) for r in rs if num(r[f"borde_{lado}_c"]) is not None]
            eps = [e for e in episodios if e["grupo"] == grupo and e["aum"] == aum and e["lado"] == lado]
            gan_tot = sum(e["gan_inicio"] for e in eps)
            # cuanto hay "sobre la mesa" en un momento cualquiera: suma por foto de las ganancias disponibles
            por_foto = defaultdict(float)
            for r in ops:
                por_foto[r["ts"]] += num(r[f"ganancia_{lado}"])
            g[lado] = {
                "filas_con_borde": len(bordes),
                "pct_filas_op": 100 * len(ops) / len(bordes) if bordes else None,
                "pct_fotos_con_alguna": 100 * len(por_foto) / len(fotos_ts),
                "borde_mediano_c": median(bordes) if bordes else None,
                "borde_p99_c": pct(bordes, 0.99), "borde_max_c": max(bordes) if bordes else None,
                "episodios": len(eps), "episodios_por_hora": len(eps) / horas if horas else None,
                "gan_inicio_mediana": median([e["gan_inicio"] for e in eps]) if eps else None,
                "gan_inicio_max": max([e["gan_inicio"] for e in eps]) if eps else None,
                "gan_total_inicio": gan_tot,
                "gan_por_hora_reaccion_inmediata": gan_tot / horas if horas else None,
                "dur_mediana_s": median([e["dur"] for e in eps]) if eps else None,
                "dur_p90_s": pct([e["dur"] for e in eps], 0.9),
                "una_sola_foto": sum(e["fotos"] == 1 for e in eps),
                "frac_gan_dura_mas": {u: (sum(e["gan_inicio"] for e in eps if e["dur"] > u) / gan_tot if gan_tot else None)
                                      for u in UMBRALES},
                "mesa_media_por_foto": sum(por_foto.values()) / len(fotos_ts),
            }
        res["grupos"][nombre] = g
    res["top_episodios"] = sorted(episodios, key=lambda e: -e["gan_inicio"])[:25]
    with open(os.path.join(CARPETA, "resumen.json"), "w") as f:
        json.dump(res, f, indent=1, default=str)

    L = [f"# Arbitraje: resumen de datos", "",
         f"{len(fotos_ts)} fotos, {horas:.1f} h medidas, paso mediano {paso:.1f} s. Archivos: {', '.join(res['archivos'])}", ""]
    for nombre, g in res["grupos"].items():
        L += [f"## {nombre}: {g['eventos']} eventos", ""]
        for lado, txt in (("si", "comprar todos los Sí"), ("no", "comprar todos los No")):
            x = g[lado]
            if not x["filas_con_borde"]:
                continue
            L.append(f"- **{txt}**: borde mediano {x['borde_mediano_c']:.2f} ¢ (p99 {x['borde_p99_c']:.2f}, máx "
                     f"{x['borde_max_c']:.2f}); oportunidad en {x['pct_filas_op']:.3f} % de las filas; "
                     f"{x['episodios']} episodios ({(x['episodios_por_hora'] or 0):.2f}/h); "
                     f"ganancia total al inicio US$ {x['gan_total_inicio']:.2f} "
                     f"(US$ {(x['gan_por_hora_reaccion_inmediata'] or 0):.2f}/h)")
            if x["episodios"]:
                fr = x["frac_gan_dura_mas"]
                L.append(f"  - duración mediana {x['dur_mediana_s']:.0f} s, p90 {x['dur_p90_s']:.0f} s, "
                         f"{x['una_sola_foto']} de una sola foto; de la ganancia dura >10 s {100 * (fr[10] or 0):.0f} %, "
                         f">1 min {100 * (fr[60] or 0):.0f} %, >15 min {100 * (fr[900] or 0):.0f} %; "
                         f"en una foto cualquiera hay US$ {x['mesa_media_por_foto']:.3f} sobre la mesa")
        L.append("")
    L += ["## Episodios más grandes", "", "| grupo | evento | jugada | ¢/juego | juegos | US$ al inicio | dura (s) |",
          "|---|---|---|---|---|---|---|"]
    for e in res["top_episodios"][:15]:
        L.append(f"| {e['grupo']} | {e['slug']} | {e['lado']} | {e['borde_c']:.2f} | {e['juegos']:.0f} | "
                 f"{e['gan_inicio']:.2f} | {e['dur']:.0f}{'+' if e['cortado'] else ''} |")
    with open(os.path.join(CARPETA, "informe_datos.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

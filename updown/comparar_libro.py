"""MEDICION (27-oct, pedida por Agus): el precio historico que usamos (prices-history, minuto 54) vs el libro real.
En vivo, en el minuto 53-54 solo ~5 % de las horas tiene el favorito a 70-90 c (historia: ~19 %). Dos explicaciones:
  a) dias tranquilos: el metodo historico tambien daria pocas horas a 70-90 en estas mismas horas;
  b) el precio historico no es el que se puede comprar: en las mismas horas daria 70-90 y el libro no.
No toca ninguna regla ni prueba. Solo lee (raw de GitHub, gamma, clob prices-history).

1) Mismas horas: por cada foto en vivo de favorito/fotos.csv (main) baja prices-history del Up y compara.
2) Por dia: % de horas con favorito a 70-90 / >=90 en el minuto 54 con el metodo historico, desde updown/datos
   y bajando lo que falte hasta hoy (asi se ve si estos dias son raros).
Salida: updown/comparar_libro.md
"""
import csv, gzip, glob, io, json, os, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests

CARPETA = os.path.dirname(os.path.abspath(__file__))
FOTOS = "https://raw.githubusercontent.com/Agustinsff/polymarket-clima/main/favorito/fotos.csv"
G, HIST = "https://gamma-api.polymarket.com/events", "https://clob.polymarket.com/prices-history"
SERIES = {"btc-up-or-down-hourly": "BTC", "eth-up-or-down-hourly": "ETH"}
DESDE_NUEVOS = datetime(2026, 10, 20, tzinfo=timezone.utc)
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-updown/0.1 (investigacion personal)"
out = []


def p(*a):
    out.append(" ".join(str(x) for x in a))


def get(url, params):
    for i in range(4):
        try:
            r = S.get(url, params=params, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(8 * (i + 1)); continue
            return None
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def precio_en(h, t, ventana=3600):
    """Igual que analizar.py: ultimo punto de los 6 min previos a t."""
    xs = [pp for ts, pp in h if t - ventana / 10 <= ts <= t]
    return xs[-1] if xs else None


def tramo(q):
    if q is None:
        return "sin dato"
    return "<70" if q < .70 else "70-90" if q < .90 else ">=90"


def ts(txt):
    return int(datetime.strptime(txt, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def info_evento(e):
    m = (e.get("markets") or [None])[0]
    if not m:
        return None
    toks = json.loads(m["clobTokenIds"]); outs = json.loads(m.get("outcomes") or '["Up","Down"]')
    pr = json.loads(m.get("outcomePrices") or "[]")
    i_up = outs.index("Up") if "Up" in outs else 0
    fin = int(datetime.fromisoformat(e["endDate"].replace("Z", "+00:00")).timestamp())
    gano = None
    if len(pr) == 2:
        pu = float(pr[i_up]); gano = 1 if pu >= .99 else 0 if pu <= .01 else None
    return {"tok_up": toks[i_up], "fin": fin, "ini": fin - 3600, "gano_up": gano}


def historia(tok, fin):
    j = get(HIST, {"market": tok, "startTs": fin - 3600 - 360, "endTs": fin + 120, "fidelity": 1})
    return [[x["t"], x["p"]] for x in (j or {}).get("history", [])]


# ---------------- 1) mismas horas ----------------
def mismas_horas():
    txt = S.get(FOTOS, timeout=40).text
    filas = list(csv.DictReader(io.StringIO(txt), delimiter=";"))
    fotos = defaultdict(dict)                 # (momento, cid) -> {lado: fila}
    for r in filas:
        fotos[(r["momento_utc"], r["condition_id"])][r["lado"]] = r
    slugs = {r["evento"] for r in filas}

    def uno(slug):
        j = get(G, {"slug": slug})
        if not j:
            return slug, None
        inf = info_evento(j[0])
        if inf:
            inf["h"] = historia(inf["tok_up"], inf["fin"])
        return slug, inf
    with ThreadPoolExecutor(6) as ex:
        evs = dict(ex.map(uno, sorted(slugs)))

    det, matriz, difs = [], Counter(), []
    for (mom, cid), lados in sorted(fotos.items()):
        up, dn = lados.get("Up"), lados.get("Down")
        if not up or not dn:
            continue
        inf = evs.get(up["evento"])
        if not inf or not inf["h"]:
            continue
        t = ts(mom)
        pu_foto = precio_en(inf["h"], t)
        pu_54 = precio_en(inf["h"], inf["ini"] + int(.9 * 3600))
        # en vivo: costo de 10 acciones de cada lado (p10); el favorito es el lado mas caro
        c_up, c_dn = fnum(up["p10"]), fnum(dn["p10"])
        b_up, b_dn = fnum(up["bid"]), fnum(dn["bid"])
        a_up = fnum(up["ask"])
        mid_up = (b_up + a_up) / 2 if b_up is not None and a_up is not None else None
        fav_vivo = max([c for c in (c_up, c_dn) if c is not None], default=None)
        if fav_vivo is not None and fav_vivo < .5:       # el lado caro no tiene asks: decidido si el bid es alto
            fav_vivo = None
        if fav_vivo is None:
            mejor_bid = max([b for b in (b_up, b_dn) if b is not None], default=None)
            t_vivo = ">=90" if mejor_bid is not None and mejor_bid >= .90 else "sin dato"
        else:
            t_vivo = tramo(fav_vivo)
        fav_h = None if pu_foto is None else max(pu_foto, 1 - pu_foto)
        fav_54 = None if pu_54 is None else max(pu_54, 1 - pu_54)
        matriz[(tramo(fav_54), t_vivo)] += 1
        if pu_foto is not None and mid_up is not None:
            difs.append(pu_foto - mid_up)
        det.append((mom[:16], up["activo"], f"{pu_foto:.3f}" if pu_foto is not None else "–",
                    f"{pu_54:.3f}" if pu_54 is not None else "–", f"{mid_up:.3f}" if mid_up is not None else "–",
                    f"{fav_vivo:.3f}" if fav_vivo is not None else "–", tramo(fav_54), t_vivo))

    n = sum(matriz.values())
    p(f"## 1) Mismas horas: {n} fotos en vivo (favorito/fotos.csv) contra el precio histórico\n")
    tramos = ["<70", "70-90", ">=90", "sin dato"]
    p("Filas: tramo del favorito con el método histórico (prices-history, minuto 54). Columnas: libro real (costo de 10 acciones).\n")
    p("| histórico \\ libro | " + " | ".join(tramos) + " | total |\n|---|" + "---|" * (len(tramos) + 1))
    for a in tramos:
        tot = sum(matriz[(a, b)] for b in tramos)
        if tot:
            p(f"| {a} | " + " | ".join(str(matriz[(a, b)]) for b in tramos) + f" | {tot} |")
    p("| total | " + " | ".join(str(sum(matriz[(a, b)] for a in tramos)) for b in tramos) + f" | {n} |")
    h7090 = sum(matriz[("70-90", b)] for b in tramos); v7090 = sum(matriz[(a, "70-90")] for a in tramos)
    p(f"\n- Horas a 70–90 ¢: histórico {h7090}/{n} ({100 * h7090 / max(n, 1):.0f} %), libro real {v7090}/{n} ({100 * v7090 / max(n, 1):.0f} %).")
    if difs:
        difs.sort()
        p(f"- Precio histórico del Up en el momento de la foto menos el medio del libro: media {sum(difs) / len(difs):+.3f}, "
          f"mediana {difs[len(difs) // 2]:+.3f}, |dif| > 2 ¢ en {sum(abs(d) > .02 for d in difs)}/{len(difs)}.")
    p("\n<details><summary>Detalle por foto</summary>\n")
    p("| foto UTC | activo | Up hist. en la foto | Up hist. min 54 | Up medio libro | favorito libro (10 acc.) | tramo hist. | tramo libro |\n|---|---|---|---|---|---|---|---|")
    for d in det:
        p("| " + " | ".join(d) + " |")
    p("\n</details>\n")


# ---------------- 2) por dia ----------------
def por_dia():
    filas = {}                                # slug -> (activo, ini, pu_54, gano)
    for f in glob.glob(os.path.join(CARPETA, "datos", "*-hourly.json.gz")):
        for slug, v in json.load(gzip.open(f, "rt", encoding="utf-8")).items():
            filas[slug] = (v["activo"], v["ini"], precio_en(v["h"], v["ini"] + int(.9 * 3600)), v["gano_up"])
    nuevos = []
    for serie, activo in SERIES.items():
        off = 0
        while True:
            j = get(G, {"series_slug": serie, "closed": "true", "limit": 100, "offset": off, "order": "endDate", "ascending": "false"})
            if not j:
                break
            seguir = True
            for e in j:
                if datetime.fromisoformat(e["endDate"].replace("Z", "+00:00")) < DESDE_NUEVOS:
                    seguir = False; break
                if e["slug"] not in filas:
                    nuevos.append((activo, e))
            if not seguir or len(j) < 100:
                break
            off += 100

    def uno(par):
        activo, e = par
        inf = info_evento(e)
        if not inf:
            return None
        h = historia(inf["tok_up"], inf["fin"])
        return e["slug"], (activo, inf["ini"], precio_en(h, inf["ini"] + int(.9 * 3600)), inf["gano_up"])
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(uno, nuevos):
            if r:
                filas[r[0]] = r[1]

    dia = defaultdict(Counter)
    for activo, ini, pu, g in filas.values():
        if pu is None:
            continue
        d = datetime.fromtimestamp(ini, timezone.utc).strftime("%Y-%m-%d")
        dia[d][tramo(max(pu, 1 - pu))] += 1
    p(f"## 2) Por día, método histórico (minuto 54, BTC+ETH 1 h; {len(nuevos)} mercados bajados ahora desde el 20-oct)\n")
    p("| día UTC | horas | 70–90 ¢ | ≥ 90 ¢ | < 70 ¢ |\n|---|---|---|---|---|")
    tot = Counter()
    for d in sorted(dia):
        c = dia[d]; n = sum(c.values()); tot += c
        p(f"| {d} | {n} | {100 * c['70-90'] / n:.0f} % | {100 * c['>=90'] / n:.0f} % | {100 * c['<70'] / n:.0f} % |")
    n = sum(tot.values())
    p(f"| total | {n} | {100 * tot['70-90'] / n:.0f} % | {100 * tot['>=90'] / n:.0f} % | {100 * tot['<70'] / n:.0f} % |")


def main():
    p(f"# Precio histórico vs. libro real en el minuto 54 — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z\n")
    p("Medición, no regla. Ver el encabezado de comparar_libro.py.\n")
    mismas_horas()
    por_dia()
    with open(os.path.join(CARPETA, "comparar_libro.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()

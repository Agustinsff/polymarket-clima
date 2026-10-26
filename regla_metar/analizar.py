"""
Analisis de regla_metar/REGLA.md (sin red: lee lo que junto el recolector).

Uso:
  python regla_metar/analizar.py                      -> con datos/fotos.csv (corte parcial y final)
  python regla_metar/analizar.py --libros             -> primer corte con libros.csv (solo cajas 3-97 c)
  opcional: --iem RUTA  historia IEM vieja (metar_iem.csv.gz de la rama investigacion-velocidad) para la brecha
            de la regla antes del 23-oct
Escribe regla_metar/resultados.json e imprime el resumen.
"""

import csv
import gzip
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from estaciones import TZ, fee, leer_caja, redondear  # noqa: E402

AQUI = os.path.join(RAIZ, "regla_metar")
DATOS = os.path.join(AQUI, "datos")
DESDE, HASTA = date(2026, 10, 23), date(2026, 11, 6)
CONTROL = (date(2026, 8, 24), date(2026, 10, 20))
VENTANA = {"M0": (-1, (6, 7)), "M1": (0, (6, 7)), "M2": (0, (12, 13))}


def orden(caja):
    lo, hi, _ = leer_caja(caja)
    return (lo if lo is not None else -1e9, hi if hi is not None else 1e9)


def leer_csv(p, delim=";"):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delim))


def media_t(xs, grupos):
    """Media, error estandar agrupado por grupo (fecha) y t."""
    n = len(xs)
    if n < 2:
        return {"n": n, "media": xs[0] if xs else None, "ee": None, "t": None}
    m = sum(xs) / n
    g = defaultdict(float)
    for x, k in zip(xs, grupos):
        g[k] += x - m
    G = len(g)
    if G < 2:
        return {"n": n, "media": m, "ee": None, "t": None}
    ee = math.sqrt(sum(v * v for v in g.values()) * G / (G - 1)) / n
    return {"n": n, "fechas": G, "media": round(m, 4), "ee": round(ee, 4), "t": round(m / ee, 2) if ee else None}


def dif_t(a, b):
    if a["ee"] is None or b["ee"] is None:
        return None
    d = a["media"] - b["media"]
    ee = math.sqrt(a["ee"] ** 2 + b["ee"] ** 2)
    return {"dif": round(d, 4), "ee": round(ee, 4), "t": round(d / ee, 2)}


# ---------------------------------------------------------------- resultados y precios del periodo nuevo

def eventos_nuevos():
    """slug -> {serie, fecha, icao, cajas (ordenadas), w}"""
    evs = defaultdict(lambda: {"cajas": []})
    for r in leer_csv(os.path.join(DATOS, "resultados.csv")):
        if r["fuente"] != "aviationweather":
            continue
        e = evs[r["slug"]]
        e.update(serie=r["serie"], fecha=date.fromisoformat(r["fecha"]), icao=r["icao"])
        e["cajas"].append((r["caja"], int(r["gano"])))
    out = {}
    for s, e in evs.items():
        if not DESDE <= e["fecha"] <= HASTA:
            continue
        e["cajas"].sort(key=lambda x: orden(x[0]))
        ws = [i for i, (_, g) in enumerate(e["cajas"]) if g]
        if len(ws) == 1:
            e["w"] = ws[0]
            e["nombres"] = [c for c, _ in e["cajas"]]
            out[s] = e
    return out


def precios_fotos():
    """(slug, momento) -> {caja: (medio, costo_no_por_accion_con_comision, costo_si)}"""
    out = defaultdict(dict)
    for r in leer_csv(os.path.join(DATOS, "fotos.csv")):
        if r["medio"] == "":
            continue
        tasa = float(r["tasa_comision"] or 0)
        no = float(r["no_10"]) + fee(float(r["no_10"]), tasa) if r["no_10"] else None
        si = float(r["si_10"]) + fee(float(r["si_10"]), tasa) if r["si_10"] else None
        out[(r["slug"], r["momento"])][r["caja"]] = (float(r["medio"]), no, si)
    return out


def precios_libros():
    """Igual, desde libros.csv (foto por hora; solo cajas entre 3 y 97 c). Primera foto dentro de cada ventana."""
    out = {}
    primera = {}
    for r in leer_csv(os.path.join(RAIZ, "libros.csv")):
        if r["grupo"] != "clima":
            continue
        m = re.match(r"^(highest|lowest)-temperature-in-(.+)-on-([a-z]+)-(\d+)-(\d{4})$", r["evento"])
        if not m or m.group(2) not in TZ:
            continue
        fecha = datetime.strptime(f"{m.group(3)} {m.group(4)} {m.group(5)}", "%B %d %Y").date()
        t = datetime.strptime(r["momento_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        loc = t.astimezone(ZoneInfo(TZ[m.group(2)]))
        for mom, (dd, horas) in VENTANA.items():
            if loc.date() == fecha + timedelta(days=dd) and loc.hour in horas:
                k = (r["evento"], mom)
                if k not in primera:
                    primera[k] = r["momento_utc"]
                if primera[k] == r["momento_utc"]:
                    medio = float(r["medio"])
                    no = (1 - medio) + float(r["costo_no_10"]) / 100 if r["costo_no_10"] else None
                    si = medio + float(r["costo_yes_10"]) / 100 if r["costo_yes_10"] else None
                    out.setdefault(k, {})[r["caja"]] = (medio, no, si)
    return out


# ---------------------------------------------------------------- medidas

def sesgo(evs, precios, mom, tipo):
    xs, gs = [], []
    for s, e in evs.items():
        if not e["serie"].startswith(tipo):
            continue
        p = precios.get((s, mom))
        if not p:
            continue
        q = [p.get(c, (0.0,))[0] for c in e["nombres"]]
        tot = sum(q)
        if tot <= 0:
            continue
        xs.append(sum(qi * k for k, qi in enumerate(q)) / tot - e["w"])
        gs.append(e["fecha"])
    return media_t(xs, gs)


def sesgo_control(mom, tipo):
    f = os.path.join(RAIZ, "historico", "cache.json.gz")
    h = {"M1": "1", "M0": "2"}.get(mom)
    if not h or not os.path.exists(f):
        return None
    d = json.load(gzip.open(f))["eventos"]
    xs, gs = [], []
    for k, e in d.items():
        serie_tipo, _, fecha = k.split("|")
        fecha = date.fromisoformat(fecha)
        if serie_tipo != tipo or not CONTROL[0] <= fecha <= CONTROL[1]:
            continue
        if not e.get("cajas"):
            continue
        cs = sorted(e["cajas"], key=lambda c: orden(c["caja"]))
        ws = [i for i, c in enumerate(cs) if c["gano"]]
        q = [c["p"].get(h) for c in cs]
        if len(ws) != 1 or any(x is None for x in q):
            continue
        tot = sum(q)
        if not 0.90 <= tot <= 1.15:
            continue
        xs.append(sum(qi * i for i, qi in enumerate(q)) / tot - ws[0])
        gs.append(fecha)
    return media_t(xs, gs)


def plata(evs, precios, mom, tipo, lado):
    """Comprar 10 No de la vecina (lado +1 arriba, -1 abajo) de la caja mas cara."""
    xs, gs, ops = [], [], []
    for s, e in evs.items():
        if not e["serie"].startswith(tipo):
            continue
        p = precios.get((s, mom))
        if not p:
            continue
        medios = [p.get(c, (0.0,))[0] for c in e["nombres"]]
        fav = max(range(len(medios)), key=lambda i: medios[i])
        v = fav + lado
        if not 0 <= v < len(e["nombres"]) or e["nombres"][v] not in p:
            continue
        costo = p[e["nombres"][v]][1]
        if costo is None or not 0.03 <= costo <= 0.97:
            continue
        cobro = 0 if v == e["w"] else 1
        r = (cobro - costo) / costo
        xs.append(r)
        gs.append(e["fecha"])
        ops.append({"slug": s, "caja": e["nombres"][v], "costo": round(costo, 4), "cobro": cobro, "r": round(r, 4)})
    res = media_t(xs, gs)
    if xs:
        fechas = sorted(set(gs))
        mitad = fechas[len(fechas) // 2] if len(fechas) > 1 else fechas[0]
        a = [x for x, g in zip(xs, gs) if g < mitad]
        b = [x for x, g in zip(xs, gs) if g >= mitad]
        res["mitades"] = [round(sum(a) / len(a), 4) if a else None, round(sum(b) / len(b), 4) if b else None]
        res["costo_medio"] = round(sum(o["costo"] for o in ops) / len(ops), 4)
        res["acierto"] = round(sum(o["cobro"] for o in ops) / len(ops), 4)
    return res, ops


# ---------------------------------------------------------------- brecha de la regla (sin precios)

def temp_t(raw):
    g = re.search(r"\bT([01])(\d{3})[01]\d{3}\b", raw or "")
    if g:
        return (-1 if g.group(1) == "1" else 1) * int(g.group(2)) / 10
    g = re.search(r" (M?\d{2})/(M?\d{2})? ", raw or "")
    if g:
        v = g.group(1)
        return -int(v[1:]) if v.startswith("M") else int(v)
    return None


def reportes_nuevos():
    """icao -> [(datetime utc, temp, es_rutina)] del recolector (aviationweather, con metarType)."""
    out = defaultdict(list)
    f = os.path.join(DATOS, "metar.csv.gz")
    if not os.path.exists(f):
        return out
    with gzip.open(f, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            t = temp_t(r["raw"])
            if t is None:
                continue
            rut = r["tipo"] != "SPECI" and not r["raw"].startswith("SPECI")
            out[r["icao"]].append((datetime.fromtimestamp(int(r["obs_epoch"]), timezone.utc), t, rut))
    return out


def reportes_iem(ruta):
    """IEM no marca SPECI: rutina = minuto mas frecuente de la estacion."""
    crudo = defaultdict(list)
    with gzip.open(ruta, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            t = temp_t(" " + (r["raw"] or "") + " ")
            if t is None or not r["valid_utc"]:
                continue
            crudo[r["icao"]].append((datetime.strptime(r["valid_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc), t))
    out = {}
    for icao, xs in crudo.items():
        moda = Counter(d.minute for d, _ in xs).most_common(2)
        mins = {moda[0][0]}
        if len(moda) > 1 and moda[1][1] > 0.6 * moda[0][1]:      # estaciones con METAR cada media hora
            mins.add(moda[1][0])
        out[icao] = [(d, t, d.minute in mins) for d, t in xs]
    return out


def caja_de(valor, nombres):
    for i, c in enumerate(nombres):
        lo, hi, _ = leer_caja(c)
        if (lo is None or valor >= lo) and (hi is None or valor <= hi):
            return i
    return None


def brecha(evs, reps):
    """Por evento: caja con todos los reportes vs con solo rutina, y rutina vs ganadora."""
    c = Counter()
    for e in evs:
        xs = reps.get(e["icao"])
        if not xs:
            continue
        ciudad = e["serie"].split("|")[1]
        tz = ZoneInfo(TZ[ciudad])
        dia = [(t, rut) for d, t, rut in xs if d.astimezone(tz).date() == e["fecha"]]
        if len(dia) < 12:
            continue
        en_f = "°F" in e["nombres"][0]
        f = max if e["serie"].startswith("highest") else min
        b_rut = caja_de(redondear(f(t for t, r in dia if r), en_f), e["nombres"]) if any(r for _, r in dia) else None
        b_tod = caja_de(redondear(f(t for t, _ in dia), en_f), e["nombres"])
        if b_rut is None or b_tod is None:
            continue
        c["n"] += 1
        signo = 1 if e["serie"].startswith("highest") else -1
        d = (b_tod - b_rut) * signo
        c["difiere"] += d != 0
        c["todos_mas_extremo"] += d > 0
        if e.get("w") is not None:
            c["con_ganadora"] += 1
            c["rutina_=_ganadora"] += b_rut == e["w"]
            c["todos_=_ganadora"] += b_tod == e["w"]
    return dict(c)


def eventos_control(evs_nuevos):
    """Eventos del control con su estacion (la misma que en el periodo nuevo para esa serie)."""
    d = json.load(gzip.open(os.path.join(RAIZ, "historico", "cache.json.gz")))["eventos"]
    est = {e["serie"]: e["icao"] for e in evs_nuevos.values()}
    out = []
    for k, e in d.items():
        tipo, ciudad, fecha = k.split("|")
        serie, fecha = f"{tipo}|{ciudad}", date.fromisoformat(fecha)
        if serie not in est or not CONTROL[0] <= fecha <= CONTROL[1]:
            continue
        if not e.get("cajas"):
            continue
        cs = sorted(e["cajas"], key=lambda c: orden(c["caja"]))
        ws = [i for i, c in enumerate(cs) if c["gano"]]
        out.append({"serie": serie, "fecha": fecha, "icao": est[serie],
                    "nombres": [c["caja"] for c in cs], "w": ws[0] if len(ws) == 1 else None})
    return out


# ----------------------------------------------------------------

def main():
    usar_libros = "--libros" in sys.argv
    evs = eventos_nuevos()
    precios = precios_libros() if usar_libros else precios_fotos()
    res = {"fuente_precios": "libros.csv (primer corte, solo cajas 3-97 c)" if usar_libros else "fotos.csv",
           "eventos_con_ganadora": len(evs),
           "fechas": [min(e["fecha"] for e in evs.values()).isoformat(),
                      max(e["fecha"] for e in evs.values()).isoformat()] if evs else None,
           "sesgo": {}, "plata": {}, "brecha": {}}
    for tipo in ("highest", "lowest"):
        for mom in ("M0", "M1", "M2"):
            nuevo = sesgo(evs, precios, mom, tipo)
            ctl = sesgo_control(mom, tipo)
            res["sesgo"][f"{tipo} {mom}"] = {"nuevo": nuevo, "control": ctl, "dif": dif_t(nuevo, ctl) if ctl else None}
            for nombre, lado in (("vecina_arriba", 1), ("vecina_abajo", -1)):
                r, _ = plata(evs, precios, mom, tipo, lado)
                res["plata"][f"{tipo} {mom} {nombre}"] = r
    res["brecha"]["nuevo"] = brecha(list(evs.values()), reportes_nuevos())
    if "--iem" in sys.argv:
        ruta = sys.argv[sys.argv.index("--iem") + 1]
        res["brecha"]["control_iem"] = brecha(eventos_control(evs), reportes_iem(ruta))

    # criterio de exito (REGLA.md)
    s = res["sesgo"]["highest M1"]
    p = res["plata"]["highest M1 vecina_arriba"]
    q = res["plata"]["highest M1 vecina_abajo"]
    c1 = bool(s["nuevo"].get("t") and s["nuevo"]["media"] > 0 and s["nuevo"]["t"] >= 2
              and s["dif"] and s["dif"]["dif"] > 0 and s["dif"]["t"] >= 2)
    c2 = bool(p.get("t") and p["media"] >= 0.02 and p["t"] >= 2 and p["n"] >= 150
              and all(x is not None and x > 0 for x in p.get("mitades", [None]))
              and q.get("media") is not None and p["media"] > q["media"])
    res["criterio"] = {"1_sesgo": c1, "2_plata": c2}
    with open(os.path.join(AQUI, "resultados_libros.json" if usar_libros else "resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

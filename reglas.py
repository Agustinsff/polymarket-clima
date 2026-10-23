"""
REGLAS: avisa cuando Polymarket cambia las reglas de los mercados que seguimos.

El 21 y el 23-oct-2026 Polymarket cambio la fuente con la que resuelve los mercados de
temperatura (Wunderground -> weather.gov -> METAR de aviationweather.gov) sin avisar,
y los bots dejaron de encontrar mercados. Este script saca una "huella" de cada familia
de mercados y la compara con la de la corrida anterior:

  fuentes     resolutionSource sin estacion ni fecha (ej. aviationweather.gov/api/data/metar)
  comisiones  feesEnabled, feeType, feeSchedule y takerBaseFee de cada caja
  parametros  orden minima y tick de precio
  reglamento  las frases del texto del mercado que se repiten en al menos el 20 % de los
              eventos (sin numeros, fechas, estaciones ni links): si aparece una frase
              nueva, cambio el reglamento
  ciudades    ciudades con mercado de temperatura abierto
  clima_otros mercados de clima que no son de temperatura diaria (tipos nuevos)

Familias: temperatura maxima, temperatura minima y las series de cripto.py.
Solo lee Polymarket; no toca ninguna prueba.

Cada novedad queda en reglas_cambios.csv; las de las ultimas 48 h aparecen arriba de
RESUMEN.md y el vigia las manda por mail. La foto actual queda en reglas_informe.md.
La primera corrida solo arma la huella de base (no avisa nada).

Uso: python reglas.py           (lo corre el workflow 'reglas' cada 3 h)
     python reglas.py --probar  (imprime sin guardar)
"""

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(CARPETA, n)
F_EST, F_CSV, F_MD = F("reglas_estado.json"), F("reglas_cambios.csv"), F("reglas_informe.md")
GAMMA = "https://gamma-api.polymarket.com/events"
COMUN = 0.20             # una frase es "del reglamento" si esta en al menos el 20 % de los eventos
OLVIDO_DIAS = 3          # lo que no se ve hace 3 dias se anota como "ya no aparece"
AVISO_HORAS = 48         # cuanto tiempo queda el aviso en RESUMEN.md / vigia
FEE_ASUMIDA = 0.05       # lo que usan fee() de nuestros scripts: 0.05 * p * (1 - p)
COLUMNAS = ["momento_utc", "familia", "que", "cambio", "detalle", "ejemplo", "origen"]
NOMBRES = {"comisiones": "comisión", "fuentes": "fuente de resolución", "parametros": "parámetros",
           "reglamento": "reglamento", "ciudades": "ciudades", "clima_otros": "mercado de clima nuevo"}
MESES = "january|february|march|april|may|june|july|august|september|october|november|december"


def log(m):
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}Z {m}", flush=True)


def traer(params, tope=3000):
    import requests              # aca y no arriba: el vigia importa este archivo sin tener requests
    evs = []
    for off in range(0, tope, 100):
        r = requests.get(GAMMA, params={**params, "closed": "false", "limit": 100, "offset": off}, timeout=30,
                         headers={"User-Agent": "polymarket-clima-reglas/1.0 (investigacion personal)"})
        r.raise_for_status()
        lote = r.json()
        evs += lote
        if len(lote) < 100:
            break
    return evs


def etiquetas(e):
    return {t.get("slug") if isinstance(t, dict) else t for t in e.get("tags") or []}


# --- normalizar --------------------------------------------------------------------------

def fuente(url):
    """'https://aviationweather.gov/api/data/metar?ids=EGLC&...' -> 'aviationweather.gov/api/data/metar'."""
    if not url:
        return "(sin fuente)"
    url = re.sub(r"^https?://(www\.)?", "", url.strip()).split("?")[0].split("#")[0].rstrip("/")
    partes = url.split("/")
    if "wunderground.com" in partes[0]:
        partes = partes[:3]                       # wunderground.com/history/daily/<pais>/<ciudad>/<ICAO>
    return "/".join("<estacion>" if re.fullmatch(r"[A-Z][A-Z0-9]{3}", p) else p for p in partes)


def comision(m):
    fs = m.get("feeSchedule")
    fs = json.dumps(fs, sort_keys=True) if isinstance(fs, (dict, list)) else str(fs)
    return f"feesEnabled={m.get('feesEnabled')} feeType={m.get('feeType')} feeSchedule={fs} takerBaseFee={m.get('takerBaseFee')}"


def parametros(m):
    return f"orden minima={m.get('orderMinSize')} tick={m.get('orderPriceMinTickSize')}"


def frases(e):
    """El texto del evento en frases sin lo que cambia de un evento a otro."""
    t = e.get("description") or ""
    t = re.sub(r"https?://\S+", "<link>", t)
    t = re.sub(r"(?:[A-Z][\w'’.\-–]*\s+(?:(?:de|do|da|del|of|the|la|le|el)\s+)?)+\(([A-Z0-9]{3,4})\)", "<estacion>", t)
    t = re.sub(r"\b[A-Z]{4}\b", "<estacion>", t)
    mes = rf"(?:{MESES}|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\.?"
    t = re.sub(rf"(?<=\d )\b{mes}\b|\b{mes}(?= \d)", "<mes>", t, flags=re.I)   # solo junto a un numero ("may" es palabra)
    t = re.sub(r"[−-]?\d+([.,]\d+)?", "#", t)
    t = re.sub(r"'#", "#", t)
    for nombre in sorted(e.get("_ciudad_nombres", []), key=len, reverse=True):
        t = re.sub(re.escape(nombre), "<ciudad>", t, flags=re.I)
    out = set()
    for f in re.split(r"(?<=[.:;])\s+|\n+", t):
        f = re.sub(r"\s+", " ", f).strip()
        if len(f) >= 25:
            out.add(f[:400])
    return out


# --- huella ------------------------------------------------------------------------------

def huella():
    """{familia: {que: {variante: (cuantos, ejemplo)}}} y los tipos de mercados de clima."""
    from cripto import SERIES
    fams = defaultdict(lambda: defaultdict(dict))
    temp = traer({"tag_slug": "daily-temperature"})
    if len(temp) == 0:
        raise RuntimeError("Polymarket no devolvio ningun mercado de temperatura")
    grupos = defaultdict(list)
    for e in temp:
        m = re.match(rf"^(highest|lowest)-temperature-in-(.+)-on-(?:{MESES})-\d+-\d{{4}}$", e.get("slug", ""))
        if not m:
            grupos["temperatura (otro formato)"].append(e)
            continue
        e["_ciudad"] = m.group(2)
        e["_ciudad_nombres"] = [m.group(2).replace("-", " ")]
        titulo = re.search(r" in (.+?) on ", e.get("title") or "")
        if titulo:
            e["_ciudad_nombres"].append(titulo.group(1))
        grupos["temperatura " + ("máxima" if m.group(1) == "highest" else "mínima")].append(e)
    for activo, tipo, serie in SERIES:
        try:
            grupos[f"cripto {serie}"] = traer({"series_slug": serie}, tope=200)
        except Exception as ex:
            log(f"no pude traer {serie}: {ex}")
    for fam, evs in grupos.items():
        h = fams[fam]
        h["_eventos"] = len(evs)
        conteo = defaultdict(Counter)
        ejemplo = {}
        for e in evs:
            slug = e.get("slug", "")
            vistas = {"fuentes": {fuente(e.get("resolutionSource"))}, "reglamento": frases(e),
                      "comisiones": {comision(m) for m in e.get("markets") or []},
                      "parametros": {parametros(m) for m in e.get("markets") or []}}
            if e.get("_ciudad"):
                vistas["ciudades"] = {e["_ciudad"]}
            for que, vs in vistas.items():
                for v in vs:
                    conteo[que][v] += 1
                    ejemplo.setdefault((que, v), slug)
        for que, c in conteo.items():
            for v, n in c.items():
                if que == "reglamento" and n < COMUN * len(evs):
                    continue                     # frase de una sola ciudad, no del reglamento
                h[que][v] = [n, ejemplo[(que, v)]]
    otros = {}
    try:
        for e in traer({"tag_slug": "weather"}):
            if "daily-temperature" in etiquetas(e):
                continue
            tipo = re.sub(rf"-(?:in|on|for)-.*|-(?:{MESES})-.*|-\d.*", "", e.get("slug", ""))
            otros.setdefault(tipo, [0, e.get("slug", "")])[0] += 1
    except Exception as ex:
        log(f"no pude traer los mercados de clima: {ex}")
        otros = None
    if otros is not None:
        fams["clima (otros)"]["clima_otros"] = otros
        fams["clima (otros)"]["_eventos"] = sum(n for n, _ in otros.values())
    return fams


def cargar():
    try:
        with open(F_EST, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def comparar(est, fams, ahora):
    """Actualiza el estado (lo visto alguna vez, con primera y ultima vez) y devuelve los cambios."""
    cambios = []
    base = not est.get("familias")
    fam_est = est.setdefault("familias", {})
    hoy = ahora.strftime("%Y-%m-%d %H:%M")
    for fam, h in fams.items():
        previo = fam_est.get(fam)
        if previo and h.get("_eventos", 0) < 0.5 * previo.get("_eventos", 0):
            log(f"{fam}: vinieron {h.get('_eventos')} eventos (antes {previo.get('_eventos')}); no comparo esta vez")
            continue
        f_est = fam_est.setdefault(fam, {})
        if previo is None and not base:
            cambios.append([fam, "familia", "nueva", f"{h.get('_eventos', 0)} eventos abiertos", ""])
        f_est["_eventos"] = h.get("_eventos", 0)
        for que, vs in h.items():
            if que.startswith("_"):
                continue
            q_est = f_est.setdefault(que, {})
            for v, (n, ej) in vs.items():
                if v not in q_est and previo is not None:
                    cambios.append([fam, que, "aparece", v, ej])
                q_est.setdefault(v, {"desde": hoy})
                q_est[v].update({"ultima": hoy, "eventos": n, "ejemplo": ej})
                q_est[v].pop("olvidada", None)
        for que, q_est in f_est.items():
            if que.startswith("_"):
                continue
            actual = h.get(que, {})
            for v, info in q_est.items():
                if v in actual or info.get("olvidada"):
                    continue
                if ahora - datetime.strptime(info["ultima"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) \
                        > timedelta(days=OLVIDO_DIAS):
                    info["olvidada"] = hoy
                    cambios.append([fam, que, "ya no aparece", v, info.get("ejemplo", "")])
    est["actualizado"] = hoy
    return [] if base else cambios


def anotar(cambios, ahora):
    nuevo = not os.path.exists(F_CSV)
    with open(F_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(COLUMNAS)
        for fam, que, cambio, detalle, ej in cambios:
            w.writerow([ahora.strftime("%Y-%m-%d %H:%M"), fam, que, cambio, detalle, ej, "auto"])


def leer_cambios():
    if not os.path.exists(F_CSV):
        return []
    with open(F_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tasa(variante):
    m = re.search(r'"rate": ([\d.]+)', variante)
    return float(m.group(1)) if m else None


def avisos(ahora=None):
    """Lo que va arriba de RESUMEN.md y al vigia: novedades automaticas de las ultimas 48 h."""
    ahora = ahora or datetime.now(timezone.utc)
    recientes = defaultdict(list)
    for c in leer_cambios():
        if c.get("origen") != "auto":
            continue
        t = datetime.strptime(c["momento_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if ahora - t <= timedelta(hours=AVISO_HORAS):
            recientes[(c["familia"], NOMBRES.get(c["que"], c["que"]), c["cambio"])].append(c)
    out = []
    for (fam, que, cambio), cs in sorted(recientes.items()):
        detalle = f"`{cs[-1]['detalle'][:150]}`" + (f" y {len(cs) - 1} más" if len(cs) > 1 else "")
        out.append(f"🔔 Polymarket cambió algo en **{fam}** ({que}, {cambio} el {cs[-1]['momento_utc']} UTC): "
                   f"{detalle}. Ver [reglas_informe.md](reglas_informe.md).")
    return out


def informe(est, ahora):
    L = ["# Reglas de los mercados de Polymarket", "",
         f"Actualizado {ahora:%Y-%m-%d %H:%M} UTC por `reglas.py` (cada 3 h). "
         "Lo que Polymarket usa hoy en cada familia de mercados, y los cambios que se detectaron.", ""]
    av = avisos(ahora)
    L += (av or ["✅ Sin cambios en las últimas 48 h."]) + [""]
    L += ["## Comisiones: lo que cobra Polymarket vs. lo que suponemos", "",
          f"Nuestros scripts calculan la comisión del taker como **{FEE_ASUMIDA} × p × (1 − p)** por acción "
          "(`fee()` en estaciones, cosechador, pronóstico, cripto y resumen_diario). Según la ayuda de Polymarket "
          "(julio 2026) la tasa es 0.05 en clima y 0.07 en cripto, pero cada mercado trae la suya en `feeSchedule`.", "",
          "| Familia | Eventos abiertos | Comisión que trae el mercado (cajas) | ¿Coincide con 0.05? |", "|---|---|---|---|"]
    fams = est.get("familias", {})
    for fam in sorted(fams):
        vivas = {v: i for v, i in fams[fam].get("comisiones", {}).items() if i.get("ultima") == est.get("actualizado")}
        for v, i in sorted(vivas.items(), key=lambda x: -x[1]["eventos"]):
            r = tasa(v)
            ok = "—" if r is None else ("✅" if abs(r - FEE_ASUMIDA) < 1e-9 else f"⚠️ cobra {r}")
            L.append(f"| {fam} | {fams[fam].get('_eventos', 0)} | `{v}` ({i['eventos']}) | {ok} |")
    L += ["", "## Fuente de resolución y parámetros", "", "| Familia | Qué | Variante (eventos o cajas) | Desde |", "|---|---|---|---|"]
    for fam in sorted(fams):
        for que in ("fuentes", "parametros"):
            for v, i in sorted(fams[fam].get(que, {}).items(), key=lambda x: -x[1]["eventos"]):
                if i.get("ultima") == est.get("actualizado"):
                    L.append(f"| {fam} | {NOMBRES[que]} | `{v}` ({i['eventos']}) | {i['desde']} |")
    otros = fams.get("clima (otros)", {}).get("clima_otros", {})
    L += ["", "## Mercados de clima que no son de temperatura diaria", ""]
    L += [f"- `{t}`: {i['eventos']} abiertos (ej. `{i['ejemplo']}`), visto desde {i['desde']}"
          for t, i in sorted(otros.items()) if i.get("ultima") == est.get("actualizado")] or ["- Ninguno abierto."]
    ciu = {f: sorted(v for v, i in fams[f].get("ciudades", {}).items() if i.get("ultima") == est.get("actualizado"))
           for f in fams if fams[f].get("ciudades")}
    L += ["", "## Ciudades con mercado de temperatura", ""]
    L += [f"- **{f}** ({len(c)}): {', '.join(c)}" for f, c in sorted(ciu.items())]
    L += ["", "## Últimos cambios", "", "| Cuándo (UTC) | Familia | Qué | Cambio | Detalle | Origen |", "|---|---|---|---|---|---|"]
    for c in leer_cambios()[-30:][::-1]:
        L.append(f"| {c['momento_utc']} | {c['familia']} | {NOMBRES.get(c['que'], c['que'])} | {c['cambio']} | "
                 f"{c['detalle'][:300].replace('|', '/')} | {c['origen']} |")
    L += ["", "## Reglamento actual (frases comunes)", ""]
    for fam in sorted(fams):
        fr = [v for v, i in fams[fam].get("reglamento", {}).items() if i.get("ultima") == est.get("actualizado")]
        if fr:
            L += [f"<details><summary>{fam} ({len(fr)} frases)</summary>", ""] + [f"- {f}" for f in sorted(fr)] + ["", "</details>", ""]
    with open(F_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main(probar=False):
    ahora = datetime.now(timezone.utc)
    fams = huella()
    est = cargar()
    cambios = comparar(est, fams, ahora)
    for c in cambios:
        log(" | ".join(c))
    log(f"{len(cambios)} cambios; familias: " + ", ".join(f"{f} ({h.get('_eventos', 0)})" for f, h in fams.items()))
    if probar:
        return
    anotar(cambios, ahora)
    with open(F_EST, "w", encoding="utf-8") as f:
        json.dump(est, f, indent=1, ensure_ascii=False)
    informe(est, ahora)


if __name__ == "__main__":
    main("--probar" in sys.argv)

"""
Genera RESUMEN.md: el estado de todos los experimentos en una sola pagina,
para mirarlo desde el celular en GitHub. Lo corre el reloj todos los dias
(y despues de cada tarea diaria). No necesita internet: lee los archivos del repo.
"""

import csv
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(CARPETA, n)


def num(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def leer(nombre, sep=";"):
    if not os.path.exists(F(nombre)):
        return []
    with open(F(nombre), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=sep))


def cargar_json(nombre):
    try:
        with open(F(nombre), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def fee(p):
    return 0.05 * p * (1 - p)


# ---------------------------------------------------------------------------

def seccion_alarmas(ahora_local):
    rel = cargar_json("reloj_estado.json")
    cos = cargar_json("cosecha_estado.json")
    alarmas = []
    ult = rel.get("liquidez")
    if not ult or ahora_local - datetime.fromisoformat(ult) > timedelta(hours=1):
        alarmas.append(f"⚠️ La medición de liquidez no corre desde {ult or 'nunca'} (el reloj puede estar caído).")
    hoy = ahora_local.date().isoformat()
    if ahora_local.hour * 60 + ahora_local.minute > 10 * 60 + 40 and rel.get("diario_am") != hoy:
        alarmas.append(f"⚠️ El monitor de las 10:05 de hoy no corrió (último: {rel.get('diario_am')}).")
    if ahora_local.hour * 60 + ahora_local.minute > 15 * 60 and rel.get("papel") != hoy:
        alarmas.append(f"⚠️ La prueba de São Paulo de hoy no se registró (último: {rel.get('papel')}).")
    diag = cos.get("diagnostico") or {}
    if diag.get("momento_utc"):
        t = datetime.strptime(diag["momento_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - t > timedelta(hours=7):
            alarmas.append(f"⚠️ El cosechador no actualiza desde {diag['momento_utc']} UTC.")
    lineas = ["## Estado de las tareas", ""]
    lineas += alarmas or ["✅ Todo corriendo normalmente."]
    lineas += ["", f"- Última foto de liquidez: {rel.get('liquidez', '-')}",
               f"- Monitor: mañana {rel.get('diario_am', '-')}, noche {rel.get('diario_pm', '-')}",
               f"- Prueba São Paulo: último día registrado {rel.get('papel', '-')}",
               f"- Cosechador: último ciclo {diag.get('momento_utc', '-')} UTC, "
               f"{diag.get('series', '-')} mercados, {diag.get('estaciones_con_datos', '-')} estaciones", ""]
    return lineas


def seccion_resultados():
    res = leer("resultados.csv")
    reg = leer("registro.csv")
    # ultima foto del monitor ANTES del dia del mercado (la de la noche anterior)
    fotos = defaultdict(list)
    for r in reg:
        fotos[(r["ciudad"], r["fecha_mercado"])].append(r)
    filas = []
    aciertos = {"mercado": 0, "modelo": 0, "n": 0}
    for r in res:
        ganadora = r.get("caja_ganadora_polymarket") or ""
        clave = (r["ciudad"], r["fecha"])
        previas = [x for x in fotos.get(clave, []) if x["momento"][:10] < r["fecha"]]
        if not previas or not ganadora:
            continue
        ultimo = max(x["momento"] for x in previas)
        foto = [x for x in previas if x["momento"] == ultimo]
        fav_m = max(foto, key=lambda x: num(x["precio_mercado"]) or 0)
        fav_o = max(foto, key=lambda x: num(x["prob_modelo"]) or 0)
        ok_m, ok_o = fav_m["caja"] == ganadora, fav_o["caja"] == ganadora
        aciertos["n"] += 1
        aciertos["mercado"] += ok_m
        aciertos["modelo"] += ok_o
        filas.append((r["fecha"], r["ciudad"], ganadora,
                      f"{fav_m['caja']} ({num(fav_m['precio_mercado']) * 100:.0f}%) {'✅' if ok_m else '❌'}",
                      f"{fav_o['caja']} ({num(fav_o['prob_modelo']) * 100:.0f}%) {'✅' if ok_o else '❌'}"))
    lineas = ["## Temperatura máxima: mercado vs. modelo (BA y SP)", ""]
    if aciertos["n"]:
        lineas.append(f"Acumulado: la caja favorita del **mercado** acertó {aciertos['mercado']}/{aciertos['n']}, "
                      f"la del **modelo** {aciertos['modelo']}/{aciertos['n']}.")
    lineas += ["", "| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |", "|---|---|---|---|---|"]
    for f in sorted(filas, reverse=True)[:10]:
        lineas.append("| " + " | ".join(f) + " |")
    return lineas + [""]


def seccion_papel():
    ops = leer("papel_operaciones.csv")
    dias = sorted({r["fecha"] for r in leer("papel_libro.csv")})
    lineas = ["## Prueba en papel São Paulo 14 hs (regla fija)", "",
              f"Días registrados: {len(dias)} (desde {dias[0] if dias else '-'})."]
    neto = bruto = comis = 0.0
    n_ok = n_mal = n_pend = 0
    tabla = []
    for r in ops:
        p, q, res = num(r["precio_medio"]), num(r["acciones"]), num(r["resultado"])
        c = q * fee(p)
        if res is None:
            n_pend += 1
            estado = "pendiente"
        else:
            bruto += res
            comis += c
            neto += res - c
            n_ok += res > 0
            n_mal += res <= 0
            estado = f"{res - c:+.2f}"
        tabla.append(f"| {r['fecha']} | {r['caja']} | {r['lado']} | {p:.3f} | {num(r['prob_modelo']) * 100:.0f}% | {estado} |")
    lineas.append(f"Operaciones: {len(ops)} ({n_ok} ganadas, {n_mal} perdidas, {n_pend} pendientes). "
                  f"**Neto con comisiones: US${neto:+.2f}** (bruto {bruto:+.2f}, comisiones −{comis:.2f}).")
    if tabla:
        lineas += ["", "| Día | Caja | Lado | Precio | Modelo | Resultado |", "|---|---|---|---|---|---|"] + tabla[-10:]
    return lineas + [""]


def seccion_cosechador():
    filas = leer("cosecha.csv")
    est = cargar_json("cosecha_estado.json")
    liq = est.get("liquidadas", {})
    lineas = ["## Cosechador en papel (cajas imposibles, todas las ciudades)", ""]
    if not filas:
        return lineas + ["Todavía sin operaciones.", ""]
    neto = pend = 0.0
    tabla = []
    for r in filas:
        p, q = num(r["precio_yes"]), num(r["acciones"])
        gano_caja = liq.get(r["condition_id"])
        if gano_caja is None:
            pend += q * (p - fee(p))
            estado = "pendiente"
        else:
            g = q * (p - fee(p)) if gano_caja == 0 else -q * (1 - p) - q * fee(p)
            neto += g
            estado = f"{g:+.2f}"
        tabla.append(f"| {r['fecha_local']} | {r['serie'].split('|')[1]} | {r['caja']} | {p:.2f} | {q:.0f} | {estado} |")
    lineas.append(f"Operaciones: {len(filas)}. **Neto liquidado: US${neto:+.2f}**. "
                  f"Pendientes: +US${pend:.2f} si salen bien.")
    lineas.append("Nota: las operaciones de Ciudad del Cabo del 18-oct se hicieron con la regla vieja (sin confirmación) "
                  "y su resolución está en disputa.")
    lineas += ["", "| Día | Ciudad | Caja | Precio Yes | Acciones | Resultado |", "|---|---|---|---|---|---|"] + tabla[-12:]
    return lineas + [""]


def seccion_liquidez():
    filas = leer("liquidez.csv")
    if not filas:
        return []
    limite = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
    por_foto = defaultdict(lambda: defaultdict(float))
    for r in filas:
        h = num(r["horas_hasta_el_dia"])
        if r["momento_utc"] >= limite and h is not None and 0 < h <= 27:
            por_foto[r["ciudad"]][r["momento_utc"]] += num(r["est_100acc_1c"]) or 0
    lineas = ["## Recompensas de liquidez (estimación, últimas 24 h)", ""]
    for ciudad, fotos in sorted(por_foto.items()):
        v = list(fotos.values())
        lineas.append(f"- {ciudad}: ~US${sum(v) / len(v):.0f}/día con 100 acciones a 1 ¢ en todas las cajas "
                      f"del mercado de mañana (sin contar pérdidas por quedar 'tomado').")
    return lineas + [""]


def main():
    ahora_utc = datetime.now(timezone.utc)
    ahora_local = datetime.now()  # el workflow usa TZ=America/Montevideo
    md = [f"# Resumen polymarket-clima", "",
          f"_Actualizado: {ahora_local:%Y-%m-%d %H:%M} (Montevideo). Todo es **en papel**: no se usa plata real._", ""]
    md += seccion_alarmas(ahora_local)
    md += seccion_resultados()
    md += seccion_papel()
    md += seccion_cosechador()
    md += seccion_liquidez()
    with open(F("RESUMEN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("RESUMEN.md actualizado")


if __name__ == "__main__":
    main()

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

CADA_15_MIN = {"liquidez.py", "hoy.py", "cripto.py"}   # una falla suelta se arregla sola en la vuelta siguiente


def alarmas(ahora_local):
    """Lista de problemas. La usan RESUMEN.md y el vigia (que abre un aviso en GitHub)."""
    rel = cargar_json("reloj_estado.json")
    cos = cargar_json("cosecha_estado.json")
    avisos = []
    ult = rel.get("liquidez")
    if not ult or ahora_local - datetime.fromisoformat(ult) > timedelta(hours=1):
        avisos.append(f"⚠️ La medición de liquidez no corre desde {ult or 'nunca'} (el reloj puede estar caído).")
    hoy = ahora_local.date().isoformat()
    if ahora_local.hour * 60 + ahora_local.minute > 10 * 60 + 40 and rel.get("diario_am") != hoy:
        avisos.append(f"⚠️ El monitor de las 10:05 de hoy no corrió (último: {rel.get('diario_am')}).")
    if ahora_local.hour * 60 + ahora_local.minute > 15 * 60 and rel.get("papel") != hoy:
        avisos.append(f"⚠️ La prueba de São Paulo de hoy no se registró (último: {rel.get('papel')}).")
    diag = cos.get("diagnostico") or {}
    if diag.get("momento_utc"):
        t = datetime.strptime(diag["momento_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - t > timedelta(hours=7):
            avisos.append(f"⚠️ El cosechador no actualiza desde {diag['momento_utc']} UTC.")
    if diag.get("momento_utc") and diag.get("series") == 0:
        avisos.append("⚠️ El cosechador no encuentra ningún mercado de temperatura abierto en Polymarket "
                      "(¿dejaron de crearlos o les cambiaron el nombre?).")
    hoy_filas = leer("hoy.csv")
    if hoy_filas:
        ult_hoy = datetime.strptime(hoy_filas[-1]["momento_utc"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - ult_hoy > timedelta(hours=4):
            avisos.append(f"⚠️ El pronóstico del mismo día no registra nada desde {hoy_filas[-1]['momento_utc'][:16]} UTC.")
    for tarea, f in sorted(cargar_json("fallas.json").items()):
        if tarea in CADA_15_MIN and f.get("veces", 0) < 2:
            continue
        veces = "en su última corrida" if f.get("veces") == 1 else f"{f.get('veces')} veces seguidas"
        avisos.append(f"⚠️ `{tarea}` falló {veces} (desde {f.get('desde')}): {f.get('detalle')}")
    try:
        import reglas                                  # cambios de reglas de Polymarket (ultimas 48 h)
        avisos += reglas.avisos()
    except Exception as e:
        avisos.append(f"⚠️ No pude leer reglas_cambios.csv: {e}")
    return avisos


def seccion_alarmas(ahora_local):
    rel = cargar_json("reloj_estado.json")
    diag = cargar_json("cosecha_estado.json").get("diagnostico") or {}
    lineas = ["## Estado de las tareas", ""]
    lineas += alarmas(ahora_local) or ["✅ Todo corriendo normalmente."]
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


def seccion_pronostico(csv_nom="pronostico.csv", ops_nom="pronostico_ops.csv",
                       titulo="Pronóstico vs. mercado (todas las ciudades, día anterior)"):
    if not os.path.exists(F(csv_nom)):
        return []
    try:
        import pronostico
        br, ops = pronostico.evaluar(F(csv_nom), F(ops_nom))
    except Exception as e:
        return [f"## {titulo}", "", f"Error al evaluar: {e}", ""]
    lineas = [f"## {titulo}", ""]
    n = sum(b["n"] for b in br.values())
    if n:
        bm = sum(b["modelo"] for b in br.values()) / n
        bk = sum(b["mercado"] for b in br.values()) / n
        lineas.append(f"Puntaje Brier (más bajo = mejor) en {n} cajas liquidadas: **modelo {bm:.4f}** vs **mercado {bk:.4f}**.")
        mejores = sorted(((b["mercado"] - b["modelo"]) / b["n"], s, len(b["dias"])) for s, b in br.items()
                         if len(b["dias"]) >= 5)
        if mejores:
            lineas.append("Series donde el modelo le gana al mercado (≥5 días): " + (", ".join(
                f"{s.replace('highest|', 'máx ').replace('lowest|', 'mín ')} ({d} días)" for v, s, d in reversed(mejores) if v > 0)[:600] or "ninguna todavía") + ".")
    else:
        lineas.append("Todavía no hay días liquidados.")
    lineas += ["", "| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |", "|---|---|---|---|---|---|"]
    modos = sorted({o["modo"] for o, r, q in ops}, key=lambda m: ["taker", "maker", "cola_taker", "cola_maker", "no80_90"].index(m) if m in ["taker", "maker", "cola_taker", "cola_maker", "no80_90"] else 9)
    for modo in modos or ["taker"]:
        for cal in ("1", "0"):
            xs = [(o, r, q) for o, r, q in ops if o["modo"] == modo and o["calibrada"] == cal]
            if not xs:
                continue
            liq = [r for o, r, q in xs if r is not None]
            lineas.append(f"| {modo} | {'sí' if cal == '1' else 'no'} | {len(liq)} | {sum(1 for r in liq if r > 0)} | "
                          f"US${sum(liq):+.2f} | {len(xs) - len(liq)} |")
    lineas.append("")
    lineas.append("_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._")
    return lineas + [""]


def seccion_sombra():
    s = cargar_json("sombra_maker.json")
    if not s:
        return []
    lineas = ["## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)", ""]
    cos = s.get("cosechador", {})
    if cos:
        lineas.append(f"Cosechador: {len(cos)} cajas muertas ya liquidadas.")
        for p in ("0.02", "0.03", "0.05"):
            q = sum(v[p]["acciones"] for v in cos.values())
            r = sum(v[p]["resultado"] for v in cos.values())
            mal = sum(1 for v in cos.values() if v["gano"] == 1 and v[p]["acciones"] > 0)
            lineas.append(f"- Vender el Yes a {float(p) * 100:.0f} ¢: {q:.0f} acciones llenadas, neto **US${r:+.2f}** "
                          f"({mal} cajas 'muertas' que terminaron ganando)")
    sp = s.get("sp14", {})
    if sp:
        r = sum(v["resultado_maker"] for v in sp.values())
        q = sum(1 for v in sp.values() if v["acciones"] > 0)
        lineas.append(f"Prueba SP: {len(sp)} operaciones; como maker se habrían llenado {q}, neto **US${r:+.2f}** (sin comisión).")
    return lineas + [""]


def seccion_cripto():
    if not os.path.exists(F("cripto_ops.csv")) and not os.path.exists(F("cripto.csv")):
        return []
    try:
        import cripto
        b, ops = cripto.evaluar()
    except Exception as e:
        return ["## Cripto en papel (Bitcoin / Ethereum above)", "", f"Error al evaluar: {e}", ""]
    liq = [(o, r) for o, r in ops if r is not None]
    costo = sum(float(o["precio"]) * float(o["acciones"]) for o, r in liq)
    neto = sum(r for o, r in liq)
    lineas = ["## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)", "",
              f"Operaciones: {len(ops)} ({len(liq)} liquidadas, {sum(1 for o, r in liq if r > 0)} ganadas). "
              f"**Neto US${neto:+.2f}** sobre US${costo:.2f} invertidos"
              + (f" (ROI {100 * neto / costo:+.1f} %)." if costo else ".")]
    if b["n"]:
        lineas.append(f"Brier en {b['n']} strikes: modelo {b['modelo'] / b['n']:.4f} vs mercado {b['mercado'] / b['n']:.4f}.")
    claves = sorted({(o["activo"], o.get("tipo", "above")) for o, r in ops})
    if claves:
        lineas += ["", "| Activo | Tipo | Liquidadas | Neto |", "|---|---|---|---|"]
        for a, t in claves:
            xs = [r for o, r in liq if (o["activo"], o.get("tipo", "above")) == (a, t)]
            lineas.append(f"| {a} | {t} | {len(xs)} | US${sum(xs):+.2f} |")
    lineas.append("")
    lineas.append("_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre "
                  "(18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. "
                  "Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._")
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
    md += seccion_pronostico()
    md += seccion_pronostico("hoy.csv", "hoy_ops.csv",
                             "Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)")
    md += seccion_cripto()
    md += seccion_sombra()
    md += seccion_liquidez()
    with open(F("RESUMEN.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("RESUMEN.md actualizado")


if __name__ == "__main__":
    main()

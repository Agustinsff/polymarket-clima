"""
RELOJ: corre las tareas periodicas sin depender de los horarios de GitHub
(que con repos nuevos se atrasan horas o directamente no disparan).

Corre en bucle ~340 minutos y, cuando le toca a cada tarea, la ejecuta y
guarda el resultado en el repositorio (git commit + push). Al terminar,
el workflow lanza la siguiente corrida (cadena 24/7).

Tareas (hora de Montevideo):
  liquidez    cada 15 minutos (+ hoy.py: pronostico del mismo dia a las 12 y 15 locales / 9 la minima)
  diario      10:05 y 20:05 (resultados.py + monitor.py)
  papel_sp14  14:12 (la regla registra entre 14:10 y 14:59; reintenta hasta 14:50)
  multi       10:20 y 20:20 (pronostico.py en todas las ciudades + sombra_maker.py + cripto liquidar)
  cripto      cada 15 min junto con liquidez (mercados 'Bitcoin/Ethereum above')
  libros      cada hora (profundidad del libro de clima y cripto, hasta el 2-nov)
  regla_metar cada 30 min (investigacion regla_metar/REGLA.md: fotos del libro, resultados y METAR, hasta el 10-nov)
  favorito    minuto 53-58 de cada hora (papel favorito/REGLA.md: Up/Down de 1 h a 70-90 c, ops hasta el 16-nov)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

CARPETA = os.path.dirname(os.path.abspath(__file__))
F_EST = os.path.join(CARPETA, "reloj_estado.json")
F_FALLAS = os.path.join(CARPETA, "fallas.json")


def log(m):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {m}", flush=True)


def cargar():
    if os.path.exists(F_EST):
        with open(F_EST, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar(e):
    with open(F_EST, "w", encoding="utf-8") as f:
        json.dump(e, f, indent=1)


def anotar_falla(tarea, r):
    """fallas.json: tareas cuya ultima corrida fallo (lo lee resumen_diario.py y el vigia)."""
    try:
        with open(F_FALLAS, encoding="utf-8") as f:
            fallas = json.load(f)
    except (OSError, ValueError):
        fallas = {}
    if r.returncode == 0:
        if tarea not in fallas:
            return
        fallas.pop(tarea)
    else:
        previa = fallas.get(tarea, {})
        detalle = (r.stderr.strip() or r.stdout.strip()).splitlines()[-1:] or [""]
        fallas[tarea] = {"desde": previa.get("desde", datetime.now().isoformat(timespec="seconds")),
                         "ultima": datetime.now().isoformat(timespec="seconds"),
                         "veces": previa.get("veces", 0) + 1, "codigo": r.returncode, "detalle": detalle[0][-300:]}
    with open(F_FALLAS, "w", encoding="utf-8") as f:
        json.dump(fallas, f, indent=1, ensure_ascii=False)


def correr(cmds, archivos, mensaje):
    cmds = cmds + [["resumen_diario.py"]]          # siempre se actualiza RESUMEN.md
    archivos = archivos + ["RESUMEN.md"]
    for c in cmds:
        try:
            r = subprocess.run([sys.executable] + c, cwd=CARPETA, capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            r = subprocess.CompletedProcess(c, -1, "", "se colgo: mas de 15 minutos sin terminar")
        log(f"  {' '.join(c)} -> codigo {r.returncode}")
        if r.returncode != 0:
            log(r.stdout[-1500:] + r.stderr[-1500:])
        anotar_falla(" ".join(c), r)
    subir(archivos + ["reloj_estado.json", "fallas.json"], mensaje)


def subir(archivos, mensaje):
    g = lambda *a: subprocess.run(["git"] + list(a), cwd=CARPETA, capture_output=True, text=True)
    for f in archivos:
        if os.path.exists(os.path.join(CARPETA, f)):
            g("add", f)
    if g("diff", "--cached", "--quiet").returncode == 0:
        return
    g("commit", "-m", f"datos: {mensaje} {datetime.utcnow():%Y-%m-%dT%H:%MZ}")
    for _ in range(5):
        if g("pull", "--rebase", "--autostash").returncode == 0 and g("push").returncode == 0:
            return
        time.sleep(10)
    log("No se pudo subir (se reintenta en la proxima tarea)")


def main(minutos):
    fin = time.time() + minutos * 60
    est = cargar()
    while time.time() < fin:
        ahora = datetime.now()
        hoy = ahora.date().isoformat()
        hm = ahora.hour * 60 + ahora.minute
        # liquidez cada 15 min
        ult = est.get("liquidez")
        if not ult or (ahora - datetime.fromisoformat(ult)) >= timedelta(minutes=15):
            log("liquidez")
            est["liquidez"] = ahora.isoformat(timespec="seconds")
            guardar(est)
            correr([["liquidez.py"], ["hoy.py"], ["cripto.py"]],
                   ["liquidez.csv", "hoy.csv", "hoy_ops.csv", "pronostico_estado.json", "estaciones.json",
                    "cripto.csv", "cripto_ops.csv", "cripto_estado.json"],
                   "liquidez y pronostico del mismo dia")
        # profundidad del libro (libros.py) cada hora; deja de medir sola despues de su FIN
        ult = est.get("libros")
        if not ult or (ahora - datetime.fromisoformat(ult)) >= timedelta(minutes=60):
            log("libros")
            est["libros"] = ahora.isoformat(timespec="seconds")
            guardar(est)
            correr([["libros.py"], ["libros.py", "resumen"]], ["libros.csv", "libros_informe.md"],
                   "profundidad del libro")
        # investigacion regla_metar cada 30 min (solo mide; el script se apaga solo despues del 10-nov)
        ult = est.get("regla_metar")
        if not ult or (ahora - datetime.fromisoformat(ult)) >= timedelta(minutes=30):
            log("regla_metar")
            est["regla_metar"] = ahora.isoformat(timespec="seconds")
            guardar(est)
            correr([["regla_metar/recolector.py"]],
                   ["regla_metar/datos/fotos.csv", "regla_metar/datos/resultados.csv", "regla_metar/datos/metar.csv.gz",
                    "regla_metar/datos/estado.json"], "regla_metar")
        # favorito tardio (papel): una vez por hora, entre el minuto 53 y 58 (la ventana la controla el script)
        if 53 <= ahora.minute <= 58 and est.get("favorito") != ahora.strftime("%Y-%m-%d %H"):
            log("favorito")
            est["favorito"] = ahora.strftime("%Y-%m-%d %H")
            guardar(est)
            correr([["favorito/tardio.py"]], ["favorito/fotos.csv", "favorito/ops.csv", "favorito/estado.json",
                                               "favorito/resultados.md"], "favorito tardio")
        # diario 10:05 y 20:05
        for etiqueta, desde in (("diario_am", 10 * 60 + 5), ("diario_pm", 20 * 60 + 5)):
            if hm >= desde and est.get(etiqueta) != hoy:
                log(etiqueta)
                est[etiqueta] = hoy
                guardar(est)
                correr([["resultados.py"], ["monitor.py"]], ["registro.csv", "resultados.csv"], "monitor y resultados")
        # pronostico vs mercado en todas las ciudades + sombra maker, 10:20 y 20:20
        for etiqueta, desde in (("multi_am", 10 * 60 + 20), ("multi_pm", 20 * 60 + 20)):
            if hm >= desde and est.get(etiqueta) != hoy:
                log(etiqueta)
                est[etiqueta] = hoy
                guardar(est)
                correr([["pronostico.py", "liquidar"], ["pronostico.py"], ["sombra_maker.py"], ["cripto.py", "liquidar"]],
                       ["pronostico.csv", "pronostico_ops.csv", "pronostico_estado.json", "estaciones.json",
                        "sombra_maker.json", "cripto_estado.json"], "pronostico multi-ciudad, sombra maker y cripto")
        # papel SP 14hs
        if 14 * 60 + 12 <= hm <= 14 * 60 + 50 and est.get("papel") != hoy:
            log("papel_sp14")
            correr([["papel_sp14.py"]], ["papel_libro.csv", "papel_operaciones.csv"], "papel SP 14hs")
            if os.path.exists(os.path.join(CARPETA, "papel_libro.csv")):
                with open(os.path.join(CARPETA, "papel_libro.csv"), encoding="utf-8-sig") as f:
                    if any(l.startswith(hoy) for l in f):
                        est["papel"] = hoy
                        guardar(est)
                        subir(["reloj_estado.json"], "reloj")
        time.sleep(30)
    guardar(est)
    subir(["reloj_estado.json"], "reloj")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 340)

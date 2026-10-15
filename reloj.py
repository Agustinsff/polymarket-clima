"""
RELOJ: corre las tareas periodicas sin depender de los horarios de GitHub
(que con repos nuevos se atrasan horas o directamente no disparan).

Corre en bucle ~340 minutos y, cuando le toca a cada tarea, la ejecuta y
guarda el resultado en el repositorio (git commit + push). Al terminar,
el workflow lanza la siguiente corrida (cadena 24/7).

Tareas (hora de Montevideo):
  liquidez    cada 15 minutos
  diario      10:05 y 20:05 (resultados.py + monitor.py)
  papel_sp14  14:12 (la regla registra entre 14:10 y 14:59; reintenta hasta 14:50)
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

CARPETA = os.path.dirname(os.path.abspath(__file__))
F_EST = os.path.join(CARPETA, "reloj_estado.json")


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


def correr(cmds, archivos, mensaje):
    for c in cmds:
        r = subprocess.run([sys.executable] + c, cwd=CARPETA, capture_output=True, text=True, timeout=900)
        log(f"  {' '.join(c)} -> codigo {r.returncode}")
        if r.returncode != 0:
            log(r.stdout[-1500:] + r.stderr[-1500:])
    subir(archivos + ["reloj_estado.json"], mensaje)


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
            correr([["liquidez.py"]], ["liquidez.csv"], "liquidez")
        # diario 10:05 y 20:05
        for etiqueta, desde in (("diario_am", 10 * 60 + 5), ("diario_pm", 20 * 60 + 5)):
            if hm >= desde and est.get(etiqueta) != hoy:
                log(etiqueta)
                est[etiqueta] = hoy
                guardar(est)
                correr([["resultados.py"], ["monitor.py"]], ["registro.csv", "resultados.csv"], "monitor y resultados")
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

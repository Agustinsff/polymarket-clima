"""
VIGIA: avisa por GitHub cuando algo deja de andar.

Junta los problemas (los mismos que muestra RESUMEN.md arriba de todo, mas las
corridas de 'reloj' y 'cosechador' que terminaron en error) y mantiene UN aviso
(issue) abierto en el repositorio:
  - si hay problemas y no hay aviso abierto  -> abre uno (GitHub te manda un mail)
  - si los problemas cambiaron               -> agrega un comentario
  - si todo volvio a la normalidad           -> lo cierra con un comentario
No toca ninguna prueba ni ningun archivo de datos: solo lee.
Lo corre el workflow 'vigia' cada hora y cuando termina cada corrida del reloj o del cosechador.
Uso: python vigia.py           (necesita gh y GH_TOKEN; sin eso solo imprime)
     python vigia.py --probar  (solo imprime lo que haria)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime

import resumen_diario

ETIQUETA = "alerta"
TITULO = "⚠️ Aviso del vigía: algo dejó de andar"
CADENAS = ["reloj.yml", "cosechador.yml"]
DUENIO = "@Agustinsff"
REPO = os.environ.get("GH_REPO", "Agustinsff/polymarket-clima")


def gh(*args):
    r = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def corridas_con_error():
    """La ultima corrida terminada de cada cadena, si fallo."""
    avisos = []
    for wf in CADENAS:
        try:
            runs = json.loads(gh("run", "list", "--workflow", wf, "--status", "completed", "-L", "1",
                                 "--json", "conclusion,url,createdAt"))
        except Exception as e:
            print(f"no pude mirar {wf}: {e}")
            continue
        if runs and runs[0]["conclusion"] not in ("success", "skipped", "cancelled"):
            avisos.append(f"⚠️ La última corrida de `{wf}` terminó en **{runs[0]['conclusion']}**: {runs[0]['url']}")
    return avisos


def esencia(texto):
    """Lo mismo sin numeros ni links: para no comentar cada hora solo porque subio un contador."""
    return re.sub(r"https?://\S+|\d+", "", texto)


def main(probar=False):
    problemas = resumen_diario.alarmas(datetime.now()) + ([] if probar else corridas_con_error())
    print("Problemas:" if problemas else "Todo bien.", *problemas, sep="\n  ")
    if probar:
        return
    abiertos = json.loads(gh("issue", "list", "--label", ETIQUETA, "--state", "open", "--json", "number,body,comments"))
    texto = "\n".join(f"- {p}" for p in problemas)
    if problemas and not abiertos:
        gh("label", "create", ETIQUETA, "--color", "d73a4a", "--description", "Aviso automático del vigía", "--force")
        gh("issue", "create", "--label", ETIQUETA, "--title", TITULO, "--body",
           f"{DUENIO} el vigía encontró esto ({datetime.now():%Y-%m-%d %H:%M} Montevideo):\n\n{texto}\n\n"
           f"Más detalle en [RESUMEN.md](https://github.com/{REPO}/blob/main/RESUMEN.md) y en "
           f"[Actions](https://github.com/{REPO}/actions). "
           "Este aviso se cierra solo cuando todo vuelva a la normalidad.")
        print("aviso abierto")
    elif problemas:
        n = abiertos[0]["number"]
        ultimo = (abiertos[0]["comments"] or [{"body": abiertos[0]["body"]}])[-1]["body"]
        if esencia(texto) not in esencia(ultimo):
            gh("issue", "comment", str(n), "--body",
               f"{DUENIO} cambió la situación ({datetime.now():%Y-%m-%d %H:%M} Montevideo):\n\n{texto}")
            print(f"comentario en el aviso #{n}")
    else:
        for a in abiertos:
            gh("issue", "close", str(a["number"]), "--comment",
               f"✅ Todo volvió a la normalidad ({datetime.now():%Y-%m-%d %H:%M} Montevideo).")
            print(f"aviso #{a['number']} cerrado")


if __name__ == "__main__":
    main("--probar" in sys.argv)

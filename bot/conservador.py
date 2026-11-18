"""
BOT DE PAPEL "CONSERVADOR" (18-nov-2026, pedido de Agus): el maker de clima (bot/maker.py, sin tocarlo) en PAPEL con
compras mas chicas (20 acciones y tope 20 por lado) y filtro rapido de 2 c. Reglas y veredicto (lunes 24-nov):
bot/conservador/REGLA.md. Parametros: bot/conservador/config.json (no usa bot/config.json). Las candidatas son las
mismas cajas de temperatura que el bot real; todo lo demas es maker.Maker en modo papel con archivos en
bot/conservador/. Reusa el bucle y las fotos diarias de bot/quietos.py.

Uso: python bot/conservador.py una | bucle | resumen
"""
import os
import sys
import time
from datetime import datetime, timezone

CARPETA_BOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA_BOT)
import maker  # noqa: E402
import mercado  # noqa: E402
import quietos  # noqa: E402
from polybot import cargar_cfg, log  # noqa: E402

CARPETA = os.path.join(CARPETA_BOT, "conservador")
F_CFG = os.path.join(CARPETA, "config.json")
F_FOTOS = os.path.join(CARPETA, "fotos_dia.json")


def armar(cfg=None, m=mercado):
    cfg = cfg or cargar_cfg(F_CFG)
    assert cfg["maker"]["modo"] == "papel", "este bot es solo de papel"
    bot = maker.Maker(cfg, m=m, carpeta=CARPETA)
    bot.f_cfg = F_CFG
    bot.avisar = lambda t: None                       # nada al celular de Agus
    return bot


def main():
    que = sys.argv[1] if len(sys.argv) > 1 else "una"
    bot = armar()
    if que == "resumen":
        bot.resumen()
        return
    if que == "una":
        quietos.ciclo(bot, ruta_fotos=F_FOTOS)
        bot.resumen()
        return
    if que == "bucle":
        k = bot.cfg["maker"]
        log(f"bot conservador (papel) arranca: {k['cajas']} cajas, {k['acciones_min']} acciones, tope {k['max_inventario_lado']}")
        try:
            while True:
                t0 = time.time()
                motivo = quietos.ciclo(bot, ruta_fotos=F_FOTOS)
                if motivo and ("freno activo" in motivo or motivo in ("perdida total", "errores seguidos")
                               or motivo.startswith("fecha")):
                    break
                if bot.toca_resumen(datetime.now(timezone.utc)):
                    bot.resumen()
                time.sleep(max(k["ciclo_seg"] - (time.time() - t0), 5))
        except KeyboardInterrupt:
            log("corte pedido (fin del tramo)")
        finally:
            bot.resumen()
            bot.ej.cancelar_todo()
            bot._guardar()


if __name__ == "__main__":
    main()

"""
BOT de Polymarket (esqueleto). Corre una estrategia de estrategias.py en modo papel (libro real, sin plata)
o real (billetera propia, solo desde un servidor fuera de los paises bloqueados). Ver bot/LEEME.md.

Uso:
  python bot/polybot.py una        una pasada: busca senales, opera si toca, liquida lo resuelto
  python bot/polybot.py bucle      se queda corriendo: una pasada por hora en el minuto objetivo (servidor)
  python bot/polybot.py resumen    ganancia, ops y limites (tambien se escribe en bot/resumen_<modo>.md)
  python bot/polybot.py probar-aviso   manda un aviso de prueba al celular (BOT_NTFY_TEMA)

Frenos (cualquiera para todo): archivo bot/PARAR (manual, cualquier modo), bot/PARAR_<modo> (lo crea un freno
automatico), fecha `apagar_despues_de`, perdida total, errores seguidos.
Archivos: bot/ops_<modo>.csv (cada intento, se llene o no), bot/estado_<modo>.json, bot/resumen_<modo>.md
"""
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA)
import ejecutor  # noqa: E402
import mercado  # noqa: E402
from estrategias import ESTRATEGIAS  # noqa: E402

F_PARAR = os.path.join(CARPETA, "PARAR")
COLS = ["momento_utc", "modo", "estrategia", "activo", "evento", "condition_id", "lado", "acciones", "precio_visto",
        "precio_max", "precio", "tasa", "min_al_cierre", "lleno", "ms", "detalle"]


def log(t):
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}Z {t}", flush=True)


def avisar(texto):
    """Aviso al celular por ntfy.sh (app gratis, sin cuenta). Solo si BOT_NTFY_TEMA esta definido; nunca frena el bot."""
    tema = os.environ.get("BOT_NTFY_TEMA")
    if not tema:
        return
    try:
        mercado.S.post(f"https://ntfy.sh/{tema}", data=texto.encode("utf-8"), timeout=10)
    except Exception as ex:
        log(f"no se pudo avisar: {ex!r}")


def cargar_cfg(ruta=None):
    with open(ruta or os.path.join(CARPETA, "config.json"), encoding="utf-8") as f:
        return json.load(f)


class Bot:
    def __init__(self, cfg, m=mercado, carpeta=CARPETA):
        self.cfg, self.m, self.carpeta = cfg, m, carpeta
        self.modo = cfg["modo"]
        self.f_ops = os.path.join(carpeta, f"ops_{self.modo}.csv")
        self.f_est = os.path.join(carpeta, f"estado_{self.modo}.json")
        self.f_res = os.path.join(carpeta, f"resumen_{self.modo}.md")
        self.f_parar = os.path.join(carpeta, "PARAR")                     # el boton manual (frena cualquier modo)
        self.f_parar_auto = os.path.join(carpeta, f"PARAR_{self.modo}")   # el que crea un freno automatico
        self.est = self._cargar()
        self.ej = None                      # se crea en la primera senal (en real conecta y chequea el pais)

    # ---------- archivos ----------
    def _cargar(self):
        try:
            with open(self.f_est, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"ganadoras": {}, "errores_seguidos": 0}

    def _guardar(self):
        with open(self.f_est + ".tmp", "w", encoding="utf-8") as f:
            json.dump(self.est, f, indent=0)
        os.replace(self.f_est + ".tmp", self.f_est)

    def ops(self):
        if not os.path.exists(self.f_ops):
            return []
        with open(self.f_ops, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter=";"))

    def _anotar(self, fila):
        nuevo = not os.path.exists(self.f_ops)
        with open(self.f_ops, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            if nuevo:
                w.writerow(COLS)
            w.writerow([fila.get(c, "") for c in COLS])

    # ---------- cuentas ----------
    @staticmethod
    def costo(acciones, precio, tasa):
        return acciones * precio + acciones * tasa * precio * (1 - precio)

    def resultado(self, o):
        """Ganancia neta de una op llenada (None si no resolvio todavia)."""
        g = self.est["ganadoras"].get(o["condition_id"])
        if g is None:
            return None
        q, p, t = float(o["acciones"]), float(o["precio"]), float(o["tasa"])
        return (q if g == o["lado"] else 0.0) - self.costo(q, p, t)

    def llenas(self):
        return [o for o in self.ops() if o["lleno"] == "1"]

    def pnl(self, dia=None):
        return sum(r for o in self.llenas() if (dia is None or o["momento_utc"][:10] == dia)
                   and (r := self.resultado(o)) is not None)

    def exposicion(self):
        return sum(self.costo(float(o["acciones"]), float(o["precio"]), float(o["tasa"]))
                   for o in self.llenas() if self.resultado(o) is None)

    # ---------- frenos ----------
    def parar(self, motivo):
        with open(self.f_parar_auto, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z {motivo}\n")
        log(f"FRENO: {motivo} (para volver a arrancar, borrar bot/PARAR_{self.modo})")
        avisar(f"Bot ({self.modo}) FRENADO: {motivo}. Para volver a arrancar, borrar bot/PARAR_{self.modo}.")

    def frenado(self):
        """Texto del freno activo (manual o automatico) o None."""
        for f in (self.f_parar, self.f_parar_auto):
            if os.path.exists(f):
                with open(f, encoding="utf-8", errors="replace") as x:
                    return f"{os.path.basename(f)}: {x.read().strip()}"
        return None

    def freno_general(self, ahora):
        """Motivo para no operar nada (o None)."""
        r = self.cfg["riesgo"]
        if self.frenado():
            return f"freno activo ({self.frenado()})"
        if ahora.strftime("%Y-%m-%d %H:%M") > self.cfg["apagar_despues_de"]:
            return f"fecha de apagado {self.cfg['apagar_despues_de']}"
        if self.pnl() <= -r["max_perdida_total"]:
            self.parar(f"perdida total {self.pnl():.2f} llego al tope {r['max_perdida_total']}")
            return "perdida total"
        if self.est.get("errores_seguidos", 0) >= r["max_errores_seguidos"]:
            self.parar(f"{self.est['errores_seguidos']} errores seguidos")
            return "errores seguidos"
        return None

    def freno_senal(self, s, ahora):
        r = self.cfg["riesgo"]
        dia = ahora.strftime("%Y-%m-%d")
        costo = self.costo(s["acciones"], s["precio_max"], s["tasa"])
        if costo > r["max_usd_por_op"]:
            return f"costo {costo:.2f} > max por op {r['max_usd_por_op']}"
        llenas = self.llenas()
        if any(o["condition_id"] == s["condition_id"] for o in llenas):
            return "ya hay una op en este mercado"
        if sum(o["momento_utc"][:10] == dia for o in llenas) >= r["max_ops_por_dia"]:
            return "tope de ops del dia"
        if self.pnl(dia) <= -r["max_perdida_dia"]:
            if self.est.get("aviso_dia") != dia:
                self.est["aviso_dia"] = dia
                avisar(f"Bot ({self.modo}): perdió {self.pnl(dia):.2f} hoy, no opera más hasta mañana (UTC).")
            return f"perdida del dia {self.pnl(dia):.2f} en el tope"
        if self.exposicion() + costo > r["max_exposicion_abierta"]:
            return f"exposicion abierta {self.exposicion():.2f} + {costo:.2f} > {r['max_exposicion_abierta']}"
        return None

    # ---------- una pasada ----------
    def pasada(self, ahora=None):
        ahora = ahora or datetime.now(timezone.utc)
        self.liquidar()
        motivo = self.freno_general(ahora)
        if motivo:
            log(f"no opera: {motivo}")
            return []
        try:
            senales = ESTRATEGIAS[self.cfg["estrategia"]](self.cfg, ahora, self.m)
            self.est["errores_seguidos"] = 0
        except Exception as ex:                          # red caida, API cambiada...
            self.est["errores_seguidos"] = self.est.get("errores_seguidos", 0) + 1
            self._guardar()
            log(f"error buscando senales: {ex!r}")
            return []
        hechas = []
        for s in senales:
            motivo = self.freno_senal(s, ahora)
            fila = dict(s, momento_utc=ahora.strftime("%Y-%m-%d %H:%M:%S"), modo=self.modo,
                        estrategia=self.cfg["estrategia"], lleno=0)
            if motivo:
                fila["detalle"] = f"frenada: {motivo}"
            else:
                t0 = time.time()
                try:
                    self.ej = self.ej or ejecutor.crear(self.modo, self.m)
                    r = self.ej.comprar(s)
                except SystemExit:
                    raise
                except Exception as ex:
                    self.est["errores_seguidos"] = self.est.get("errores_seguidos", 0) + 1
                    r = {"lleno": False, "precio": None, "detalle": f"error: {ex!r}"}
                fila.update(lleno=int(r["lleno"]), precio=r["precio"] or "", detalle=r["detalle"],
                            acciones=r.get("acciones", s["acciones"]), ms=int(1000 * (time.time() - t0)))
                if r["lleno"] and self.modo == "real":
                    avisar(f"Compra real: {fila['activo']} {fila['lado']} {fila['acciones']} acc a {fila['precio']}")
            self._anotar(fila)
            log(f"{fila['activo']} {fila['lado']} visto {s['precio_visto']} -> {fila['detalle']}")
            hechas.append(fila)
        self._guardar()
        return hechas

    def liquidar(self):
        gan = self.est["ganadoras"]
        for cid in {o["condition_id"] for o in self.llenas() if o["condition_id"] not in gan}:
            try:
                g = self.m.ganador(cid)
            except Exception:
                continue
            if g is not None:
                gan[cid] = g
        # en real, cobrar las ganadoras (en papel no hace nada)
        cobradas = self.est.setdefault("cobradas", [])
        for o in self.llenas():
            cid = o["condition_id"]
            if gan.get(cid) == o["lado"] and cid not in cobradas and self.modo == "real":
                try:
                    self.ej = self.ej or ejecutor.crear(self.modo, self.m)
                    self.ej.cobrar(cid)
                    cobradas.append(cid)
                except SystemExit:
                    raise
                except Exception as ex:
                    log(f"no se pudo cobrar {cid}: {ex!r} (se reintenta en la proxima pasada)")
        self._guardar()

    def resumen(self):
        ops, llenas = self.ops(), self.llenas()
        liq = [(o, r) for o in llenas if (r := self.resultado(o)) is not None]
        puesto = sum(self.costo(float(o["acciones"]), float(o["precio"]), float(o["tasa"])) for o, _ in liq)
        neto = sum(r for _, r in liq)
        lin = [f"# Bot ({self.modo}, estrategia {self.cfg['estrategia']}) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z", "",
               f"- Intentos: {len(ops)}; llenadas: {len(llenas)}; resueltas: {len(liq)} "
               f"({sum(r > 0 for _, r in liq)} ganadas).",
               f"- Neto con comisión: US$ {neto:+.2f} sobre US$ {puesto:.2f} puestos "
               f"(ROI {100 * neto / puesto if puesto else 0:+.1f} %). Abierto ahora: US$ {self.exposicion():.2f}.",
               f"- Frenadas por riesgo: {sum(o['detalle'].startswith('frenada') for o in ops)}; "
               f"sin llenar (el libro se movió): {sum(o['lleno'] == '0' and not o['detalle'].startswith('frenada') for o in ops)}.",
               f"- Freno general: {'ACTIVO — ' + self.frenado() if self.frenado() else 'no'}."]
        with open(self.f_res, "w", encoding="utf-8") as f:
            f.write("\n".join(lin) + "\n")
        print("\n".join(lin))


def esperar_hasta(minuto):
    """Duerme hasta el proximo minuto `minuto`:05 de alguna hora. En tramos de 30 s, para no pasarse si la PC
    se suspende y vuelve."""
    ahora = datetime.now(timezone.utc)
    obj = ahora.replace(minute=minuto, second=5, microsecond=0)
    if obj <= ahora:
        obj += timedelta(hours=1)
    while (falta := (obj - datetime.now(timezone.utc)).total_seconds()) > 0:
        time.sleep(min(falta, 30))


def resumen_diario(bot, ahora=None):
    """Una vez por dia (a la hora UTC `resumen_diario_utc`) manda al celular como fue el dia anterior y el total."""
    ahora = ahora or datetime.now(timezone.utc)
    hora = bot.cfg.get("resumen_diario_utc", 3)
    if ahora.hour < hora or bot.est.get("resumen_enviado") == ahora.strftime("%Y-%m-%d"):
        return None
    ayer = (ahora - timedelta(days=1)).strftime("%Y-%m-%d")
    ops = [o for o in bot.llenas() if o["momento_utc"][:10] == ayer]
    txt = (f"Bot ({bot.modo}) {ayer}: {len(ops)} ops, neto US$ {bot.pnl(ayer):+.2f}. "
           f"Total US$ {bot.pnl():+.2f}, abierto US$ {bot.exposicion():.2f}.")
    bot.est["resumen_enviado"] = ahora.strftime("%Y-%m-%d")
    bot._guardar()
    avisar(txt)
    return txt


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "una"
    cfg = cargar_cfg()
    bot = Bot(cfg)
    log(f"modo {cfg['modo']}, estrategia {cfg['estrategia']}")
    if cmd == "resumen":
        bot.resumen()
    elif cmd == "una":
        bot.pasada()
        bot.resumen()
    elif cmd == "probar-aviso":
        avisar(f"Prueba del bot ({cfg['modo']}): si ves esto, los avisos andan.")
    elif cmd == "bucle":
        minuto = cfg[cfg["estrategia"]]["minuto_objetivo"]
        avisar(f"Bot ({cfg['modo']}) arrancó.")
        while True:
            esperar_hasta(minuto)
            try:
                bot.est = bot._cargar()
                bot.pasada()
                bot.resumen()
                resumen_diario(bot)
            except SystemExit:
                raise
            except Exception as ex:                  # nunca se cae el bucle; los frenos cuentan los errores
                log(f"error inesperado: {ex!r}")
                bot.est["errores_seguidos"] = bot.est.get("errores_seguidos", 0) + 1
                bot._guardar()
            if bot.frenado() or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M") > cfg["apagar_despues_de"]:
                log("bot apagado")
                avisar(f"Bot ({cfg['modo']}) apagado.")
                break
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()

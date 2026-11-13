"""
BOT DE PAPEL "MERCADOS QUIETOS" (13-nov-2026, pedido de Agus): el mismo bot maker de clima (bot/maker.py, sin tocarlo)
cotizando en PAPEL mercados de Polymarket que NO son de clima, pagan recompensa de liquidez y se mueven poco.
Reglas fijas y veredicto: bot/quietos/REGLA.md. Parametros: bot/quietos/config.json (no usa bot/config.json).

Lo unico que cambia respecto del maker es de donde salen las cajas candidatas: en vez de los eventos de temperatura,
un "censo" que cada hora lee todos los mercados con recompensa (CLOB /sampling-markets), deja los que cumplen la regla
(no clima, minimo <= 50 acciones, medio 0,25-0,75, cierre en > 24 h) y que estuvieron quietos en las ultimas 24 h, y
le ofrece al bot los 60 con mas recompensa esperada. Todo lo demas (ordenes, llenado prudente, filtros, rotacion,
frenos, resumen) es maker.Maker en modo papel, con sus archivos en bot/quietos/.

Uso: python bot/quietos.py una | bucle | resumen | censo (solo el censo, imprime los quietos)
Archivos (bot/quietos/): maker_ops_papel.csv, maker_estado_papel.json, maker_resumen_papel.md, censo_quietos.csv,
fotos_dia.json (como iba la cuenta al final de cada dia de Uruguay, para el veredicto).
"""
import csv
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

CARPETA_BOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA_BOT)
import maker  # noqa: E402
import mercado  # noqa: E402
from polybot import cargar_cfg, log  # noqa: E402

CARPETA = os.path.join(CARPETA_BOT, "quietos")
F_CFG = os.path.join(CARPETA, "config.json")
F_CENSO = os.path.join(CARPETA, "censo_quietos.csv")
F_FOTOS = os.path.join(CARPETA, "fotos_dia.json")


def leer_sampling(m=mercado):
    """Todos los mercados que pagan recompensa de liquidez (CLOB /sampling-markets, paginas de 1000)."""
    out, cursor = [], None
    for _ in range(60):
        d = m.S.get(f"{mercado.CLOB}/sampling-markets", params={"next_cursor": cursor} if cursor else {}, timeout=30).json()
        out += d.get("data") or []
        cursor = d.get("next_cursor")
        if not cursor or cursor == "LTE=":
            break
    return out


def a_caja(mk, ahora):
    """Mercado del CLOB -> caja con los campos que usa maker.Maker. None si no paga recompensa o le faltan datos."""
    r = mk.get("rewards") or {}
    pozo = sum((x.get("rewards_daily_rate") or 0) for x in (r.get("rates") or []))
    v = (r.get("max_spread") or 0) / 100
    toks = mk.get("tokens") or []
    if pozo <= 0 or v <= 0 or len(toks) != 2 or not mk.get("condition_id") or not mk.get("end_date_iso"):
        return None
    try:
        horas = (datetime.fromisoformat(mk["end_date_iso"].replace("Z", "+00:00")) - ahora).total_seconds() / 3600
    except ValueError:
        return None
    si = next((t for t in toks if str(t.get("outcome", "")).lower() == "yes"), toks[0])
    no = next(t for t in toks if t is not si)
    return {"evento": mk.get("market_slug") or "", "caja": mk.get("question") or mk["condition_id"][:10],
            "cid": mk["condition_id"], "si": si["token_id"], "no": no["token_id"], "pozo": pozo, "v": v,
            "tam_min": r.get("min_size") or 0, "tick": float(mk.get("minimum_tick_size") or 0.01),
            "horas": round(horas, 1), "fin": mk["end_date_iso"], "precio": float(si.get("price") or 0),
            "etiquetas": mk.get("tags") or [], "partido": mk.get("game_start_time") is not None,
            "abierto": bool(mk.get("accepting_orders")) and not mk.get("closed")}


def cumple_base(c, cfg):
    """Regla de entrada sin el historial: abierto, no clima, no partido, minimo chico, cierre lejos, medio en rango."""
    k, q = cfg["maker"], cfg["quietos"]
    return (c["abierto"] and not c["partido"] and not set(c["etiquetas"]) & set(q["etiquetas_fuera"])
            and c["tam_min"] <= q["tam_min_max"] and c["horas"] >= k["horas_min_fin"]
            and q["medio_min"] <= c["precio"] <= q["medio_max"])


def quietud(c, ahora, m=mercado):
    """(rango 24 h, movimiento medio en 1 h, puntos) con el historial publico del CLOB, un punto cada 10 min."""
    t = int(ahora.timestamp())
    h = m.S.get(f"{mercado.CLOB}/prices-history", params={"market": c["si"], "startTs": t - 86400, "endTs": t,
                                                         "fidelity": 10}, timeout=20).json()
    p = [float(x["p"]) for x in (h.get("history") or [])]
    if len(p) < 7:
        return None, None, len(p)
    saltos = [abs(p[i] - p[i - 6]) for i in range(6, len(p))]       # 6 puntos de 10 min = 1 hora
    return round(max(p) - min(p), 4), round(statistics.mean(saltos), 4), len(p)


def es_quieta(c, cfg):
    q = cfg["quietos"]
    return (c.get("rango24") is not None and c["puntos"] >= q["puntos_min"]
            and c["rango24"] <= q["rango24_max"] + 1e-9 and c["mov1h"] <= q["mov1h_max"] + 1e-9)


class Censo:
    """Lista de cajas quietas que se le ofrecen al bot. Se rehace cada `censo_cada_min` (60)."""

    def __init__(self, cfg, m=mercado):
        self.cfg, self.m = cfg, m
        self.ts = 0
        self.ofrecidas = []          # cajas quietas, mejores primero
        self.todas = {}              # cid -> caja (todos los mercados con recompensa, para las cajas que ya tenemos)

    def vencido(self, ahora):
        return ahora.timestamp() - self.ts >= 60 * self.cfg["quietos"]["censo_cada_min"]

    def actualizar(self, ahora):
        t0 = time.time()
        q = self.cfg["quietos"]
        cajas = [c for c in (a_caja(mk, ahora) for mk in leer_sampling(self.m)) if c]
        self.todas = {c["cid"]: c for c in cajas}
        base = [c for c in cajas if cumple_base(c, self.cfg)]

        def medir(c):
            try:
                c["rango24"], c["mov1h"], c["puntos"] = quietud(c, ahora, self.m)
                if not es_quieta(c, self.cfg):
                    return None
                ok = maker.medir_libro(c, self.cfg, self.m)
                return c if ok and q["medio_min"] <= c["medio"] <= q["medio_max"] else None
            except Exception:            # noqa: BLE001  (un mercado que no contesta queda afuera esta hora)
                return None

        with ThreadPoolExecutor(max_workers=q.get("hilos", 8)) as ex:
            quietas = [c for c in ex.map(medir, base) if c]
        quietas.sort(key=lambda c: -c["rec_pes"])
        self.ofrecidas = quietas[:q["ofrecer"]]
        self.ts = ahora.timestamp()
        log(f"censo: {len(cajas)} mercados con recompensa, {len(base)} cumplen la regla base, {len(quietas)} quietos; "
            f"se ofrecen {len(self.ofrecidas)} ({time.time() - t0:.0f} s)")
        self.guardar(ahora, len(cajas), len(base), len(quietas))

    def guardar(self, ahora, n_todas, n_base, n_quietas):
        cols = ["censo_utc", "pregunta", "evento", "cid", "medio", "spread", "pozo", "v", "tam_min", "comp", "rec_pes",
                "rango24", "mov1h", "dias_al_cierre"]
        with open(F_CENSO, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(cols)
            w.writerow([ahora.strftime("%Y-%m-%d %H:%M"), f"(totales: {n_todas} con recompensa, {n_base} regla base, "
                        f"{n_quietas} quietos)"] + [""] * (len(cols) - 2))
            for c in self.ofrecidas:
                w.writerow([ahora.strftime("%Y-%m-%d %H:%M"), c["caja"], c["evento"], c["cid"], c["medio"], c["spread"],
                            c["pozo"], c["v"], c["tam_min"], c["comp"], c["rec_pes"], c["rango24"], c["mov1h"],
                            round(c["horas"] / 24, 1)])

    def candidatas(self, ahora, actuales):
        """Lo que recibe maker.Maker.elegir: las quietas ofrecidas y, ademas, las cajas que el bot ya cotiza mientras
        sigan pagando recompensa y cierren en mas de 24 h (desde ahi las cuidan los filtros del bot)."""
        if self.vencido(ahora):
            self.actualizar(ahora)
        out = {c["cid"]: dict(c) for c in self.ofrecidas}
        for cid in actuales:
            c = self.todas.get(cid)
            if cid not in out and c and c["abierto"]:
                horas = (datetime.fromisoformat(c["fin"].replace("Z", "+00:00")) - ahora).total_seconds() / 3600
                if horas >= self.cfg["maker"]["horas_min_fin"]:
                    out[cid] = dict(c, horas=round(horas, 1))
        for c in out.values():
            c["horas"] = round((datetime.fromisoformat(c["fin"].replace("Z", "+00:00")) - ahora).total_seconds() / 3600, 1)
        return list(out.values())


def armar(cfg=None, m=mercado):
    """El bot: maker.Maker en papel con carpeta propia y las candidatas del censo."""
    cfg = cfg or cargar_cfg(F_CFG)
    assert cfg["maker"]["modo"] == "papel", "este bot es solo de papel"
    os.makedirs(CARPETA, exist_ok=True)
    bot = maker.Maker(cfg, m=m, carpeta=CARPETA)
    bot.f_cfg = F_CFG
    bot.avisar = lambda t: None                       # nada al celular de Agus
    censo = Censo(cfg, m)
    maker.candidatas = lambda cfg_, ahora, m_=None: censo.candidatas(ahora, list(bot.est.get("cajas", {})))
    return bot, censo


def foto_dia(bot, ahora=None):
    """Como va la cuenta (a precio de mercado) y la recompensa estimada acumulada; queda la ultima foto de cada dia de
    Uruguay. El veredicto compara la foto del 20-nov con la del 13-nov (ver REGLA.md)."""
    ahora = ahora or datetime.now(timezone.utc)
    try:
        fotos = json.load(open(F_FOTOS, encoding="utf-8"))
    except (OSError, ValueError):
        fotos = {}
    valor, costo = bot.valor_mercado()
    est = bot.est["recompensas"].get("estimada", {})
    llen = [o for o in bot.ops() if o["lado"] in ("BUY", "SELL")]
    fotos[bot.dia_local(ahora)] = {
        "momento_utc": ahora.strftime("%Y-%m-%d %H:%M"),
        "llenados_mercado": round(bot.pnl(inventario=False) + valor, 2),
        "acciones_mercado": valor, "acciones_costo": costo,
        "recompensa_estimada_acum": round(sum(est.values()), 3),
        "n_llenados": len(llen), "cajas": len(bot.est["cajas"]),
        "freno_diario_saltos": len(bot.est.get("saltos_freno_dia", [])),
        "frenado": bot.frenado()}
    with open(F_FOTOS + ".tmp", "w", encoding="utf-8") as f:
        json.dump(fotos, f, indent=1, ensure_ascii=False)
    os.replace(F_FOTOS + ".tmp", F_FOTOS)


def ciclo(bot, ahora=None):
    ahora = ahora or datetime.now(timezone.utc)
    motivo = bot.ciclo(ahora)
    if motivo and "perdida del dia" in motivo:        # cuantas veces salto el freno diario (para el veredicto)
        saltos = bot.est.setdefault("saltos_freno_dia", [])
        dia = bot.dia_local(ahora)
        if dia not in saltos:
            saltos.append(dia)
            bot._guardar()
    foto_dia(bot, ahora)
    return motivo


def main():
    que = sys.argv[1] if len(sys.argv) > 1 else "una"
    bot, censo = armar()
    if que == "censo":
        censo.actualizar(datetime.now(timezone.utc))
        for c in censo.ofrecidas:
            print(f"rec {c['rec_pes']:6.2f} | pozo {c['pozo']:6.0f} | medio {c['medio']:.3f} | spread {c['spread'] * 100:.1f} c"
                  f" | tam {c['tam_min']:.0f} | rango24 {c['rango24'] * 100:.1f} c | mov1h {c['mov1h'] * 100:.2f} c | "
                  f"{c['horas'] / 24:.0f} d | {c['caja'][:70]}")
        return
    if que == "resumen":
        bot.resumen()
        return
    if que == "una":
        ciclo(bot)
        bot.resumen()
        return
    if que == "bucle":
        log(f"bot quietos (papel) arranca: hasta {bot.cfg['maker']['cajas']} cajas, US$ {bot.cfg['maker']['capital_usd']}")
        try:
            while True:
                t0 = time.time()
                motivo = ciclo(bot)
                if motivo and ("freno activo" in motivo or motivo in ("perdida total", "errores seguidos")
                               or motivo.startswith("fecha")):
                    break
                if bot.toca_resumen(datetime.now(timezone.utc)):
                    bot.resumen()
                time.sleep(max(bot.cfg["maker"]["ciclo_seg"] - (time.time() - t0), 5))
        except KeyboardInterrupt:
            log("corte pedido (fin del tramo)")
        finally:
            bot.resumen()
            bot.ej.cancelar_todo()       # papel: al volver se ponen de nuevo
            bot._guardar()


if __name__ == "__main__":
    main()

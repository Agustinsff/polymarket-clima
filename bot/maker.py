"""
BOT MAKER (prueba real chica, 3-nov-2026): deja ordenes de compra de los dos lados (Si y No) a `distancia` del
precio medio en unas pocas cajas de temperatura con libro apretado, para cobrar las recompensas de liquidez de
Polymarket. Regla y numeros que lo justifican: maker/REGLA.md y maker/informe_datos.md (rama medidor-maker).

Que hace cada ciclo (60 s):
  1. frenos (bot/PARAR, bot/PARAR_maker_<modo>, fecha, perdida del dia / total, errores seguidos)
  2. cobra las cajas resueltas (en real: redeem) y anota el resultado
  3. elige las cajas: temperatura, con pozo, spread del libro <= spread_max, precio 3-97 c, evento que termina en
     >= horas_min_fin; las ordena por recompensa esperada "pesimista" (los rivales nos copian) y se queda con
     `cajas` (no cambia de caja mientras siga sirviendo, para no perder el lugar en la fila)
  4. en cada caja pone/renueva dos ordenes post-only: comprar Si a medio - d y comprar No a 1 - medio - d
     (= vender Si a medio + d). Si ya tenemos acciones de un lado, vende esas en vez de comprar el otro lado,
     asi el capital no crece. Solo renueva si el medio se movio >= 1 tick (si no, deja la orden en la fila).
  5. anota los llenados, la recompensa cobrada (real: lo que informa Polymarket; papel: la formula) y el resumen
  Al salir por cualquier motivo cancela TODAS las ordenes.

Modos: papel (libro real, llenado prudente como el medidor: solo si alguien opero a peor precio) y real (SDK
oficial, post-only GTC). Uso:
  python bot/maker.py bucle | una | resumen | probar-aviso
Archivos: bot/maker_ops_<modo>.csv, bot/maker_estado_<modo>.json, bot/maker_resumen_<modo>.md
"""
import csv
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARPETA)
import mercado  # noqa: E402
from polybot import avisar, cargar_cfg, log  # noqa: E402

GAMMA = "https://gamma-api.polymarket.com/events"
DATA = "https://data-api.polymarket.com"
COLS = ["momento_utc", "modo", "evento", "caja", "condition_id", "token", "lado", "precio", "acciones", "medio",
        "detalle"]


def puntaje(v, s):
    return ((v - s) / v) ** 2 if 0 <= s < v else 0.0


def redondear(p, tick, abajo):
    k = p / tick
    k = math.floor(k + 1e-9) if abajo else math.ceil(k - 1e-9)
    return round(k * tick, 4)


# ---------------------------------------------------------------------------
# cajas candidatas (datos publicos)
# ---------------------------------------------------------------------------

def eventos_temperatura(m=mercado):
    out = []
    for off in range(0, 2000, 100):
        r = m.S.get(GAMMA, params={"tag_slug": "daily-temperature", "closed": "false", "limit": 100, "offset": off},
                    timeout=30).json()
        out += r
        if len(r) < 100:
            break
    return out


def candidatas(cfg, ahora, m=mercado):
    """Cajas de temperatura que cumplen la regla, con su libro y la recompensa esperada pesimista."""
    c = cfg["maker"]
    out = []
    for e in eventos_temperatura(m):
        if not e.get("endDate"):
            continue
        horas = (datetime.fromisoformat(e["endDate"].replace("Z", "+00:00")) - ahora).total_seconds() / 3600
        if horas < c["horas_min_fin"]:
            continue
        for mk in e.get("markets", []):
            if mk.get("closed") or not mk.get("clobTokenIds") or not mk.get("conditionId"):
                continue
            pozo = sum((x.get("rewardsDailyRate") or 0) for x in (mk.get("clobRewards") or []))
            v = (mk.get("rewardsMaxSpread") or 0) / 100
            if pozo <= 0 or v <= 0:
                continue
            toks = json.loads(mk["clobTokenIds"])
            out.append({"evento": e["slug"], "caja": mk.get("groupItemTitle") or mk["question"], "cid": mk["conditionId"],
                        "si": toks[0], "no": toks[1], "pozo": pozo, "v": v, "tam_min": mk.get("rewardsMinSize") or 0,
                        "tick": float(mk.get("orderPriceMinTickSize") or 0.01), "horas": round(horas, 1), "fin": e["endDate"]})
    return out


def medir_libro(c, cfg, m=mercado):
    """Completa la caja con medio, spread, competencia y recompensa esperada. False si no cumple la regla."""
    k = cfg["maker"]
    bids, asks = m.libro(c["si"])
    if not bids or not asks:
        return False
    medio = (bids[0][0] + asks[0][0]) / 2
    spread = asks[0][0] - bids[0][0]
    tam = max(k["acciones_min"], c["tam_min"])
    q1 = sum(puntaje(c["v"], medio - p) * t for p, t in bids if t >= c["tam_min"])
    q2 = sum(puntaje(c["v"], p - medio) * t for p, t in asks if t >= c["tam_min"])
    comp = max(min(q1, q2), max(q1, q2) / 3) if 0.10 <= medio <= 0.90 else min(q1, q2)
    d = k["distancia"]
    nuestro = puntaje(c["v"], d) * tam          # los dos lados a la misma distancia: Q_min = un lado
    c.update(medio=round(medio, 4), spread=round(spread, 4), bid=bids[0][0], ask=asks[0][0], tam=tam, comp=round(comp, 1),
             rec_pes=round(c["pozo"] * nuestro / (2 * nuestro + comp), 3) if nuestro > 0 else 0.0)
    return 0.03 <= medio <= 0.97 and spread <= k["spread_max"] + 1e-9


# ---------------------------------------------------------------------------
# ejecutores: papel (simulado con llenado prudente) y real (SDK oficial)
# ---------------------------------------------------------------------------

class Papel:
    """Ordenes simuladas. Un llenado se cuenta solo si, desde que se puso la orden, alguien opero como taker a un
    precio estrictamente peor que el nuestro (misma cuenta prudente que maker/medir.py)."""
    nombre = "papel"

    def __init__(self, m, est):
        self.m, self.est = m, est
        est.setdefault("ordenes", {})      # id -> {token, cid, lado, precio, acciones, desde, yes}
        est.setdefault("inventario", {})   # token -> acciones
        self.n = est.get("n_ordenes", 0)

    def colocar(self, token, cid, lado, precio, acciones, es_si):
        self.n += 1
        self.est["n_ordenes"] = self.n
        oid = f"papel-{self.n}"
        self.est["ordenes"][oid] = {"token": token, "cid": cid, "lado": lado, "precio": precio, "acciones": acciones,
                                    "desde": int(time.time()), "si": es_si}
        return oid

    def cancelar(self, ids):
        for i in ids:
            self.est["ordenes"].pop(i, None)

    def cancelar_todo(self):
        self.est["ordenes"].clear()

    def abiertas(self):
        return [dict(o, id=i) for i, o in self.est["ordenes"].items()]

    def llenados(self):
        """Revisa las operaciones taker desde que se puso cada orden. Devuelve [(orden, acciones, precio_taker)]."""
        out = []
        por_cid = {}
        for oid, o in list(self.est["ordenes"].items()):
            if o["cid"] not in por_cid:
                try:
                    r = self.m.S.get(f"{DATA}/trades", params={"market": o["cid"], "limit": 100, "takerOnly": "true"},
                                     timeout=30).json()
                    if not isinstance(r, list):      # a veces devuelve un dict de error
                        r = None
                except Exception:
                    r = None
                por_cid[o["cid"]] = r
            tr = por_cid[o["cid"]]
            if not tr:
                continue
            # en terminos del token de la orden: un taker que VENDE ese token mas barato que nuestra compra nos llena
            # (o que COMPRA mas caro que nuestra venta)
            resto = o["acciones"]
            ultimo = o["desde"]
            for t in sorted(tr, key=lambda x: int(x.get("timestamp") or 0)):
                ts = int(t.get("timestamp") or 0)
                if ts <= o["desde"] or resto <= 0:
                    continue
                ultimo = max(ultimo, ts)
                p, q, lado = float(t["price"]), float(t["size"]), t["side"]
                mismo_token = (t.get("outcomeIndex") == 0) == o["si"]
                if not mismo_token:              # paso a nuestro token: comprar el otro a p = vender este a 1-p
                    p, lado = 1 - p, ("SELL" if lado == "BUY" else "BUY")
                if o["lado"] == "BUY" and lado == "SELL" and p < o["precio"] - 1e-9:
                    pass
                elif o["lado"] == "SELL" and lado == "BUY" and p > o["precio"] + 1e-9:
                    pass
                else:
                    continue
                x = min(resto, q)
                resto -= x
                out.append((dict(o, id=oid), x, p))
            o["desde"] = ultimo                  # no volver a contar las mismas operaciones
            if resto < o["acciones"]:
                if resto <= 0:
                    self.est["ordenes"].pop(oid, None)
                else:
                    o["acciones"] = resto
                inv = self.est["inventario"]
                lleno = sum(x for oo, x, _ in out if oo["id"] == oid)
                inv[o["token"]] = round(inv.get(o["token"], 0) + (lleno if o["lado"] == "BUY" else -lleno), 2)
        return out

    def inventario(self):
        return {t: q for t, q in self.est["inventario"].items() if q > 1e-6}

    def cobrar(self, cid, tokens, ganador):
        inv = self.est["inventario"]
        cobrado = 0.0
        for i, t in enumerate(tokens):
            q = inv.pop(t, 0)
            if ganador == i:
                cobrado += q
        return cobrado

    def recompensa_dia(self, fecha):
        return None   # en papel se estima con la formula (ver Maker.resumen)


class Real:
    """SDK oficial polymarket-client 0.14.0 (verificado contra el codigo del SDK, sin plata):
    place_limit_order(token_id, price, size, side, post_only=True) -> AcceptedOrder(order_id, status) | RejectedOrder;
    cancel_orders(order_ids) / cancel_all(); list_open_orders() -> OpenOrder(id, asset_id, side, price, original_size,
    size_matched); list_positions() -> Position(asset_id, condition_id, current_size, redeemable);
    get_total_earnings_for_user_for_day(date) -> earnings; redeem_positions(condition_id).wait()."""
    nombre = "real"

    def __init__(self, m, est):
        if os.environ.get("BOT_REAL_CONFIRMO") != "si":
            raise SystemExit("modo real: falta BOT_REAL_CONFIRMO=si en el entorno")
        if not os.environ.get("POLYMARKET_PRIVATE_KEY"):
            raise SystemExit("modo real: falta POLYMARKET_PRIVATE_KEY en el entorno")
        geo = m.geobloqueo()
        if geo.get("blocked") is not False:
            raise SystemExit(f"modo real: Polymarket bloquea operar desde aca ({geo.get('country')}, {geo.get('region')})")
        from polymarket import SecureClient
        self.client = SecureClient.create(private_key=os.environ["POLYMARKET_PRIVATE_KEY"],
                                          wallet=os.environ.get("POLYMARKET_WALLET") or None)
        self.est = est
        self.vistos = est.setdefault("llenado_visto", {})   # order_id -> size_matched ya anotado

    def colocar(self, token, cid, lado, precio, acciones, es_si):
        r = self.client.place_limit_order(token_id=token, price=str(precio), size=str(acciones), side=lado, post_only=True)
        if not r.ok:
            raise RuntimeError(f"orden rechazada ({r.code}): {r.message}")
        return r.order_id

    def cancelar(self, ids):
        if ids:
            self.client.cancel_orders(order_ids=list(ids))

    def cancelar_todo(self):
        self.client.cancel_all()

    @staticmethod
    def _items(r):
        """El SDK devuelve un Paginator (iter_items) en list_open_orders/list_positions; acepta tambien listas."""
        return list(r.iter_items()) if hasattr(r, "iter_items") else list(r)

    def abiertas(self):
        return [{"id": o.id, "token": o.asset_id, "cid": o.condition_id, "lado": o.side, "precio": float(o.price),
                 "acciones": float(o.original_size) - float(o.size_matched), "llenado": float(o.size_matched)}
                for o in self._items(self.client.list_open_orders())]

    def llenados(self):
        """Compara lo llenado de cada orden abierta con lo ya anotado. Las ordenes que se llenaron del todo
        desaparecen de la lista: se detectan por el inventario (list_positions) en Maker.revisar_inventario."""
        out = []
        for o in self.abiertas():
            nuevo = o["llenado"] - self.vistos.get(o["id"], 0)
            if nuevo > 1e-6:
                self.vistos[o["id"]] = o["llenado"]
                out.append((o, nuevo, o["precio"]))
        return out

    def inventario(self):
        """Posiciones de la cuenta (data-api). Se consulta una vez por ciclo como mucho (cache de 45 s): el bot la
        pide 3-4 veces por ciclo y data-api limita las consultas (RateLimitError el 7-nov en real). Si Polymarket
        frena la consulta y hay una copia reciente (< 10 min), se usa esa en vez de perder el ciclo."""
        t = time.time()
        if getattr(self, "_inv_cache", None) is None:
            self._inv_cache, self._inv_ts = None, 0.0
        if self._inv_cache is not None and t - self._inv_ts < 45:
            return dict(self._inv_cache)
        try:
            inv = {p.asset_id: float(p.current_size) for p in self._items(self.client.list_positions())
                   if float(p.current_size) > 1e-6}
        except Exception as ex:
            if "ratelimit" in type(ex).__name__.lower() and self._inv_cache is not None and t - self._inv_ts < 600:
                log(f"posiciones: limite de consultas, uso la copia de hace {int(t - self._inv_ts)} s")
                return dict(self._inv_cache)
            raise
        self._inv_cache, self._inv_ts = inv, t
        return dict(inv)

    def cobrar(self, cid, tokens, ganador):
        inv = self.inventario()
        q = inv.get(tokens[ganador], 0)
        self.client.redeem_positions(condition_id=cid).wait()
        self._inv_cache = None
        return q

    def recompensa_dia(self, fecha):
        return float(sum(float(e.earnings) for e in self.client.get_total_earnings_for_user_for_day(date=fecha)))


# ---------------------------------------------------------------------------

class Maker:
    def __init__(self, cfg, m=mercado, carpeta=CARPETA, ej=None):
        self.cfg, self.m, self.carpeta = cfg, m, carpeta
        self.modo = cfg["maker"]["modo"]
        self.f_ops = os.path.join(carpeta, f"maker_ops_{self.modo}.csv")
        self.f_est = os.path.join(carpeta, f"maker_estado_{self.modo}.json")
        self.f_res = os.path.join(carpeta, f"maker_resumen_{self.modo}.md")
        self.f_parar = os.path.join(carpeta, "PARAR")
        self.f_parar_auto = os.path.join(carpeta, f"PARAR_maker_{self.modo}")
        self.est = self._cargar()
        self.ej = ej or {"papel": Papel, "real": Real}[self.modo](m, self.est)
        # avisos al celular: siempre en real; en papel solo si la config lo pide (si no, marea)
        self.avisar = avisar if (self.modo == "real" or cfg["maker"].get("avisar_papel")) else (lambda t: None)

    # ---------- archivos ----------
    def _cargar(self):
        try:
            with open(self.f_est, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"cajas": {}, "resultados": {}, "errores_seguidos": 0, "recompensas": {}, "costo": {}}

    def _guardar(self):
        with open(self.f_est + ".tmp", "w", encoding="utf-8") as f:
            json.dump(self.est, f, indent=0)
        os.replace(self.f_est + ".tmp", self.f_est)

    def anotar(self, **fila):
        nuevo = not os.path.exists(self.f_ops)
        with open(self.f_ops, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            if nuevo:
                w.writerow(COLS)
            w.writerow([fila.get(c, "") for c in COLS])

    def ops(self):
        if not os.path.exists(self.f_ops):
            return []
        with open(self.f_ops, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter=";"))

    # ---------- cuentas ----------
    def pnl(self, dia=None):
        """Ganancia realizada: cobros de cajas resueltas menos lo pagado por las acciones (ventas cuentan como cobro)."""
        total = 0.0
        for o in self.ops():
            if o["lado"] not in ("BUY", "SELL") or (dia and o["momento_utc"][:10] != dia):
                continue
            q, p = float(o["acciones"]), float(o["precio"])
            total += -q * p if o["lado"] == "BUY" else q * p
        for cid, r in self.est["resultados"].items():
            if not dia or r.get("dia") == dia:
                total += r.get("cobrado", 0)
        return round(total, 2)

    def capital_puesto(self):
        """Plata en acciones sin resolver (al precio pagado) + plata reservada en ordenes abiertas."""
        inv = self.ej.inventario()
        costo = sum(self.est["costo"].get(t, {}).get("precio", 0.5) * q for t, q in inv.items())
        reservado = sum(o["precio"] * o["acciones"] for o in self.ej.abiertas() if o["lado"] == "BUY")
        return round(costo + reservado, 2)

    # ---------- frenos ----------
    def parar(self, motivo):
        with open(self.f_parar_auto, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z {motivo}\n")
        log(f"FRENO: {motivo}")
        self.avisar(f"Maker ({self.modo}) FRENADO: {motivo}. Ordenes canceladas. Para volver: borrar bot/PARAR_maker_{self.modo}.")

    def frenado(self):
        for f in (self.f_parar, self.f_parar_auto):
            if os.path.exists(f):
                with open(f, encoding="utf-8", errors="replace") as x:
                    return f"{os.path.basename(f)}: {x.read().strip()}"
        return None

    def freno(self, ahora):
        r = self.cfg["maker"]
        if self.frenado():
            return f"freno activo ({self.frenado()})"
        if ahora.strftime("%Y-%m-%d %H:%M") > r["apagar_despues_de"]:
            return f"fecha de apagado {r['apagar_despues_de']}"
        if self.pnl() <= -r["max_perdida_total"]:
            self.parar(f"perdida total {self.pnl():.2f} llego al tope {r['max_perdida_total']}")
            return "perdida total"
        dia = ahora.strftime("%Y-%m-%d")
        if self.pnl(dia) <= -r["max_perdida_dia"]:
            return f"perdida del dia {self.pnl(dia):.2f} en el tope (sigue manana)"
        if self.est.get("errores_seguidos", 0) >= r["max_errores_seguidos"]:
            self.parar(f"{self.est['errores_seguidos']} errores seguidos")
            return "errores seguidos"
        return None

    # ---------- eleccion de cajas ----------
    def elegir(self, ahora):
        k = self.cfg["maker"]
        cand = {c["cid"]: c for c in candidatas(self.cfg, ahora, self.m)}
        actuales = self.est["cajas"]
        # las que ya tenemos siguen mientras cumplan (con 3 c de tolerancia en el spread, para no cambiar a cada rato)
        elegidas = {}
        for cid, c in list(actuales.items()):
            cc = cand.get(cid)
            if cc and medir_libro(cc, self.cfg, self.m) or (cc and cc.get("spread", 1) <= k["spread_max"] + 0.03
                                                              and 0.03 <= cc.get("medio", 0) <= 0.97):
                elegidas[cid] = cc
            else:
                log(f"se deja la caja {c['evento']} {c['caja']}: ya no cumple la regla")
        # completar con las mejores del resto (medir solo las que no tenemos, ordenadas por pozo para no leer 1500 libros)
        if len(elegidas) < k["cajas"]:
            resto = sorted((c for cid, c in cand.items() if cid not in elegidas), key=lambda c: -c["pozo"])[:60]
            ok = [c for c in resto if medir_libro(c, self.cfg, self.m)]
            for c in sorted(ok, key=lambda c: -c["rec_pes"]):
                if len(elegidas) >= k["cajas"]:
                    break
                if c["tam"] > k["capital_usd"] / k["cajas"]:
                    continue
                elegidas[c["cid"]] = c
                log(f"caja nueva: {c['evento']} {c['caja']} (medio {c['medio']}, spread {c['spread'] * 100:.1f} c, "
                    f"pozo {c['pozo']}, rec. esperada {c['rec_pes']} US$/dia)")
        self.est["cajas"] = {cid: {k2: c[k2] for k2 in ("evento", "caja", "cid", "si", "no", "pozo", "v", "tam_min", "tick",
                                                         "fin", "medio", "spread", "tam", "rec_pes", "comp")}
                             for cid, c in elegidas.items()}
        return elegidas

    # ---------- ordenes ----------
    def cotizar(self, c, inv):
        """Las dos ordenes que queremos en la caja: [(token, lado, precio, acciones, es_si)]."""
        d, tick, tam = self.cfg["maker"]["distancia"], c["tick"], c["tam"]
        medio = c["medio"]
        si, no = inv.get(c["si"], 0), inv.get(c["no"], 0)
        ordenes = []
        # lado "comprar Si": si tenemos No, vendemos No (= comprar Si); si no, compramos Si
        p_si = redondear(medio - d, tick, True)
        if 0.01 <= p_si <= 0.99:
            if no >= tam:
                ordenes.append((c["no"], "SELL", redondear(1 - p_si, tick, False), tam, False))
            else:
                ordenes.append((c["si"], "BUY", p_si, tam, True))
        # lado "vender Si": si tenemos Si, lo vendemos; si no, compramos No
        p_no = redondear(1 - medio - d, tick, True)
        if 0.01 <= p_no <= 0.99:
            if si >= tam:
                ordenes.append((c["si"], "SELL", redondear(1 - p_no, tick, False), tam, True))
            else:
                ordenes.append((c["no"], "BUY", p_no, tam, False))
        return ordenes

    def renovar(self, elegidas):
        abiertas = self.ej.abiertas()
        inv = self.ej.inventario()
        quiero = []
        for c in elegidas.values():
            quiero += [(c["cid"], c["evento"], c["caja"], c["medio"]) + o for o in self.cotizar(c, inv)]
        # cancelar lo que no corresponde (otra caja, otro precio, otro lado) o lo que ya quedo con poco
        cancelar = []
        quedan = []
        for o in abiertas:
            igual = [q for q in quiero if q[4] == o["token"] and q[5] == o["lado"] and abs(q[6] - o["precio"]) < 1e-9
                     and o["acciones"] >= q[7] * 0.5]
            if igual:
                quedan.append(igual[0])
            else:
                cancelar.append(o["id"])
        if cancelar:
            self.ej.cancelar(cancelar)
        errores = 0
        for q in quiero:
            if q in quedan:
                continue
            cid, evento, caja, medio, token, lado, precio, tam, es_si = q
            try:
                oid = self.ej.colocar(token, cid, lado, precio, tam, es_si)
                self.anotar(momento_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), modo=self.modo,
                            evento=evento, caja=caja, condition_id=cid, token=token, lado=f"orden_{lado}", precio=precio,
                            acciones=tam, medio=medio, detalle=oid)
            except SystemExit:
                raise
            except Exception as ex:
                errores += 1
                log(f"no se pudo poner la orden {lado} {precio} en {caja}: {ex!r}")
        return errores

    def revisar_llenados(self):
        for o, q, p_taker in self.ej.llenados():
            c = self.est["cajas"].get(o["cid"], {})
            self.anotar(momento_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), modo=self.modo,
                        evento=c.get("evento", ""), caja=c.get("caja", ""), condition_id=o["cid"], token=o["token"],
                        lado=o["lado"], precio=o["precio"], acciones=round(q, 2), medio=c.get("medio", ""),
                        detalle=f"taker a {p_taker}")
            costo = self.est["costo"].setdefault(o["token"], {"precio": o["precio"], "acciones": 0})
            if o["lado"] == "BUY":
                tot = costo["acciones"] + q
                costo["precio"] = (costo["precio"] * costo["acciones"] + o["precio"] * q) / tot if tot else o["precio"]
                costo["acciones"] = tot
            else:
                costo["acciones"] = max(costo["acciones"] - q, 0)
            self.avisar(f"Maker ({self.modo}): {o['lado']} {q:.0f} acc a {o['precio']} en {c.get('caja', '?')} ({c.get('evento', '')})")
            log(f"llenado: {o['lado']} {q:.1f} a {o['precio']} en {c.get('caja', '?')}")

    def liquidar(self):
        """Cajas con inventario cuyo evento ya resolvio: cobrar y anotar."""
        inv = self.ej.inventario()
        tokens_cajas = {}
        for cid, c in self.est["cajas"].items():
            tokens_cajas[cid] = (c["si"], c["no"], c)
        for cid, (si, no, c) in list(tokens_cajas.items()):
            if cid in self.est["resultados"] or (inv.get(si, 0) <= 1e-6 and inv.get(no, 0) <= 1e-6):
                continue
            try:
                g = self.m.ganador(cid)
            except Exception:
                continue
            if g is None:
                continue
            gi = 0 if g == "Yes" else 1
            try:
                cobrado = self.ej.cobrar(cid, [si, no], gi)
            except Exception as ex:
                log(f"no se pudo cobrar {c['caja']}: {ex!r}")
                continue
            self.est["resultados"][cid] = {"dia": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "gano": g,
                                           "cobrado": round(cobrado, 2), "caja": c["caja"], "evento": c["evento"]}
            for t in (si, no):
                self.est["costo"].pop(t, None)
            self.anotar(momento_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), modo=self.modo,
                        evento=c["evento"], caja=c["caja"], condition_id=cid, lado="cobro", precio=1, acciones=round(cobrado, 2),
                        detalle=f"gano {g}")
            log(f"cobrado {cobrado:.2f} en {c['caja']} ({c['evento']}, gano {g})")
        # las cajas cuyo evento ya termino se sueltan (sin ordenes), aunque no se haya resuelto todavia
        ahora = datetime.now(timezone.utc)
        for cid, c in list(self.est["cajas"].items()):
            if datetime.fromisoformat(c["fin"].replace("Z", "+00:00")) < ahora:
                self.est["cajas"].pop(cid)

    # ---------- un ciclo ----------
    def ciclo(self, ahora=None):
        ahora = ahora or datetime.now(timezone.utc)
        try:
            self.revisar_llenados()
            self.liquidar()
            motivo = self.freno(ahora)
            if motivo:
                log(f"no opera: {motivo}")
                self.ej.cancelar_todo()
                self._guardar()
                return motivo
            elegidas = self.elegir(ahora)
            errores = self.renovar(elegidas)
            self.est["errores_seguidos"] = self.est.get("errores_seguidos", 0) + errores if errores else 0
            self.est["ultimo_ciclo"] = ahora.strftime("%Y-%m-%d %H:%M:%S")
            self.recompensas(ahora)
        except SystemExit:
            raise
        except Exception as ex:
            self.est["errores_seguidos"] = self.est.get("errores_seguidos", 0) + 1
            log(f"error en el ciclo: {ex!r}")
        self._guardar()
        return None

    def recompensas(self, ahora):
        """Una vez por dia (a las 00:30 UTC) anota la recompensa del dia anterior: real la informa Polymarket,
        papel la estima (promedio de rec_pes de las cajas que tuvimos, por el tiempo que las tuvimos)."""
        ayer = (ahora - timedelta(days=1)).strftime("%Y-%m-%d")
        est = self.est["recompensas"].setdefault("estimada", {})
        hoy = ahora.strftime("%Y-%m-%d")
        # acumulado estimado de hoy: suma de rec_pes de las cajas elegidas, prorrateado por ciclo
        ciclo = self.cfg["maker"]["ciclo_seg"] / 86400
        est[hoy] = round(est.get(hoy, 0) + sum(c.get("rec_pes", 0) for c in self.est["cajas"].values()) * ciclo, 3)
        if ahora.hour == 0 and ahora.minute >= 30 and ayer not in self.est["recompensas"]:
            real = None
            try:
                real = self.ej.recompensa_dia(ayer)
            except Exception as ex:
                log(f"no se pudo leer la recompensa de {ayer}: {ex!r}")
                return
            self.est["recompensas"][ayer] = real if real is not None else est.get(ayer, 0)
            self.resumen()
            self.avisar(f"Maker ({self.modo}) {ayer}: recompensa {self.est['recompensas'][ayer]:.2f} US$, "
                   f"resultado de llenados {self.pnl(ayer):+.2f}, {len(self.est['cajas'])} cajas.")

    def resumen(self):
        rec = self.est["recompensas"]
        cobradas = {k: v for k, v in rec.items() if k != "estimada"}
        est = rec.get("estimada", {})
        ops = self.ops()
        llen = [o for o in ops if o["lado"] in ("BUY", "SELL")]
        lin = [f"# Maker ({self.modo}) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z", "",
               f"- Cajas ahora: {len(self.est['cajas'])}: " + ", ".join(f"{c['caja']} ({c['evento']}, medio {c['medio']}, "
                                                                     f"rec. esp. {c['rec_pes']}/día)" for c in self.est["cajas"].values()),
               f"- Recompensas cobradas (lo que dice Polymarket; en papel, estimadas): US$ {sum(cobradas.values()):.2f} en {len(cobradas)} días"
               + (": " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(cobradas.items())) if cobradas else "."),
               f"- Estimación por fórmula (pesimista): " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(est.items())),
               f"- Llenados: {len(llen)} ({sum(float(o['acciones']) for o in llen):.0f} acciones); cajas resueltas: {len(self.est['resultados'])}.",
               f"- Resultado realizado de los llenados (cobros − compras + ventas): US$ {self.pnl():+.2f}. "
               f"Capital puesto ahora: US$ {self.capital_puesto():.2f}.",
               f"- Neto = recompensas + realizado: US$ {sum(cobradas.values()) + self.pnl():+.2f}.",
               f"- Freno: {'ACTIVO — ' + self.frenado() if self.frenado() else 'no'}."]
        with open(self.f_res, "w", encoding="utf-8") as f:
            f.write("\n".join(lin) + "\n")
        print("\n".join(lin))


def main():
    cfg = cargar_cfg()
    que = sys.argv[1] if len(sys.argv) > 1 else "una"
    if que == "probar-aviso":
        avisar("Prueba de aviso del bot maker: si ves esto, los avisos funcionan.")
        return
    bot = Maker(cfg)
    if que == "resumen":
        bot.resumen()
        return
    if que == "una":
        bot.ciclo()
        bot.resumen()
        return
    if que == "bucle":
        log(f"maker ({bot.modo}) arranca: {cfg['maker']['cajas']} cajas, US$ {cfg['maker']['capital_usd']}, "
            f"orden a {cfg['maker']['distancia'] * 100:.0f} c del medio")
        bot.avisar(f"Maker ({bot.modo}) arrancó.")
        try:
            while True:
                t0 = time.time()
                motivo = bot.ciclo()
                if motivo and "freno activo" in motivo or motivo == "perdida total" or motivo == "errores seguidos" \
                        or (motivo and motivo.startswith("fecha")):
                    break
                if datetime.now(timezone.utc).minute % 30 == 0:
                    bot.resumen()
                time.sleep(max(cfg["maker"]["ciclo_seg"] - (time.time() - t0), 5))
        except KeyboardInterrupt:
            log("corte pedido (Ctrl+C o fin del tramo)")
        finally:
            bot.resumen()                   # con las ordenes todavia puestas, para que el capital se vea
            try:
                bot.ej.cancelar_todo()
                log("ordenes canceladas")
            except Exception as ex:
                log(f"NO SE PUDIERON CANCELAR LAS ORDENES: {ex!r} (cancelar a mano en polymarket.com)")
                bot.avisar(f"Maker ({bot.modo}): se apagó y NO pudo cancelar las órdenes. Cancelalas a mano en polymarket.com.")
            bot._guardar()
            bot.avisar(f"Maker ({bot.modo}) apagado.")


if __name__ == "__main__":
    main()

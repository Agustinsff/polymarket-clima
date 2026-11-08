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
     En las cajas que ya solto pero donde le quedan acciones, deja una venta post-only (mismo precio) del tamano que
     tenga, para no esperar a la resolucion; no cuentan como caja ni suman capital.
  5. anota los llenados, la recompensa cobrada (real: lo que informa Polymarket; papel: la formula) y el resumen
  Al salir por cualquier motivo cancela TODAS las ordenes, salvo si se le pidio REINICIAR (bot/REINICIAR o
  bot/actualizar.cmd): ahi sale con codigo 3 dejando las ordenes en el libro y, al volver a arrancar, adopta las que
  siguen correspondiendo (mismo token, lado y precio), asi no pierde el lugar en la fila. Relee config.json en cada
  ciclo (todo menos `modo`), asi cambiar capital, cajas, distancia o topes no necesita reinicio.

Modos: papel (libro real, llenado prudente como el medidor: solo si alguien opero a peor precio) y real (SDK
oficial, post-only GTC). Uso:
  python bot/maker.py bucle | una | resumen | probar-aviso | inventario (solo lectura: compara el inventario propio
  con el saldo de la billetera)
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
                    # data-api v1 (/trades) esta retirada: contesta {"error": "Data API v1 has been retired"} y el
                    # papel no veia ningun llenado (0 en 4-7 nov). v2: /v2/trades?condition=..., respuesta {"data": [...]}
                    r = self.m.S.get(f"{DATA}/v2/trades", params={"condition": o["cid"], "limit": 100, "taker_only": "true"},
                                     timeout=30).json()
                    if isinstance(r, dict):
                        r = r.get("data")
                    if not isinstance(r, list):      # dict de error
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
                if t.get("token_id"):            # v2 dice el token; v1 solo el indice del resultado
                    mismo_token = str(t["token_id"]) == str(o["token"])
                else:
                    mismo_token = (t.get("outcomeIndex", t.get("outcome_index")) == 0) == o["si"]
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
    size_matched); list_account_trades(after) -> ClobTrade(id, condition_id, trader_side, status, taker_order_id, asset_id,
    side, price, size, maker_orders=[MakerOrder(order_id, asset_id, side, price, matched_amount)], matched_at);
    get_balance_allowance(asset_type="CONDITIONAL", token_id) -> BalanceAllowance(balance en millonesimas);
    get_total_earnings_for_user_for_day(date) -> earnings; redeem_positions(condition_id).wait().

    INVENTARIO PROPIO (8-nov-2026): el bot ya no le pregunta las posiciones a data-api (limita las consultas: RateLimitError
    el 7-nov). Lleva la cuenta el mismo con sus llenados, que lee del CLOB ("mis operaciones", limites altos): cada
    operacion en la que una orden SUYA se lleno suma (compra) o resta (venta) acciones de ese token. Solo cuenta ordenes
    que puso el bot (las acciones viejas de la cuenta no entran) y anota tambien las ordenes que se llenaron del todo
    (antes se perdian porque desaparecen de la lista de abiertas). La primera vez reconstruye todo desde DESDE_INICIAL
    y anota en maker_ops_real.csv los llenados que faltaban."""
    nombre = "real"
    DESDE_INICIAL = datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp()   # antes del primer arranque en real
    RELEER = 3600            # cada ciclo relee la ultima hora (por si una operacion cambia de estado, p. ej. FAILED)

    def __init__(self, m, est, ops=None):
        if os.environ.get("BOT_REAL_CONFIRMO") != "si":
            raise SystemExit("modo real: falta BOT_REAL_CONFIRMO=si en el entorno")
        if not os.environ.get("POLYMARKET_PRIVATE_KEY"):
            raise SystemExit("modo real: falta POLYMARKET_PRIVATE_KEY en el entorno")
        geo = m.geobloqueo()
        if geo.get("blocked") is not False:
            raise SystemExit(f"modo real: Polymarket bloquea operar desde aca ({geo.get('country')}, {geo.get('region')})")
        from polymarket import SecureClient
        relayer = self.clave_relayer()
        client = SecureClient.create(private_key=os.environ["POLYMARKET_PRIVATE_KEY"],
                                     wallet=os.environ.get("POLYMARKET_WALLET") or None, api_key=relayer)
        log("cobro automatico (relayer): " + ("si" if relayer else "no, cobrar a mano en Portfolio -> Claim"))
        self._preparar(client, est, ops)

    @staticmethod
    def clave_relayer():
        """Clave de Relayer (polymarket.com -> Settings -> API Keys -> Relayer API Keys) para que el cobro (redeem)
        funcione con la billetera proxy. Opcional: BOT_RELAYER_API_KEY y BOT_RELAYER_API_ADDRESS en secreto.cmd."""
        clave, direccion = os.environ.get("BOT_RELAYER_API_KEY"), os.environ.get("BOT_RELAYER_API_ADDRESS")
        if not clave or not direccion:
            return None
        from polymarket import RelayerApiKey
        return RelayerApiKey(key=clave, address=direccion)

    def _preparar(self, client, est, ops=None):
        self.client, self.est, self.ops = client, est, ops or (lambda: [])
        est.pop("llenado_visto", None)                     # cuenta vieja (por orden abierta), ya no se usa
        est.setdefault("inv", {})                           # token -> acciones (inventario propio)
        est.setdefault("token_cid", {})                     # token -> condition_id
        est.setdefault("vistos", {})                        # "operacion:orden" -> [momento, token, +-acciones]
        est.setdefault("mis_ordenes", {})                   # order_id -> momento en que la puso el bot

    def colocar(self, token, cid, lado, precio, acciones, es_si):
        r = self.client.place_limit_order(token_id=token, price=str(precio), size=str(acciones), side=lado, post_only=True)
        if not r.ok:
            raise RuntimeError(f"orden rechazada ({r.code}): {r.message}")
        self.est["mis_ordenes"][r.order_id] = int(time.time())
        self.est["token_cid"][token] = cid
        return r.order_id

    def cancelar(self, ids):
        if ids:
            self.client.cancel_orders(order_ids=list(ids))

    def cancelar_todo(self):
        self.client.cancel_all()

    @staticmethod
    def _items(r):
        """El SDK devuelve un Paginator (iter_items) en list_open_orders/list_account_trades; acepta tambien listas."""
        return list(r.iter_items()) if hasattr(r, "iter_items") else list(r)

    def abiertas(self):
        return [{"id": o.id, "token": o.asset_id, "cid": o.condition_id, "lado": o.side, "precio": float(o.price),
                 "acciones": float(o.original_size) - float(o.size_matched), "llenado": float(o.size_matched)}
                for o in self._items(self.client.list_open_orders())]

    # ---------- inventario propio a partir de los llenados del CLOB ----------
    def _mis_ordenes(self):
        """Ordenes que puso el bot: las del estado mas las anotadas en maker_ops_real.csv (para la primera vez)."""
        ids = set(self.est["mis_ordenes"])
        for o in self.ops():
            if o.get("lado", "").startswith("orden_") and o.get("detalle"):
                ids.add(o["detalle"])
        return ids

    def _operaciones(self, desde):
        """Partes de las operaciones de la cuenta (desde `desde`, unix) que llenaron ordenes del bot."""
        mias = self._mis_ordenes()
        out = []
        for t in self._items(self.client.list_account_trades(after=str(int(desde)))):
            ts = t.matched_at.timestamp() if hasattr(t.matched_at, "timestamp") else float(t.matched_at)
            partes = []
            if t.trader_side == "MAKER":
                partes = [(mo.order_id, mo.asset_id, mo.side, float(mo.price), float(mo.matched_amount))
                          for mo in t.maker_orders if mo.order_id in mias]
            elif t.taker_order_id in mias:                  # no deberia pasar (post-only), pero se cuenta igual
                partes = [(t.taker_order_id, t.asset_id, t.side, float(t.price), float(t.size))]
            for oid, token, lado, precio, q in partes:
                if q > 1e-9:
                    out.append({"clave": f"{t.id}:{oid}", "id": oid, "token": token, "cid": t.condition_id, "lado": lado,
                                "precio": precio, "acciones": q, "estado": t.status, "ts": ts})
        return out

    def _sumar(self, token, q):
        inv = self.est["inv"]
        inv[token] = round(inv.get(token, 0) + q, 6)
        if abs(inv[token]) < 1e-6:
            inv.pop(token)

    def llenados(self):
        """Lee "mis operaciones" del CLOB y devuelve los llenados nuevos [(orden, acciones, detalle)]."""
        primera = "inv_desde" not in self.est
        desde = self.DESDE_INICIAL if primera else self.est["inv_desde"] - self.RELEER
        ops = self._operaciones(desde)
        vistos, out = self.est["vistos"], []
        for x in sorted(ops, key=lambda x: x["ts"]):
            self.est["token_cid"][x["token"]] = x["cid"]
            if x["estado"] == "FAILED":
                if x["clave"] in vistos:                    # se habia contado y fallo en la cadena: se deshace
                    _, token, q = vistos.pop(x["clave"])
                    self._sumar(token, -q)
                    contra = dict(x, lado="SELL" if x["lado"] == "BUY" else "BUY")
                    out.append((contra, x["acciones"], "operacion fallida en la cadena: se deshace"))
                continue
            if x["clave"] in vistos:
                continue
            q = x["acciones"] if x["lado"] == "BUY" else -x["acciones"]
            vistos[x["clave"]] = [int(x["ts"]), x["token"], q]
            self._sumar(x["token"], q)
            if not primera:
                out.append((x, x["acciones"], f"CLOB {x['estado']}"))
        if primera:
            out = self._recuperar(ops)
            log(f"inventario propio armado desde el CLOB: {len(vistos)} llenados, "
                f"{sum(1 for q in self.est['inv'].values() if q > 1e-6)} tokens con acciones")
        ahora = time.time()
        self.est["inv_desde"] = ahora
        # limpieza: llenados y ordenes de hace mas de 2 dias ya no se releen
        for k in [k for k, v in vistos.items() if v[0] < ahora - 2 * 86400]:
            vistos.pop(k)
        for k in [k for k, v in self.est["mis_ordenes"].items() if v < ahora - 2 * 86400]:
            self.est["mis_ordenes"].pop(k)
        return out

    def _recuperar(self, ops):
        """Primera vez: los llenados que el CSV no tiene (la cuenta vieja se perdia las ordenes llenadas del todo)."""
        def clave(token, lado, precio):
            return token, lado, round(float(precio), 4)
        anotado = {}
        for o in self.ops():
            if o.get("lado") in ("BUY", "SELL"):
                k = clave(o["token"], o["lado"], o["precio"])
                anotado[k] = anotado.get(k, 0) + float(o["acciones"])
        en_clob, ejemplo = {}, {}
        for x in ops:
            if x["estado"] != "FAILED":
                k = clave(x["token"], x["lado"], x["precio"])
                en_clob[k] = en_clob.get(k, 0) + x["acciones"]
                ejemplo[k] = x
        out = []
        for k, q in en_clob.items():
            falta = round(q - anotado.get(k, 0), 4)
            if falta > 1e-6:
                out.append((ejemplo[k], falta, "recuperado del CLOB (no estaba anotado)"))
        return out

    def inventario(self):
        """Inventario propio (sin consultar nada): acciones que el bot compro y todavia tiene."""
        return {t: q for t, q in self.est["inv"].items() if q > 1e-6}

    def cid_de(self, token):
        return self.est["token_cid"].get(token)

    def saldo_token(self, token):
        """Acciones del token en la billetera segun el CLOB (para comparar con el inventario propio)."""
        b = self.client.get_balance_allowance(asset_type="CONDITIONAL", token_id=token)
        return int(b.balance) / 1e6

    def cobrar(self, cid, tokens, ganador):
        """Caja resuelta: lo que vale es lo que tenemos del lado ganador. Se intenta cobrar (redeem); con billetera
        proxy puede fallar por falta de clave extra: entonces queda anotado igual y hay que cobrar a mano (Claim)."""
        q = self.inventario().get(tokens[ganador], 0)
        try:
            self.client.redeem_positions(condition_id=cid).wait()
        except Exception as ex:
            log(f"no se pudo cobrar solo {cid[:10]}: {ex!r}; queda para cobrar a mano")
            if q > 0:
                avisar(f"Maker (real): una caja resolvio a favor (US$ {q:.2f}) y no se pudo cobrar sola. "
                       f"Cobrala a mano en polymarket.com: Portfolio -> Claim.")
        for t in tokens:
            self.est["inv"].pop(t, None)
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
        self.f_reiniciar = os.path.join(carpeta, "REINICIAR")
        self.f_cfg = None                                   # ruta de config.json para releer (None: no relee)
        self.est = self._cargar()
        self.ej = ej or (Real(m, self.est, ops=self.ops) if self.modo == "real" else Papel(m, self.est))
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
    def pnl(self, dia=None, inventario=True):
        """Resultado total: cobros de cajas resueltas menos lo pagado por las acciones (ventas cuentan como cobro) MAS, si
        inventario, las acciones que todavia se tienen valuadas al costo medio pagado. Sin eso una compra sin resolver
        contaba como perdida y el freno saltaba (7-nov en real: "perdida -40,74" que eran US$ 40 en acciones en cartera).
        Con dia: resultado DEL DIA = ventas del dia al costo medio (q * (precio - costo)) + cajas resueltas ese dia
        (cobrado - costo de lo que se tenia). Las compras del dia no cuentan (son acciones al costo), y una caja que
        resuelve en contra cuenta ese dia aunque las acciones se hayan comprado antes."""
        total = 0.0
        if dia:
            for o in self.ops():
                if o["lado"] != "SELL" or o["momento_utc"][:10] != dia:
                    continue
                q, p = float(o["acciones"]), float(o["precio"])
                c = self.est["costo"].get(o["token"])
                total += q * (p - (c["precio"] if c else p))
            for r in self.est["resultados"].values():
                if r.get("dia") == dia:
                    total += r.get("cobrado", 0) - r.get("costo", 0)
            return round(total, 2)
        for o in self.ops():
            if o["lado"] not in ("BUY", "SELL"):
                continue
            q, p = float(o["acciones"]), float(o["precio"])
            total += -q * p if o["lado"] == "BUY" else q * p
        for r in self.est["resultados"].values():
            total += r.get("cobrado", 0)
        if inventario:
            for t, q in self.ej.inventario().items():
                c = self.est["costo"].get(t)
                if c:
                    total += q * c["precio"]
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
        meta = self.est.setdefault("meta", {})            # datos de cada caja usada, para cobrarla aunque ya se haya soltado
        for cid, c in elegidas.items():
            meta[cid] = {k2: c[k2] for k2 in ("evento", "caja", "si", "no", "fin", "tick")}
        return elegidas

    def ventas_soltadas(self, elegidas, inv):
        """Ventas post-only en las cajas que el bot ya solto pero donde todavia tiene acciones (8-nov, pedido de Agus):
        mismo precio que siempre (medio + distancia, con el libro actual), del tamano que tenga, sin contar como caja ni
        sumar capital. Se cancelan solas (renovar) cuando la caja resuelve, el evento termino o el libro no se puede leer."""
        d, minimo = self.cfg["maker"]["distancia"], self.cfg["maker"].get("acciones_min_venta", 5)
        ahora = datetime.now(timezone.utc)
        out = []
        for cid, c in self.est.get("meta", {}).items():
            if cid in elegidas or cid in self.est["resultados"]:
                continue
            tiene = [(t, inv.get(t, 0)) for t in (c["si"], c["no"]) if inv.get(t, 0) >= minimo]
            if not tiene:
                continue
            try:
                if c.get("fin") and datetime.fromisoformat(c["fin"].replace("Z", "+00:00")) < ahora:
                    continue
                bids, asks = self.m.libro(c["si"])
                if not bids or not asks:
                    continue
                medio = (bids[0][0] + asks[0][0]) / 2
            except Exception as ex:
                log(f"no se pudo leer el libro de {c.get('caja', cid[:10])} para vender lo que queda: {ex!r}")
                continue
            tick = c.get("tick", 0.01)
            for t, q in tiene:
                es_si = t == c["si"]
                p = redondear((medio if es_si else 1 - medio) + d, tick, False)
                if 0.01 <= p <= 0.99:
                    out.append((cid, c.get("evento", ""), c.get("caja", ""), round(medio, 4), t, "SELL", p, math.floor(q * 100) / 100, es_si))
        return out

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
        quiero += self.ventas_soltadas(elegidas, inv)
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
            c = self.est["cajas"].get(o["cid"]) or self.est.get("meta", {}).get(o["cid"]) or {}
            self.anotar(momento_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), modo=self.modo,
                        evento=c.get("evento", ""), caja=c.get("caja", ""), condition_id=o["cid"], token=o["token"],
                        lado=o["lado"], precio=o["precio"], acciones=round(q, 2), medio=c.get("medio", ""),
                        detalle=p_taker if isinstance(p_taker, str) else f"taker a {p_taker}")
            costo = self.est["costo"].setdefault(o["token"], {"precio": o["precio"], "acciones": 0})
            if o["lado"] == "BUY":
                tot = costo["acciones"] + q
                costo["precio"] = (costo["precio"] * costo["acciones"] + o["precio"] * q) / tot if tot else o["precio"]
                costo["acciones"] = tot
            else:
                costo["acciones"] = max(costo["acciones"] - q, 0)
            self.avisar(f"Maker ({self.modo}): {o['lado']} {q:.0f} acc a {o['precio']} en {c.get('caja', '?')} ({c.get('evento', '')})")
            log(f"llenado: {o['lado']} {q:.1f} a {o['precio']} en {c.get('caja', '?')}")

    def meta_caja(self, cid):
        """Evento, caja y tokens de una caja (del estado; si no esta, del CLOB: cajas de antes del 8-nov)."""
        meta = self.est.setdefault("meta", {})
        if cid not in meta:
            r = self.m.S.get(f"{mercado.CLOB}/markets/{cid}", timeout=20).json()
            toks = [t["token_id"] for t in r["tokens"]]
            meta[cid] = {"evento": r.get("market_slug", ""), "caja": r.get("question", cid[:10]), "si": toks[0], "no": toks[1],
                         "fin": r.get("end_date_iso") or "", "tick": float(r.get("minimum_tick_size") or 0.01)}
        return meta[cid]

    def liquidar(self):
        """Cajas con inventario cuyo evento ya resolvio: cobrar y anotar. Mira todas las cajas donde tenemos acciones,
        no solo las elegidas ahora (antes una caja soltada al terminar el evento nunca se cobraba en la cuenta)."""
        inv = self.ej.inventario()
        cids = {cid for cid, c in self.est.get("meta", {}).items() if inv.get(c["si"], 0) > 1e-6 or inv.get(c["no"], 0) > 1e-6}
        cid_de = getattr(self.ej, "cid_de", lambda t: None)
        cids |= {cid_de(t) for t in inv} - {None}
        for cid in cids:
            if cid in self.est["resultados"]:
                continue
            try:
                g = self.m.ganador(cid)
                if g is None:
                    continue
                c = self.meta_caja(cid)
            except Exception:
                continue
            si, no = c["si"], c["no"]
            gi = 0 if g == "Yes" else 1
            costo = sum(inv.get(t, 0) * self.est["costo"].get(t, {}).get("precio", 0) for t in (si, no))
            try:
                cobrado = self.ej.cobrar(cid, [si, no], gi)
            except Exception as ex:
                log(f"no se pudo cobrar {c['caja']}: {ex!r}")
                continue
            self.est["resultados"][cid] = {"dia": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "gano": g,
                                           "cobrado": round(cobrado, 2), "costo": round(costo, 2), "caja": c["caja"],
                                           "evento": c["evento"]}
            for t in (si, no):
                self.est["costo"].pop(t, None)
            self.est["meta"].pop(cid, None)
            self.anotar(momento_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), modo=self.modo,
                        evento=c["evento"], caja=c["caja"], condition_id=cid, lado="cobro", precio=1, acciones=round(cobrado, 2),
                        detalle=f"gano {g}")
            log(f"cobrado {cobrado:.2f} en {c['caja']} ({c['evento']}, gano {g})")
        # las cajas cuyo evento ya termino se sueltan (sin ordenes), aunque no se haya resuelto todavia
        ahora = datetime.now(timezone.utc)
        for cid, c in list(self.est["cajas"].items()):
            if datetime.fromisoformat(c["fin"].replace("Z", "+00:00")) < ahora:
                self.est["cajas"].pop(cid)

    def comparar_inventario(self):
        """Solo lectura (no pone ni cancela nada): inventario propio armado con el CLOB vs saldo de cada token."""
        self.revisar_llenados_sin_anotar()
        inv = self.ej.inventario()
        lin = [f"Inventario propio (llenados del bot leidos del CLOB): {len(inv)} tokens"]
        dif = 0
        for t, q in sorted(inv.items()):
            cid = getattr(self.ej, "cid_de", lambda x: None)(t)
            try:
                c = self.meta_caja(cid) if cid else {}
            except Exception:
                c = {}
            saldo = self.ej.saldo_token(t) if hasattr(self.ej, "saldo_token") else None
            ok = saldo is not None and saldo + 1e-6 >= q
            dif += 0 if ok else 1
            lin.append(f"  {c.get('caja', '?'):>8} {c.get('evento', (cid or '')[:12])}: bot {q:.2f} acc., "
                       f"billetera {saldo if saldo is not None else '?'} {'OK' if ok else 'NO COINCIDE'}")
        lin.append("Todo coincide." if not dif else f"{dif} tokens no coinciden: no reiniciar todavia, avisar en el hilo.")
        print("\n".join(lin))
        return dif

    def revisar_llenados_sin_anotar(self):
        for _ in self.ej.llenados():
            pass

    # ---------- un ciclo ----------
    def recargar_cfg(self):
        """Relee config.json (si se pidio con f_cfg) y aplica los cambios de la seccion maker salvo `modo`."""
        if not self.f_cfg:
            return
        try:
            nueva = cargar_cfg(self.f_cfg)["maker"]
        except (OSError, ValueError, KeyError) as ex:
            log(f"config.json no se pudo leer, sigo con la anterior: {ex!r}")
            return
        vieja = self.cfg["maker"]
        cambios = {k: v for k, v in nueva.items() if k != "modo" and vieja.get(k) != v}
        if cambios:
            log("config nueva: " + ", ".join(f"{k} {vieja.get(k)} -> {v}" for k, v in cambios.items()))
            vieja.update(cambios)

    def pedido_reinicio(self):
        """True si alguien dejo bot/REINICIAR: el bot sale SIN cancelar las ordenes (las adopta al volver)."""
        if not os.path.exists(self.f_reiniciar):
            return False
        try:
            os.remove(self.f_reiniciar)
        except OSError:
            pass
        return True

    def sigo_vivo(self, ahora):
        """Un aviso por dia a las 12 UTC (9 de la manana en Uruguay) con el estado, para notar si el bot esta caido."""
        hoy = ahora.strftime("%Y-%m-%d")
        if ahora.hour == 12 and self.est.get("ultimo_vivo") != hoy:
            self.est["ultimo_vivo"] = hoy
            try:
                n = len(self.ej.abiertas())
            except Exception:
                n = "?"
            self.avisar(f"Maker ({self.modo}) sigo vivo: {n} ordenes en {len(self.est['cajas'])} cajas, "
                        f"resultado del dia {self.pnl(hoy):+.2f}, total al costo {self.pnl():+.2f}, "
                        f"errores seguidos {self.est.get('errores_seguidos', 0)}.")

    def ciclo(self, ahora=None):
        ahora = ahora or datetime.now(timezone.utc)
        try:
            self.recargar_cfg()
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
            self.sigo_vivo(ahora)
        except SystemExit:
            raise
        except Exception as ex:
            self.est["errores_seguidos"] = self.est.get("errores_seguidos", 0) + 1
            log(f"error en el ciclo: {ex!r}")
        self.avisar_errores()
        self._guardar()
        return None

    def avisar_errores(self):
        """Un aviso al llegar a `avisar_errores` (3) errores seguidos, una vez por racha, antes del freno de 10."""
        n, tope = self.est.get("errores_seguidos", 0), self.cfg["maker"].get("avisar_errores", 3)
        if n >= tope and not self.est.get("errores_avisados"):
            self.est["errores_avisados"] = True
            self.avisar(f"Maker ({self.modo}): {n} errores seguidos (se frena a los {self.cfg['maker']['max_errores_seguidos']}). "
                        f"Mirar la ventana del bot.")
        elif n == 0:
            self.est["errores_avisados"] = False

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
               f"- Resultado realizado de los llenados (cobros − compras + ventas): US$ {self.pnl(inventario=False):+.2f}; "
               f"contando las acciones en cartera al costo: US$ {self.pnl():+.2f}. "
               f"Capital puesto ahora: US$ {self.capital_puesto():.2f}.",
               f"- Neto = recompensas + realizado: US$ {sum(cobradas.values()) + self.pnl():+.2f}.",
               f"- Freno: {'ACTIVO — ' + self.frenado() if self.frenado() else 'no'}."]
        with open(self.f_res, "w", encoding="utf-8") as f:
            f.write("\n".join(lin) + "\n")
        print("\n".join(lin))


def cargar_secretos(ruta=os.path.join(CARPETA, "secreto.cmd")):
    """Lee las lineas `set NOMBRE=valor` de bot/secreto.cmd y completa el entorno con las que falten. Asi un reinicio
    con REINICIAR (que no vuelve a pasar por iniciar_maker.cmd) toma secretos agregados despues de arrancar."""
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            lineas = f.read().splitlines()
    except OSError:
        return 0
    n = 0
    for l in lineas:
        l = l.strip()
        if l.lower().startswith("set ") and "=" in l:
            k, v = l[4:].split("=", 1)
            k, v = k.strip(), v.strip().strip('"')
            if k and v and not os.environ.get(k):
                os.environ[k] = v
                n += 1
    return n


def main():
    cargar_secretos()
    cfg = cargar_cfg()
    que = sys.argv[1] if len(sys.argv) > 1 else "una"
    if que == "probar-aviso":
        avisar("Prueba de aviso del bot maker: si ves esto, los avisos funcionan.")
        return
    bot = Maker(cfg)
    bot.f_cfg = os.path.join(CARPETA, "config.json")
    if que == "resumen":
        bot.resumen()
        return
    if que == "inventario":          # solo lectura: no guarda el estado ni toca ordenes
        sys.exit(1 if bot.comparar_inventario() else 0)
    if que == "una":
        bot.ciclo()
        bot.resumen()
        return
    if que == "bucle":
        log(f"maker ({bot.modo}) arranca: {cfg['maker']['cajas']} cajas, US$ {cfg['maker']['capital_usd']}, "
            f"orden a {cfg['maker']['distancia'] * 100:.0f} c del medio")
        bot.pedido_reinicio()                               # un REINICIAR viejo no vale
        bot.avisar(f"Maker ({bot.modo}) arrancó.")
        reiniciar = False
        try:
            while True:
                t0 = time.time()
                if bot.pedido_reinicio():
                    reiniciar = True
                    log("reinicio pedido: salgo SIN cancelar las ordenes; al volver las adopto")
                    break
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
            if reiniciar:
                bot._guardar()
                sys.exit(3)                 # iniciar_maker.cmd lo vuelve a arrancar enseguida
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

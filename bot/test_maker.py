"""Pruebas sin red del bot maker: python bot/test_maker.py"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maker  # noqa: E402

AHORA = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
FIN = (AHORA + timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ")


def mercado_gamma(cid, titulo, pozo=30, min_size=20, spread_max=4.5):
    return {"conditionId": cid, "groupItemTitle": titulo, "question": titulo, "closed": False,
            "clobTokenIds": json.dumps([f"si-{cid}", f"no-{cid}"]), "clobRewards": [{"rewardsDailyRate": pozo}],
            "rewardsMinSize": min_size, "rewardsMaxSpread": spread_max, "orderPriceMinTickSize": 0.01}


class Resp:
    def __init__(self, d):
        self.d = d

    def json(self):
        return self.d


class MercadoFalso:
    """Un evento con dos cajas: 'apretada' (spread 3 c) y 'ancha' (spread 20 c)."""
    def __init__(self):
        self.libros = {"si-A": ([(0.30, 100), (0.25, 200)], [(0.33, 80), (0.40, 100)]),
                       "si-B": ([(0.20, 50)], [(0.40, 50)])}
        self.trades = {}
        self.ganadores = {}
        self.slug = "highest-temperature-in-x"
        self.S = self

    def get(self, url, params=None, timeout=None):
        if "gamma" in url:
            if params.get("offset", 0) > 0:
                return Resp([])
            return Resp([{"slug": self.slug, "endDate": FIN,
                          "markets": [mercado_gamma("A", "20°C"), mercado_gamma("B", "21°C", pozo=90)]}])
        if "/v2/trades" in url:
            return Resp({"data": self.trades.get(params["condition"], [])})
        if "trades" in url:
            return Resp({"error": "Data API v1 has been retired"})
        raise AssertionError(url)

    def libro(self, token):
        return self.libros[token]

    def ganador(self, cid):
        return self.ganadores.get(cid)

    def geobloqueo(self):
        return {"blocked": False}


def cfg(**k):
    c = {"maker": {"modo": "papel", "capital_usd": 150, "cajas": 3, "acciones_min": 25, "distancia": 0.02, "spread_max": 0.05,
                   "horas_min_fin": 3, "ciclo_seg": 60, "apagar_despues_de": "2026-11-30 23:59", "max_perdida_dia": 10,
                   "max_perdida_total": 30, "max_errores_seguidos": 10, "guardia_metar": False}}
    c["maker"].update(k)
    return c


class Pruebas(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.m = MercadoFalso()
        maker.avisar = lambda t: None
        self.bot = maker.Maker(cfg(), m=self.m, carpeta=self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_elige_solo_la_apretada(self):
        el = self.bot.elegir(AHORA)
        self.assertEqual(list(el), ["A"])              # B tiene mas pozo pero spread 20 c
        c = el["A"]
        self.assertAlmostEqual(c["medio"], 0.315)
        self.assertEqual(c["tam"], 25)
        self.assertGreater(c["rec_pes"], 0)

    def test_rota_si_otra_caja_paga_mucho_mas(self):
        """9-nov: una caja que ya tenemos y se llena de rivales se cambia por otra que espera 3 veces mas (y +2 US$/dia),
        midiendo cada 30 min y de a una; la soltada no vuelve por 6 h."""
        self.bot.cfg["maker"]["cajas"] = 1
        avisos = []
        self.bot.avisar = avisos.append
        self.assertEqual(list(self.bot.elegir(AHORA)), ["A"])
        self.m.libros["si-B"] = ([(0.39, 30)], [(0.41, 30)])                       # B se aprieta y tiene 90 de pozo
        self.m.libros["si-A"] = ([(0.31, 5000), (0.30, 100)], [(0.32, 5000)])      # A se llena de rivales
        self.assertEqual(list(self.bot.elegir(AHORA + timedelta(minutes=1))), ["A"])   # sin rotacion hace < 30 min
        self.assertEqual(list(self.bot.elegir(AHORA + timedelta(minutes=10))), ["A"])
        # con acciones en mano en A no rota (seguiria vendiendo como caja activa)
        self.bot.ej.est["inventario"]["no-A"] = 25.0
        self.assertEqual(list(self.bot.elegir(AHORA + timedelta(minutes=31))), ["A"])
        self.bot.ej.est["inventario"]["no-A"] = 0.0
        self.bot.est["rotacion_ts"] = AHORA.isoformat()
        el = self.bot.elegir(AHORA + timedelta(minutes=31))
        self.assertEqual(list(el), ["B"])
        self.assertIn("A", self.bot.est["rotadas"])
        self.assertTrue(any("rotacion" in a for a in avisos))
        # B tambien se llena: A no vuelve (rotada hace < 6 h) aunque espere mas
        self.m.libros["si-B"] = ([(0.39, 5000)], [(0.41, 5000)])
        self.m.libros["si-A"] = ([(0.30, 30)], [(0.33, 30)])
        self.assertEqual(list(self.bot.elegir(AHORA + timedelta(minutes=70))), ["B"])
        # con rotar_cada_min 0 no rota nunca
        self.bot.est["rotadas"].clear()
        self.bot.cfg["maker"]["rotar_cada_min"] = 0
        self.assertEqual(list(self.bot.elegir(AHORA + timedelta(minutes=200))), ["B"])
        self.bot.cfg["maker"]["rotar_cada_min"] = 30
        self.assertEqual(list(self.bot.elegir(AHORA + timedelta(minutes=201))), ["A"])

    def test_cotiza_dos_compras(self):
        c = self.bot.elegir(AHORA)["A"]
        o = self.bot.cotizar(c, {})
        self.assertEqual(o, [("si-A", "BUY", 0.29, 25, True), ("no-A", "BUY", 0.66, 25, False)])
        # con 25 acciones de Si en mano, vende Si en vez de comprar No
        o = self.bot.cotizar(c, {"si-A": 25})
        self.assertEqual(o[1], ("si-A", "SELL", 0.34, 25, True))

    def test_renueva_solo_si_se_mueve(self):
        self.bot.ciclo(AHORA)
        ab = self.bot.ej.abiertas()
        self.assertEqual(len(ab), 2)
        ids = {o["id"] for o in ab}
        self.bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertEqual({o["id"] for o in self.bot.ej.abiertas()}, ids)   # mismo libro: no toca nada
        self.m.libros["si-A"] = ([(0.31, 100)], [(0.34, 80)])           # el medio sube 1 c
        self.bot.ciclo(AHORA + timedelta(minutes=2))
        nuevas = self.bot.ej.abiertas()
        self.assertEqual(len(nuevas), 2)
        self.assertFalse({o["id"] for o in nuevas} & ids)
        self.assertEqual(sorted(o["precio"] for o in nuevas), [0.30, 0.65])

    def test_llenado_prudente_y_cobro(self):
        self.bot.ciclo(AHORA)
        desde = self.bot.ej.abiertas()[0]["desde"]
        # un taker vende Si a 0.29 (igual a nuestro precio): NO cuenta; otro vende a 0.28: cuenta 10 acciones
        self.m.trades["A"] = [{"timestamp": desde + 5, "price": 0.29, "size": 50, "side": "SELL", "outcomeIndex": 0},
                              {"timestamp": desde + 9, "price": 0.28, "size": 10, "side": "SELL", "outcomeIndex": 0},
                              {"timestamp": desde + 12, "price": 0.70, "size": 5, "side": "BUY", "outcomeIndex": 1}]
        # el ultimo: alguien COMPRA No a 0.70 = vende Si a 0.30: no es peor que nuestra compra de No a 0.66
        self.bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertEqual(self.bot.ej.inventario(), {"si-A": 10})
        llen = [o for o in self.bot.ops() if o["lado"] in ("BUY", "SELL")]
        self.assertEqual(len(llen), 1)
        self.assertEqual(float(llen[0]["acciones"]), 10)
        self.assertAlmostEqual(self.bot.pnl(inventario=False), -2.9)   # pagado
        self.assertAlmostEqual(self.bot.pnl(), 0.0)                     # pero las acciones estan en cartera
        # resuelve a favor del Si: cobramos 10
        self.m.ganadores["A"] = "Yes"
        self.bot.ciclo(AHORA + timedelta(minutes=2))
        self.assertAlmostEqual(self.bot.pnl(), 7.1)
        self.assertEqual(self.bot.ej.inventario(), {})

    def test_llenado_papel_con_token_v2(self):
        """data-api v2 dice el token de cada operacion (token_id) en vez de outcomeIndex."""
        self.bot.ciclo(AHORA)
        desde = self.bot.ej.abiertas()[0]["desde"]
        self.m.trades["A"] = [{"timestamp": desde + 9, "price": 0.28, "size": 10, "side": "SELL", "token_id": "si-A"},
                              {"timestamp": desde + 10, "price": 0.30, "size": 7, "side": "BUY", "token_id": "si-A"},
                              {"timestamp": desde + 11, "price": 0.30, "size": 4, "side": "BUY", "token_id": "no-A"}]
        # 2do: alguien compra Si a 0.30: no llena nada nuestro (no vendemos Si). 3ro: compra No a 0.30 = vende Si a 0.70: no
        self.bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertEqual(self.bot.ej.inventario(), {"si-A": 10})

    def test_parar_cancela_todo(self):
        self.bot.ciclo(AHORA)
        self.assertEqual(len(self.bot.ej.abiertas()), 2)
        open(os.path.join(self.dir, "PARAR"), "w").close()
        motivo = self.bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertIn("freno activo", motivo)
        self.assertEqual(self.bot.ej.abiertas(), [])

    def test_perdida_total_frena(self):
        self.bot.ciclo(AHORA)
        self.bot.est["resultados"]["X"] = {"dia": "2026-11-02", "cobrado": -40}
        motivo = self.bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertEqual(motivo, "perdida total")
        self.assertTrue(os.path.exists(os.path.join(self.dir, "PARAR_maker_papel")))

    def test_capital_limita_tamano(self):
        bot = maker.Maker(cfg(capital_usd=30, cajas=3), m=self.m, carpeta=self.dir)
        self.assertEqual(bot.elegir(AHORA), {})        # 25 acciones > 30/3 US$ por caja


class SDKFalso:
    """Imita al SDK: ordenes, "mis operaciones" (list_account_trades) y saldo por token."""
    def __init__(self):
        self.ordenes, self.cancel, self.redimidas, self.trades = {}, [], [], []
        self.saldos, self.falla_redeem, self.consultas_after = {}, False, []
        import types
        self.types = types

    def place_limit_order(self, token_id, price, size, side, post_only):
        assert post_only
        oid = f"o{len(self.ordenes) + len(self.cancel) + 1}"
        self.ordenes[oid] = self.types.SimpleNamespace(id=oid, asset_id=token_id, condition_id="A", side=side, price=price,
                                                        original_size=size, size_matched="0")
        return self.types.SimpleNamespace(ok=True, order_id=oid)

    def cancel_orders(self, order_ids):
        for i in order_ids:
            self.ordenes.pop(i, None)
            self.cancel.append(i)

    def cancel_all(self):
        self.cancel += list(self.ordenes)
        self.ordenes.clear()

    def list_open_orders(self):
        # como el SDK real: un paginador con iter_items(), no una lista
        return self.types.SimpleNamespace(iter_items=lambda: iter(list(self.ordenes.values())))

    def list_positions(self):
        raise AssertionError("el bot ya no debe consultar posiciones a data-api")

    def list_account_trades(self, after=None):
        self.consultas_after.append(int(after))
        sel = [t for t in self.trades if t.matched_at.timestamp() >= int(after)]
        return self.types.SimpleNamespace(iter_items=lambda: iter(sel))

    def llenar(self, oid, q, tid=None, cuando=None, estado="CONFIRMED", cid="A", token=None, lado=None, precio=None):
        """Un taker llena `q` acciones de nuestra orden `oid` (aunque ya no este abierta)."""
        o = self.ordenes.get(oid)
        token, lado, precio = token or o.asset_id, lado or o.side, precio or o.price
        if o:
            o.size_matched = str(float(o.size_matched) + q)
            if float(o.size_matched) >= float(o.original_size) - 1e-9:
                self.ordenes.pop(oid)              # llena del todo: desaparece de las abiertas
        mo = self.types.SimpleNamespace(order_id=oid, asset_id=token, side=lado, price=str(precio), matched_amount=str(q))
        otro = self.types.SimpleNamespace(order_id="ajena", asset_id=token, side=lado, price=str(precio), matched_amount="99")
        t = self.types.SimpleNamespace(id=tid or f"t{len(self.trades) + 1}", condition_id=cid, trader_side="MAKER",
                                       taker_order_id="x", asset_id="otro", side="SELL", price="0.1", size=str(q),
                                       status=estado, maker_orders=(mo, otro),
                                       matched_at=cuando or datetime.now(timezone.utc))
        self.trades.append(t)
        return t

    efectivo = 1000.0                                  # USDC en la cuenta (COLLATERAL)

    def get_balance_allowance(self, asset_type, token_id=None):
        if asset_type == "COLLATERAL":
            return self.types.SimpleNamespace(balance=int(self.efectivo * 1e6))
        assert asset_type == "CONDITIONAL"
        return self.types.SimpleNamespace(balance=int(self.saldos.get(token_id, 0) * 1e6))

    def redeem_positions(self, condition_id):
        if self.falla_redeem:
            raise RuntimeError("falta relayer api key")
        self.redimidas.append(condition_id)
        return self.types.SimpleNamespace(wait=lambda: None)

    def get_total_earnings_for_user_for_day(self, date):
        return [self.types.SimpleNamespace(earnings="1.25")]


def bot_real(sdk=None, carpeta=None):
    d = carpeta or tempfile.mkdtemp()
    m = MercadoFalso()
    maker.avisar = lambda t: None
    ej = maker.Real.__new__(maker.Real)
    ej._preparar(sdk or SDKFalso(), {})
    bot = maker.Maker(cfg(modo="real"), m=m, carpeta=d, ej=ej)
    ej.est = bot.est                       # como en la vida real: el ejecutor escribe en el estado del bot
    ej._preparar(ej.client, bot.est, bot.ops)
    return bot, ej, m, d


class PruebasReal(unittest.TestCase):
    def test_real_con_sdk_falso(self):
        bot, ej, m, d = bot_real()
        bot.ciclo(AHORA)
        self.assertEqual(len(ej.client.ordenes), 2)
        self.assertEqual(sorted(o.price for o in ej.client.ordenes.values()), ["0.29", "0.66"])
        # se llena media orden: se anota una vez sola aunque el CLOB la siga mostrando
        oid = [o.id for o in ej.client.ordenes.values() if o.price == "0.29"][0]
        ej.client.llenar(oid, 10)
        bot.ciclo(AHORA + timedelta(minutes=1))
        bot.ciclo(AHORA + timedelta(minutes=2))
        self.assertEqual(len([o for o in bot.ops() if o["lado"] == "BUY"]), 1)
        self.assertEqual(ej.inventario(), {"si-A": 10})
        self.assertEqual(ej.recompensa_dia("2026-11-02"), 1.25)
        ej.cancelar_todo()
        self.assertEqual(ej.client.ordenes, {})
        shutil.rmtree(d)

    def test_llenado_completo_se_anota(self):
        """Orden llenada del todo entre dos ciclos (desaparece de las abiertas): antes se perdia."""
        bot, ej, m, d = bot_real()
        bot.ciclo(AHORA)
        oid = [o.id for o in ej.client.ordenes.values() if o.price == "0.66"][0]
        ej.client.llenar(oid, 25)
        bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertEqual(ej.inventario(), {"no-A": 25})
        llen = [o for o in bot.ops() if o["lado"] in ("BUY", "SELL")]
        self.assertEqual([(o["token"], float(o["acciones"]), float(o["precio"])) for o in llen], [("no-A", 25, 0.66)])
        self.assertAlmostEqual(bot.pnl(inventario=False), -16.5)
        self.assertAlmostEqual(bot.pnl(), 0.0)      # 25 No en cartera al costo
        # con 25 No en mano, el lado "comprar Si" pasa a ser vender No
        self.assertIn(("no-A", "SELL"), {(o.asset_id, o.side) for o in ej.client.ordenes.values()})
        # la parte ajena de la misma operacion (otra orden) no cuenta
        self.assertNotIn("99", [o["acciones"] for o in llen])
        shutil.rmtree(d)

    def test_primer_arranque_reconstruye_y_recupera(self):
        """Caso 7-nov: el CSV tiene 2 de 27 acciones (orden llenada del todo con la PC apagada). Al arrancar con el
        codigo nuevo, el bot rearma el inventario desde el CLOB y anota solo lo que faltaba."""
        d = tempfile.mkdtemp()
        sdk = SDKFalso()
        ayer = datetime(2026, 11, 7, 20, 10, tzinfo=timezone.utc)
        with open(os.path.join(d, "maker_ops_real.csv"), "w", encoding="utf-8", newline="") as f:
            f.write(";".join(maker.COLS) + "\n")
            f.write("2026-11-07 19:10:00;real;karachi;34°C;K;si-K;orden_BUY;0.51;25;0.53;oK1\n")
            f.write("2026-11-07 19:20:00;real;karachi;34°C;K;si-K;BUY;0.51;2.13;0.53;taker a 0.51\n")
            f.write("2026-11-07 19:30:00;real;karachi;34°C;K;si-K;orden_BUY;0.51;25;0.53;oK2\n")
        sdk.llenar("oK1", 2.13, cuando=ayer, cid="K", token="si-K", lado="BUY", precio="0.51")
        sdk.llenar("oK1", 22.87, cuando=ayer, cid="K", token="si-K", lado="BUY", precio="0.51")
        sdk.llenar("oK2", 2.12, cuando=ayer, cid="K", token="si-K", lado="BUY", precio="0.51")
        sdk.llenar("manual", 50, cuando=ayer, cid="K", token="si-K", lado="BUY", precio="0.40")   # orden que no es del bot
        bot, ej, m, _ = bot_real(sdk, d)
        bot.ciclo(AHORA.replace(year=2026, month=11, day=8))
        self.assertEqual(sdk.consultas_after[0], int(maker.Real.DESDE_INICIAL))
        self.assertAlmostEqual(ej.inventario()["si-K"], 27.12)
        llen = [o for o in bot.ops() if o["lado"] == "BUY"]
        self.assertAlmostEqual(sum(float(o["acciones"]) for o in llen), 27.12)
        self.assertIn("recuperado", llen[-1]["detalle"])
        # el ciclo siguiente no vuelve a anotar nada y solo relee la ultima hora
        bot.ciclo(AHORA.replace(day=8) + timedelta(minutes=1))
        self.assertEqual(len([o for o in bot.ops() if o["lado"] == "BUY"]), len(llen))
        self.assertGreater(sdk.consultas_after[-1], int(maker.Real.DESDE_INICIAL))
        # solo lectura: coincide con la billetera
        sdk.saldos["si-K"] = 27.12 + 13                      # la billetera tiene ademas acciones viejas: no molesta
        self.assertEqual(bot.comparar_inventario(), 0)
        sdk.saldos["si-K"] = 2.13
        self.assertEqual(bot.comparar_inventario(), 1)
        shutil.rmtree(d)

    def test_operacion_fallida_se_deshace(self):
        bot, ej, m, d = bot_real()
        bot.ciclo(AHORA)
        oid = [o.id for o in ej.client.ordenes.values() if o.price == "0.29"][0]
        t = ej.client.llenar(oid, 10, estado="MATCHED")
        bot.ciclo(AHORA + timedelta(minutes=1))
        self.assertEqual(ej.inventario(), {"si-A": 10})
        t.status = "FAILED"
        bot.ciclo(AHORA + timedelta(minutes=2))
        self.assertEqual(ej.inventario(), {})
        self.assertAlmostEqual(bot.pnl(), 0)
        shutil.rmtree(d)

    def test_caja_soltada_se_cobra_y_avisa(self):
        """Caso Karachi: el bot dejo la caja con acciones; al resolver se cobra igual. Si el redeem falla
        (billetera proxy), se anota y se avisa una sola vez para cobrar a mano."""
        bot, ej, m, d = bot_real()
        avisos = []
        maker.avisar = avisos.append
        bot.ciclo(AHORA)
        oid = [o.id for o in ej.client.ordenes.values() if o.price == "0.29"][0]
        ej.client.llenar(oid, 10)
        bot.ciclo(AHORA + timedelta(minutes=1))
        bot.est["cajas"].clear()                          # la caja sale de las elegidas
        m.libros["si-A"] = ([(0.20, 50)], [(0.40, 50)])   # y ya no cumple la regla
        bot.ciclo(AHORA + timedelta(minutes=2))
        self.assertNotIn("A", bot.est["cajas"])
        ej.client.falla_redeem = True
        m.ganadores["A"] = "Yes"
        bot.ciclo(AHORA + timedelta(minutes=3))
        bot.ciclo(AHORA + timedelta(minutes=4))
        self.assertEqual(bot.est["resultados"]["A"]["cobrado"], 10)
        self.assertAlmostEqual(bot.pnl(), 7.1)
        self.assertEqual(ej.inventario(), {})
        self.assertEqual(sum("Claim" in a for a in avisos), 1)
        shutil.rmtree(d)

    def test_canje_real_por_el_sdk(self):
        """Real.fusionar llama merge_positions(condition_id, amount en unidades de 6 decimales).wait(). Si el relayer
        tarda (TimeoutError) pero la billetera ya no tiene los pares, cuenta como hecho; si los sigue teniendo, no."""
        bot, ej, m, d = bot_real()
        llamadas, modo = [], ["ok"]

        def merge_positions(condition_id, amount):
            llamadas.append((condition_id, amount))
            if modo[0] == "ok":
                return ej.client.types.SimpleNamespace(wait=lambda: None)
            if modo[0] == "salio":
                ej.client.saldos.update({"si-A": 0.0, "no-A": 5.0})
            raise TimeoutError("relayer")
        ej.client.merge_positions = merge_positions
        ej.est["inv"] = {"si-A": 20.0, "no-A": 25.0}
        self.assertTrue(ej.fusionar("A", ("si-A", "no-A"), 20.0))
        self.assertEqual(llamadas, [("A", 20000000)])
        self.assertEqual(ej.inventario(), {"no-A": 5.0})
        ej.est["inv"] = {"si-A": 20.0, "no-A": 25.0}
        ej.client.saldos.update({"si-A": 20.0, "no-A": 25.0})
        modo[0] = "falla"
        self.assertFalse(ej.fusionar("A", ("si-A", "no-A"), 20.0))
        self.assertEqual(ej.inventario(), {"si-A": 20.0, "no-A": 25.0})
        modo[0] = "salio"
        self.assertTrue(ej.fusionar("A", ("si-A", "no-A"), 20.0))
        self.assertEqual(ej.inventario(), {"no-A": 5.0})
        shutil.rmtree(d)

    def test_caja_vieja_sin_datos_se_busca_en_el_clob(self):
        bot, ej, m, d = bot_real()
        ej.est["inv"]["si-Z"] = 5.0
        ej.est["token_cid"]["si-Z"] = "Z"
        m.ganadores["Z"] = "No"
        viejo_get = m.get

        def get(url, params=None, timeout=None):
            if url.endswith("/markets/Z"):
                return Resp({"question": "Karachi 34°C", "market_slug": "karachi",
                             "tokens": [{"token_id": "si-Z", "outcome": "Yes"}, {"token_id": "no-Z", "outcome": "No"}]})
            return viejo_get(url, params, timeout)
        m.get = get
        bot.liquidar()
        self.assertEqual(bot.est["resultados"]["Z"]["cobrado"], 0)
        self.assertEqual(ej.inventario(), {})
        shutil.rmtree(d)




class PruebasFreno(unittest.TestCase):
    def test_compras_sin_resolver_no_frenan(self):
        """Acciones compradas y todavia en cartera no son perdida: el freno por perdida total/diaria no salta (7-nov real)."""
        import types
        d = tempfile.mkdtemp()
        c = cfg(modo="real")
        c["maker"]["max_perdida_total"], c["maker"]["max_perdida_dia"] = 30, 10
        inv = {"T1": 25.0, "T2": 27.12}
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        bot = maker.Maker(c, m=MercadoFalso(), carpeta=d, ej=ej)
        hoy = AHORA.strftime("%Y-%m-%d")
        for t, q, p in (("T1", 25, 0.40), ("T2", 27.12, 0.51)):
            bot.anotar(momento_utc=f"{hoy} 18:00:00", modo="real", evento="e", caja="c", condition_id="A", token=t,
                       lado="BUY", precio=p, acciones=q, medio="", detalle="recuperado")
            bot.est["costo"][t] = {"precio": p, "acciones": q}
        self.assertAlmostEqual(bot.pnl(inventario=False), -23.83, places=2)   # lo pagado
        self.assertAlmostEqual(bot.pnl(), 0.0, places=2)                      # pero las acciones estan en cartera
        self.assertAlmostEqual(bot.pnl(hoy), 0.0, places=2)
        self.assertIsNone(bot.freno(AHORA))
        self.assertFalse(bot.frenado())
        inv["T1"] = 0.0                                                       # T1 se resolvio en contra sin cobro
        self.assertAlmostEqual(bot.pnl(), -10.0, places=2)
        shutil.rmtree(d)

    def test_perdida_del_dia_ventas_y_resoluciones(self):
        """El freno diario mira ventas al costo medio y cajas resueltas ese dia (cobrado - costo), no las compras."""
        import types
        d = tempfile.mkdtemp()
        c = cfg(modo="real")
        c["maker"]["max_perdida_dia"] = 10
        inv = {"T1": 0.0}
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        bot = maker.Maker(c, m=MercadoFalso(), carpeta=d, ej=ej)
        hoy = AHORA.strftime("%Y-%m-%d")
        bot.anotar(momento_utc="2026-11-01 10:00:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="BUY", precio=0.40, acciones=50, medio="", detalle="")
        bot.est["costo"]["T1"] = {"precio": 0.40, "acciones": 25}
        bot.anotar(momento_utc=f"{hoy} 09:00:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="SELL", precio=0.43, acciones=25, medio="", detalle="")
        self.assertAlmostEqual(bot.pnl(hoy), 0.75, places=2)                  # 25 * (0.43 - 0.40)
        self.assertIsNone(bot.freno(AHORA))
        bot.est["resultados"]["A"] = {"dia": hoy, "gano": "No", "cobrado": 0, "costo": 10.0, "caja": "c", "evento": "e"}
        self.assertAlmostEqual(bot.pnl(hoy), -9.25, places=2)
        bot.est["resultados"]["A"]["costo"] = 12.0
        self.assertAlmostEqual(bot.pnl(hoy), -11.25, places=2)
        self.assertIn("perdida del dia", bot.freno(AHORA))
        self.assertFalse(bot.frenado())                                       # el diario no deja archivo PARAR
        shutil.rmtree(d)

    def test_perdida_del_dia_usa_el_costo_de_ese_momento(self):
        """Tokio 14 °C (8-nov): vendio a 0,12 lo comprado a 0,15 (−0,75) y despues recompro a 0,33. La perdida del dia
        es −0,75, no 25 × (0,12 − 0,33) = −5,25 como daba midiendo contra el costo actual."""
        import types
        d = tempfile.mkdtemp()
        inv = {"T1": 25.0}
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        bot = maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d, ej=ej)
        hoy = AHORA.strftime("%Y-%m-%d")
        for hora, lado, p in (("09:00", "BUY", 0.15), ("10:00", "SELL", 0.12), ("14:00", "BUY", 0.33)):
            bot.anotar(momento_utc=f"{hoy} {hora}:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                       lado=lado, precio=p, acciones=25, medio="", detalle="")
        bot.est["costo"]["T1"] = {"precio": 0.33, "acciones": 25}             # costo actual: el de la recompra
        self.assertAlmostEqual(bot.pnl(hoy), -0.75, places=2)
        self.assertAlmostEqual(bot.pnl(), -0.75, places=2)                    # total: -3.75 - 3 + 8.25 pagado/cobrado, +8.25 cartera
        # una venta de ayer no cuenta hoy; la de hoy se mide contra el costo medio acumulado (0,15 y 0,33 -> 0,24)
        bot.anotar(momento_utc=f"{hoy} 15:00:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="BUY", precio=0.15, acciones=25, medio="", detalle="")
        bot.anotar(momento_utc=f"{hoy} 16:00:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="SELL", precio=0.30, acciones=50, medio="", detalle="")
        self.assertAlmostEqual(bot.pnl(hoy), -0.75 + 50 * (0.30 - 0.24), places=2)
        shutil.rmtree(d)

    def test_alertas_casos_raros(self):
        """Pedido de Agus 8-nov: avisar al celular compras seguidas bajando, ventas bajo el costo y perdida del dia cerca
        del freno. Solo avisan: no cambian ordenes."""
        import types
        d = tempfile.mkdtemp()
        cola = []
        ej = types.SimpleNamespace(inventario=lambda: {}, abiertas=lambda: [], cancelar_todo=lambda: None, nombre="real",
                                   llenados=lambda: [cola.pop(0)] if cola else [])
        bot = maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d, ej=ej)
        avisos = []
        bot.avisar = avisos.append
        bot.est["cajas"]["A"] = {"caja": "14C", "evento": "tokio"}
        alertas = lambda: [a for a in avisos if a.startswith("ALERTA")]   # noqa: E731

        def llena(lado, p, q=25, minutos=0):
            cola.append(({"cid": "A", "token": "T1", "lado": lado, "precio": p}, q, "maker"))
            bot.revisar_llenados(AHORA + timedelta(minutes=minutos))

        llena("BUY", 0.40)
        llena("BUY", 0.4000004, minutos=5)                                # ruido de redondeo: no es escalon
        llena("BUY", 0.38, minutos=10)
        self.assertEqual(alertas(), [])
        llena("BUY", 0.36, minutos=20)                                     # tercer escalon bajando
        self.assertEqual(len(alertas()), 1)
        self.assertIn("3 compras seguidas bajando", alertas()[0])
        self.assertIn("0.40 > 0.38 > 0.36", alertas()[0])
        llena("BUY", 0.36, q=5, minutos=21)                                # mismo precio (llenado parcial): no repite
        self.assertEqual(len(alertas()), 1)
        llena("BUY", 0.34, minutos=30)                                     # otro escalon: avisa de nuevo
        self.assertEqual(len(alertas()), 2)
        # venta 1 c bajo el costo: nada; 7 c bajo el costo: alerta
        costo = bot.est["costo"]["T1"]["precio"]
        llena("SELL", round(costo - 0.01, 2), minutos=40)
        self.assertEqual(len(alertas()), 2)
        llena("SELL", 0.30, minutos=50)
        self.assertEqual(len(alertas()), 3)
        self.assertIn("vendio 25 acc a 0.30", alertas()[2])
        llena("BUY", 0.33, q=10, minutos=51)
        llena("SELL", 0.30, q=10, minutos=52)                              # parcial de la misma venta: no repite
        self.assertEqual(len(alertas()), 3)
        # despues de vender, la escalera arranca de cero
        llena("BUY", 0.29, minutos=60)
        self.assertEqual(len(alertas()), 3)
        # perdida del dia: vender 25 a 0,05 con costo ~0,32 => -6,8 + lo anterior pasa el 70 % de 10
        llena("SELL", 0.05, minutos=70)
        dia = [a for a in alertas() if "perdida del dia" in a]
        self.assertEqual(len(dia), 1)
        llena("BUY", 0.05, minutos=80)
        llena("SELL", 0.01, minutos=90)
        self.assertEqual(len([a for a in alertas() if "perdida del dia" in a]), 1)   # una vez por dia
        # apagadas
        bot.cfg["maker"]["alertas"] = False
        n = len(alertas())
        llena("SELL", 0.01, minutos=100)
        self.assertEqual(len(alertas()), n)
        shutil.rmtree(d)

    def test_canje_de_pares(self):
        """9-nov: con acciones Si y No de la misma caja se canjean min(Si, No) pares por US$ 1 cada uno. Se anotan como
        dos ventas para que el resultado sea pares x (1 - costo Si - costo No); se cancelan antes las ventas abiertas."""
        import types
        d = tempfile.mkdtemp()
        inv = {"si-A": 40.0, "no-A": 15.3}
        canjes, canceladas = [], []
        sale = [True]

        def fusionar(cid, tokens, q):
            canjes.append((cid, tokens, q))
            if sale[0]:
                for t in tokens:
                    inv[t] -= q
            return sale[0]
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), llenados=lambda: [], cancelar_todo=lambda: None,
                                   nombre="real", fusionar=fusionar, cancelar=canceladas.extend,
                                   abiertas=lambda: [{"id": "v1", "token": "no-A", "lado": "SELL"},
                                                     {"id": "c1", "token": "si-A", "lado": "BUY"},
                                                     {"id": "v2", "token": "otro", "lado": "SELL"}])
        bot = maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d, ej=ej)
        avisos = []
        bot.avisar = avisos.append
        fin = (AHORA + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        bot.est["cajas"]["A"] = {"caja": "22C", "evento": "tel-aviv", "si": "si-A", "no": "no-A", "fin": fin, "medio": 0.40}
        bot.est["costo"] = {"si-A": {"precio": 0.35, "acciones": 40}, "no-A": {"precio": 0.55, "acciones": 15.3}}
        antes_total = bot.pnl()
        self.assertEqual(bot.fusionar_pares(AHORA), 1)
        self.assertEqual(canjes, [("A", ("si-A", "no-A"), 15.3)])
        self.assertEqual(canceladas, ["v1"])                                  # solo ventas de esa caja
        self.assertEqual(inv, {"si-A": 24.7, "no-A": 0.0})
        self.assertAlmostEqual(bot.est["costo"]["si-A"]["acciones"], 24.7)
        hoy = bot.dia_local(AHORA)
        ops = [o for o in bot.ops() if o["detalle"] == "canje Si+No"]
        self.assertEqual([(o["token"], o["lado"], float(o["precio"])) for o in ops],
                         [("si-A", "SELL", 0.40), ("no-A", "SELL", 0.60)])
        # sin compras anotadas, el costo medio de la venta es su propio precio: lo que cuenta es el total y el costo
        self.assertAlmostEqual(bot.pnl(), antes_total + 15.3 * (1 - 0.35 - 0.55), delta=0.011)  # pnl redondea
        self.assertTrue(any("canje de 15 pares" in a for a in avisos))
        self.assertEqual(bot.fusionar_pares(AHORA), 0)                        # ya no quedan pares
        # con compras anotadas el dia da pares x (1 - costo Si - costo No)
        d2 = tempfile.mkdtemp()
        inv.update({"si-A": 25.0, "no-A": 25.0})
        bot2 = maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d2, ej=ej)
        bot2.avisar = lambda t: None
        bot2.est["cajas"]["A"] = dict(bot.est["cajas"]["A"])
        bot2.est["costo"] = {"si-A": {"precio": 0.35, "acciones": 25}, "no-A": {"precio": 0.55, "acciones": 25}}
        for t, p in (("si-A", 0.35), ("no-A", 0.55)):
            bot2.anotar(momento_utc=AHORA.strftime("%Y-%m-%d %H:%M:%S"), modo="real", evento="e", caja="c",
                        condition_id="A", token=t, lado="BUY", precio=p, acciones=25, medio="", detalle="")
        bot2.fusionar_pares(AHORA)
        self.assertAlmostEqual(bot2.pnl(hoy), 25 * (1 - 0.35 - 0.55), places=2)
        # menos que el minimo, caja terminada o resuelta: no canjea
        inv.update({"si-A": 4.0, "no-A": 4.0})
        self.assertEqual(bot2.fusionar_pares(AHORA), 0)
        inv.update({"si-A": 30.0, "no-A": 30.0})
        self.assertEqual(bot2.fusionar_pares(AHORA + timedelta(days=2)), 0)
        bot2.est["resultados"]["A"] = {"dia": hoy, "cobrado": 0}
        self.assertEqual(bot2.fusionar_pares(AHORA), 0)
        del bot2.est["resultados"]["A"]
        # si el canje falla: un aviso, no anota nada y no reintenta (ni cancela ventas) por 30 min
        sale[0] = False
        n_ops, canceladas[:] = len(bot2.ops()), []
        avisos2 = []
        bot2.avisar = avisos2.append
        self.assertEqual(bot2.fusionar_pares(AHORA), 0)
        self.assertEqual((len(bot2.ops()), canceladas, len(avisos2)), (n_ops, ["v1"], 1))
        self.assertEqual(bot2.fusionar_pares(AHORA + timedelta(minutes=10)), 0)
        self.assertEqual((canceladas, len(avisos2)), (["v1"], 1))
        sale[0] = True
        self.assertEqual(bot2.fusionar_pares(AHORA + timedelta(minutes=31)), 1)
        self.assertNotIn("A", bot2.est["canje_fallo"])
        bot2.cfg["maker"]["fusionar_pares_min"] = 0                           # 0 apaga
        inv.update({"si-A": 30.0, "no-A": 30.0})
        self.assertEqual(bot2.fusionar_pares(AHORA), 0)
        shutil.rmtree(d)
        shutil.rmtree(d2)

    def test_valor_a_mercado(self):
        """El resumen valua las acciones al medio actual del libro ademas del costo (8-nov: la web mostraba 5 menos)."""
        import types
        d = tempfile.mkdtemp()
        inv = {"T1": 10.0, "T2": 20.0}
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        m = MercadoFalso()
        m.libro = lambda t: ([(0.40, 100)], [(0.42, 100)]) if t == "T1" else ([], [])
        bot = maker.Maker(cfg(modo="real"), m=m, carpeta=d, ej=ej)
        bot.est["costo"] = {"T1": {"precio": 0.50, "acciones": 10}, "T2": {"precio": 0.30, "acciones": 20}}
        valor, costo = bot.valor_mercado()
        self.assertAlmostEqual(costo, 11.0, places=2)                         # 10*0.50 + 20*0.30
        self.assertAlmostEqual(valor, 4.1 + 6.0, places=2)                    # T1 al medio 0,41; T2 sin libro: al costo
        shutil.rmtree(d)

    def test_freno_diario_sin_cajas_resueltas(self):
        """Con freno_dia_cuenta_resueltas en false una caja que resuelve en contra (Nueva York 9-nov, -11,97) no frena el
        dia; las ventas del dia si, y el freno total sigue contando la resolucion."""
        import types
        d = tempfile.mkdtemp()
        inv = {"T1": 0.0, "T2": 50.0}
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        bot = maker.Maker(cfg(modo="real", max_perdida_dia=10, freno_dia_cuenta_resueltas=False), m=MercadoFalso(),
                          carpeta=d, ej=ej)
        hoy = AHORA.strftime("%Y-%m-%d")
        bot.anotar(momento_utc="2026-11-01 10:00:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="BUY", precio=0.4058, acciones=29.5, medio="", detalle="")
        bot.est["resultados"]["A"] = {"dia": hoy, "gano": "Yes", "cobrado": 0, "costo": 11.97, "caja": "c", "evento": "e"}
        self.assertAlmostEqual(bot.pnl(hoy), -11.97, places=2)                # el resultado del dia la sigue mostrando
        self.assertAlmostEqual(bot.perdida_dia_freno(hoy), 0.0, places=2)     # pero el freno diario no la cuenta
        self.assertIsNone(bot.freno(AHORA))
        self.assertAlmostEqual(bot.pnl(), -11.97, places=2)                   # y el total si
        bot.anotar(momento_utc="2026-11-01 11:00:00", modo="real", evento="e", caja="c2", condition_id="B", token="T2",
                   lado="BUY", precio=0.50, acciones=100, medio="", detalle="")
        bot.est["costo"]["T2"] = {"precio": 0.50, "acciones": 50}
        bot.anotar(momento_utc=f"{hoy} 09:00:00", modo="real", evento="e", caja="c2", condition_id="B", token="T2",
                   lado="SELL", precio=0.29, acciones=50, medio="", detalle="")
        self.assertAlmostEqual(bot.perdida_dia_freno(hoy), -10.5, places=2)   # ventas del dia: 50 * (0.29 - 0.50)
        self.assertIn("perdida del dia -10.50", bot.freno(AHORA))
        bot.cfg["maker"]["freno_dia_cuenta_resueltas"] = True                 # como antes: cuenta todo
        self.assertAlmostEqual(bot.perdida_dia_freno(hoy), -22.47, places=2)
        bot.cfg["maker"]["max_perdida_total"] = 20                            # el total frena con resolucion + ventas
        self.assertEqual(bot.freno(AHORA), "perdida total")
        shutil.rmtree(d)

    def test_dia_en_hora_de_uruguay(self):
        """El 'dia' del freno es el de Uruguay (UTC-3): una venta a las 02:30Z del 9-nov cuenta para el 8-nov local."""
        import types
        from datetime import datetime, timezone
        d = tempfile.mkdtemp()
        ej = types.SimpleNamespace(inventario=lambda: {}, abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        bot = maker.Maker(cfg(modo="real", max_perdida_dia=10), m=MercadoFalso(), carpeta=d, ej=ej)
        self.assertEqual(bot.dia_local("2026-11-09 02:30:00"), "2026-11-08")
        self.assertEqual(bot.dia_local("2026-11-09 03:00:00"), "2026-11-09")
        bot.anotar(momento_utc="2026-11-08 20:00:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="BUY", precio=0.50, acciones=50, medio="", detalle="")
        bot.anotar(momento_utc="2026-11-09 02:30:00", modo="real", evento="e", caja="c", condition_id="A", token="T1",
                   lado="SELL", precio=0.28, acciones=50, medio="", detalle="")
        self.assertAlmostEqual(bot.pnl("2026-11-08"), -11.0, places=2)
        self.assertAlmostEqual(bot.pnl("2026-11-09"), 0.0, places=2)
        a = datetime(2026, 11, 9, 2, 45, tzinfo=timezone.utc)                  # 23:45 del 8-nov en Uruguay: frenado
        self.assertIn("sigue a las 00:00 de Uruguay, 03:00Z", bot.freno(a))
        a = datetime(2026, 11, 9, 3, 5, tzinfo=timezone.utc)                   # 00:05 del 9-nov: opera de nuevo
        self.assertIsNone(bot.freno(a))
        shutil.rmtree(d)


class PruebasVentasSoltadas(unittest.TestCase):
    def _bot(self, d, inv):
        import types
        self.puestas = []
        ej = types.SimpleNamespace(inventario=lambda: dict(inv), abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, cancelar=lambda ids: None, nombre="real",
                                   colocar=lambda token, cid, lado, precio, acciones, es_si:
                                   self.puestas.append((token, cid, lado, precio, acciones, es_si)) or f"o{len(self.puestas)}")
        bot = maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d, ej=ej)
        # caja soltada: ya no esta en est["cajas"], pero queda en meta y con acciones
        bot.est.setdefault("meta", {})["Z"] = {"evento": "e", "caja": "34°C", "si": "si-A", "no": "no-A", "tick": 0.01,
                                                 "fin": (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        return bot

    def test_vende_lo_que_queda_en_caja_soltada(self):
        d = tempfile.mkdtemp()
        bot = self._bot(d, {"no-A": 27.12})
        v = bot.ventas_soltadas({}, bot.ej.inventario())
        self.assertEqual(len(v), 1)
        cid, _, _, medio, token, lado, precio, q, es_si = v[0]
        self.assertEqual((cid, token, lado, es_si, q), ("Z", "no-A", "SELL", False, 27.12))
        self.assertAlmostEqual(medio, 0.315)                                   # libro si-A: 0.30 / 0.33
        self.assertAlmostEqual(precio, 0.71)                                   # 1 - 0.315 + 0.02 = 0.705 -> 0.71 (arriba)
        bot.renovar({})
        self.assertEqual([p[:4] for p in self.puestas], [("no-A", "Z", "SELL", 0.71)])
        bot.est["costo"]["no-A"] = {"precio": 0.75, "acciones": 27.12}      # compradas mas caras que el medio
        v = bot.ventas_soltadas({}, bot.ej.inventario())
        self.assertAlmostEqual(v[0][6], 0.76)                                 # costo + 1 tick: solo vende con ganancia
        bot.est["costo"]["no-A"] = {"precio": 0.50, "acciones": 27.12}
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.71)
        shutil.rmtree(d)

    def test_piso_de_costo_dura_unas_horas(self):
        """Plata trabada (9-nov): con soltada_piso_horas 6 el piso de costo vale 6 h desde que la caja quedo soltada con
        acciones; despues vende a medio + 1 tick aunque sea bajo el costo, y avisa una sola vez."""
        d = tempfile.mkdtemp()
        bot = self._bot(d, {"no-A": 25.0})
        bot.cfg["maker"]["soltada_piso_horas"] = 6
        avisos = []
        bot.avisar = avisos.append
        bot.est["costo"]["no-A"] = {"precio": 0.75, "acciones": 25.0}        # medio del No 0,685: 6,5 c bajo el costo
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.76)   # recien soltada: costo + 1 tick
        self.assertIn("Z", bot.est["soltada_desde"])
        bot.est["soltada_desde"]["Z"] = (datetime.now(timezone.utc) - timedelta(hours=5, minutes=50)).isoformat()
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.76)   # 5 h 50: todavia con piso
        self.assertEqual(avisos, [])
        bot.est["soltada_desde"]["Z"] = (datetime.now(timezone.utc) - timedelta(hours=6, minutes=1)).isoformat()
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.70)   # 0,685 + 0,01 -> 0,70 (arriba)
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.70)
        self.assertEqual(len(avisos), 1)                                      # avisa una vez
        self.assertIn("se saca el piso de costo", avisos[0])
        self.assertEqual(bot.ventas_soltadas({"Z": {}}, bot.ej.inventario()), [])   # vuelve a elegirse: el reloj se borra
        self.assertNotIn("Z", bot.est["soltada_desde"])
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.76)   # soltada de nuevo: piso otra vez
        del bot.cfg["maker"]["soltada_piso_horas"]                             # sin la clave: piso siempre, como antes
        bot.est["soltada_desde"]["Z"] = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        self.assertAlmostEqual(bot.ventas_soltadas({}, bot.ej.inventario())[0][6], 0.76)
        shutil.rmtree(d)

    def test_caja_soltada_sin_meta_se_busca_por_token(self):
        d = tempfile.mkdtemp()
        bot = self._bot(d, {"no-A": 27.12})
        bot.est["meta"].clear()
        bot.ej.cid_de = lambda t: "Z" if t == "no-A" else None
        fin = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        bot.m.get = lambda url, params=None, timeout=None: Resp({"tokens": [{"token_id": "si-A"}, {"token_id": "no-A"}],
                                                                "question": "34°C", "market_slug": "karachi",
                                                                "end_date_iso": fin, "minimum_tick_size": "0.01"})
        v = bot.ventas_soltadas({}, bot.ej.inventario())
        self.assertEqual(len(v), 1)
        self.assertEqual(bot.est["meta"]["Z"]["caja"], "34°C")
        shutil.rmtree(d)

    def test_no_vende_si_resolvio_termino_o_es_poco(self):
        d = tempfile.mkdtemp()
        bot = self._bot(d, {"no-A": 27.12, "si-A": 3})
        self.assertEqual(len(bot.ventas_soltadas({}, bot.ej.inventario())), 1)  # 3 acciones de Si no llegan al minimo
        self.assertEqual(bot.ventas_soltadas({"Z": {}}, bot.ej.inventario()), [])  # sigue elegida: la cotiza cotizar()
        bot.est["resultados"]["Z"] = {"dia": "2026-11-08", "cobrado": 0}
        self.assertEqual(bot.ventas_soltadas({}, bot.ej.inventario()), [])
        del bot.est["resultados"]["Z"]
        bot.est["meta"]["Z"]["fin"] = "2026-01-01T00:00:00Z"
        self.assertEqual(bot.ventas_soltadas({}, bot.ej.inventario()), [])
        shutil.rmtree(d)


class PruebasSinSaldo(unittest.TestCase):
    def test_falta_de_saldo_no_cuenta_como_error(self):
        import types
        d = tempfile.mkdtemp()
        puestas, intentos = [], []

        def colocar(token, cid, lado, precio, acciones, es_si):
            intentos.append(lado)
            if lado == "BUY":
                raise RuntimeError("RequestRejectedError: not enough balance / allowance")
            puestas.append((token, lado, precio))
            return f"o{len(puestas)}"
        ej = types.SimpleNamespace(inventario=lambda: {"no-A": 30.0}, abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, cancelar=lambda ids: None, colocar=colocar, nombre="real")
        bot = maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d, ej=ej)
        avisos = []
        bot.avisar = avisos.append
        c = {"cid": "A", "evento": "e", "si": "si-A", "no": "no-A", "medio": 0.615, "tick": 0.01, "tam": 25, "caja": "17°C"}
        c2 = dict(c, cid="B", si="si-B", no="no-B", caja="18°C")
        errores = bot.renovar({"A": c, "B": c2})
        self.assertEqual(errores, 0)                                          # falta de saldo no es error
        self.assertEqual(intentos.count("BUY"), 1)                            # tras la primera compra fallida no insiste
        self.assertEqual(len(puestas), 1)                                     # la venta de No si se puso
        self.assertEqual(len(avisos), 1)
        bot.renovar({"A": c, "B": c2})
        self.assertEqual(len(avisos), 1)                                      # una vez por racha
        bot.est["sin_saldo_avisado"] = False                                  # la racha se corto un ciclo (9-nov: 11 avisos)
        bot.renovar({"A": c, "B": c2})
        self.assertEqual(len(avisos), 1)                                      # no avisa de nuevo antes de 6 h
        bot.est["sin_saldo_avisado"], bot.est["sin_saldo_ts"] = False, time.time() - 7 * 3600
        bot.renovar({"A": c, "B": c2})
        self.assertEqual(len(avisos), 2)                                      # pasadas 6 h si
        self.assertTrue(maker.Maker.es_falta_de_saldo(RuntimeError("InsufficientAllowanceError")))
        self.assertFalse(maker.Maker.es_falta_de_saldo(RuntimeError("timeout")))
        shutil.rmtree(d)


class PruebasEfectivo(unittest.TestCase):
    """8-nov-2026 (pedido de Agus): el bot compra solo con la plata que tiene de verdad y nunca por encima de capital_usd."""
    def _bot(self, efectivo, abiertas=(), inv=None, capital=100):
        import types
        d = tempfile.mkdtemp()
        puestas = []

        def colocar(token, cid, lado, precio, acciones, es_si):
            puestas.append((cid, token, lado, precio, acciones))
            return f"o{len(puestas)}"
        ej = types.SimpleNamespace(inventario=lambda: dict(inv or {}), abiertas=lambda: list(abiertas), llenados=lambda: [],
                                   cancelar_todo=lambda: None, cancelar=lambda ids: None, colocar=colocar, nombre="real",
                                   efectivo=lambda: efectivo)
        bot = maker.Maker(cfg(modo="real", capital_usd=capital), m=MercadoFalso(), carpeta=d, ej=ej)
        bot.avisos = []
        bot.avisar = bot.avisos.append
        return bot, puestas, d

    def _cajas(self):
        a = {"cid": "A", "evento": "e", "si": "si-A", "no": "no-A", "medio": 0.43, "tick": 0.01, "tam": 25, "caja": "22°C",
             "rec_pes": 2.0}
        b = dict(a, cid="B", si="si-B", no="no-B", caja="23°C", rec_pes=5.0)
        return {"A": a, "B": b}

    def test_poco_efectivo_no_intenta_comprar(self):
        # el caso real del 8-nov 02:04Z: 22,68 en la cuenta, 13,75 reservados, compras de 25 a 0,41 (10,25) no entran
        # (la compra de Si-B ya esta puesta y se mantiene: queda reservada)
        bot, puestas, d = self._bot(22.68, abiertas=[{"id": "x", "token": "si-B", "lado": "BUY", "precio": 0.41, "acciones": 25}],
                                    inv={"no-A": 30.0})
        errores = bot.renovar(self._cajas())
        self.assertEqual(errores, 0)
        self.assertEqual([p[2] for p in puestas], ["SELL"])                   # solo la venta de No-A (no necesita plata)
        self.assertEqual(bot.est["efectivo"]["libre"], 12.43)                # 22,68 - 10,25 reservados; 13,75 no entra
        self.assertEqual(bot.est["efectivo"]["reservado"], 10.25)
        self.assertEqual(len(bot.avisos), 1)
        self.assertIn("12.43", bot.avisos[0])
        shutil.rmtree(d)

    def test_presupuesto_va_a_la_caja_que_mas_paga(self):
        # alcanza para dos compras (2 x 10,25 = 20,5): van a la caja B (rec_pes 5) antes que a la A (rec_pes 2)
        bot, puestas, d = self._bot(24.0)
        bot.renovar(self._cajas())
        self.assertEqual([p[0] for p in puestas], ["B", "B"])
        self.assertEqual(bot.est["efectivo"]["libre"], 24.0)                 # medido antes de poner las ordenes
        # con 21: B Si (10,25), B No (13,75) no entra, A Si (10,25) si
        bot2, puestas2, d2 = self._bot(21.0)
        bot2.renovar(self._cajas())
        self.assertEqual([(p[0], p[1]) for p in puestas2], [("B", "si-B"), ("A", "si-A")])
        shutil.rmtree(d2)
        shutil.rmtree(d)

    def test_sin_tope_de_capital_reinvierte(self):
        # 500 en la cuenta y 90 ya en acciones: compra igual (decision de Agus 8-nov: sin tope de 100, reinvierte)
        bot, puestas, d = self._bot(500.0, inv={"si-Z": 150.0})
        bot.est["costo"]["si-Z"] = {"precio": 0.6, "acciones": 150.0}
        bot.renovar(self._cajas())
        self.assertEqual(len([p for p in puestas if p[2] == "BUY"]), 4)
        self.assertEqual(bot.est["efectivo"], {"cuenta": 500.0, "reservado": 0, "libre": 500.0, "acciones_costo": 90.0})
        shutil.rmtree(d)

    def test_sin_lectura_de_efectivo_no_limita(self):
        bot, puestas, d = self._bot(None)
        bot.ej.efectivo = lambda: (_ for _ in ()).throw(RuntimeError("clob caido"))
        libre, cuenta, reservado = bot.efectivo_libre()
        self.assertEqual((libre, cuenta, reservado), (None, None, 0))
        bot.renovar(self._cajas())                                            # sin lectura: intenta igual (como antes)
        self.assertEqual(len(puestas), 4)
        self.assertEqual(bot.avisos, [])
        shutil.rmtree(d)

    def test_no_agrega_caja_que_no_puede_cotizar(self):
        d = tempfile.mkdtemp()
        m = MercadoFalso()
        bot = maker.Maker(cfg(), m=m, carpeta=d)                               # papel: efectivo = capital - acciones
        bot.est["costo"]["si-Z"] = {"precio": 0.5, "acciones": 280.0}
        bot.ej.est["inventario"]["si-Z"] = 280.0                              # 140 de 150 en acciones -> 10 libres
        self.assertEqual(bot.elegir(AHORA), {})                               # la caja A necesita 25 x 0,96 = 24
        bot.ej.est["inventario"]["si-Z"] = 200.0                              # 100 en acciones -> 50 libres
        self.assertEqual(list(bot.elegir(AHORA)), ["A"])
        shutil.rmtree(d)


    def test_compras_de_cajas_soltadas_cuentan_como_libres(self):
        """9-nov 12:00Z: al vencer las cajas del dia siguiente, sus compras abiertas (que renovar cancela en ese mismo
        ciclo) no tienen que trabar la entrada de cajas nuevas."""
        bot, puestas, d = self._bot(30.0, abiertas=[{"id": "x", "token": "si-Z", "lado": "BUY", "precio": 0.5, "acciones": 25}])
        self.assertEqual(list(bot.elegir(AHORA)), ["A"])                     # 30 - 12,5 reservados = 17,5 no alcanza
        self.assertEqual(bot.est["efectivo"]["libre"], 17.5)                  # pero Z no esta elegida: cuenta como libre
        shutil.rmtree(d)

    def test_rota_aunque_falten_cajas_por_efectivo(self):
        """10-nov: con la plata en acciones el bot quedo con 2 cajas de 3 y una esperaba 0,275 US$/dia; la rotacion solo
        corria con las 3 completas. Ahora rota igual: suelta la peor y sus compras abiertas pagan la que entra."""
        compras_a = [{"id": "a1", "token": "si-A", "lado": "BUY", "precio": 0.29, "acciones": 25},
                     {"id": "a2", "token": "no-A", "lado": "BUY", "precio": 0.66, "acciones": 25}]
        bot, puestas, d = self._bot(30.0, abiertas=compras_a)
        self.assertEqual(list(bot.elegir(AHORA)), ["A"])                     # 1 caja de 3: no hay plata para otra
        bot.m.libros["si-B"] = ([(0.39, 30)], [(0.41, 30)])                  # B se aprieta (pozo 90)
        bot.m.libros["si-A"] = ([(0.31, 5000), (0.30, 100)], [(0.32, 5000)])  # A se llena de rivales
        self.assertEqual(list(bot.elegir(AHORA + timedelta(minutes=10))), ["A"])   # B no entra: 6,25 libres, necesita 24
        self.assertEqual(list(bot.elegir(AHORA + timedelta(minutes=31))), ["B"])   # rota: las compras de A la pagan
        self.assertIn("A", bot.est["rotadas"])
        self.assertTrue(any("rotacion" in a for a in bot.avisos))
        shutil.rmtree(d)


class PruebasGuardiaMetar(unittest.TestCase):
    """Guardia METAR fina (8-nov-2026): soltar cajas ya decididas por la temperatura observada; piso de compra 0,10."""
    EST = {"chengdu": {"icao": "ZUUU", "tz": "Asia/Shanghai", "en_f": False},
           "nyc": {"icao": "KLGA", "tz": "America/New_York", "en_f": True}}

    @staticmethod
    def rep(hora_utc, temp=None, raw="", tipo="METAR", dia=8):
        from datetime import datetime, timezone
        t = int(datetime(2026, 11, dia, hora_utc, 0, tzinfo=timezone.utc).timestamp())
        return {"obsTime": t, "metarType": tipo, "temp": temp, "rawOb": raw}

    def test_parseo(self):
        import guardia_metar as g
        self.assertEqual(g.evento_de("highest-temperature-in-tel-aviv-on-november-8-2026")[0:2], ("max", "tel-aviv"))
        self.assertEqual(g.evento_de("lowest-temperature-in-nyc-on-november-10-2026")[2].day, 10)
        self.assertIsNone(g.evento_de("btc-up-or-down"))
        self.assertEqual(g.caja_de("17°C"), ("exacta", 17, "C"))
        self.assertEqual(g.caja_de("35°C or below"), ("hasta", 35, "C"))
        self.assertEqual(g.caja_de("55°F or higher"), ("desde", 55, "F"))
        self.assertEqual(g.caja_de("-3°C"), ("exacta", -3, "C"))
        self.assertIsNone(g.caja_de("between 64-65°F"))
        self.assertEqual(g.temp_reporte({"rawOb": "METAR KLGA 081251Z 15/09 A3012 RMK T01720094", "temp": 15}), 17.2)
        self.assertEqual(g.temp_reporte({"rawOb": "METAR KLGA RMK T10280050", "temp": -3}), -2.8)
        self.assertEqual(g.temp_reporte({"rawOb": "METAR ZUUU 080500Z 17/08 Q1035", "temp": 17}), 17.0)
        self.assertEqual([g.redondear_pm(x) for x in (17.4, 17.5, -0.5, -0.6)], [17, 18, 0, -1])

    def test_temps_del_dia_rutina_y_fahrenheit(self):
        import guardia_metar as g
        from datetime import date
        reps = [self.rep(3, 15, "METAR ZUUU 080300Z 15/11"), self.rep(5, 17, "METAR ZUUU 080500Z 17/08"),
                self.rep(6, 19, "SPECI ZUUU 080630Z 19/08", tipo="SPECI"),            # SPECI no cuenta
                self.rep(15, 20, "METAR ZUUU 071500Z 20/10", dia=7)]                   # otro dia local (7-nov 23:00)
        self.assertEqual(g.temps_del_dia(reps, date(2026, 11, 8), "Asia/Shanghai", False), [15, 17])
        # °F: 17,2 °C -> 62,96 -> 63 °F; el dia local de NYC (UTC-5): 03Z y 05Z del 8 son 22 y 00 h -> 7 y 8 nov
        reps = [self.rep(3, 15, "RMK T01720094"), self.rep(5, 15, "RMK T01500094")]
        self.assertEqual(g.temps_del_dia(reps, date(2026, 11, 8), "America/New_York", True), [59])

    def test_decidida(self):
        import guardia_metar as g
        self.assertIsNone(g.decidida("max", "17°C", [15, 17]))                      # llego justo: sigue abierta (Chengdu)
        self.assertIn("ya no puede ganar", g.decidida("max", "17°C", [15, 18]))
        self.assertIn("ya no puede ganar", g.decidida("max", "17°C or below", [18]))
        self.assertIn("ya gano", g.decidida("max", "18°C or higher", [18]))
        self.assertIsNone(g.decidida("max", "18°C or higher", [17]))
        self.assertIsNone(g.decidida("min", "10°C", [12, 10]))
        self.assertIn("ya no puede ganar", g.decidida("min", "10°C", [12, 9]))
        self.assertIn("ya gano", g.decidida("min", "9°C or below", [9]))
        self.assertIsNone(g.decidida("max", "17°C", []))

    def test_guardia_consulta_y_cache(self):
        import guardia_metar as g
        from datetime import datetime, timezone
        llamadas = []

        def buscar(icao):
            llamadas.append(icao)
            return [self.rep(5, 18, "METAR ZUUU 080500Z 18/08")]
        gu = g.Guardia(estaciones=self.EST, buscar=buscar, log=lambda t: None)
        ahora = datetime(2026, 11, 8, 6, 0, tzinfo=timezone.utc).timestamp()
        self.assertIn("18 > 17°C", gu.motivo("highest-temperature-in-chengdu-on-november-8-2026", "17°C", ahora))
        self.assertIsNone(gu.motivo("highest-temperature-in-chengdu-on-november-8-2026", "18°C", ahora))
        self.assertEqual(llamadas, ["ZUUU"])                                        # cache: una sola consulta
        # antes del dia del evento (hora local) no consulta; ciudad sin estacion tampoco
        self.assertIsNone(gu.motivo("highest-temperature-in-chengdu-on-november-9-2026", "17°C", ahora))
        self.assertIsNone(gu.motivo("highest-temperature-in-paris-on-november-8-2026", "17°C", ahora))
        self.assertEqual(llamadas, ["ZUUU"])
        # si la consulta falla, sigue sin guardia

        def roto(icao):
            raise RuntimeError("awc caido")
        gu2 = g.Guardia(estaciones=self.EST, buscar=roto, log=lambda t: None)
        self.assertIsNone(gu2.motivo("highest-temperature-in-chengdu-on-november-8-2026", "17°C", ahora))

    def test_bot_suelta_caja_decidida_y_avisa_una_vez(self):
        import guardia_metar as g
        d = tempfile.mkdtemp()
        m = MercadoFalso()
        bot = maker.Maker(cfg(guardia_metar=True), m=m, carpeta=d)
        avisos = []
        bot.avisar = avisos.append
        bot.guardia = g.Guardia(estaciones={"x": {"icao": "XXXX", "tz": "UTC", "en_f": False}},
                                buscar=lambda icao: [self.rep(5, 21, "METAR XXXX 030500Z 21/08", dia=3)], log=lambda t: None)
        # el evento falso es "highest-temperature-in-x": no parsea -> sin guardia -> elige A como siempre
        self.assertEqual(list(bot.elegir(AHORA)), ["A"])
        # con un slug real del dia (AHORA es 3-nov en las pruebas): la caja 17°C ya decidida se suelta
        m.slug = "highest-temperature-in-x-on-november-3-2026"
        self.assertEqual(bot.elegir(AHORA), {})                                     # maxima 21 > "20°C": A se suelta; B es ancha
        self.assertEqual(len(avisos), 1)
        self.assertIn("guardia METAR", avisos[0])
        bot.elegir(AHORA)
        self.assertEqual(len(avisos), 1)                                            # una vez por caja
        self.assertEqual(len(bot.est["guardia"]), 1)
        shutil.rmtree(d)

    def test_piso_de_compra(self):
        d = tempfile.mkdtemp()
        bot = maker.Maker(cfg(), m=MercadoFalso(), carpeta=d)
        c = {"si": "s", "no": "n", "medio": 0.91, "tick": 0.01, "tam": 25}
        o = bot.cotizar(c, {})
        self.assertEqual(o, [("s", "BUY", 0.89, 25, True)])                         # el No a 0,07 no se compra
        o = bot.cotizar(c, {"n": 30})                                               # pero el No que tenemos si se vende
        self.assertEqual(o[0], ("n", "SELL", 0.11, 25, False))
        bot.cfg["maker"]["precio_min_compra"] = 0.0
        self.assertEqual(len(bot.cotizar(c, {})), 2)
        shutil.rmtree(d)

    def test_tope_inventario_por_lado(self):
        """Moscu 4 °C (8-nov): con 86 No ya comprados no sigue comprando No; el No que tiene si lo vende."""
        d = tempfile.mkdtemp()
        bot = maker.Maker(cfg(), m=MercadoFalso(), carpeta=d)
        c = {"si": "s", "no": "n", "medio": 0.62, "tick": 0.01, "tam": 25}
        o = bot.cotizar(c, {"n": 86, "s": 0})
        self.assertEqual(o, [("n", "SELL", 0.40, 25, False)])                        # vende No, no compra mas No
        o = bot.cotizar(c, {"n": 25})                                                # 25 + 25 = 50: todavia cabe
        self.assertEqual([(x[0], x[1]) for x in o], [("n", "SELL"), ("n", "BUY")])
        o = bot.cotizar(c, {"n": 30})                                                # 30 + 25 > 50: ya no
        self.assertEqual([(x[0], x[1]) for x in o], [("n", "SELL")])
        bot.cfg["maker"]["max_inventario_lado"] = 0                                  # 0 = sin tope
        self.assertEqual(len(bot.cotizar(c, {"n": 86})), 2)
        bot.cfg["maker"]["max_inventario_lado"] = 50
        o = bot.cotizar(c, {"s": 60})                                                # tambien del lado Si
        self.assertEqual([(x[0], x[1]) for x in o], [("s", "SELL")])
        shutil.rmtree(d)

    def test_filtro_movimiento(self):
        """Tokio 14 °C (8-nov): si el medio se movio 6 c o mas en la ultima hora, la caja queda sin compras; se calma, vuelven."""
        from datetime import datetime, timedelta, timezone
        d = tempfile.mkdtemp()
        bot = maker.Maker(cfg(), m=MercadoFalso(), carpeta=d)
        c = {"cid": "x", "evento": "e", "caja": "14°C", "si": "s", "no": "n", "medio": 0.50, "tick": 0.01, "tam": 25}
        t0 = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
        self.assertIsNone(bot.movimiento(c, t0))                                     # sin historia: no se filtra
        self.assertFalse(bot.sin_compras(c, t0 + timedelta(minutes=5)))
        c["medio"] = 0.45                                                            # 20 min despues, bajo 5 c: no llega
        self.assertFalse(bot.sin_compras(c, t0 + timedelta(minutes=20)))
        c["medio"] = 0.43                                                            # 30 min: 7 c en la hora -> sin compras
        self.assertTrue(bot.sin_compras(c, t0 + timedelta(minutes=30)))
        self.assertEqual(bot.movimiento(c, t0 + timedelta(minutes=30)), -0.07)
        self.assertIn("x", bot.est["filtro"])
        o = bot.cotizar(c, {"n": 30}, sin_compras=True)                              # solo la venta del No que tenemos
        self.assertEqual([(x[0], x[1]) for x in o], [("n", "SELL")])
        self.assertEqual(bot.cotizar(c, {}, sin_compras=True), [])
        c["medio"] = 0.56                                                            # subida fuerte tambien filtra
        self.assertTrue(bot.sin_compras(c, t0 + timedelta(minutes=40)))
        c["medio"] = 0.55                                                            # 95 min: en la ventana solo queda el 0,56 de los 40 min
        self.assertFalse(bot.sin_compras(c, t0 + timedelta(minutes=95)))             # se calmo: vuelven las compras
        bot.cfg["maker"]["filtro_movimiento_c"] = 0                                  # 0 = apagado
        c["medio"] = 0.80
        self.assertFalse(bot.sin_compras(c, t0 + timedelta(minutes=100)))
        # SIN_COMPRAS.txt: caja sin compras a mano (aunque el filtro este apagado), se saca la linea y vuelven
        with open(os.path.join(d, "SIN_COMPRAS.txt"), "w", encoding="utf-8") as f:
            f.write("# comentario\n\n14°c\n")
        self.assertTrue(bot.sin_compras(c, t0 + timedelta(minutes=101)))
        self.assertEqual(bot.est["filtro"]["x"]["a_mano"], "14°c")
        with open(os.path.join(d, "SIN_COMPRAS.txt"), "w", encoding="utf-8") as f:
            f.write("moscow\n")
        self.assertFalse(bot.sin_compras(c, t0 + timedelta(minutes=102)))
        shutil.rmtree(d)


class PruebasReinicioConfig(unittest.TestCase):
    def _bot(self, d):
        import types
        ej = types.SimpleNamespace(inventario=lambda: {}, abiertas=lambda: [], llenados=lambda: [],
                                   cancelar_todo=lambda: None, nombre="real")
        return maker.Maker(cfg(modo="real"), m=MercadoFalso(), carpeta=d, ej=ej)

    def test_pedido_reinicio(self):
        d = tempfile.mkdtemp()
        bot = self._bot(d)
        self.assertFalse(bot.pedido_reinicio())
        open(os.path.join(d, "REINICIAR"), "w").close()
        self.assertTrue(bot.pedido_reinicio())
        self.assertFalse(os.path.exists(os.path.join(d, "REINICIAR")))        # lo borra para no repetirlo
        self.assertFalse(bot.pedido_reinicio())
        shutil.rmtree(d)

    def test_relee_config_sin_cambiar_modo(self):
        d = tempfile.mkdtemp()
        bot = self._bot(d)
        bot.f_cfg = os.path.join(d, "config.json")
        c = cfg(modo="papel")
        c["maker"]["cajas"], c["maker"]["distancia"] = 5, 0.03
        with open(bot.f_cfg, "w", encoding="utf-8") as f:
            json.dump(c, f)
        bot.recargar_cfg()
        self.assertEqual(bot.cfg["maker"]["cajas"], 5)
        self.assertEqual(bot.cfg["maker"]["distancia"], 0.03)
        self.assertEqual(bot.cfg["maker"]["modo"], "real")                   # el modo no se cambia en caliente
        with open(bot.f_cfg, "w", encoding="utf-8") as f:
            f.write("{roto")
        bot.recargar_cfg()                                                    # config rota: sigue con la anterior
        self.assertEqual(bot.cfg["maker"]["cajas"], 5)
        shutil.rmtree(d)

    def test_carga_secretos_sin_pisar(self):
        d = tempfile.mkdtemp()
        ruta = os.path.join(d, "secreto.cmd")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("@echo off\nrem comentario\nset PRUEBA_RELAYER_KEY=abc\nset PRUEBA_RELAYER_ADDR=\"0x1\"\n"
                    "set PRUEBA_VACIO=\nSET PRUEBA_YA=nuevo\n")
        os.environ["PRUEBA_YA"] = "viejo"
        os.environ.pop("PRUEBA_RELAYER_KEY", None)
        self.assertEqual(maker.cargar_secretos(ruta), 2)
        self.assertEqual(os.environ["PRUEBA_RELAYER_KEY"], "abc")
        self.assertEqual(os.environ["PRUEBA_RELAYER_ADDR"], "0x1")
        self.assertEqual(os.environ["PRUEBA_YA"], "viejo")                   # no pisa lo que ya estaba
        self.assertNotIn("PRUEBA_VACIO", os.environ)
        self.assertEqual(maker.cargar_secretos(os.path.join(d, "no_existe.cmd")), 0)
        shutil.rmtree(d)

    def test_clave_relayer_opcional(self):
        for k in ("BOT_RELAYER_API_KEY", "BOT_RELAYER_API_ADDRESS"):
            os.environ.pop(k, None)
        self.assertIsNone(maker.Real.clave_relayer())
        os.environ["BOT_RELAYER_API_KEY"] = "k"
        self.assertIsNone(maker.Real.clave_relayer())                        # falta la direccion
        os.environ.pop("BOT_RELAYER_API_KEY")

    def test_aviso_a_tres_errores_una_vez(self):
        d = tempfile.mkdtemp()
        bot = self._bot(d)
        avisos = []
        bot.avisar = avisos.append
        bot.est["errores_seguidos"] = 2
        bot.avisar_errores()
        bot.est["errores_seguidos"] = 3
        bot.avisar_errores()
        bot.est["errores_seguidos"] = 4
        bot.avisar_errores()
        self.assertEqual(len(avisos), 1)
        bot.est["errores_seguidos"] = 0
        bot.avisar_errores()
        bot.est["errores_seguidos"] = 3
        bot.avisar_errores()
        self.assertEqual(len(avisos), 2)                                      # nueva racha, nuevo aviso
        shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)

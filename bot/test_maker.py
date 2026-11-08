"""Pruebas sin red del bot maker: python bot/test_maker.py"""
import json
import os
import shutil
import sys
import tempfile
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
        self.S = self

    def get(self, url, params=None, timeout=None):
        if "gamma" in url:
            if params.get("offset", 0) > 0:
                return Resp([])
            return Resp([{"slug": "highest-temperature-in-x", "endDate": FIN,
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
                   "max_perdida_total": 30, "max_errores_seguidos": 10}}
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

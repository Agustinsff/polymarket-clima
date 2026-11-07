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
        self.assertAlmostEqual(self.bot.pnl(), -2.9)
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

    def get_balance_allowance(self, asset_type, token_id):
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
        self.assertAlmostEqual(bot.pnl(), -16.5)
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


if __name__ == "__main__":
    unittest.main(verbosity=1)

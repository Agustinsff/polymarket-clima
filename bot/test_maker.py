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
        if "trades" in url:
            return Resp(self.trades.get(params["market"], []))
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
    def __init__(self):
        self.ordenes, self.cancel, self.redimidas = {}, [], []
        import types
        self.types = types

    def place_limit_order(self, token_id, price, size, side, post_only):
        assert post_only
        oid = f"o{len(self.ordenes) + 1}"
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
        return self.types.SimpleNamespace(iter_items=lambda: iter([]))

    def redeem_positions(self, condition_id):
        self.redimidas.append(condition_id)
        return self.types.SimpleNamespace(wait=lambda: None)

    def get_total_earnings_for_user_for_day(self, date):
        return [self.types.SimpleNamespace(earnings="1.25")]


class PruebasReal(unittest.TestCase):
    def test_real_con_sdk_falso(self):
        d = tempfile.mkdtemp()
        m = MercadoFalso()
        maker.avisar = lambda t: None
        ej = maker.Real.__new__(maker.Real)
        ej.client, ej.est = SDKFalso(), {}
        ej.vistos = ej.est.setdefault("llenado_visto", {})
        c = cfg(modo="real")
        bot = maker.Maker(c, m=m, carpeta=d, ej=ej)
        bot.ciclo(AHORA)
        self.assertEqual(len(ej.client.ordenes), 2)
        self.assertEqual(sorted(o.price for o in ej.client.ordenes.values()), ["0.29", "0.66"])
        # se llena media orden: se anota una vez sola
        list(ej.client.ordenes.values())[0].size_matched = "10"
        bot.ciclo(AHORA + timedelta(minutes=1))
        bot.ciclo(AHORA + timedelta(minutes=2))
        self.assertEqual(len([o for o in bot.ops() if o["lado"] == "BUY"]), 1)
        self.assertEqual(ej.recompensa_dia("2026-11-02"), 1.25)
        ej.cancelar_todo()
        self.assertEqual(ej.client.ordenes, {})
        shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)

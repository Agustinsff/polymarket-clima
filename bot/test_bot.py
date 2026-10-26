"""
Pruebas sin red: un mercado falso con libros armados a mano. Correr: python bot/test_bot.py
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mercado  # noqa: E402
from polybot import Bot, cargar_cfg  # noqa: E402

AHORA = datetime(2026, 10, 27, 15, 54, 10, tzinfo=timezone.utc)


class MercadoFalso:
    """Un evento BTC de 1 h que cierra a las 16:00 con Up a 0,80 y Down a 0,22."""
    costo_compra = staticmethod(mercado.costo_compra)
    lados = staticmethod(mercado.lados)
    tasa_comision = staticmethod(mercado.tasa_comision)
    minutos_al_cierre = staticmethod(mercado.minutos_al_cierre)

    def __init__(self, up=((0.80, 50),), down=((0.22, 50),), gana=None):
        self.asks = {"tUP": list(up), "tDN": list(down)}
        self.gana = gana

    def eventos_abiertos(self, serie):
        if serie != "btc-up-or-down-hourly":
            return []
        return [{"slug": "btc-up-or-down-oct-27-11am-et", "endDate": "2026-10-27T16:00:00Z",
                 "markets": [{"conditionId": "0xc1", "clobTokenIds": json.dumps(["tUP", "tDN"]),
                              "outcomes": json.dumps(["Up", "Down"]), "feesEnabled": True,
                              "feeSchedule": {"rate": 0.07}}]}]

    def libro(self, tok):
        return [], self.asks[tok]

    def ganador(self, cid):
        return self.gana


class PruebasBot(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cfg = cargar_cfg()
        self.cfg["modo"] = "papel"
        self.cfg["favorito"]["acciones"] = 10        # las cuentas de abajo usan 10 acciones y frenos holgados
        self.cfg["riesgo"].update(max_usd_por_op=9.5, max_perdida_dia=20, max_perdida_total=50, max_exposicion_abierta=40)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def bot(self, m):
        return Bot(self.cfg, m=m, carpeta=self.dir)

    def test_compra_el_favorito_y_liquida(self):
        m = MercadoFalso()
        b = self.bot(m)
        hechas = b.pasada(AHORA)
        self.assertEqual(len(hechas), 1)
        self.assertEqual((hechas[0]["lado"], hechas[0]["lleno"], hechas[0]["precio"]), ("Up", 1, 0.8))
        m.gana = "Up"
        b.liquidar()
        esperado = 10 - (10 * 0.8 + 10 * 0.07 * 0.8 * 0.2)
        self.assertAlmostEqual(b.pnl(), esperado, places=6)

    def test_fuera_de_horario_no_hace_nada(self):
        self.assertEqual(self.bot(MercadoFalso()).pasada(AHORA.replace(minute=30)), [])

    def test_fuera_de_rango_no_opera(self):
        self.assertEqual(self.bot(MercadoFalso(up=((0.93, 50),), down=((0.08, 50),))).pasada(AHORA), [])

    def test_libro_que_se_mueve_no_llena(self):
        m = MercadoFalso()
        b = self.bot(m)
        orig = m.libro
        llamadas = []

        def libro(tok):                      # la segunda lectura (la del ejecutor) ya subio a 0,85
            llamadas.append(tok)
            return ([], [(0.85, 50)]) if llamadas.count(tok) > 1 else orig(tok)
        m.libro = libro
        h = b.pasada(AHORA)
        self.assertEqual(h[0]["lleno"], 0)
        self.assertEqual(b.llenas(), [])

    def test_no_repite_mercado(self):
        b = self.bot(MercadoFalso())
        b.pasada(AHORA)
        h = b.pasada(AHORA + timedelta(minutes=1))
        self.assertTrue(h[0]["detalle"].startswith("frenada: ya hay"))

    def test_tope_por_operacion(self):
        self.cfg["riesgo"]["max_usd_por_op"] = 5
        h = self.bot(MercadoFalso()).pasada(AHORA)
        self.assertEqual(h[0]["lleno"], 0)
        self.assertIn("max por op", h[0]["detalle"])

    def test_perdida_total_activa_el_freno(self):
        self.cfg["riesgo"]["max_perdida_total"] = 5
        m = MercadoFalso()
        b = self.bot(m)
        b.pasada(AHORA)
        m.gana = "Down"                       # se pierden ~8,1
        b.pasada(AHORA + timedelta(hours=1))
        self.assertTrue(os.path.exists(os.path.join(self.dir, "PARAR_papel")))
        self.assertEqual(b.pasada(AHORA + timedelta(hours=2)), [])

    def test_archivo_parar(self):
        open(os.path.join(self.dir, "PARAR"), "w").close()
        self.assertEqual(self.bot(MercadoFalso()).pasada(AHORA), [])

    def test_fecha_de_apagado(self):
        self.cfg["apagar_despues_de"] = "2026-10-27 15:00"
        self.assertEqual(self.bot(MercadoFalso()).pasada(AHORA), [])

    def test_errores_seguidos_frenan(self):
        self.cfg["riesgo"]["max_errores_seguidos"] = 2
        m = MercadoFalso()

        def roto(serie):
            raise ConnectionError("sin red")
        m.eventos_abiertos = roto
        b = self.bot(m)
        b.pasada(AHORA); b.pasada(AHORA); b.pasada(AHORA)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "PARAR_papel")))

    def test_real_no_arranca_sin_confirmar(self):
        self.cfg["modo"] = "real"
        os.environ.pop("BOT_REAL_CONFIRMO", None)
        with self.assertRaises(SystemExit):
            self.bot(MercadoFalso()).pasada(AHORA)

    def test_costo_compra_recorre_el_libro(self):
        asks = [(0.80, 4), (0.82, 10)]
        self.assertAlmostEqual(mercado.costo_compra(asks, 10), (4 * 0.80 + 6 * 0.82) / 10)
        self.assertIsNone(mercado.costo_compra(asks, 10, tope=0.81))
        self.assertIsNone(mercado.costo_compra(asks, 20))


class SDKFalso:
    """Imita polymarket-client 0.14.0 (AcceptedOrder / RejectedOrder / InsufficientLiquidityError)."""
    def __init__(self, modo):
        import types
        self.modo, self.llamadas, self.cobros = modo, [], []
        errs = types.SimpleNamespace(InsufficientLiquidityError=type("InsufficientLiquidityError", (Exception,), {}))
        sdk = self

        class SecureClient:
            @classmethod
            def create(cls, private_key, wallet=None):
                return cls()

            def place_market_order(self, **kw):
                sdk.llamadas.append(kw)
                if sdk.modo == "sin_liquidez":
                    raise errs.InsufficientLiquidityError("no alcanza")
                if sdk.modo == "rechazada":
                    return types.SimpleNamespace(ok=False, code="fok_not_filled", message="no se lleno")
                return types.SimpleNamespace(ok=True, order_id="0xabc", status="matched",
                                             making_amount="3.96", taking_amount="5")

            def redeem_positions(self, condition_id):
                sdk.cobros.append(condition_id)
                return types.SimpleNamespace(wait=lambda: None)

        self.modulo = types.SimpleNamespace(SecureClient=SecureClient, errors=errs)


class PruebasReal(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cfg = cargar_cfg()
        self.cfg["modo"] = "real"
        os.environ.update(BOT_REAL_CONFIRMO="si", POLYMARKET_PRIVATE_KEY="0x" + "1" * 64)
        os.environ.pop("BOT_NTFY_TEMA", None)

    def tearDown(self):
        shutil.rmtree(self.dir)
        sys.modules.pop("polymarket", None)
        for k in ("BOT_REAL_CONFIRMO", "POLYMARKET_PRIVATE_KEY"):
            os.environ.pop(k, None)

    def correr(self, modo, geo=False, gana=None):
        sdk = SDKFalso(modo)
        sys.modules["polymarket"] = sdk.modulo
        m = MercadoFalso(gana=gana)
        m.geobloqueo = lambda: {"blocked": geo, "country": "UY"}
        b = Bot(self.cfg, m=m, carpeta=self.dir)
        return b, b.pasada(AHORA), sdk

    def test_compra_real_anota_precio_y_acciones_del_sdk(self):
        b, h, sdk = self.correr("ok")
        self.assertEqual(h[0]["lleno"], 1)
        self.assertEqual((h[0]["acciones"], h[0]["precio"]), (5.0, 0.792))
        kw = sdk.llamadas[0]
        self.assertEqual((kw["token_id"], kw["side"], kw["order_type"], kw["max_price"], kw["amount"]),
                         ("tUP", "BUY", "FOK", "0.81", "4.05"))

    def test_rechazo_fok_no_llena(self):
        _, h, _ = self.correr("rechazada")
        self.assertEqual(h[0]["lleno"], 0)
        self.assertIn("fok_not_filled", h[0]["detalle"])

    def test_sin_liquidez_no_llena(self):
        _, h, _ = self.correr("sin_liquidez")
        self.assertEqual(h[0]["lleno"], 0)

    def test_pais_bloqueado_no_arranca(self):
        with self.assertRaises(SystemExit):
            self.correr("ok", geo=True)

    def test_cobra_ganadoras(self):
        b, _, sdk = self.correr("ok")
        b.m.gana = "Up"
        b.liquidar()
        b.liquidar()
        self.assertEqual(sdk.cobros, ["0xc1"])


class PruebasResumenDiario(unittest.TestCase):
    def test_una_vez_por_dia(self):
        from polybot import resumen_diario
        d = tempfile.mkdtemp()
        cfg = cargar_cfg(); cfg["modo"] = "papel"
        b = Bot(cfg, m=MercadoFalso(), carpeta=d)
        t = datetime(2026, 10, 28, 4, 0, tzinfo=timezone.utc)
        self.assertIsNone(resumen_diario(b, t.replace(hour=1)))
        self.assertIn("2026-10-27", resumen_diario(b, t))
        self.assertIsNone(resumen_diario(b, t.replace(hour=5)))
        shutil.rmtree(d)


class PruebasSombra(unittest.TestCase):
    def test_llenado_prudente(self):
        import sombra_maker as sm
        trs = [(1, "Up", "SELL", 0.79, 3),      # igual a L: no cuenta
               (2, "Up", "SELL", 0.78, 2),      # menor a L: llena 2
               (3, "Down", "BUY", 0.23, 10),    # compra del otro lado a 0,23 = venta de Up a 0,77: llena el resto
               (4, "Up", "BUY", 0.70, 50)]      # compras de nuestro lado no llenan
        self.assertEqual(sm.llenado(trs, "Up", 0.79, 5), 5)
        self.assertEqual(sm.llenado(trs[:2], "Up", 0.79, 5), 2)
        self.assertEqual(sm.llenado([trs[3]], "Up", 0.79, 5), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

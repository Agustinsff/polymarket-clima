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
        self.assertTrue(os.path.exists(os.path.join(self.dir, "PARAR")))
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
        self.assertTrue(os.path.exists(os.path.join(self.dir, "PARAR")))

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

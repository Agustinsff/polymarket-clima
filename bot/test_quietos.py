"""Pruebas sin red del bot de papel de mercados quietos: python bot/test_quietos.py"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quietos  # noqa: E402

AHORA = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)
CFG = {"maker": {"horas_min_fin": 24, "acciones_min": 25, "distancia": 0.02, "spread_max": 0.05},
       "quietos": {"medio_min": 0.25, "medio_max": 0.75, "rango24_max": 0.05, "mov1h_max": 0.006, "tam_min_max": 50,
                   "puntos_min": 30, "ofrecer": 60, "censo_cada_min": 60,
                   "etiquetas_fuera": ["Weather", "Daily Temperature", "Tweet Markets"]}}


def mk(cid, precio=0.5, dias=10, min_size=20, tags=("Politics",), partido=False, pozo=50):
    return {"condition_id": cid, "question": f"q {cid}", "market_slug": cid, "accepting_orders": True, "closed": False,
            "end_date_iso": (AHORA + timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ"), "minimum_tick_size": 0.01,
            "game_start_time": "2026-11-14T00:00:00Z" if partido else None, "tags": list(tags),
            "rewards": {"rates": [{"rewards_daily_rate": pozo}], "min_size": min_size, "max_spread": 4.5},
            "tokens": [{"token_id": f"si-{cid}", "outcome": "Yes", "price": precio},
                       {"token_id": f"no-{cid}", "outcome": "No", "price": 1 - precio}]}


class Prueba(unittest.TestCase):
    def test_regla_base(self):
        ok = lambda m: quietos.cumple_base(quietos.a_caja(m, AHORA), CFG)  # noqa: E731
        self.assertTrue(ok(mk("a")))
        self.assertFalse(ok(mk("b", tags=("Weather",))))
        self.assertFalse(ok(mk("c", tags=("Tweet Markets", "Politics"))))
        self.assertFalse(ok(mk("d", partido=True)))
        self.assertFalse(ok(mk("e", min_size=100)))
        self.assertFalse(ok(mk("f", dias=0.5)))
        self.assertFalse(ok(mk("g", precio=0.80)))
        self.assertIsNone(quietos.a_caja(mk("h", pozo=0), AHORA))

    def test_quieta(self):
        base = {"puntos": 140}
        self.assertTrue(quietos.es_quieta(dict(base, rango24=0.05, mov1h=0.006), CFG))
        self.assertFalse(quietos.es_quieta(dict(base, rango24=0.06, mov1h=0.001), CFG))
        self.assertFalse(quietos.es_quieta(dict(base, rango24=0.01, mov1h=0.01), CFG))
        self.assertFalse(quietos.es_quieta({"puntos": 10, "rango24": 0.0, "mov1h": 0.0}, CFG))

    def test_candidatas_mantiene_las_propias(self):
        c = quietos.Censo(CFG)
        c.ts = AHORA.timestamp()
        propia = quietos.a_caja(mk("x", precio=0.85), AHORA)          # ya no cumpliria la entrada
        c.todas = {"x": propia}
        c.ofrecidas = [quietos.a_caja(mk("y"), AHORA)]
        cids = {x["cid"] for x in c.candidatas(AHORA, ["x", "z"])}
        self.assertEqual(cids, {"x", "y"})


if __name__ == "__main__":
    unittest.main()

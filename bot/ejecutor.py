"""
Ejecutores: reciben una senal y devuelven {"lleno": bool, "precio": float|None, "detalle": str}.

- Papel: vuelve a leer el libro en el momento de "mandar" la orden y simula una orden FOK (todo o nada) con precio
  tope `precio_max`: se llena solo si las `acciones` alcanzan sin pasar el tope. No usa plata.
- Real: manda una orden de mercado FOK con el SDK oficial (`pip install polymarket-client`, clase SecureClient).
  FOK = nunca queda una orden colgada en el libro, asi que no hay nada que cancelar si el bot se cae.
  ESCRITO SEGUN LA DOC OFICIAL, SIN PROBAR (no tenemos billetera todavia). Antes del primer uso real:
  ver LEEME.md, paso "Primera orden real".
"""
import os


class Papel:
    nombre = "papel"

    def __init__(self, m):
        self.m = m

    def comprar(self, s):
        _, asks = self.m.libro(s["token"])
        precio = self.m.costo_compra(asks, s["acciones"], tope=s["precio_max"])
        if precio is None:
            mejor = asks[0][0] if asks else None
            return {"lleno": False, "precio": None, "detalle": f"no alcanza bajo el tope {s['precio_max']} (mejor ask {mejor})"}
        return {"lleno": True, "precio": precio, "detalle": "simulado contra el libro real"}


class Real:
    nombre = "real"

    def __init__(self, m):
        self.m = m
        if os.environ.get("BOT_REAL_CONFIRMO") != "si":
            raise SystemExit("modo real: falta BOT_REAL_CONFIRMO=si en el entorno (seguro contra arranques por error)")
        if not os.environ.get("POLYMARKET_PRIVATE_KEY"):
            raise SystemExit("modo real: falta POLYMARKET_PRIVATE_KEY en el entorno")
        geo = m.geobloqueo()
        if geo.get("blocked") is not False:
            raise SystemExit(f"modo real: Polymarket bloquea operar desde este servidor ({geo.get('country')}, {geo.get('region')})")
        from polymarket import SecureClient          # se importa solo en modo real
        self.client = SecureClient.create(private_key=os.environ["POLYMARKET_PRIVATE_KEY"])

    def comprar(self, s):
        # Monto en pUSD = acciones * tope. Con FOK, o se llena todo a <= tope, o no se hace nada.
        # OJO mercados "v2": la doc pide position_id en vez de token_id (verificar en la primera orden).
        monto = round(s["acciones"] * s["precio_max"], 2)
        r = self.client.place_market_order(asset_id=s["token"], side="BUY", amount=str(monto),
                                           max_price=str(s["precio_max"]), order_type="FOK")
        if not getattr(r, "ok", False):
            return {"lleno": False, "precio": None, "detalle": f"rechazada: {r}"}
        # Precio exacto de llenado: hasta verificar la respuesta del SDK se anota el tope (lo peor posible).
        return {"lleno": True, "precio": s["precio_max"], "detalle": f"orden real ok: {r}"}


def crear(modo, m):
    return {"papel": Papel, "real": Real}[modo](m)

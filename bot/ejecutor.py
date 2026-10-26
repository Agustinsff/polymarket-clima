"""
Ejecutores: reciben una senal y devuelven {"lleno": bool, "precio": float|None, "detalle": str}.

- Papel: vuelve a leer el libro en el momento de "mandar" la orden y simula una orden FOK (todo o nada) con precio
  tope `precio_max`: se llena solo si las `acciones` alcanzan sin pasar el tope. No usa plata.
- Real: manda una orden de mercado FOK con el SDK oficial (`pip install -r bot/requirements_real.txt`).
  FOK = nunca queda una orden colgada en el libro, asi que no hay nada que cancelar si el bot se cae.
  Nombres y respuestas verificados contra el codigo del SDK; nunca se mando una orden de verdad (ver LEEME.md).
"""
import os


class Papel:
    nombre = "papel"

    def __init__(self, m):
        self.m = m

    def cobrar(self, condition_id):
        pass

    def comprar(self, s):
        _, asks = self.m.libro(s["token"])
        precio = self.m.costo_compra(asks, s["acciones"], tope=s["precio_max"])
        if precio is None:
            mejor = asks[0][0] if asks else None
            return {"lleno": False, "precio": None, "detalle": f"no alcanza bajo el tope {s['precio_max']} (mejor ask {mejor})"}
        return {"lleno": True, "precio": precio, "detalle": "simulado contra el libro real"}


class Real:
    """Verificado el 26-oct-2026 contra polymarket-client 0.14.0 (codigo del SDK, sin plata):
    - SecureClient.create(private_key=..., wallet=...): wallet por defecto = la Deposit Wallet del firmante.
    - place_market_order(token_id=..., side="BUY", amount=<pUSD a gastar>, max_price=..., order_type="FOK"):
      token_id es el mismo id de clobTokenIds de gamma. Devuelve AcceptedOrder (ok=True, making_amount = pUSD
      pagados, taking_amount = acciones recibidas) o RejectedOrder (ok=False, code p.ej. "fok_not_filled").
      Puede tirar InsufficientLiquidityError si el libro no alcanza bajo el tope.
    - redeem_positions(condition_id=...).wait(): cobra un mercado resuelto (sin gas en la Deposit Wallet).
    Falta confirmar con la primera orden real: si la comision sale de making_amount o de las acciones."""
    nombre = "real"

    def __init__(self, m):
        self.m = m
        if os.environ.get("BOT_REAL_CONFIRMO") != "si":
            raise SystemExit("modo real: falta BOT_REAL_CONFIRMO=si en el entorno (seguro contra arranques por error)")
        if not os.environ.get("POLYMARKET_PRIVATE_KEY"):
            raise SystemExit("modo real: falta POLYMARKET_PRIVATE_KEY en el entorno")
        geo = m.geobloqueo()
        if geo.get("blocked") is not False:
            raise SystemExit(f"modo real: Polymarket bloquea operar desde aca ({geo.get('country')}, {geo.get('region')})")
        from polymarket import SecureClient          # se importa solo en modo real
        from polymarket import errors
        self.errores = errors
        self.client = SecureClient.create(private_key=os.environ["POLYMARKET_PRIVATE_KEY"],
                                          wallet=os.environ.get("POLYMARKET_WALLET") or None)

    def comprar(self, s):
        # FOK: o se llena todo sin pasar el tope, o no se hace nada. Se gasta como mucho acciones * tope;
        # si el libro esta mas barato, entran algunas acciones mas por la misma plata.
        monto = round(s["acciones"] * s["precio_max"], 2)
        try:
            r = self.client.place_market_order(token_id=s["token"], side="BUY", amount=str(monto),
                                               max_price=str(s["precio_max"]), order_type="FOK")
        except self.errores.InsufficientLiquidityError as ex:
            return {"lleno": False, "precio": None, "detalle": f"no alcanza bajo el tope: {ex}"}
        if not r.ok:
            return {"lleno": False, "precio": None, "detalle": f"rechazada ({r.code}): {r.message}"}
        pagado, acciones = float(r.making_amount), float(r.taking_amount)
        if acciones <= 0:
            return {"lleno": False, "precio": None, "detalle": f"aceptada sin llenar ({r.status}), orden {r.order_id}"}
        return {"lleno": True, "precio": round(pagado / acciones, 4), "acciones": acciones,
                "detalle": f"orden real {r.order_id} ({r.status}): {acciones} acc por {pagado} pUSD"}

    def cobrar(self, condition_id):
        self.client.redeem_positions(condition_id=condition_id).wait()


def crear(modo, m):
    return {"papel": Papel, "real": Real}[modo](m)

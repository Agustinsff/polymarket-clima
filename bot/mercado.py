"""
Lectura de datos publicos de Polymarket (sin claves): eventos de gamma, libro del CLOB, resultado de un mercado
y el control de bloqueo por pais. Lo usan los dos modos (papel y real).
"""
import json
from datetime import datetime, timezone

import requests

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
S = requests.Session()
S.headers["User-Agent"] = "polymarket-clima-bot/0.1 (investigacion personal)"


def eventos_abiertos(serie):
    return S.get(f"{GAMMA}/events", params={"series_slug": serie, "closed": "false", "limit": 20}, timeout=30).json()


def minutos_al_cierre(evento, ahora=None):
    ahora = ahora or datetime.now(timezone.utc)
    fin = datetime.fromisoformat(evento["endDate"].replace("Z", "+00:00"))
    return (fin - ahora).total_seconds() / 60


def lados(mercado):
    """[(nombre, token_id), ...] de un mercado de gamma (Up/Down, Yes/No)."""
    toks = json.loads(mercado["clobTokenIds"])
    outs = json.loads(mercado.get("outcomes") or '["Yes","No"]')
    return list(zip(outs, toks))


def tasa_comision(mercado):
    """Tasa taker del mercado (fee = tasa * p * (1-p) por accion). 0 si el mercado no cobra."""
    if mercado.get("feesEnabled") is False:
        return 0.0
    fs = mercado.get("feeSchedule")
    if isinstance(fs, dict) and fs.get("rate") is not None:
        return float(fs["rate"])
    return 0.07


def libro(token):
    """(bids de mayor a menor, asks de menor a mayor), cada uno [(precio, tamano), ...]."""
    b = S.get(f"{CLOB}/book", params={"token_id": token}, timeout=20).json()
    bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in b.get("asks", []))
    return bids, asks


def costo_compra(asks, acciones, tope=None):
    """Precio medio de comprar `acciones` recorriendo los asks sin pasar de `tope`. None si no alcanza."""
    falta, total = acciones, 0.0
    for precio, tam in asks:
        if tope is not None and precio > tope + 1e-9:
            break
        toma = min(falta, tam)
        total += toma * precio
        falta -= toma
        if falta <= 1e-9:
            return round(total / acciones, 4)
    return None


def ganador(condition_id):
    """Nombre del lado ganador si el mercado ya resolvio; None si sigue abierto."""
    r = S.get(f"{CLOB}/markets/{condition_id}", timeout=20).json()
    if not r.get("closed"):
        return None
    for t in r.get("tokens", []):
        if t.get("winner"):
            return t.get("outcome")
    return None


def geobloqueo():
    """{'blocked': bool, 'country': 'AR', ...} segun polymarket.com/api/geoblock (doc oficial)."""
    return S.get("https://polymarket.com/api/geoblock", timeout=20).json()

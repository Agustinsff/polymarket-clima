"""
Estrategias del bot. Cada una es una funcion buscar(cfg, ahora, m) que devuelve senales:
  {"activo", "evento", "condition_id", "lado", "token", "acciones", "precio_visto", "precio_max", "tasa", "min_al_cierre"}
El bot no sabe nada de la estrategia: solo pasa cada senal por los limites de riesgo y el ejecutor.
`m` es el modulo mercado (en las pruebas se reemplaza por uno falso).

Para sumar otra (por ejemplo maker con recompensas, si el corte del 2-nov da algo), se agrega una funcion aca
y una entrada en ESTRATEGIAS; una estrategia maker ademas necesita cancelar y reponer ordenes, que el ejecutor
todavia no hace (ver LEEME.md).
"""


def favorito(cfg, ahora, m):
    """Favorito tardio (misma regla que favorito/REGLA.md): entre el minuto `minuto_objetivo` y `minuto_ultimo`
    de la hora, en los Up/Down de 1 h, comprar el lado cuyo costo para `acciones` acciones este en [min, max)."""
    p = cfg["favorito"]
    if not p["minuto_objetivo"] <= ahora.minute <= p["minuto_ultimo"]:
        return []
    senales = []
    for serie, activo in p["series"].items():
        for e in m.eventos_abiertos(serie):
            try:
                mins = m.minutos_al_cierre(e, ahora)
            except (KeyError, ValueError):
                continue
            if not 1 <= mins <= 8:
                continue
            mk = (e.get("markets") or [None])[0]
            if not mk or mk.get("closed"):
                continue
            califica = []
            for lado, tok in m.lados(mk):
                _, asks = m.libro(tok)
                precio = m.costo_compra(asks, p["acciones"])
                if precio is not None and p["precio_min"] <= precio < p["precio_max"]:
                    califica.append((lado, tok, precio))
            if len(califica) != 1:          # ninguno, o los dos (libro raro): no se opera
                continue
            lado, tok, precio = califica[0]
            senales.append({
                "activo": activo, "evento": e["slug"], "condition_id": mk["conditionId"], "lado": lado, "token": tok,
                "acciones": p["acciones"], "precio_visto": precio,
                "precio_max": round(min(precio + p["tolerancia"], 0.99), 4),
                "tasa": m.tasa_comision(mk), "min_al_cierre": round(mins, 1),
            })
    return senales


ESTRATEGIAS = {"favorito": favorito}

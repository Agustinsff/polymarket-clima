# Medición: qué pasa con el precio después de cada llenado del bot maker (regla fija, 8-nov-2026)

Pedido de Agus (8-nov 03:33Z): "optimizar los llenados", primero medir. Se fija la regla ANTES de mirar los números.

**Pregunta.** Cuando a nuestra orden la llena un taker, ¿el precio medio después se va a favor o en contra nuestro,
y cuánto? En papel (maker/informe_datos.md) los llenados perdían −4,7 ¢/acción a la resolución. El 7–8 nov en real
ganaron (Tokio). Esta medición dice cuál de las dos es la regla.

**Datos (todo público, sin tocar el bot).**
- Llenados: data-api `/v2/activity?user=<billetera>&type=TRADE` (cada operación: token, lado, precio, acciones,
  momento). Solo desde el 7-nov-2026 18:00Z (arranque en real). Incluye los llenados por corte de luz (son
  llenados igual).
- Precio: CLOB `/prices-history?market=<token>&fidelity=1` (precio medio del token, aprox. por minuto).
- Resolución: gamma `markets?condition_ids=` (`closed`, `outcomePrices`).

**Medida.** Para cada llenado, con p(t) el precio medio del token:
- `antes` = p(t0) − precio (compras) o precio − p(t0) (ventas): cuánto mejor que el medio operamos (≈ la distancia 2 ¢).
- `m5`, `m30`, `m60`, `m180` = (p(t0+k) − precio) para compras, (precio − p(t0+k)) para ventas, en centavos: positivo
  = a favor nuestro. Se usa el último precio registrado hasta t0+k; si ese momento todavía no llegó, queda vacío.
- `m_res` = lo mismo contra 1/0 cuando la caja resolvió.
Todo ponderado por acciones y también simple (n llenados), con error típico y t (media/EE).

**Cortes fijos:** total; por lado (compra/venta); por ciudad/caja; por hora UTC del llenado (6 franjas de 4 h);
por horas que faltaban para el fin del evento (<6, 6–24, >24); con/sin corte de luz (7-nov 20:05–20:30Z).

**Lectura (fijada antes de mirar):**
- Si `m60` ponderado es ≥ 0 con t ≥ 2: los llenados en promedio no pierden → no hace falta cambiar nada; el neto es
  recompensa + llenados.
- Si `m60` está entre −2 y 0 ¢: pierden menos que la distancia que cobramos (`antes` ≈ +2 ¢): neutro, seguir.
- Si `m60` < −2 ¢ con t ≤ −2: los llenados nos cuestan más que lo que ganamos al medio → candidatos a cambiar
  (distancia, tamaño o guardia por METAR), a proponer con estos datos después de la semana de medición.
- Mínimo para concluir: 100 llenados en ≥ 5 días. Antes de eso, solo informativo.

**Salida.** `markout/datos/llenados.csv` (una fila por llenado, se acumula sin repetir) y `markout/informe.md`
(tablas). Corre `python markout/markout.py <billetera>` (Actions: `markout.yml`, diario 02:30Z, billetera en la
variable `MAKER_WALLET` del repo).

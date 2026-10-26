# Sombra maker del favorito tardío (regla fija, 26-oct-2026 ~16:00 UTC, antes de ver datos)

Pregunta: ¿conviene, en vez de comprar al precio de venta (taker, paga ~1,1 ¢ de comisión por acción a 80 ¢),
dejar una orden de compra 1 ¢ más abajo hasta el cierre (maker, no paga comisión)?

No pone órdenes ni toca la prueba `favorito/` ni la regla del bot. Solo mira lo que el bot en papel ya anotó.

## Regla
- Para cada mercado en el que el bot en papel (`bot/ops_papel.csv`) tuvo señal (primera fila de cada mercado,
  se haya llenado o no, frenada o no), se imagina una orden de compra de **las mismas acciones** del mismo lado a
  `L = precio_visto − 0,01`, puesta en el momento de la señal y viva hasta el cierre de la ventana.
- Se llena (prudente) solo con operaciones taker de **venta de ese lado a precio estrictamente menor que L**
  (o compra del otro lado a más de 1 − L), posteriores a la señal y anteriores al cierre, sumando acciones hasta
  completar. Datos: `data-api.polymarket.com/trades?market=<condition_id>&takerOnly=true`.
- Ganancia maker = acciones llenadas × (1 si gana − L). Comisión 0. **No se suma el reembolso maker** (sería
  ~0,2 ¢ por acción): el resultado queda del lado prudente.
- Se compara con el taker en los mismos mercados: acciones × (1 si gana − precio_visto) − comisión del mercado.

## Qué se informa (bot/sombra_maker.md)
- Cuántas se llenan (total y parcial), ganancia maker vs taker en los mismos mercados.
- Selección adversa: % de aciertos de las llenadas vs las no llenadas. Si las llenadas ganan mucho menos que las
  no llenadas, la orden se llena justo cuando el favorito se da vuelta.
- Se decide junto con la prueba el 16/17-nov: si maker gana más que taker con P(≤ taker) < 10 % por bloques de
  día, el bot real pasa a usar orden límite 1 ¢ abajo.

## Minuto de entrada (agregado 26-oct-2026 ~18:40 UTC, antes de ver datos)
- `bot/fotos_minuto.py` saca una foto del libro de los dos lados en cada minuto del 54 al 58 de cada hora
  (`bot/fotos_minuto.csv`). No se mira el resultado por minuto hasta el 17-nov.
- El 17-nov, `python bot/fotos_minuto.py analizar` da el ROI del favorito (5 acciones, 70–90 ¢, comisión + 1 ¢)
  según el minuto. Se cambia el minuto del bot solo si otro minuto le gana al 54 con P(≤0) < 5 % **y** el mismo
  minuto también es el mejor (o empatado) en el histórico de 61 días (`updown/`), para no elegir por ruido.

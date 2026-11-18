# Bot de papel: clima con menos riesgo por compra ("conservador")

Escrita el 18-nov-2026, ANTES de ver un solo llenado. No se cambia durante la medición.
Pedido de Agus (18-nov, hilo del maker real: "dale, coordiná tu recomendación").

## Qué se prueba
Si el maker de clima pierde menos en los saltos de precio con compras más chicas y un filtro más sensible, sin
perder demasiada recompensa. Es solo papel: no toca el bot real, ni `bot/config.json`, ni el papel de clima.

## Reglas fijas (`bot/conservador/config.json`), lo distinto respecto del bot real de hoy
- **20 acciones por orden y tope de 20 por lado** (hoy 25 y 25). Se pidió 10 a 15, pero Polymarket no paga
  recompensa en clima por órdenes de menos de 20 acciones (todas las cajas de temperatura piden 20 como mínimo el
  18-nov): con 15 la prueba no cobraría nada. 20 es lo más chico que cobra.
- **Filtro rápido 2 ¢ en 15 min** (hoy 3 ¢): frena las compras de la caja antes.
- Igual que el real: 3 cajas, sin techo de compra, piso de costo de 3 h en soltadas, orden a 2 ¢ del medio, solo
  cajas que cierran en más de 24 h, guardia METAR, filtro de 6 ¢ en 60 min, frenos −10 por día y −30 total.
- Capital simulado US$ 95. Llenado prudente (solo si alguien operó a un precio peor que el nuestro), sin reembolso.

## Comparación
Al lado corre el papel de clima con la config de siempre (`bot/maker_*_papel`, 25 acciones y 3 ¢): sirve de
referencia del mismo período, pero la regla de abajo se aplica solo al conservador.

## Período y veredicto
- Arranca el 18-nov-2026. Cuentan los **5 días completos de Uruguay del 19 al 23-nov**.
- **Veredicto: lunes 24-nov-2026, 10:00 de Uruguay** (foto del 23-nov menos la del 18-nov, `fotos_dia.json`).
- **Neto prudente** = resultado de llenados a precio de mercado + 50 % de la recompensa estimada (la fórmula exagera).
  - **PASA** (se le propone a Agus usar esta config en real): neto prudente ≥ +1,00 US$/día **y** llenados a mercado
    no peores que −1,00 US$/día **y** el freno diario saltó como mucho 1 vez.
  - **DUDOSO** (no se cambia el real; se decide con Agus): neto prudente entre 0 y +1,00 US$/día.
  - **NO PASA**: neto prudente negativo, o llenados peores que −1,00 US$/día, o saltó el freno total.
- Con menos de 10 llenados en los 5 días, el resultado de llenados no dice nada: se informa así.

## Cómo se apaga
Archivo `bot/conservador/PARAR` o `apagar_despues_de` (24-nov 03:00 UTC = 00:00 de Uruguay).

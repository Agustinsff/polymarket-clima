# Bot de papel: mercados quietos con recompensa (fuera de clima)

Escrita el 13-nov-2026, ANTES de ver un solo llenado. No se cambia durante la medición.
Pedido de Agus (13-nov, hilo del maker real): "armalo en un bot de papel nuevo".

## Qué se prueba
Si el mismo bot maker que corre en real en clima (`bot/maker.py`, sin tocarlo) gana plata cotizando mercados de
Polymarket que **no son de clima**, pagan recompensa de liquidez y **se mueven poco**. Es solo papel: no hay billetera,
no se pone ninguna orden real, no toca la config ni los archivos del maker real ni los del papel de clima.

## Reglas fijas
**Qué mercados entran (al elegir una caja nueva):**
- Pagan recompensa de liquidez (lista `sampling-markets` del CLOB), aceptan órdenes, cierran en más de 24 h.
- No son de clima (etiquetas Weather / Daily Temperature) ni partidos (con `game_start_time`), ni conteos de posts
  (Tweet Markets: se cuentan en vivo y el precio corre hacia un lado en cuanto empieza la semana) ni de precio de
  cripto o acciones (Hit Price, Finance Updown).
- Tamaño mínimo de la recompensa de 50 acciones o menos.
- Precio medio entre 0,25 y 0,75 (para poder poner los dos lados).
- **Quietos:** en las últimas 24 h el precio se movió en total 5 ¢ o menos (rango máximo − mínimo) y el movimiento
  medio en 1 hora fue de 0,6 ¢ o menos (historial público del CLOB, un punto cada 10 min, al menos 30 puntos).
- De los que cumplen, se ofrecen al bot los 60 con más recompensa esperada (la fórmula del bot, con el libro de ese
  momento). La lista se rehace cada hora.

**Cómo cotiza:** igual que el maker real, con sus mismos filtros y frenos (`bot/quietos/config.json`):
- Compras post-only de Sí y No a 2 ¢ del medio, 25 acciones por lado (o el mínimo del mercado si es mayor, hasta 50),
  tope 50 por lado, vende con 25 de un lado, no compra bajo 0,10.
- Hasta 6 cajas; una caja nueva entra solo si el efectivo libre cubre sus compras.
- Filtros de movimiento 6 ¢/60 min y 3 ¢/15 min, rotación cada 30 min, soltadas con piso de costo 3 h.
- Frenos: −10 por día (ventas), −30 total.
- Diferencias con el real, a propósito: sin guardia METAR (no hay temperatura) y **sin el tope de compra 0,60**
  (ese tope es una prueba de clima; acá el medio está entre 0,25 y 0,75 y queremos los dos lados).
- Una caja que ya se cotiza sigue mientras cumpla las reglas del bot, aunque deje de estar "quieta": desde ahí la
  cuidan los filtros de movimiento, como en el real.

**Capital simulado:** US$ 95 (como la cuenta real).

**Llenado en papel (prudente):** una orden nuestra se llena solo si alguien operó como taker a un precio
**estrictamente peor** que el nuestro (la misma cuenta que el papel de clima). No hay reembolso de comisión en papel.

## Qué se mide
- Resultado de los llenados a precio de mercado (cobros − compras + ventas + acciones en cartera al medio del libro).
- Recompensa **estimada** por la fórmula del bot (con un solo lado cuenta un tercio). La fórmula sobreestima: el
  12-nov en clima estimó 8,67 y Polymarket pagó 4,92 (57 %). Por eso para decidir se usa **la mitad** de lo estimado.
- Cuántos llenados hay, en qué mercados, y cuántas veces saltaron los filtros y frenos.

## Período y veredicto
- Arranca el 13-nov-2026. Cuentan los **7 días completos de Uruguay del 14 al 20-nov**.
- **Veredicto: viernes 21-nov-2026, 10:00 de Uruguay.**
- **Neto prudente** = resultado de llenados a mercado + 50 % de la recompensa estimada, en esos 7 días.
  - **PASA** (se le propone a Agus probarlo en real con una parte chica de la plata): neto prudente ≥ +1,00 US$/día
    en promedio **y** llenados a mercado no peores que −1,00 US$/día (que la recompensa no esté tapando pérdidas
    grandes) **y** el freno diario saltó como mucho 1 vez.
  - **DUDOSO** (no se pone plata; se decide con Agus si se mide otra semana): neto prudente entre 0 y +1,00 US$/día.
  - **NO PASA** (se apaga): neto prudente negativo, o llenados peores que −1,00 US$/día, o el freno total saltó.
- Si hay menos de 10 llenados en los 7 días, el resultado de llenados no dice nada: se informa así y se mira solo
  si la recompensa estimada justifica seguir.

## Cómo se apaga
Archivo `bot/quietos/PARAR` (lo frena en la próxima pasada) o `apagar_despues_de` en la config (22-nov 00:00 Uruguay).

# Prueba en papel: favorito tardío en los Up/Down de 1 hora (regla fija)

Fijada el 26-oct-2026 ~14:55 UTC, antes de registrar nada. Sale de la hipótesis vista **después** de mirar el
histórico (`updown/LEEME.md`): a 6 min del cierre de la ventana de 1 h, el lado a 70–90 ¢ ganó 87 % cuando el precio
decía 80 %. Esta prueba la confirma o la descarta con el libro real. No usa plata ni pone órdenes.

## Qué y cuándo
- Mercados `btc-up-or-down-hourly` y `eth-up-or-down-hourly` (resuelven con la vela de 1 min de Binance).
- Momento: el reloj intenta entre el minuto **53 y 58** de cada hora (6 a 2 min antes del cierre). Si el reloj
  llega tarde (otra tarea lo demoró), esa hora no se registra y queda anotada como perdida.
- Se mira el libro real de los dos tokens (Up y Down).

## Operación
- Precio = lo que cuesta comprar **10 acciones** recorriendo el libro de ventas (asks) del token.
- Si el precio de 10 acciones de un lado está en **[0,70, 0,90)**, se compra ese lado: 10 acciones a ese precio.
  Si los dos lados califican (no debería pasar) o ninguno, no se opera.
- Una operación por mercado. Comisión: la del mercado (`feeSchedule.rate`, hoy 0,07·p·(1−p)).
- Se guarda siempre la foto (mejor bid/ask y precio de 10 y 50 acciones de cada lado), opere o no.

## Resultado
- Gana si el lado comprado resuelve a 1: neto = 10·(1 − p) − comisión; pierde: −10·p − comisión.
- Se liquida con `clob.polymarket.com/markets/<condition_id>` en cada pasada.

## Cuánto dura y qué decide
- Registra operaciones hasta el **16-nov-2026 23:59 UTC** (3 semanas, ~190 ops esperadas); después solo liquida.
- Pasa si: ROI > 0 con comisión, P(ROI ≤ 0) < 5 % por bootstrap de bloques (día), y neto positivo en BTC y en ETH
  por separado. Si no pasa, se cierra y no se arma bot.
- Se informa además con 1 ¢ extra de costo por acción (por si el bot real llega un poco más tarde que la foto).

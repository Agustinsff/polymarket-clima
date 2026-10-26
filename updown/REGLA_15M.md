# Favorito tardío en los Up/Down de 15 minutos (regla fija)

Fijada el 26-oct-2026 ~16:10 UTC, antes de bajar los 60 días de 15 min y sin mirar la muestra de 3 días de BTC
15 min que ya estaba bajada. Pregunta: ¿el sesgo que se vio en la ventana de 1 h (el favorito a 70–90 ¢ cerca del
cierre gana más de lo que dice el precio) también está en las ventanas de 15 min? Si está, el bot (que corre en la
PC de Agus, no en Actions) podría operar 4 veces más mercados. No se opera.

## Datos
- Series `btc-up-or-down-15m` y `eth-up-or-down-15m`, eventos cerrados con ganador de los últimos **60 días**.
- Precio del Up con `clob.polymarket.com/prices-history` a 1 minuto (último pago, no ask).
- Comisión del mercado (`feeSchedule.rate`; 0,07 si falta).

## Regla principal (la única que decide)
- A **90 s del cierre** (90 % de la ventana, igual que el 90 % de la de 1 h), con el último precio de los 90 s
  anteriores: si un lado está entre **70 y 90 ¢** (precio ≥ 0,70 y < 0,90), comprar 10 acciones de ese lado.
- Costo: precio + **1 ¢** por acción + comisión del mercado.
- **Pasa** si ROI > 0 con P(ROI ≤ 0) < 5 % por bootstrap de bloques (activo, día), 2.000 remuestreos, **y** el
  signo se repite en las dos mitades de las fechas **y** en BTC y ETH por separado.

## Se informa además (no decide)
- Lo mismo a 6, 4 y 3 min del cierre y con 0 y 2 ¢ de costo extra.
- Calibración de los tramos 60–70, 70–80, 80–90 y 90–100 ¢ en cada momento.
- Control: la misma cuenta sobre la ventana de 1 h a 6 min del cierre tiene que dar lo ya publicado
  (545 ops, +4,8 % con 1 ¢); si no, hay un error en el script.

## Si pasa
Se propone sumarla al bot en papel con la misma forma que el favorito de 1 h (regla nueva: se consulta a Agus).
Si no pasa, queda anotado y el bot sigue solo con 1 h.

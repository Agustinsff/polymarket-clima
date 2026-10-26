# Versión maker de la regla de las corridas. Resultados

Generado 2026-10-26 14:21Z con la regla fija de `REGLA_MAKER.md`. 1193 señales (las mismas de la prueba B de `REGLA.md`), 410 eventos, 2026-10-09 a 2026-10-22.

## Tasa de llenado (orden de compra que vale 3 h)

| orden | se llena | mediana del tiempo hasta llenarse |
|---|---|---|
| precio en W − 1 ¢ (principal) | 31% | 1.00 h |
| precio en W | 47% | 0.74 h |
| precio en W − 2 ¢ | 22% | 1.30 h |
| precio en W − 1 ¢, contando también operaciones justo a nuestro precio | 40% |  |

| tramo / modelo | señales | se llena (principal) |
|---|---|---|
| 5–20 ¢ | 476 | 30% |
| 20–40 ¢ | 690 | 32% |
| 40–60 ¢ | 27 | 41% |
| ecmwf | 649 | 29% |
| gfs | 544 | 33% |

## Resultado por operación

Ganancia = (venta − compra) / compra. t = media / error estándar agrupado por evento. Las filas taker usan las mismas señales y la misma salida, cambiando sólo la entrada.

| entrada | salida | operaciones | ganancia media | t | 1ª mitad | 2ª mitad |
|---|---|---|---|---|---|---|
| maker, W − 1 ¢ | taker a W + 6 h (principal) | 373 | -4.3% | -3.0 | -2.5% | -6.4% |
| maker, W − 1 ¢ | taker a W + 3 h | 373 | -7.8% | -7.5 | -6.0% | -9.8% |
| maker, W − 1 ¢ | taker 3 h después del llenado | 373 | -6.0% | -5.1 | -3.5% | -8.9% |
| maker, W − 1 ¢ | maker a W + 6 h + 1 ¢ (si no, taker a 9 h) | 373 | -6.1% | -3.7 | -4.9% | -7.5% |
| maker, W − 1 ¢ | quedarse hasta la resolución | 373 | -6.7% | -0.6 | +9.9% | -25.4% |
| maker, W | taker a W + 6 h (principal) | 559 | -5.5% | -4.9 | -3.6% | -7.7% |
| maker, W | taker a W + 3 h | 559 | -8.0% | -9.5 | -6.7% | -9.4% |
| maker, W | taker 3 h después del llenado | 559 | -6.8% | -7.2 | -5.4% | -8.4% |
| maker, W | maker a W + 6 h + 1 ¢ (si no, taker a 9 h) | 559 | -7.7% | -6.1 | -5.9% | -9.6% |
| maker, W | quedarse hasta la resolución | 559 | -1.3% | -0.1 | +11.0% | -15.3% |
| maker, W − 2 ¢ | taker a W + 6 h (principal) | 260 | -3.5% | -1.9 | -2.3% | -4.8% |
| maker, W − 2 ¢ | taker a W + 3 h | 260 | -7.5% | -5.5 | -6.5% | -8.5% |
| maker, W − 2 ¢ | taker 3 h después del llenado | 260 | -5.0% | -3.0 | -2.8% | -7.3% |
| maker, W − 2 ¢ | maker a W + 6 h + 1 ¢ (si no, taker a 9 h) | 260 | -5.0% | -2.4 | -5.4% | -4.5% |
| maker, W − 2 ¢ | quedarse hasta la resolución | 260 | -2.3% | -0.2 | +14.5% | -20.6% |
| taker (compra en W) | taker a W + 6 h | 1193 | -0.8% | -0.9 | -0.4% | -1.3% |
| taker (compra en W) | taker a W + 3 h | 1193 | -4.0% | -6.0 | -4.1% | -3.8% |

## Selección adversa: ¿qué pasó con las órdenes que no se llenaron?

Movimiento del precio de la caja de W a W + 6 h (sin costos), según si la orden principal se llenó o no.

| orden principal | señales | precio W → W+6 h | t | precio en W | pago final medio |
|---|---|---|---|---|---|
| se llenó | 373 | -3.0% | -2.2 | 23.7 ¢ | 21.2 ¢ |
| no se llenó | 820 | +17.4% | +14.0 | 22.7 ¢ | 27.9 ¢ |

## Por tramo de precio y modelo (entrada principal, salida principal)

| tramo / modelo | operaciones | ganancia media | t |
|---|---|---|---|
| 5–20 ¢ | 143 | -6.8% | -2.6 |
| 20–40 ¢ | 219 | -3.1% | -1.8 |
| 40–60 ¢ | 11 | +5.0% | +1.3 |
| ecmwf | 191 | -5.5% | -2.6 |
| gfs | 182 | -3.0% | -1.5 |

## Criterio de éxito

1. ≥ +2 % por operación llenada, t ≥ 2, ≥ 150 llenadas: **no** (-4.3%, t -3.0 , 373 ops).
2. Positiva en las dos mitades: **no** (-2.5% / -6.4%).
3. Tasa de llenado ≥ 30 %: **sí** (31%).


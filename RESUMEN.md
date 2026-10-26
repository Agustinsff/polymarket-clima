# Resumen polymarket-clima

_Actualizado: 2026-10-26 15:21 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

✅ Todo corriendo normalmente.

- Última foto de liquidez: 2026-10-26T15:21:42
- Monitor: mañana 2026-10-26, noche 2026-10-25
- Prueba São Paulo: último día registrado 2026-10-26
- Cosechador: último ciclo 2026-10-26 15:49 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 12/24, la del **modelo** 8/24.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-25 | Sao Paulo | 21°C | 23°C (32%) ❌ | 23°C (31%) ❌ |
| 2026-10-25 | Buenos Aires | 16°C | 16°C (44%) ✅ | 17°C (25%) ❌ |
| 2026-10-24 | Sao Paulo | 26°C | 26°C (30%) ✅ | 29°C or higher (27%) ❌ |
| 2026-10-24 | Buenos Aires | 18°C | 18°C (40%) ✅ | 18°C (25%) ✅ |
| 2026-10-23 | Sao Paulo | 23°C | 23°C (23%) ✅ | 24°C (21%) ❌ |
| 2026-10-23 | Buenos Aires | 24°C | 23°C (39%) ❌ | 25°C or higher (26%) ❌ |
| 2026-10-22 | Sao Paulo | 24°C | 23°C (35%) ❌ | 24°C (20%) ✅ |
| 2026-10-22 | Buenos Aires | 23°C | 21°C (31%) ❌ | 20°C (23%) ❌ |
| 2026-10-21 | Sao Paulo | 24°C | 24°C (38%) ✅ | 24°C (22%) ✅ |
| 2026-10-21 | Buenos Aires | 19°C | 21°C (40%) ❌ | 19°C (21%) ✅ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 13 (desde 2026-10-14).
Operaciones: 9 (2 ganadas, 6 perdidas, 1 pendientes). **Neto con comisiones: US$-7.41** (bruto -6.96, comisiones −0.45). _Con la comisión vieja (0,05 para todo) sería US$-7.62._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 27°C | Yes | 0.550 | 81% | +4.38 |
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |
| 2026-10-24 | 26°C | No | 0.229 | 58% | -2.29 |
| 2026-10-24 | 27°C | Yes | 0.178 | 37% | -1.78 |
| 2026-10-25 | 21°C | No | 0.060 | 57% | -0.60 |
| 2026-10-25 | 22°C | Yes | 0.057 | 37% | -0.57 |
| 2026-10-26 | 19°C | Yes | 0.062 | 16% | pendiente |

## Cosechador en papel (cajas imposibles, todas las ciudades)

Operaciones: 5. **Neto liquidado: US$-68.18**. Pendientes: +US$0.00 si salen bien. _Con la comisión vieja (0,05 para todo) sería US$-68.18._
Nota: las operaciones de Ciudad del Cabo del 18-oct se hicieron con la regla vieja (sin confirmación) y su resolución está en disputa.

| Día | Ciudad | Caja | Precio Yes | Acciones | Resultado |
|---|---|---|---|---|---|
| 2026-10-18 | cape-town | 17°C | 0.04 | 100 | +3.81 |
| 2026-10-18 | cape-town | 16°C | 0.03 | 100 | -97.15 |
| 2026-10-21 | istanbul | 15°C or below | 0.09 | 100 | +8.59 |
| 2026-10-22 | istanbul | 15°C or below | 0.17 | 61 | +10.24 |
| 2026-10-22 | istanbul | 15°C or below | 0.17 | 39 | +6.33 |

## Pronóstico vs. mercado (todas las ciudades, día anterior)

Puntaje Brier (más bajo = mejor) en 1387 cajas liquidadas: **modelo 0.0882** vs **mercado 0.0732**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 539 | 226 | US$-146.88 | 582 |
| maker | no | 2132 | 231 | US$-552.54 | 2289 |
| cola_taker | no | 354 | 12 | US$+1.69 | 368 |
| cola_maker | no | 384 | 9 | US$-26.64 | 389 |

Taker en total: US$-145.18. _Con la comisión vieja (0,05 para todo) sería US$-149.17._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 1460 cajas liquidadas: **modelo 0.0727** vs **mercado 0.0601**.
Series donde el modelo le gana al mercado (≥5 días): máx san-francisco (5 días), máx buenos-aires (5 días), máx toronto (5 días), máx chicago (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 385 | 94 | US$-218.99 | 160 |
| maker | no | 1189 | 129 | US$-198.50 | 563 |
| cola_taker | no | 154 | 4 | US$-20.10 | 91 |
| cola_maker | no | 369 | 7 | US$-38.85 | 197 |
| no80_90 | no | 138 | 105 | US$-136.96 | 81 |

Taker en total: US$-376.06. _Con la comisión vieja (0,05 para todo) sería US$-390.77._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 120 (114 liquidadas, 38 ganadas). **Neto US$+101.28** sobre US$269.08 invertidos (ROI +37.6 %). _Con la comisión vieja (0,05 para todo) sería US$+103.11._
Brier en 364 strikes: modelo 0.1679 vs mercado 0.1736.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 13 | US$+26.60 |
| BTC | rango | 26 | US$+76.84 |
| BTC | toca | 32 | US$-2.65 |
| ETH | above | 8 | US$-8.46 |
| ETH | rango | 18 | US$+9.83 |
| ETH | toca | 17 | US$-0.88 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 2190 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 6 operaciones; como maker se habrían llenado 4, neto **US$-10.19** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$41/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$45/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


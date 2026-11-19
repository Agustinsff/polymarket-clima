# Resumen polymarket-clima

_Actualizado: 2026-11-19 19:21 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, aparece el 2026-11-19 20:57 UTC): `highest-st-johns-river-level-at-cocoa-by` y 2 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-18 20:53 UTC): `biggest-earthquake` y 1 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-19T19:21:53
- Monitor: mañana 2026-11-19, noche 2026-11-18
- Prueba São Paulo: último día registrado 2026-11-19
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 27/72, la del **modelo** 15/72.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-18 | Sao Paulo | 31°C | 32°C (33%) ❌ | 31°C (25%) ✅ |
| 2026-11-18 | Buenos Aires | 26°C | 26°C (34%) ✅ | 27°C (25%) ❌ |
| 2026-11-17 | Sao Paulo | 28°C | 29°C (36%) ❌ | 27°C (23%) ❌ |
| 2026-11-17 | Buenos Aires | 27°C | 28°C (34%) ❌ | 28°C (23%) ❌ |
| 2026-11-16 | Sao Paulo | 26°C | 25°C (34%) ❌ | 26°C (24%) ✅ |
| 2026-11-16 | Buenos Aires | 30°C | 28°C (38%) ❌ | 28°C (25%) ❌ |
| 2026-11-15 | Sao Paulo | 31°C | 29°C (33%) ❌ | 30°C (24%) ❌ |
| 2026-11-15 | Buenos Aires | 29°C | 28°C (38%) ❌ | 27°C (24%) ❌ |
| 2026-11-14 | Sao Paulo | 28°C | 29°C (38%) ❌ | 27°C (23%) ❌ |
| 2026-11-14 | Buenos Aires | 29°C | 28°C (36%) ❌ | 28°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 37 (desde 2026-10-14).
Operaciones: 27 (3 ganadas, 22 perdidas, 2 pendientes). **Neto con comisiones: US$-8.42** (bruto -7.65, comisiones −0.77). _Con la comisión vieja (0,05 para todo) sería US$-8.80._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-11-06 | 28°C | No | 0.040 | 69% | -0.42 |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | -0.44 |
| 2026-11-09 | 17°C | No | 0.020 | 81% | -0.21 |
| 2026-11-09 | 18°C | Yes | 0.023 | 16% | -0.24 |
| 2026-11-11 | 29°C | No | 0.057 | 84% | +9.40 |
| 2026-11-12 | 28°C | No | 0.041 | 84% | -0.43 |
| 2026-11-16 | 26°C | No | 0.070 | 82% | -0.73 |
| 2026-11-18 | 31°C | No | 0.021 | 85% | -0.22 |
| 2026-11-19 | 31°C | Yes | 0.550 | 81% | pendiente |
| 2026-11-19 | 32°C | No | 0.545 | 16% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 12838 cajas liquidadas: **modelo 0.0879** vs **mercado 0.0735**.
Series donde el modelo le gana al mercado (≥5 días): mín dallas (7 días), mín chengdu (8 días), mín mexico-city (8 días), mín karachi (23 días), mín hong-kong (27 días), mín tel-aviv (10 días), máx buenos-aires (27 días), máx dallas (27 días), mín sao-paulo (18 días), mín taipei (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 3497 | 1354 | US$-1614.00 | 558 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 16992 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 1806 | 38 | US$-284.93 | 308 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 3402 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-2489.81. _Con la comisión vieja (0,05 para todo) sería US$-2662.35._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 7758 cajas liquidadas: **modelo 0.0934** vs **mercado 0.0744**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (11 días), máx buenos-aires (29 días), máx denver (26 días), mín cape-town (10 días), mín sao-paulo (17 días), mín seattle (19 días), mín houston (15 días), mín san-francisco (14 días), mín ankara (13 días), mín austin (23 días), mín buenos-aires (8 días), mín munich (14 días), mín mexico-city (19 días), mín chicago (16 días), mín toronto (9 días), mín guangzhou (16 días), mín karachi (7 días), mín chongqing (16 días), mín wuhan (14 días), mín istanbul (16 días), mín madrid (18 días), mín atlanta (15 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 2592 | 577 | US$-1324.52 | 162 |
| maker | no | 3169 | 382 | US$-397.61 | 5117 |
| cola_taker | no | 1288 | 34 | US$-158.33 | 75 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 1688 |
| no80_90 | no | 1052 | 716 | US$-1939.99 | 74 |

Taker en total: US$-3422.85. _Con la comisión vieja (0,05 para todo) sería US$-3511.94._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 647 (631 liquidadas, 317 ganadas). **Neto US$+187.76** sobre US$2920.94 invertidos (ROI +6.4 %). _Con la comisión vieja (0,05 para todo) sería US$+204.35._
Brier en 2427 strikes: modelo 0.1405 vs mercado 0.1390.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 81 | US$+48.02 |
| BTC | rango | 125 | US$+41.45 |
| BTC | toca | 181 | US$-39.73 |
| ETH | above | 52 | US$+12.99 |
| ETH | rango | 84 | US$+34.09 |
| ETH | toca | 108 | US$+90.95 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$35/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$20/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


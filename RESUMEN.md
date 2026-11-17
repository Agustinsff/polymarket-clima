# Resumen polymarket-clima

_Actualizado: 2026-11-17 15:16 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **temperatura mínima** (ciudades, ya no aparece el 2026-11-16 07:14 UTC): `san-francisco` y 7 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-17T15:16:36
- Monitor: mañana 2026-11-17, noche 2026-11-16
- Prueba São Paulo: último día registrado 2026-11-17
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 26/68, la del **modelo** 14/68.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-16 | Sao Paulo | 26°C | 25°C (34%) ❌ | 26°C (24%) ✅ |
| 2026-11-16 | Buenos Aires | 30°C | 28°C (38%) ❌ | 28°C (25%) ❌ |
| 2026-11-15 | Sao Paulo | 31°C | 29°C (33%) ❌ | 30°C (24%) ❌ |
| 2026-11-15 | Buenos Aires | 29°C | 28°C (38%) ❌ | 27°C (24%) ❌ |
| 2026-11-14 | Sao Paulo | 28°C | 29°C (38%) ❌ | 27°C (23%) ❌ |
| 2026-11-14 | Buenos Aires | 29°C | 28°C (36%) ❌ | 28°C (25%) ❌ |
| 2026-11-13 | Sao Paulo | 28°C | 28°C (36%) ✅ | 27°C (20%) ❌ |
| 2026-11-13 | Buenos Aires | 25°C | 28°C (38%) ❌ | 29°C (20%) ❌ |
| 2026-11-12 | Sao Paulo | 28°C | 28°C (32%) ✅ | 27°C (22%) ❌ |
| 2026-11-12 | Buenos Aires | 31°C | 30°C (43%) ❌ | 30°C (22%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 35 (desde 2026-10-14).
Operaciones: 24 (3 ganadas, 21 perdidas, 0 pendientes). **Neto con comisiones: US$-8.20** (bruto -7.44, comisiones −0.76). _Con la comisión vieja (0,05 para todo) sería US$-8.58._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-11-02 | 25°C | Yes | 0.160 | 38% | -1.67 |
| 2026-11-05 | 26°C | No | 0.039 | 52% | -0.41 |
| 2026-11-05 | 27°C | Yes | 0.040 | 41% | -0.42 |
| 2026-11-06 | 28°C | No | 0.040 | 69% | -0.42 |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | -0.44 |
| 2026-11-09 | 17°C | No | 0.020 | 81% | -0.21 |
| 2026-11-09 | 18°C | Yes | 0.023 | 16% | -0.24 |
| 2026-11-11 | 29°C | No | 0.057 | 84% | +9.40 |
| 2026-11-12 | 28°C | No | 0.041 | 84% | -0.43 |
| 2026-11-16 | 26°C | No | 0.070 | 82% | -0.73 |

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

Puntaje Brier (más bajo = mejor) en 11986 cajas liquidadas: **modelo 0.0877** vs **mercado 0.0733**.
Series donde el modelo le gana al mercado (≥5 días): mín dallas (7 días), mín karachi (21 días), mín chengdu (8 días), mín mexico-city (8 días), mín hong-kong (25 días), máx buenos-aires (25 días), máx dallas (25 días), mín sao-paulo (16 días), mín taipei (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 3119 | 1220 | US$-1348.59 | 530 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 15523 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 1603 | 37 | US$-220.29 | 282 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 3040 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-2159.76. _Con la comisión vieja (0,05 para todo) sería US$-2332.30._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 7312 cajas liquidadas: **modelo 0.0935** vs **mercado 0.0745**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (11 días), máx buenos-aires (27 días), mín cape-town (10 días), mín sao-paulo (17 días), máx denver (24 días), mín seattle (17 días), mín houston (14 días), mín san-francisco (14 días), mín ankara (13 días), mín austin (21 días), mín buenos-aires (8 días), mín mexico-city (18 días), mín chicago (16 días), mín munich (13 días), mín toronto (9 días), mín guangzhou (16 días), mín madrid (17 días), mín karachi (7 días), mín chongqing (16 días), mín wuhan (14 días), mín istanbul (16 días), mín atlanta (15 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 2415 | 542 | US$-1228.05 | 158 |
| maker | no | 3169 | 382 | US$-397.61 | 4606 |
| cola_taker | no | 1193 | 31 | US$-147.32 | 78 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 1533 |
| no80_90 | no | 984 | 670 | US$-1814.71 | 67 |

Taker en total: US$-3190.09. _Con la comisión vieja (0,05 para todo) sería US$-3279.18._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 617 (595 liquidadas, 288 ganadas). **Neto US$+186.85** sobre US$2635.38 invertidos (ROI +7.1 %). _Con la comisión vieja (0,05 para todo) sería US$+202.43._
Brier en 2254 strikes: modelo 0.1408 vs mercado 0.1390.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 77 | US$+52.06 |
| BTC | rango | 120 | US$+68.23 |
| BTC | toca | 166 | US$-69.90 |
| ETH | above | 50 | US$+19.70 |
| ETH | rango | 82 | US$+40.88 |
| ETH | toca | 100 | US$+75.88 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$18/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$15/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


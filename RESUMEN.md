# Resumen polymarket-clima

_Actualizado: 2026-11-18 14:51 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, aparece el 2026-11-18 01:17 UTC): `which-cities-will-get-more-snow-than-average-this-winter` y 1 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-18 01:17 UTC): `when-will-the-danube-river-return-to-normal-levels`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-18T14:51:08
- Monitor: mañana 2026-11-18, noche 2026-11-17
- Prueba São Paulo: último día registrado 2026-11-18
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 26/70, la del **modelo** 14/70.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-17 | Sao Paulo | 28°C | 29°C (36%) ❌ | 27°C (23%) ❌ |
| 2026-11-17 | Buenos Aires | 27°C | 28°C (34%) ❌ | 28°C (23%) ❌ |
| 2026-11-16 | Sao Paulo | 26°C | 25°C (34%) ❌ | 26°C (24%) ✅ |
| 2026-11-16 | Buenos Aires | 30°C | 28°C (38%) ❌ | 28°C (25%) ❌ |
| 2026-11-15 | Sao Paulo | 31°C | 29°C (33%) ❌ | 30°C (24%) ❌ |
| 2026-11-15 | Buenos Aires | 29°C | 28°C (38%) ❌ | 27°C (24%) ❌ |
| 2026-11-14 | Sao Paulo | 28°C | 29°C (38%) ❌ | 27°C (23%) ❌ |
| 2026-11-14 | Buenos Aires | 29°C | 28°C (36%) ❌ | 28°C (25%) ❌ |
| 2026-11-13 | Sao Paulo | 28°C | 28°C (36%) ✅ | 27°C (20%) ❌ |
| 2026-11-13 | Buenos Aires | 25°C | 28°C (38%) ❌ | 29°C (20%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 36 (desde 2026-10-14).
Operaciones: 25 (3 ganadas, 21 perdidas, 1 pendientes). **Neto con comisiones: US$-8.20** (bruto -7.44, comisiones −0.76). _Con la comisión vieja (0,05 para todo) sería US$-8.58._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-11-05 | 26°C | No | 0.039 | 52% | -0.41 |
| 2026-11-05 | 27°C | Yes | 0.040 | 41% | -0.42 |
| 2026-11-06 | 28°C | No | 0.040 | 69% | -0.42 |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | -0.44 |
| 2026-11-09 | 17°C | No | 0.020 | 81% | -0.21 |
| 2026-11-09 | 18°C | Yes | 0.023 | 16% | -0.24 |
| 2026-11-11 | 29°C | No | 0.057 | 84% | +9.40 |
| 2026-11-12 | 28°C | No | 0.041 | 84% | -0.43 |
| 2026-11-16 | 26°C | No | 0.070 | 82% | -0.73 |
| 2026-11-18 | 31°C | No | 0.021 | 85% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 12391 cajas liquidadas: **modelo 0.0880** vs **mercado 0.0736**.
Series donde el modelo le gana al mercado (≥5 días): mín dallas (7 días), mín chengdu (8 días), mín mexico-city (8 días), mín karachi (22 días), mín hong-kong (26 días), máx buenos-aires (26 días), máx dallas (26 días), mín sao-paulo (17 días), mín taipei (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 3303 | 1287 | US$-1479.52 | 538 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 16264 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 1695 | 37 | US$-254.62 | 296 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 3236 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-2325.03. _Con la comisión vieja (0,05 para todo) sería US$-2497.57._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 7533 cajas liquidadas: **modelo 0.0935** vs **mercado 0.0745**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (11 días), máx buenos-aires (28 días), mín cape-town (10 días), mín sao-paulo (17 días), mín seattle (18 días), máx denver (25 días), mín houston (14 días), mín san-francisco (14 días), mín ankara (13 días), mín austin (22 días), mín buenos-aires (8 días), mín munich (14 días), mín mexico-city (19 días), mín chicago (16 días), mín toronto (9 días), mín guangzhou (16 días), mín karachi (7 días), mín chongqing (16 días), mín wuhan (14 días), mín istanbul (16 días), mín madrid (18 días), mín atlanta (15 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 2509 | 561 | US$-1274.02 | 138 |
| maker | no | 3169 | 382 | US$-397.61 | 4837 |
| cola_taker | no | 1239 | 31 | US$-167.37 | 77 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 1598 |
| no80_90 | no | 1022 | 695 | US$-1892.14 | 56 |

Taker en total: US$-3333.54. _Con la comisión vieja (0,05 para todo) sería US$-3422.63._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 631 (617 liquidadas, 303 ganadas). **Neto US$+162.49** sobre US$2807.44 invertidos (ROI +5.8 %). _Con la comisión vieja (0,05 para todo) sería US$+178.73._
Brier en 2346 strikes: modelo 0.1421 vs mercado 0.1402.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 80 | US$+45.76 |
| BTC | rango | 125 | US$+41.45 |
| BTC | toca | 172 | US$-57.39 |
| ETH | above | 52 | US$+12.99 |
| ETH | rango | 84 | US$+34.09 |
| ETH | toca | 104 | US$+85.59 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$18/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$14/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


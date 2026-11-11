# Resumen polymarket-clima

_Actualizado: 2026-11-11 18:37 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

⚠️ El cosechador no actualiza desde 2026-11-04 16:12 UTC.

- Última foto de liquidez: 2026-11-11T18:37:49
- Monitor: mañana 2026-11-11, noche 2026-11-10
- Prueba São Paulo: último día registrado 2026-11-11
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 23/56, la del **modelo** 12/56.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-10 | Sao Paulo | 23°C | 23°C (34%) ✅ | 22°C (21%) ❌ |
| 2026-11-10 | Buenos Aires | 25°C | 28°C (44%) ❌ | 27°C (22%) ❌ |
| 2026-11-09 | Sao Paulo | 17°C | 17°C (39%) ✅ | 16°C (19%) ❌ |
| 2026-11-09 | Buenos Aires | 26°C | 25°C (47%) ❌ | 25°C (23%) ❌ |
| 2026-11-08 | Sao Paulo | 21°C | 20°C (36%) ❌ | 22°C (23%) ❌ |
| 2026-11-08 | Buenos Aires | 23°C | 22°C (42%) ❌ | 23°C (25%) ✅ |
| 2026-11-07 | Sao Paulo | 32°C | 32°C (32%) ✅ | 31°C (19%) ❌ |
| 2026-11-07 | Buenos Aires | 17°C | 19°C (42%) ❌ | 19°C (23%) ❌ |
| 2026-11-06 | Sao Paulo | 28°C | 26°C (28%) ❌ | 25°C (23%) ❌ |
| 2026-11-06 | Buenos Aires | 25°C | 26°C (41%) ❌ | 26°C (24%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 29 (desde 2026-10-14).
Operaciones: 22 (2 ganadas, 19 perdidas, 1 pendientes). **Neto con comisiones: US$-16.44** (bruto -15.76, comisiones −0.68). _Con la comisión vieja (0,05 para todo) sería US$-16.82._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-28 | 22°C | Yes | 0.100 | 37% | -1.00 |
| 2026-11-02 | 24°C | No | 0.165 | 59% | -1.72 |
| 2026-11-02 | 25°C | Yes | 0.160 | 38% | -1.67 |
| 2026-11-05 | 26°C | No | 0.039 | 52% | -0.41 |
| 2026-11-05 | 27°C | Yes | 0.040 | 41% | -0.42 |
| 2026-11-06 | 28°C | No | 0.040 | 69% | -0.42 |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | -0.44 |
| 2026-11-09 | 17°C | No | 0.020 | 81% | -0.21 |
| 2026-11-09 | 18°C | Yes | 0.023 | 16% | -0.24 |
| 2026-11-11 | 29°C | No | 0.057 | 84% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 9228 cajas liquidadas: **modelo 0.0872** vs **mercado 0.0724**.
Series donde el modelo le gana al mercado (≥5 días): mín karachi (15 días), mín dallas (6 días), mín tel-aviv (7 días), mín chengdu (7 días), mín mexico-city (7 días), mín chicago (8 días), mín hong-kong (19 días), máx dallas (19 días), máx buenos-aires (19 días), máx qingdao (19 días), mín milan (11 días), mín sao-paulo (13 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 1929 | 744 | US$-889.40 | 539 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 11038 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 1007 | 21 | US$-155.11 | 268 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 2179 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-1635.40. _Con la comisión vieja (0,05 para todo) sería US$-1807.94._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 5722 cajas liquidadas: **modelo 0.0928** vs **mercado 0.0733**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (10 días), máx buenos-aires (21 días), mín cape-town (7 días), mín sao-paulo (13 días), mín ankara (8 días), mín seattle (13 días), mín houston (11 días), máx london (21 días), mín moscow (9 días), mín mexico-city (13 días), mín dallas (8 días), mín munich (11 días), mín austin (16 días), mín guangzhou (13 días), mín san-francisco (12 días), máx atlanta (21 días), mín karachi (7 días), mín chongqing (13 días), mín wuhan (11 días), mín istanbul (13 días), mín toronto (7 días), mín buenos-aires (5 días), mín milan (11 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 1821 | 415 | US$-1000.85 | 197 |
| maker | no | 3169 | 382 | US$-397.61 | 3208 |
| cola_taker | no | 904 | 20 | US$-136.11 | 92 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 1042 |
| no80_90 | no | 744 | 515 | US$-1280.12 | 85 |

Taker en total: US$-2417.07. _Con la comisión vieja (0,05 para todo) sería US$-2506.16._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 469 (466 liquidadas, 183 ganadas). **Neto US$+49.68** sobre US$1735.81 invertidos (ROI +2.9 %). _Con la comisión vieja (0,05 para todo) sería US$+61.48._
Brier en 1718 strikes: modelo 0.1380 vs mercado 0.1350.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 58 | US$+36.05 |
| BTC | rango | 95 | US$+27.61 |
| BTC | toca | 125 | US$-61.83 |
| ETH | above | 39 | US$-7.47 |
| ETH | rango | 71 | US$+6.34 |
| ETH | toca | 78 | US$+48.99 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$21/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$41/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


# Resumen polymarket-clima

_Actualizado: 2026-11-07 08:33 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

⚠️ El cosechador no actualiza desde 2026-11-04 16:12 UTC.
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-07 10:40 UTC): `how-many-chinook-will-pass-bonneville-dam-by`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-07T08:32:52
- Monitor: mañana 2026-11-06, noche 2026-11-06
- Prueba São Paulo: último día registrado 2026-11-06
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 20/46, la del **modelo** 11/46.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-05 | Sao Paulo | 26°C | 27°C (22%) ❌ | 29°C (17%) ❌ |
| 2026-11-05 | Buenos Aires | 27°C | 27°C (52%) ✅ | 26°C (25%) ❌ |
| 2026-11-04 | Sao Paulo | 33°C | 32°C (42%) ❌ | 32°C (22%) ❌ |
| 2026-11-04 | Buenos Aires | 26°C | 25°C (46%) ❌ | 25°C (25%) ❌ |
| 2026-11-03 | Sao Paulo | 31°C | 31°C (42%) ✅ | 31°C (21%) ✅ |
| 2026-11-03 | Buenos Aires | 23°C | 23°C (44%) ✅ | 22°C (24%) ❌ |
| 2026-11-02 | Sao Paulo | 24°C | 24°C (20%) ✅ | 27°C (18%) ❌ |
| 2026-11-02 | Buenos Aires | 26°C | 27°C (46%) ❌ | 27°C (25%) ❌ |
| 2026-11-01 | Sao Paulo | 29°C | 28°C (34%) ❌ | 28°C (22%) ❌ |
| 2026-11-01 | Buenos Aires | 22°C | 24°C (36%) ❌ | 25°C (20%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 24 (desde 2026-10-14).
Operaciones: 19 (2 ganadas, 15 perdidas, 2 pendientes). **Neto con comisiones: US$-15.13** (bruto -14.51, comisiones −0.62). _Con la comisión vieja (0,05 para todo) sería US$-15.51._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-27 | 21°C | No | 0.040 | 82% | -0.40 |
| 2026-10-27 | 22°C | Yes | 0.039 | 16% | -0.39 |
| 2026-10-28 | 21°C | No | 0.110 | 58% | -1.10 |
| 2026-10-28 | 22°C | Yes | 0.100 | 37% | -1.00 |
| 2026-11-02 | 24°C | No | 0.165 | 59% | -1.72 |
| 2026-11-02 | 25°C | Yes | 0.160 | 38% | -1.67 |
| 2026-11-05 | 26°C | No | 0.039 | 52% | -0.41 |
| 2026-11-05 | 27°C | Yes | 0.040 | 41% | -0.42 |
| 2026-11-06 | 28°C | No | 0.040 | 69% | pendiente |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 6744 cajas liquidadas: **modelo 0.0887** vs **mercado 0.0731**.
Series donde el modelo le gana al mercado (≥5 días): mín karachi (10 días), máx buenos-aires (14 días), mín mexico-city (5 días), mín hong-kong (14 días), máx seattle (14 días), mín toronto (5 días), mín seattle (5 días), máx dallas (14 días), mín atlanta (6 días), mín helsinki (6 días), mín buenos-aires (7 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 950 | 364 | US$-392.43 | 676 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 6645 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 526 | 10 | US$-85.36 | 322 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 1370 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-1068.67. _Con la comisión vieja (0,05 para todo) sería US$-1241.21._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 4372 cajas liquidadas: **modelo 0.0925** vs **mercado 0.0734**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (7 días), máx denver (13 días), máx buenos-aires (16 días), máx london (16 días), mín sao-paulo (8 días), máx seattle (16 días), mín ankara (6 días), mín munich (7 días), mín houston (7 días), mín mexico-city (10 días), mín austin (11 días), mín dallas (5 días), mín guangzhou (8 días), mín chongqing (9 días), mín chengdu (5 días), mín moscow (7 días), mín karachi (5 días), mín seattle (9 días), mín shenzhen (8 días), mín wuhan (7 días), mín san-francisco (7 días), mín jeddah (6 días), mín istanbul (9 días), mín toronto (5 días), mín buenos-aires (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 1381 | 315 | US$-811.10 | 227 |
| maker | no | 3169 | 382 | US$-397.61 | 1881 |
| cola_taker | no | 662 | 12 | US$-124.81 | 129 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 641 |
| no80_90 | no | 557 | 392 | US$-888.10 | 88 |

Taker en total: US$-1824.01. _Con la comisión vieja (0,05 para todo) sería US$-1913.10._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 380 (350 liquidadas, 140 ganadas). **Neto US$+74.29** sobre US$1292.32 invertidos (ROI +5.7 %). _Con la comisión vieja (0,05 para todo) sería US$+82.91._
Brier en 1391 strikes: modelo 0.1400 vs mercado 0.1371.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 44 | US$+40.14 |
| BTC | rango | 75 | US$+54.55 |
| BTC | toca | 97 | US$-70.98 |
| ETH | above | 27 | US$-3.74 |
| ETH | rango | 53 | US$+6.34 |
| ETH | toca | 54 | US$+47.97 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$39/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$57/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


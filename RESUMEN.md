# Resumen polymarket-clima

_Actualizado: 2026-11-05 08:15 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

⚠️ El cosechador no actualiza desde 2026-11-04 16:12 UTC.
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, aparece el 2026-11-03 19:47 UTC): `phivolcs-raises-mayon-to-alert-level`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-04 11:32 UTC): `what-category-will-vance-reach`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura máxima** (comisión, ya no aparece el 2026-11-04 01:38 UTC): `feesEnabled=True feeType=zero_fees feeSchedule={"exponent": 1, "rate": 0, "rebateRate": 0, "takerOnly": true} takerBaseFee=1000`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (comisión, ya no aparece el 2026-11-04 01:38 UTC): `feesEnabled=True feeType=zero_fees feeSchedule={"exponent": 1, "rate": 0, "rebateRate": 0, "takerOnly": true} takerBaseFee=1000`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-05T08:15:02
- Monitor: mañana 2026-11-04, noche 2026-11-04
- Prueba São Paulo: último día registrado 2026-11-04
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 19/42, la del **modelo** 11/42.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-03 | Sao Paulo | 31°C | 31°C (42%) ✅ | 31°C (21%) ✅ |
| 2026-11-03 | Buenos Aires | 23°C | 23°C (44%) ✅ | 22°C (24%) ❌ |
| 2026-11-02 | Sao Paulo | 24°C | 24°C (20%) ✅ | 27°C (18%) ❌ |
| 2026-11-02 | Buenos Aires | 26°C | 27°C (46%) ❌ | 27°C (25%) ❌ |
| 2026-11-01 | Sao Paulo | 29°C | 28°C (34%) ❌ | 28°C (22%) ❌ |
| 2026-11-01 | Buenos Aires | 22°C | 24°C (36%) ❌ | 25°C (20%) ❌ |
| 2026-10-31 | Sao Paulo | 28°C | 26°C (34%) ❌ | 26°C (25%) ❌ |
| 2026-10-31 | Buenos Aires | 26°C | 25°C (38%) ❌ | 25°C (25%) ❌ |
| 2026-10-30 | Sao Paulo | 25°C | 25°C (32%) ✅ | 26°C (23%) ❌ |
| 2026-10-30 | Buenos Aires | 24°C | 22°C (34%) ❌ | 23°C (22%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 22 (desde 2026-10-14).
Operaciones: 15 (2 ganadas, 13 perdidas, 0 pendientes). **Neto con comisiones: US$-14.30** (bruto -13.72, comisiones −0.58). _Con la comisión vieja (0,05 para todo) sería US$-14.68._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-24 | 27°C | Yes | 0.178 | 37% | -1.78 |
| 2026-10-25 | 21°C | No | 0.060 | 57% | -0.60 |
| 2026-10-25 | 22°C | Yes | 0.057 | 37% | -0.57 |
| 2026-10-26 | 19°C | Yes | 0.062 | 16% | -0.62 |
| 2026-10-27 | 21°C | No | 0.040 | 82% | -0.40 |
| 2026-10-27 | 22°C | Yes | 0.039 | 16% | -0.39 |
| 2026-10-28 | 21°C | No | 0.110 | 58% | -1.10 |
| 2026-10-28 | 22°C | Yes | 0.100 | 37% | -1.00 |
| 2026-11-02 | 24°C | No | 0.165 | 59% | -1.72 |
| 2026-11-02 | 25°C | Yes | 0.160 | 38% | -1.67 |

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

Puntaje Brier (más bajo = mejor) en 5715 cajas liquidadas: **modelo 0.0896** vs **mercado 0.0735**.
Series donde el modelo le gana al mercado (≥5 días): máx seattle (12 días), máx buenos-aires (12 días), mín mexico-city (5 días), mín hong-kong (12 días), máx atlanta (12 días), mín toronto (5 días), máx karachi (12 días), mín buenos-aires (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 529 | 207 | US$-172.76 | 675 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 4869 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 309 | 7 | US$-36.56 | 346 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 1020 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-800.20. _Con la comisión vieja (0,05 para todo) sería US$-972.74._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 3841 cajas liquidadas: **modelo 0.0911** vs **mercado 0.0722**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (6 días), máx denver (11 días), máx buenos-aires (14 días), mín sao-paulo (7 días), máx seattle (14 días), mín atlanta (7 días), mín munich (5 días), máx qingdao (12 días), mín houston (6 días), mín austin (11 días), mín guangzhou (6 días), mín seattle (7 días), mín karachi (5 días), mín mexico-city (8 días), mín moscow (5 días), mín san-francisco (6 días), mín wuhan (6 días), mín shenzhen (6 días), mín jeddah (5 días), mín toronto (5 días), mín istanbul (7 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 1205 | 279 | US$-670.64 | 223 |
| maker | no | 3169 | 382 | US$-397.61 | 1339 |
| cola_taker | no | 564 | 11 | US$-100.92 | 120 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 453 |
| no80_90 | no | 469 | 341 | US$-630.45 | 112 |

Taker en total: US$-1402.01. _Con la comisión vieja (0,05 para todo) sería US$-1491.10._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 319 (319 liquidadas, 116 ganadas). **Neto US$+85.84** sobre US$1043.83 invertidos (ROI +8.2 %). _Con la comisión vieja (0,05 para todo) sería US$+93.59._
Brier en 1203 strikes: modelo 0.1381 vs mercado 0.1347.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 36 | US$+41.95 |
| BTC | rango | 67 | US$+79.36 |
| BTC | toca | 93 | US$-69.17 |
| ETH | above | 22 | US$-10.44 |
| ETH | rango | 50 | US$+0.11 |
| ETH | toca | 51 | US$+44.04 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$52/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$56/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


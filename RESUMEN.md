# Resumen polymarket-clima

_Actualizado: 2026-11-04 06:45 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, aparece el 2026-11-03 19:47 UTC): `phivolcs-raises-mayon-to-alert-level` y 2 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-02 19:45 UTC): `will-it-rain-during-the-united-states-grand-prix`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura máxima** (comisión, ya no aparece el 2026-11-04 01:38 UTC): `feesEnabled=True feeType=zero_fees feeSchedule={"exponent": 1, "rate": 0, "rebateRate": 0, "takerOnly": true} takerBaseFee=1000`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (comisión, ya no aparece el 2026-11-04 01:38 UTC): `feesEnabled=True feeType=zero_fees feeSchedule={"exponent": 1, "rate": 0, "rebateRate": 0, "takerOnly": true} takerBaseFee=1000`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-04T06:37:36
- Monitor: mañana 2026-11-03, noche 2026-11-03
- Prueba São Paulo: último día registrado 2026-11-03
- Cosechador: último ciclo 2026-11-04 04:48 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 17/40, la del **modelo** 10/40.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-02 | Sao Paulo | 24°C | 24°C (20%) ✅ | 27°C (18%) ❌ |
| 2026-11-02 | Buenos Aires | 26°C | 27°C (46%) ❌ | 27°C (25%) ❌ |
| 2026-11-01 | Sao Paulo | 29°C | 28°C (34%) ❌ | 28°C (22%) ❌ |
| 2026-11-01 | Buenos Aires | 22°C | 24°C (36%) ❌ | 25°C (20%) ❌ |
| 2026-10-31 | Sao Paulo | 28°C | 26°C (34%) ❌ | 26°C (25%) ❌ |
| 2026-10-31 | Buenos Aires | 26°C | 25°C (38%) ❌ | 25°C (25%) ❌ |
| 2026-10-30 | Sao Paulo | 25°C | 25°C (32%) ✅ | 26°C (23%) ❌ |
| 2026-10-30 | Buenos Aires | 24°C | 22°C (34%) ❌ | 23°C (22%) ❌ |
| 2026-10-29 | Sao Paulo | 21°C | 20°C (38%) ❌ | 22°C (18%) ❌ |
| 2026-10-29 | Buenos Aires | 25°C | 25°C (44%) ✅ | 24°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 21 (desde 2026-10-14).
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

Puntaje Brier (más bajo = mejor) en 5218 cajas liquidadas: **modelo 0.0900** vs **mercado 0.0735**.
Series donde el modelo le gana al mercado (≥5 días): mín hong-kong (11 días), máx seattle (11 días), máx atlanta (11 días), máx buenos-aires (11 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 327 | 125 | US$-127.98 | 677 |
| taker | no | 1826 | 735 | US$-546.88 | 4 |
| maker | sí | 441 | 52 | US$-175.56 | 3921 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 190 | 4 | US$-27.26 | 364 |
| cola_taker | no | 1191 | 37 | US$-23.24 | 4 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 840 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-725.36. _Con la comisión vieja (0,05 para todo) sería US$-891.80._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 3566 cajas liquidadas: **modelo 0.0905** vs **mercado 0.0716**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (6 días), máx buenos-aires (13 días), máx denver (10 días), máx qingdao (11 días), máx seattle (13 días), mín sao-paulo (7 días), mín houston (5 días), mín atlanta (6 días), mín austin (10 días), mín guangzhou (5 días), mín seattle (7 días), mín karachi (5 días), mín mexico-city (8 días), mín moscow (5 días), mín shenzhen (5 días), mín wuhan (5 días), mín san-francisco (5 días), mín toronto (5 días), mín istanbul (6 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 1128 | 257 | US$-639.26 | 202 |
| maker | no | 3169 | 382 | US$-397.61 | 1021 |
| cola_taker | no | 531 | 10 | US$-100.62 | 96 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 363 |
| no80_90 | no | 428 | 314 | US$-544.04 | 108 |

Taker en total: US$-1283.91. _Con la comisión vieja (0,05 para todo) sería US$-1373.01._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 311 (299 liquidadas, 101 ganadas). **Neto US$+84.33** sobre US$897.39 invertidos (ROI +9.4 %). _Con la comisión vieja (0,05 para todo) sería US$+91.49._
Brier en 1094 strikes: modelo 0.1290 vs mercado 0.1260.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 35 | US$+40.15 |
| BTC | rango | 63 | US$+87.87 |
| BTC | toca | 84 | US$-62.95 |
| ETH | above | 21 | US$-11.29 |
| ETH | rango | 49 | US$-0.82 |
| ETH | toca | 47 | US$+31.37 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$35/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$51/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


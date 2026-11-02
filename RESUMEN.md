# Resumen polymarket-clima

_Actualizado: 2026-11-01 22:18 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-01 06:49 UTC): `tornado`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (comisión, aparece el 2026-11-01 06:49 UTC): `feesEnabled=True feeType=weather_fees feeSchedule={"exponent": 1, "rate": 0.05, "rebateRate": 0.25, "takerOnly": true} takerBaseFee=1000`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-01T22:18:05
- Monitor: mañana 2026-11-01, noche 2026-11-01
- Prueba São Paulo: último día registrado 2026-11-01
- Cosechador: último ciclo 2026-11-01 19:46 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 16/36, la del **modelo** 10/36.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-31 | Sao Paulo | 28°C | 26°C (34%) ❌ | 26°C (25%) ❌ |
| 2026-10-31 | Buenos Aires | 26°C | 25°C (38%) ❌ | 25°C (25%) ❌ |
| 2026-10-30 | Sao Paulo | 25°C | 25°C (32%) ✅ | 26°C (23%) ❌ |
| 2026-10-30 | Buenos Aires | 24°C | 22°C (34%) ❌ | 23°C (22%) ❌ |
| 2026-10-29 | Sao Paulo | 21°C | 20°C (38%) ❌ | 22°C (18%) ❌ |
| 2026-10-29 | Buenos Aires | 25°C | 25°C (44%) ✅ | 24°C (25%) ❌ |
| 2026-10-28 | Sao Paulo | 21°C | 23°C (34%) ❌ | 23°C (25%) ❌ |
| 2026-10-28 | Buenos Aires | 25°C | 24°C (44%) ❌ | 23°C (24%) ❌ |
| 2026-10-27 | Sao Paulo | 21°C | 21°C (40%) ✅ | 21°C (22%) ✅ |
| 2026-10-27 | Buenos Aires | 19°C | 20°C (45%) ❌ | 20°C (22%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 19 (desde 2026-10-14).
Operaciones: 13 (2 ganadas, 11 perdidas, 0 pendientes). **Neto con comisiones: US$-10.92** (bruto -10.47, comisiones −0.45). _Con la comisión vieja (0,05 para todo) sería US$-11.29._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |
| 2026-10-24 | 26°C | No | 0.229 | 58% | -2.29 |
| 2026-10-24 | 27°C | Yes | 0.178 | 37% | -1.78 |
| 2026-10-25 | 21°C | No | 0.060 | 57% | -0.60 |
| 2026-10-25 | 22°C | Yes | 0.057 | 37% | -0.57 |
| 2026-10-26 | 19°C | Yes | 0.062 | 16% | -0.62 |
| 2026-10-27 | 21°C | No | 0.040 | 82% | -0.40 |
| 2026-10-27 | 22°C | Yes | 0.039 | 16% | -0.39 |
| 2026-10-28 | 21°C | No | 0.110 | 58% | -1.10 |
| 2026-10-28 | 22°C | Yes | 0.100 | 37% | -1.00 |

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

Puntaje Brier (más bajo = mejor) en 4172 cajas liquidadas: **modelo 0.0924** vs **mercado 0.0754**.
Series donde el modelo le gana al mercado (≥5 días): mín hong-kong (8 días), máx atlanta (9 días), máx seattle (9 días), máx karachi (9 días), máx buenos-aires (9 días), máx san-francisco (9 días), máx tel-aviv (8 días), mín karachi (5 días), mín shenzhen (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 0 | 0 | US$+0.00 | 578 |
| taker | no | 1745 | 699 | US$-543.72 | 85 |
| maker | sí | 0 | 0 | US$+0.00 | 2434 |
| maker | no | 7247 | 819 | US$-1498.11 | 454 |
| cola_taker | sí | 0 | 0 | US$+0.00 | 335 |
| cola_taker | no | 1150 | 34 | US$-40.50 | 45 |
| cola_maker | sí | 0 | 0 | US$+0.00 | 461 |
| cola_maker | no | 1229 | 28 | US$-92.38 | 89 |

Taker en total: US$-584.21. _Con la comisión vieja (0,05 para todo) sería US$-709.94._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 3031 cajas liquidadas: **modelo 0.0896** vs **mercado 0.0718**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (5 días), máx denver (8 días), máx buenos-aires (11 días), máx guangzhou (9 días), máx seattle (11 días), máx qingdao (9 días), mín sao-paulo (6 días), mín shanghai (8 días), mín austin (9 días), mín atlanta (5 días), mín seattle (5 días), mín moscow (5 días), mín mexico-city (6 días), mín istanbul (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 933 | 221 | US$-485.74 | 198 |
| maker | no | 2877 | 349 | US$-306.06 | 645 |
| cola_taker | no | 427 | 9 | US$-67.45 | 105 |
| cola_maker | no | 975 | 21 | US$-52.08 | 224 |
| no80_90 | no | 353 | 266 | US$-374.45 | 82 |

Taker en total: US$-927.63. _Con la comisión vieja (0,05 para todo) sería US$-1002.71._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 279 (262 liquidadas, 84 ganadas). **Neto US$+71.24** sobre US$745.20 invertidos (ROI +9.6 %). _Con la comisión vieja (0,05 para todo) sería US$+77.05._
Brier en 916 strikes: modelo 0.1377 vs mercado 0.1338.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 31 | US$+38.02 |
| BTC | rango | 55 | US$+74.47 |
| BTC | toca | 71 | US$-44.05 |
| ETH | above | 20 | US$-9.15 |
| ETH | rango | 45 | US$+1.53 |
| ETH | toca | 40 | US$+10.42 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4754 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$38/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$62/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


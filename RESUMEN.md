# Resumen polymarket-clima

_Actualizado: 2026-10-29 21:16 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-10-29 06:25 UTC): `what-intensity-will-champi-reach`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura máxima** (fuente de resolución, ya no aparece el 2026-10-28 18:29 UTC): `weather.gov/wrh/timeseries`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (fuente de resolución, ya no aparece el 2026-10-28 00:43 UTC): `weather.gov/wrh/timeseries`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-10-29T21:15:24
- Monitor: mañana 2026-10-29, noche 2026-10-29
- Prueba São Paulo: último día registrado 2026-10-29
- Cosechador: último ciclo 2026-10-29 23:31 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 14/30, la del **modelo** 10/30.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-28 | Sao Paulo | 21°C | 23°C (34%) ❌ | 23°C (25%) ❌ |
| 2026-10-28 | Buenos Aires | 25°C | 24°C (44%) ❌ | 23°C (24%) ❌ |
| 2026-10-27 | Sao Paulo | 21°C | 21°C (40%) ✅ | 21°C (22%) ✅ |
| 2026-10-27 | Buenos Aires | 19°C | 20°C (45%) ❌ | 20°C (22%) ❌ |
| 2026-10-26 | Sao Paulo | 18°C | 19°C (38%) ❌ | 18°C (24%) ✅ |
| 2026-10-26 | Buenos Aires | 18°C | 18°C (42%) ✅ | 19°C (23%) ❌ |
| 2026-10-25 | Sao Paulo | 21°C | 23°C (32%) ❌ | 23°C (31%) ❌ |
| 2026-10-25 | Buenos Aires | 16°C | 16°C (44%) ✅ | 17°C (25%) ❌ |
| 2026-10-24 | Sao Paulo | 26°C | 26°C (30%) ✅ | 29°C or higher (27%) ❌ |
| 2026-10-24 | Buenos Aires | 18°C | 18°C (40%) ✅ | 18°C (25%) ✅ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 16 (desde 2026-10-14).
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

Puntaje Brier (más bajo = mejor) en 2798 cajas liquidadas: **modelo 0.0911** vs **mercado 0.0751**.
Series donde el modelo le gana al mercado (≥5 días): mín hong-kong (6 días), máx karachi (6 días), máx seattle (6 días), máx san-francisco (6 días), máx tel-aviv (5 días), máx atlanta (6 días), máx buenos-aires (6 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 1157 | 478 | US$-335.71 | 641 |
| maker | no | 4585 | 537 | US$-944.46 | 2939 |
| cola_taker | no | 744 | 24 | US$-4.51 | 434 |
| cola_maker | no | 798 | 20 | US$-40.50 | 491 |

Taker en total: US$-340.22. _Con la comisión vieja (0,05 para todo) sería US$-406.20._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 2220 cajas liquidadas: **modelo 0.0856** vs **mercado 0.0700**.
Series donde el modelo le gana al mercado (≥5 días): máx denver (5 días), máx taipei (6 días), máx buenos-aires (8 días), máx guangzhou (6 días), máx seattle (8 días), máx san-francisco (8 días), máx istanbul (6 días), mín shanghai (6 días), máx tokyo (6 días), mín austin (7 días), mín mexico-city (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 650 | 163 | US$-280.69 | 189 |
| maker | no | 2061 | 240 | US$-190.30 | 536 |
| cola_taker | no | 296 | 6 | US$-46.80 | 84 |
| cola_maker | no | 673 | 14 | US$-37.71 | 193 |
| no80_90 | no | 252 | 188 | US$-283.19 | 68 |

Taker en total: US$-610.68. _Con la comisión vieja (0,05 para todo) sería US$-655.64._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 163 (151 liquidadas, 51 ganadas). **Neto US$+102.38** sobre US$393.81 invertidos (ROI +26.0 %). _Con la comisión vieja (0,05 para todo) sería US$+105.40._
Brier en 691 strikes: modelo 0.1391 vs mercado 0.1396.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 14 | US$+27.92 |
| BTC | rango | 30 | US$+63.20 |
| BTC | toca | 49 | US$-1.71 |
| ETH | above | 9 | US$-7.62 |
| ETH | rango | 23 | US$+2.87 |
| ETH | toca | 26 | US$+17.72 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 3581 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$55/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$52/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


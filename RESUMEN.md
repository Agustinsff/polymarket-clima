# Resumen polymarket-clima

_Actualizado: 2026-10-30 12:53 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-10-29 06:25 UTC): `what-intensity-will-champi-reach`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura máxima** (fuente de resolución, ya no aparece el 2026-10-28 18:29 UTC): `weather.gov/wrh/timeseries`. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-10-30T12:48:41
- Monitor: mañana 2026-10-30, noche 2026-10-29
- Prueba São Paulo: último día registrado 2026-10-29
- Cosechador: último ciclo 2026-10-30 10:53 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 15/32, la del **modelo** 10/32.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-29 | Sao Paulo | 21°C | 20°C (38%) ❌ | 22°C (18%) ❌ |
| 2026-10-29 | Buenos Aires | 25°C | 25°C (44%) ✅ | 24°C (25%) ❌ |
| 2026-10-28 | Sao Paulo | 21°C | 23°C (34%) ❌ | 23°C (25%) ❌ |
| 2026-10-28 | Buenos Aires | 25°C | 24°C (44%) ❌ | 23°C (24%) ❌ |
| 2026-10-27 | Sao Paulo | 21°C | 21°C (40%) ✅ | 21°C (22%) ✅ |
| 2026-10-27 | Buenos Aires | 19°C | 20°C (45%) ❌ | 20°C (22%) ❌ |
| 2026-10-26 | Sao Paulo | 18°C | 19°C (38%) ❌ | 18°C (24%) ✅ |
| 2026-10-26 | Buenos Aires | 18°C | 18°C (42%) ✅ | 19°C (23%) ❌ |
| 2026-10-25 | Sao Paulo | 21°C | 23°C (32%) ❌ | 23°C (31%) ❌ |
| 2026-10-25 | Buenos Aires | 16°C | 16°C (44%) ✅ | 17°C (25%) ❌ |

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

Puntaje Brier (más bajo = mejor) en 3243 cajas liquidadas: **modelo 0.0930** vs **mercado 0.0759**.
Series donde el modelo le gana al mercado (≥5 días): mín hong-kong (7 días), máx seattle (7 días), máx tel-aviv (6 días), máx atlanta (7 días), máx karachi (7 días), máx san-francisco (7 días), máx buenos-aires (7 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 0 | 0 | US$+0.00 | 86 |
| taker | no | 1346 | 543 | US$-407.53 | 463 |
| maker | sí | 0 | 0 | US$+0.00 | 308 |
| maker | no | 5378 | 620 | US$-1076.91 | 2206 |
| cola_taker | sí | 0 | 0 | US$+0.00 | 54 |
| cola_taker | no | 872 | 26 | US$-28.56 | 312 |
| cola_maker | sí | 0 | 0 | US$+0.00 | 61 |
| cola_maker | no | 915 | 21 | US$-65.58 | 382 |

Taker en total: US$-436.09. _Con la comisión vieja (0,05 para todo) sería US$-520.70._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 2486 cajas liquidadas: **modelo 0.0881** vs **mercado 0.0722**.
Series donde el modelo le gana al mercado (≥5 días): máx denver (6 días), máx buenos-aires (9 días), máx qingdao (7 días), máx guangzhou (7 días), máx seattle (9 días), máx milan (9 días), mín shanghai (7 días), mín austin (7 días), mín mexico-city (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 744 | 186 | US$-315.81 | 162 |
| maker | no | 2322 | 280 | US$-151.42 | 496 |
| cola_taker | no | 339 | 6 | US$-61.77 | 76 |
| cola_maker | no | 753 | 15 | US$-50.32 | 191 |
| no80_90 | no | 278 | 203 | US$-357.76 | 69 |

Taker en total: US$-735.34. _Con la comisión vieja (0,05 para todo) sería US$-789.91._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 193 (161 liquidadas, 55 ganadas). **Neto US$+77.73** sobre US$457.57 invertidos (ROI +17.0 %). _Con la comisión vieja (0,05 para todo) sería US$+81.01._
Brier en 713 strikes: modelo 0.1425 vs mercado 0.1419.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 14 | US$+27.92 |
| BTC | rango | 30 | US$+63.20 |
| BTC | toca | 55 | US$-15.84 |
| ETH | above | 9 | US$-7.62 |
| ETH | rango | 23 | US$+2.87 |
| ETH | toca | 30 | US$+7.20 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 3779 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$45/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$51/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


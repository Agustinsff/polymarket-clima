# Resumen polymarket-clima

_Actualizado: 2026-11-16 02:16 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-15 16:34 UTC): `state-d4-drought` y 1 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (ciudades, ya no aparece el 2026-11-15 23:09 UTC): `cape-town` y 8 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-16T02:06:14
- Monitor: mañana 2026-11-15, noche 2026-11-15
- Prueba São Paulo: último día registrado 2026-11-15
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 26/64, la del **modelo** 13/64.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-14 | Sao Paulo | 28°C | 29°C (38%) ❌ | 27°C (23%) ❌ |
| 2026-11-14 | Buenos Aires | 29°C | 28°C (36%) ❌ | 28°C (25%) ❌ |
| 2026-11-13 | Sao Paulo | 28°C | 28°C (36%) ✅ | 27°C (20%) ❌ |
| 2026-11-13 | Buenos Aires | 25°C | 28°C (38%) ❌ | 29°C (20%) ❌ |
| 2026-11-12 | Sao Paulo | 28°C | 28°C (32%) ✅ | 27°C (22%) ❌ |
| 2026-11-12 | Buenos Aires | 31°C | 30°C (43%) ❌ | 30°C (22%) ❌ |
| 2026-11-11 | Sao Paulo | 30°C | 27°C (41%) ❌ | 27°C (25%) ❌ |
| 2026-11-11 | Buenos Aires | 29°C | 29°C (37%) ✅ | 29°C (21%) ✅ |
| 2026-11-10 | Sao Paulo | 23°C | 23°C (34%) ✅ | 22°C (21%) ❌ |
| 2026-11-10 | Buenos Aires | 25°C | 28°C (44%) ❌ | 27°C (22%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 33 (desde 2026-10-14).
Operaciones: 23 (3 ganadas, 20 perdidas, 0 pendientes). **Neto con comisiones: US$-7.47** (bruto -6.74, comisiones −0.73). _Con la comisión vieja (0,05 para todo) sería US$-7.85._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-11-02 | 24°C | No | 0.165 | 59% | -1.72 |
| 2026-11-02 | 25°C | Yes | 0.160 | 38% | -1.67 |
| 2026-11-05 | 26°C | No | 0.039 | 52% | -0.41 |
| 2026-11-05 | 27°C | Yes | 0.040 | 41% | -0.42 |
| 2026-11-06 | 28°C | No | 0.040 | 69% | -0.42 |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | -0.44 |
| 2026-11-09 | 17°C | No | 0.020 | 81% | -0.21 |
| 2026-11-09 | 18°C | Yes | 0.023 | 16% | -0.24 |
| 2026-11-11 | 29°C | No | 0.057 | 84% | +9.40 |
| 2026-11-12 | 28°C | No | 0.041 | 84% | -0.43 |

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

Puntaje Brier (más bajo = mejor) en 11097 cajas liquidadas: **modelo 0.0876** vs **mercado 0.0730**.
Series donde el modelo le gana al mercado (≥5 días): mín dallas (7 días), mín karachi (19 días), mín chengdu (8 días), mín mexico-city (8 días), mín tel-aviv (8 días), mín hong-kong (22 días), máx buenos-aires (23 días), máx dallas (23 días), máx qingdao (23 días), mín sao-paulo (14 días), mín taipei (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 2716 | 1062 | US$-1157.29 | 648 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 14471 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 1405 | 30 | US$-213.40 | 329 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 2814 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-1961.57. _Con la comisión vieja (0,05 para todo) sería US$-2134.11._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 6832 cajas liquidadas: **modelo 0.0932** vs **mercado 0.0738**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (11 días), máx buenos-aires (25 días), mín cape-town (10 días), mín sao-paulo (17 días), máx london (25 días), mín seattle (15 días), máx denver (22 días), mín houston (14 días), mín san-francisco (14 días), mín ankara (11 días), mín buenos-aires (8 días), mín moscow (10 días), mín austin (19 días), mín mexico-city (16 días), mín chicago (16 días), mín munich (13 días), mín toronto (9 días), mín guangzhou (16 días), mín karachi (7 días), mín chongqing (16 días), mín wuhan (14 días), mín istanbul (16 días), mín atlanta (15 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 2230 | 506 | US$-1149.51 | 204 |
| maker | no | 3169 | 382 | US$-397.61 | 4245 |
| cola_taker | no | 1093 | 30 | US$-116.54 | 108 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 1413 |
| no80_90 | no | 907 | 620 | US$-1644.08 | 88 |

Taker en total: US$-2910.13. _Con la comisión vieja (0,05 para todo) sería US$-2999.22._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 578 (553 liquidadas, 246 ganadas). **Neto US$+112.83** sobre US$2293.25 invertidos (ROI +4.9 %). _Con la comisión vieja (0,05 para todo) sería US$+127.32._
Brier en 2134 strikes: modelo 0.1466 vs mercado 0.1441.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 74 | US$+47.92 |
| BTC | rango | 114 | US$+60.94 |
| BTC | toca | 147 | US$-97.49 |
| ETH | above | 49 | US$+17.34 |
| ETH | rango | 81 | US$+38.54 |
| ETH | toca | 88 | US$+45.57 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$12/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$15/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


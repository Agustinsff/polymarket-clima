# Resumen polymarket-clima

_Actualizado: 2026-10-23 22:27 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **temperatura máxima** (reglamento, aparece el 2026-10-23 23:58 UTC): `The qualifying value is converted using °F = °C × #/# + # and rounded to the nearest whole degree, with a value ending in exactly half rounded up to t` y 4 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (reglamento, aparece el 2026-10-23 19:31 UTC): `#°C is exactly #°F and counts as #°F.` y 4 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-10-23T22:27:32
- Monitor: mañana 2026-10-23, noche 2026-10-23
- Prueba São Paulo: último día registrado 2026-10-23
- Cosechador: último ciclo 2026-10-23 19:38 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 8/16, la del **modelo** 6/16.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-21 | Sao Paulo | 24°C | 24°C (38%) ✅ | 24°C (22%) ✅ |
| 2026-10-21 | Buenos Aires | 19°C | 21°C (40%) ❌ | 19°C (21%) ✅ |
| 2026-10-20 | Sao Paulo | 23°C | 23°C (38%) ✅ | 24°C or higher (21%) ❌ |
| 2026-10-20 | Buenos Aires | 21°C | 21°C (50%) ✅ | 20°C (25%) ❌ |
| 2026-10-19 | Sao Paulo | 22°C | 22°C (34%) ✅ | 22°C (17%) ✅ |
| 2026-10-19 | Buenos Aires | 19°C | 18°C (48%) ❌ | 18°C (25%) ❌ |
| 2026-10-18 | Sao Paulo | 24°C | 25°C (46%) ❌ | 24°C (22%) ✅ |
| 2026-10-18 | Buenos Aires | 16°C | 16°C (52%) ✅ | 17°C (21%) ❌ |
| 2026-10-17 | Sao Paulo | 22°C | 22°C (32%) ✅ | 22°C (23%) ✅ |
| 2026-10-17 | Buenos Aires | 13°C | 14°C (48%) ❌ | 14°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 10 (desde 2026-10-14).
Operaciones: 4 (2 ganadas, 2 perdidas, 0 pendientes). **Neto con comisiones: US$-2.17** (bruto -1.72, comisiones −0.45). _Con la comisión vieja (0,05 para todo) sería US$-2.17._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 27°C | Yes | 0.550 | 81% | +4.38 |
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |

## Cosechador en papel (cajas imposibles, todas las ciudades)

Operaciones: 5. **Neto liquidado: US$+8.59**. Pendientes: +US$23.23 si salen bien. _Con la comisión vieja (0,05 para todo) sería US$+8.59._
Nota: las operaciones de Ciudad del Cabo del 18-oct se hicieron con la regla vieja (sin confirmación) y su resolución está en disputa.

| Día | Ciudad | Caja | Precio Yes | Acciones | Resultado |
|---|---|---|---|---|---|
| 2026-10-18 | cape-town | 17°C | 0.04 | 100 | pendiente |
| 2026-10-18 | cape-town | 16°C | 0.03 | 100 | pendiente |
| 2026-10-21 | istanbul | 15°C or below | 0.09 | 100 | +8.59 |
| 2026-10-22 | istanbul | 15°C or below | 0.17 | 61 | pendiente |
| 2026-10-22 | istanbul | 15°C or below | 0.17 | 39 | pendiente |

## Pronóstico vs. mercado (todas las ciudades, día anterior)

Puntaje Brier (más bajo = mejor) en 486 cajas liquidadas: **modelo 0.0739** vs **mercado 0.0636**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 146 | 65 | US$-24.38 | 449 |
| maker | no | 559 | 64 | US$-141.21 | 1856 |
| cola_taker | no | 90 | 3 | US$+0.94 | 292 |
| cola_maker | no | 152 | 3 | US$-8.77 | 272 |

Taker en total: US$-23.44. _Con la comisión vieja (0,05 para todo) sería US$-23.44._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 674 cajas liquidadas: **modelo 0.0545** vs **mercado 0.0479**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 134 | 39 | US$-34.37 | 157 |
| maker | no | 444 | 47 | US$-46.38 | 496 |
| cola_taker | no | 58 | 3 | US$+7.68 | 54 |
| cola_maker | no | 140 | 3 | US$-8.74 | 133 |
| no80_90 | no | 43 | 33 | US$-40.28 | 63 |

Taker en total: US$-66.97. _Con la comisión vieja (0,05 para todo) sería US$-66.97._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 62 (36 liquidadas, 15 ganadas). **Neto US$+26.25** sobre US$120.54 invertidos (ROI +21.8 %). _Con la comisión vieja (0,05 para todo) sería US$+26.41._
Brier en 186 strikes: modelo 0.1747 vs mercado 0.1780.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 2 | US$-0.29 |
| BTC | rango | 6 | US$+22.48 |
| BTC | toca | 18 | US$+4.30 |
| ETH | above | 1 | US$-1.15 |
| ETH | rango | 2 | US$+6.98 |
| ETH | toca | 7 | US$-6.07 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 964 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1514 acciones llenadas, neto **US$+30.28** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1029 acciones llenadas, neto **US$+30.89** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 593 acciones llenadas, neto **US$+29.64** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 4 operaciones; como maker se habrían llenado 2, neto **US$-7.76** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$40/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$60/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


# Resumen polymarket-clima

_Actualizado: 2026-10-25 04:34 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **temperatura máxima** (reglamento, aparece el 2026-10-23 23:58 UTC): `The qualifying value is converted using °F = °C × #/# + # and rounded to the nearest whole degree, with a value ending in exactly half rounded up to t` y 4 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (reglamento, aparece el 2026-10-23 19:31 UTC): `#°C is exactly #°F and counts as #°F.` y 4 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-10-25T04:34:51
- Monitor: mañana 2026-10-24, noche 2026-10-24
- Prueba São Paulo: último día registrado 2026-10-24
- Cosechador: último ciclo 2026-10-25 05:43 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 9/20, la del **modelo** 7/20.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-23 | Sao Paulo | 23°C | 23°C (23%) ✅ | 24°C (21%) ❌ |
| 2026-10-23 | Buenos Aires | 24°C | 23°C (39%) ❌ | 25°C or higher (26%) ❌ |
| 2026-10-22 | Sao Paulo | 24°C | 23°C (35%) ❌ | 24°C (20%) ✅ |
| 2026-10-22 | Buenos Aires | 23°C | 21°C (31%) ❌ | 20°C (23%) ❌ |
| 2026-10-21 | Sao Paulo | 24°C | 24°C (38%) ✅ | 24°C (22%) ✅ |
| 2026-10-21 | Buenos Aires | 19°C | 21°C (40%) ❌ | 19°C (21%) ✅ |
| 2026-10-20 | Sao Paulo | 23°C | 23°C (38%) ✅ | 24°C or higher (21%) ❌ |
| 2026-10-20 | Buenos Aires | 21°C | 21°C (50%) ✅ | 20°C (25%) ❌ |
| 2026-10-19 | Sao Paulo | 22°C | 22°C (34%) ✅ | 22°C (17%) ✅ |
| 2026-10-19 | Buenos Aires | 19°C | 18°C (48%) ❌ | 18°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 11 (desde 2026-10-14).
Operaciones: 6 (2 ganadas, 2 perdidas, 2 pendientes). **Neto con comisiones: US$-2.17** (bruto -1.72, comisiones −0.45). _Con la comisión vieja (0,05 para todo) sería US$-2.17._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 27°C | Yes | 0.550 | 81% | +4.38 |
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |
| 2026-10-24 | 26°C | No | 0.229 | 58% | pendiente |
| 2026-10-24 | 27°C | Yes | 0.178 | 37% | pendiente |

## Cosechador en papel (cajas imposibles, todas las ciudades)

Operaciones: 5. **Neto liquidado: US$+25.16**. Pendientes: +US$6.66 si salen bien. _Con la comisión vieja (0,05 para todo) sería US$+25.16._
Nota: las operaciones de Ciudad del Cabo del 18-oct se hicieron con la regla vieja (sin confirmación) y su resolución está en disputa.

| Día | Ciudad | Caja | Precio Yes | Acciones | Resultado |
|---|---|---|---|---|---|
| 2026-10-18 | cape-town | 17°C | 0.04 | 100 | pendiente |
| 2026-10-18 | cape-town | 16°C | 0.03 | 100 | pendiente |
| 2026-10-21 | istanbul | 15°C or below | 0.09 | 100 | +8.59 |
| 2026-10-22 | istanbul | 15°C or below | 0.17 | 61 | +10.24 |
| 2026-10-22 | istanbul | 15°C or below | 0.17 | 39 | +6.33 |

## Pronóstico vs. mercado (todas las ciudades, día anterior)

Puntaje Brier (más bajo = mejor) en 952 cajas liquidadas: **modelo 0.0808** vs **mercado 0.0679**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 377 | 155 | US$-128.66 | 442 |
| maker | no | 1487 | 156 | US$-398.41 | 1648 |
| cola_taker | no | 245 | 7 | US$-13.08 | 282 |
| cola_maker | no | 300 | 6 | US$-22.44 | 280 |

Taker en total: US$-141.74. _Con la comisión vieja (0,05 para todo) sería US$-141.74._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 1021 cajas liquidadas: **modelo 0.0624** vs **mercado 0.0525**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 237 | 59 | US$-142.99 | 169 |
| maker | no | 781 | 75 | US$-161.72 | 537 |
| cola_taker | no | 90 | 3 | US$-3.79 | 82 |
| cola_maker | no | 217 | 3 | US$-36.95 | 192 |
| no80_90 | no | 90 | 69 | US$-85.06 | 64 |

Taker en total: US$-231.84. _Con la comisión vieja (0,05 para todo) sería US$-231.84._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 96 (71 liquidadas, 32 ganadas). **Neto US$+133.96** sobre US$180.22 invertidos (ROI +74.3 %). _Con la comisión vieja (0,05 para todo) sería US$+134.72._
Brier en 251 strikes: modelo 0.1837 vs mercado 0.1971.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 6 | US$+35.56 |
| BTC | rango | 15 | US$+97.74 |
| BTC | toca | 23 | US$+2.82 |
| ETH | above | 4 | US$-4.54 |
| ETH | rango | 10 | US$+4.28 |
| ETH | toca | 13 | US$-1.89 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 1620 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1716 acciones llenadas, neto **US$+34.32** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1142 acciones llenadas, neto **US$+34.27** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 705 acciones llenadas, neto **US$+35.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 4 operaciones; como maker se habrían llenado 2, neto **US$-7.76** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$52/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$64/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


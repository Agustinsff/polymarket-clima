# Resumen polymarket-clima

_Actualizado: 2026-10-26 09:11 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

✅ Todo corriendo normalmente.

- Última foto de liquidez: 2026-10-26T09:11:33
- Monitor: mañana 2026-10-25, noche 2026-10-25
- Prueba São Paulo: último día registrado 2026-10-25
- Cosechador: último ciclo 2026-10-26 10:08 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 11/22, la del **modelo** 8/22.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-24 | Sao Paulo | 26°C | 26°C (30%) ✅ | 29°C or higher (27%) ❌ |
| 2026-10-24 | Buenos Aires | 18°C | 18°C (40%) ✅ | 18°C (25%) ✅ |
| 2026-10-23 | Sao Paulo | 23°C | 23°C (23%) ✅ | 24°C (21%) ❌ |
| 2026-10-23 | Buenos Aires | 24°C | 23°C (39%) ❌ | 25°C or higher (26%) ❌ |
| 2026-10-22 | Sao Paulo | 24°C | 23°C (35%) ❌ | 24°C (20%) ✅ |
| 2026-10-22 | Buenos Aires | 23°C | 21°C (31%) ❌ | 20°C (23%) ❌ |
| 2026-10-21 | Sao Paulo | 24°C | 24°C (38%) ✅ | 24°C (22%) ✅ |
| 2026-10-21 | Buenos Aires | 19°C | 21°C (40%) ❌ | 19°C (21%) ✅ |
| 2026-10-20 | Sao Paulo | 23°C | 23°C (38%) ✅ | 24°C or higher (21%) ❌ |
| 2026-10-20 | Buenos Aires | 21°C | 21°C (50%) ✅ | 20°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 12 (desde 2026-10-14).
Operaciones: 8 (2 ganadas, 4 perdidas, 2 pendientes). **Neto con comisiones: US$-6.24** (bruto -5.79, comisiones −0.45). _Con la comisión vieja (0,05 para todo) sería US$-6.40._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 27°C | Yes | 0.550 | 81% | +4.38 |
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |
| 2026-10-24 | 26°C | No | 0.229 | 58% | -2.29 |
| 2026-10-24 | 27°C | Yes | 0.178 | 37% | -1.78 |
| 2026-10-25 | 21°C | No | 0.060 | 57% | pendiente |
| 2026-10-25 | 22°C | Yes | 0.057 | 37% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 952 cajas liquidadas: **modelo 0.0808** vs **mercado 0.0679**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 377 | 155 | US$-128.66 | 628 |
| maker | no | 1487 | 156 | US$-398.41 | 2461 |
| cola_taker | no | 245 | 7 | US$-13.08 | 399 |
| cola_maker | no | 300 | 6 | US$-22.44 | 398 |

Taker en total: US$-141.74. _Con la comisión vieja (0,05 para todo) sería US$-141.74._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 1163 cajas liquidadas: **modelo 0.0656** vs **mercado 0.0547**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 288 | 71 | US$-173.86 | 229 |
| maker | no | 897 | 87 | US$-204.04 | 770 |
| cola_taker | no | 109 | 3 | US$-12.12 | 121 |
| cola_maker | no | 260 | 4 | US$-39.97 | 275 |
| no80_90 | no | 106 | 81 | US$-102.93 | 101 |

Taker en total: US$-288.91. _Con la comisión vieja (0,05 para todo) sería US$-293.48._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 117 (106 liquidadas, 35 ganadas). **Neto US$+97.44** sobre US$244.00 invertidos (ROI +39.9 %). _Con la comisión vieja (0,05 para todo) sería US$+98.98._
Brier en 316 strikes: modelo 0.1649 vs mercado 0.1704.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 13 | US$+26.60 |
| BTC | rango | 26 | US$+76.84 |
| BTC | toca | 25 | US$+1.42 |
| ETH | above | 8 | US$-8.46 |
| ETH | rango | 17 | US$+1.91 |
| ETH | toca | 17 | US$-0.88 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 1988 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1916 acciones llenadas, neto **US$+38.32** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1242 acciones llenadas, neto **US$+37.27** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 6 operaciones; como maker se habrían llenado 4, neto **US$-10.19** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$43/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$43/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


# Resumen polymarket-clima

_Actualizado: 2026-10-21 01:14 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

✅ Todo corriendo normalmente.

- Última foto de liquidez: 2026-10-21T01:14:07
- Monitor: mañana 2026-10-20, noche 2026-10-20
- Prueba São Paulo: último día registrado 2026-10-20
- Cosechador: último ciclo 2026-10-20 23:29 UTC, 86 mercados, 45 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 4/10, la del **modelo** 3/10.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-18 | Sao Paulo | 24°C | 25°C (46%) ❌ | 24°C (22%) ✅ |
| 2026-10-18 | Buenos Aires | 16°C | 16°C (52%) ✅ | 17°C (21%) ❌ |
| 2026-10-17 | Sao Paulo | 22°C | 22°C (32%) ✅ | 22°C (23%) ✅ |
| 2026-10-17 | Buenos Aires | 13°C | 14°C (48%) ❌ | 14°C (25%) ❌ |
| 2026-10-16 | Sao Paulo | 27°C | 27°C (37%) ✅ | 26°C (24%) ❌ |
| 2026-10-16 | Buenos Aires | 15°C | 17°C (40%) ❌ | 18°C (23%) ❌ |
| 2026-10-15 | Sao Paulo | 27°C | 28°C (35%) ❌ | 26°C (24%) ❌ |
| 2026-10-15 | Buenos Aires | 21°C | 19°C (46%) ❌ | 19°C (25%) ❌ |
| 2026-10-14 | Sao Paulo | 30°C | 28°C (26%) ❌ | 27°C (16%) ❌ |
| 2026-10-14 | Buenos Aires | 20°C | 20°C (28%) ✅ | 20°C (25%) ✅ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 7 (desde 2026-10-14).
Operaciones: 4 (2 ganadas, 2 perdidas, 0 pendientes). **Neto con comisiones: US$-2.17** (bruto -1.72, comisiones −0.45).

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 27°C | Yes | 0.550 | 81% | +4.38 |
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |

## Cosechador en papel (cajas imposibles, todas las ciudades)

Operaciones: 2. **Neto liquidado: US$+0.00**. Pendientes: +US$6.66 si salen bien.
Nota: las operaciones de Ciudad del Cabo del 18-oct se hicieron con la regla vieja (sin confirmación) y su resolución está en disputa.

| Día | Ciudad | Caja | Precio Yes | Acciones | Resultado |
|---|---|---|---|---|---|
| 2026-10-18 | cape-town | 17°C | 0.04 | 100 | pendiente |
| 2026-10-18 | cape-town | 16°C | 0.03 | 100 | pendiente |

## Pronóstico vs. mercado (todas las ciudades, día anterior)

Todavía no hay días liquidados.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 0 | 0 | US$+0.00 | 241 |
| maker | no | 0 | 0 | US$+0.00 | 913 |
| cola_taker | no | 0 | 0 | US$+0.00 | 158 |
| cola_maker | no | 0 | 0 | US$+0.00 | 225 |

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Todavía no hay días liquidados.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 0 | 0 | US$+0.00 | 60 |
| maker | no | 0 | 0 | US$+0.00 | 217 |
| cola_taker | no | 0 | 0 | US$+0.00 | 27 |
| cola_maker | no | 0 | 0 | US$+0.00 | 80 |
| no80_90 | no | 0 | 0 | US$+0.00 | 23 |

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 8 (0 liquidadas, 0 ganadas). **Neto US$+0.00** sobre US$0.00 invertidos.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 0 | US$+0.00 |
| BTC | rango | 0 | US$+0.00 |
| BTC | toca | 0 | US$+0.00 |
| ETH | above | 0 | US$+0.00 |
| ETH | rango | 0 | US$+0.00 |
| ETH | toca | 0 | US$+0.00 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Prueba SP: 4 operaciones; como maker se habrían llenado 2, neto **US$-7.76** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$47/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$48/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


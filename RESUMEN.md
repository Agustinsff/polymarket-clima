# Resumen polymarket-clima

_Actualizado: 2026-10-22 09:50 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

✅ Todo corriendo normalmente.

- Última foto de liquidez: 2026-10-22T09:50:37
- Monitor: mañana 2026-10-21, noche 2026-10-21
- Prueba São Paulo: último día registrado 2026-10-21
- Cosechador: último ciclo 2026-10-22 09:33 UTC, 86 mercados, 45 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 5/12, la del **modelo** 4/12.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-19 | Sao Paulo | 22°C | 22°C (34%) ✅ | 22°C (17%) ✅ |
| 2026-10-19 | Buenos Aires | 19°C | 18°C (48%) ❌ | 18°C (25%) ❌ |
| 2026-10-18 | Sao Paulo | 24°C | 25°C (46%) ❌ | 24°C (22%) ✅ |
| 2026-10-18 | Buenos Aires | 16°C | 16°C (52%) ✅ | 17°C (21%) ❌ |
| 2026-10-17 | Sao Paulo | 22°C | 22°C (32%) ✅ | 22°C (23%) ✅ |
| 2026-10-17 | Buenos Aires | 13°C | 14°C (48%) ❌ | 14°C (25%) ❌ |
| 2026-10-16 | Sao Paulo | 27°C | 27°C (37%) ✅ | 26°C (24%) ❌ |
| 2026-10-16 | Buenos Aires | 15°C | 17°C (40%) ❌ | 18°C (23%) ❌ |
| 2026-10-15 | Sao Paulo | 27°C | 28°C (35%) ❌ | 26°C (24%) ❌ |
| 2026-10-15 | Buenos Aires | 21°C | 19°C (46%) ❌ | 19°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 8 (desde 2026-10-14).
Operaciones: 4 (2 ganadas, 2 perdidas, 0 pendientes). **Neto con comisiones: US$-2.17** (bruto -1.72, comisiones −0.45).

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 27°C | Yes | 0.550 | 81% | +4.38 |
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |

## Cosechador en papel (cajas imposibles, todas las ciudades)

Operaciones: 3. **Neto liquidado: US$+0.00**. Pendientes: +US$15.25 si salen bien.
Nota: las operaciones de Ciudad del Cabo del 18-oct se hicieron con la regla vieja (sin confirmación) y su resolución está en disputa.

| Día | Ciudad | Caja | Precio Yes | Acciones | Resultado |
|---|---|---|---|---|---|
| 2026-10-18 | cape-town | 17°C | 0.04 | 100 | pendiente |
| 2026-10-18 | cape-town | 16°C | 0.03 | 100 | pendiente |
| 2026-10-21 | istanbul | 15°C or below | 0.09 | 100 | pendiente |

## Pronóstico vs. mercado (todas las ciudades, día anterior)

Todavía no hay días liquidados.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 0 | 0 | US$+0.00 | 380 |
| maker | no | 0 | 0 | US$+0.00 | 1493 |
| cola_taker | no | 0 | 0 | US$+0.00 | 249 |
| cola_maker | no | 0 | 0 | US$+0.00 | 302 |

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Todavía no hay días liquidados.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 0 | 0 | US$+0.00 | 200 |
| maker | no | 0 | 0 | US$+0.00 | 663 |
| cola_taker | no | 0 | 0 | US$+0.00 | 81 |
| cola_maker | no | 0 | 0 | US$+0.00 | 183 |
| no80_90 | no | 0 | 0 | US$+0.00 | 70 |

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 28 (10 liquidadas, 4 ganadas). **Neto US$+16.26** sobre US$23.04 invertidos (ROI +70.6 %).
Brier en 42 strikes: modelo 0.3539 vs mercado 0.3621.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 1 | US$-2.08 |
| BTC | rango | 1 | US$+6.69 |
| BTC | toca | 3 | US$+1.43 |
| ETH | above | 1 | US$-1.15 |
| ETH | rango | 2 | US$+6.98 |
| ETH | toca | 2 | US$+4.39 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 106 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 0 acciones llenadas, neto **US$+0.00** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 0 acciones llenadas, neto **US$+0.00** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 0 acciones llenadas, neto **US$+0.00** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 4 operaciones; como maker se habrían llenado 2, neto **US$-7.76** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$38/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$49/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


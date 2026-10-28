# Resumen polymarket-clima

_Actualizado: 2026-10-28 04:51 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, aparece el 2026-10-26 20:44 UTC): `what-intensity-will-arnab-reach` y 1 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura máxima** (reglamento, ya no aparece el 2026-10-27 00:47 UTC): `To toggle between Fahrenheit and Celsius, click the "Switch to Metric Units" button until the relevant table displays °C.` y 7 más. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (fuente de resolución, ya no aparece el 2026-10-28 00:43 UTC): `weather.gov/wrh/timeseries`. Ver [reglas_informe.md](reglas_informe.md).
🔔 Polymarket cambió algo en **temperatura mínima** (reglamento, ya no aparece el 2026-10-27 00:47 UTC): `To toggle between Fahrenheit and Celsius, click the "Switch to Metric Units" button until the relevant table displays °C.` y 7 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-10-28T04:51:52
- Monitor: mañana 2026-10-27, noche 2026-10-27
- Prueba São Paulo: último día registrado 2026-10-27
- Cosechador: último ciclo 2026-10-28 01:58 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 13/26, la del **modelo** 9/26.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-10-26 | Sao Paulo | 18°C | 19°C (38%) ❌ | 18°C (24%) ✅ |
| 2026-10-26 | Buenos Aires | 18°C | 18°C (42%) ✅ | 19°C (23%) ❌ |
| 2026-10-25 | Sao Paulo | 21°C | 23°C (32%) ❌ | 23°C (31%) ❌ |
| 2026-10-25 | Buenos Aires | 16°C | 16°C (44%) ✅ | 17°C (25%) ❌ |
| 2026-10-24 | Sao Paulo | 26°C | 26°C (30%) ✅ | 29°C or higher (27%) ❌ |
| 2026-10-24 | Buenos Aires | 18°C | 18°C (40%) ✅ | 18°C (25%) ✅ |
| 2026-10-23 | Sao Paulo | 23°C | 23°C (23%) ✅ | 24°C (21%) ❌ |
| 2026-10-23 | Buenos Aires | 24°C | 23°C (39%) ❌ | 25°C or higher (26%) ❌ |
| 2026-10-22 | Sao Paulo | 24°C | 23°C (35%) ❌ | 24°C (20%) ✅ |
| 2026-10-22 | Buenos Aires | 23°C | 21°C (31%) ❌ | 20°C (23%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 14 (desde 2026-10-14).
Operaciones: 11 (2 ganadas, 7 perdidas, 2 pendientes). **Neto con comisiones: US$-8.03** (bruto -7.58, comisiones −0.45). _Con la comisión vieja (0,05 para todo) sería US$-8.27._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-15 | 28°C | No | 0.614 | 16% | +3.74 |
| 2026-10-17 | 20°C or below | Yes | 0.288 | 60% | -2.98 |
| 2026-10-17 | 22°C | No | 0.720 | 3% | -7.30 |
| 2026-10-24 | 26°C | No | 0.229 | 58% | -2.29 |
| 2026-10-24 | 27°C | Yes | 0.178 | 37% | -1.78 |
| 2026-10-25 | 21°C | No | 0.060 | 57% | -0.60 |
| 2026-10-25 | 22°C | Yes | 0.057 | 37% | -0.57 |
| 2026-10-26 | 19°C | Yes | 0.062 | 16% | -0.62 |
| 2026-10-27 | 21°C | No | 0.040 | 82% | pendiente |
| 2026-10-27 | 22°C | Yes | 0.039 | 16% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 1863 cajas liquidadas: **modelo 0.0902** vs **mercado 0.0748**.

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 741 | 311 | US$-207.25 | 681 |
| maker | no | 2831 | 337 | US$-646.74 | 2858 |
| cola_taker | no | 469 | 16 | US$+2.13 | 456 |
| cola_maker | no | 513 | 12 | US$-33.75 | 466 |

Taker en total: US$-205.12. _Con la comisión vieja (0,05 para todo) sería US$-228.66._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 1731 cajas liquidadas: **modelo 0.0780** vs **mercado 0.0663**.
Series donde el modelo le gana al mercado (≥5 días): máx buenos-aires (6 días), máx chicago (6 días), máx san-francisco (6 días), máx seattle (6 días), mín austin (5 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 468 | 119 | US$-186.10 | 216 |
| maker | no | 1485 | 171 | US$-155.34 | 682 |
| cola_taker | no | 200 | 6 | US$-13.45 | 117 |
| cola_maker | no | 462 | 11 | US$-20.03 | 254 |
| no80_90 | no | 184 | 138 | US$-203.54 | 77 |

Taker en total: US$-403.09. _Con la comisión vieja (0,05 para todo) sería US$-427.37._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 136 (127 liquidadas, 41 ganadas). **Neto US$+92.84** sobre US$305.99 invertidos (ROI +30.3 %). _Con la comisión vieja (0,05 para todo) sería US$+95.11._
Brier en 518 strikes: modelo 0.1506 vs mercado 0.1527.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 13 | US$+26.60 |
| BTC | rango | 28 | US$+66.49 |
| BTC | toca | 40 | US$+0.27 |
| ETH | above | 8 | US$-8.46 |
| ETH | rango | 19 | US$+12.58 |
| ETH | toca | 19 | US$-4.65 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 2776 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 9 operaciones; como maker se habrían llenado 7, neto **US$-10.74** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$37/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$47/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


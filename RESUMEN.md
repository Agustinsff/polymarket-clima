# Resumen polymarket-clima

_Actualizado: 2026-11-10 02:18 (Montevideo). Todo es **en papel**: no se usa plata real._

## Estado de las tareas

⚠️ El cosechador no actualiza desde 2026-11-04 16:12 UTC.
🔔 Polymarket cambió algo en **clima (otros)** (mercado de clima nuevo, ya no aparece el 2026-11-09 12:05 UTC): `what-intensity-will` y 1 más. Ver [reglas_informe.md](reglas_informe.md).

- Última foto de liquidez: 2026-11-10T02:18:43
- Monitor: mañana 2026-11-09, noche 2026-11-09
- Prueba São Paulo: último día registrado 2026-11-09
- Cosechador: último ciclo 2026-11-04 16:12 UTC, 88 mercados, 46 estaciones

## Temperatura máxima: mercado vs. modelo (BA y SP)

Acumulado: la caja favorita del **mercado** acertó 21/52, la del **modelo** 12/52.

| Día | Ciudad | Ganó | Favorita del mercado | Favorita del modelo |
|---|---|---|---|---|
| 2026-11-08 | Sao Paulo | 21°C | 20°C (36%) ❌ | 22°C (23%) ❌ |
| 2026-11-08 | Buenos Aires | 23°C | 22°C (42%) ❌ | 23°C (25%) ✅ |
| 2026-11-07 | Sao Paulo | 32°C | 32°C (32%) ✅ | 31°C (19%) ❌ |
| 2026-11-07 | Buenos Aires | 17°C | 19°C (42%) ❌ | 19°C (23%) ❌ |
| 2026-11-06 | Sao Paulo | 28°C | 26°C (28%) ❌ | 25°C (23%) ❌ |
| 2026-11-06 | Buenos Aires | 25°C | 26°C (41%) ❌ | 26°C (24%) ❌ |
| 2026-11-05 | Sao Paulo | 26°C | 27°C (22%) ❌ | 29°C (17%) ❌ |
| 2026-11-05 | Buenos Aires | 27°C | 27°C (52%) ✅ | 26°C (25%) ❌ |
| 2026-11-04 | Sao Paulo | 33°C | 32°C (42%) ❌ | 32°C (22%) ❌ |
| 2026-11-04 | Buenos Aires | 26°C | 25°C (46%) ❌ | 25°C (25%) ❌ |

## Prueba en papel São Paulo 14 hs (regla fija)

Días registrados: 27 (desde 2026-10-14).
Operaciones: 21 (2 ganadas, 17 perdidas, 2 pendientes). **Neto con comisiones: US$-15.99** (bruto -15.33, comisiones −0.66). _Con la comisión vieja (0,05 para todo) sería US$-16.37._

| Día | Caja | Lado | Precio | Modelo | Resultado |
|---|---|---|---|---|---|
| 2026-10-28 | 21°C | No | 0.110 | 58% | -1.10 |
| 2026-10-28 | 22°C | Yes | 0.100 | 37% | -1.00 |
| 2026-11-02 | 24°C | No | 0.165 | 59% | -1.72 |
| 2026-11-02 | 25°C | Yes | 0.160 | 38% | -1.67 |
| 2026-11-05 | 26°C | No | 0.039 | 52% | -0.41 |
| 2026-11-05 | 27°C | Yes | 0.040 | 41% | -0.42 |
| 2026-11-06 | 28°C | No | 0.040 | 69% | -0.42 |
| 2026-11-06 | 29°C or higher | Yes | 0.042 | 31% | -0.44 |
| 2026-11-09 | 17°C | No | 0.020 | 81% | pendiente |
| 2026-11-09 | 18°C | Yes | 0.023 | 16% | pendiente |

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

Puntaje Brier (más bajo = mejor) en 8248 cajas liquidadas: **modelo 0.0878** vs **mercado 0.0724**.
Series donde el modelo le gana al mercado (≥5 días): mín dallas (5 días), mín karachi (13 días), mín chengdu (6 días), mín mexico-city (6 días), mín chicago (7 días), máx dallas (17 días), máx buenos-aires (17 días), máx atlanta (17 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | sí | 1555 | 592 | US$-738.86 | 583 |
| taker | no | 1830 | 735 | US$-566.68 | 0 |
| maker | sí | 441 | 52 | US$-175.56 | 9516 |
| maker | no | 7591 | 856 | US$-1577.04 | 110 |
| cola_taker | sí | 819 | 17 | US$-124.95 | 285 |
| cola_taker | no | 1195 | 37 | US$-24.20 | 0 |
| cola_maker | sí | 83 | 2 | US$-8.88 | 1904 |
| cola_maker | no | 1299 | 32 | US$-78.78 | 19 |

Taker en total: US$-1454.69. _Con la comisión vieja (0,05 para todo) sería US$-1627.24._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Pronóstico del mismo día (12 y 15 hs locales la máxima, 9 hs la mínima)

Puntaje Brier (más bajo = mejor) en 5188 cajas liquidadas: **modelo 0.0932** vs **mercado 0.0735**.
Series donde el modelo le gana al mercado (≥5 días): mín denver (9 días), máx buenos-aires (19 días), mín cape-town (5 días), máx atlanta (19 días), mín sao-paulo (11 días), mín ankara (8 días), mín munich (9 días), mín seattle (11 días), mín houston (10 días), mín mexico-city (13 días), mín chongqing (12 días), mín guangzhou (11 días), mín austin (14 días), mín dallas (7 días), mín shenzhen (10 días), mín moscow (8 días), mín karachi (6 días), mín san-francisco (10 días), mín wuhan (9 días), mín busan (6 días), mín istanbul (11 días), mín buenos-aires (5 días), mín toronto (6 días).

| Modo | Serie calibrada | Liquidadas | Ganadas | Neto (10 acc. c/u) | Pendientes |
|---|---|---|---|---|---|
| taker | no | 1657 | 380 | US$-900.73 | 185 |
| maker | no | 3169 | 382 | US$-397.61 | 2692 |
| cola_taker | no | 816 | 19 | US$-111.91 | 96 |
| cola_maker | no | 1074 | 21 | US$-76.63 | 889 |
| no80_90 | no | 654 | 459 | US$-1060.07 | 104 |

Taker en total: US$-2072.72. _Con la comisión vieja (0,05 para todo) sería US$-2161.81._

_Taker = compra al instante pagando comisión. Maker = orden en el libro, solo cuenta si alguien la habría tomado (sin comisión). Cola = cajas de ≤10 ¢ a las que el modelo les da ≥2,5 veces el precio. no80_90 = comprar el No de cajas todavía posibles que cotizan 10–20 ¢ (solo en el pronóstico del mismo día)._

## Cripto en papel (Bitcoin / Ethereum: above, rango y toca; modelo de opciones)

Operaciones: 450 (443 liquidadas, 166 ganadas). **Neto US$+40.93** sobre US$1576.96 invertidos (ROI +2.6 %). _Con la comisión vieja (0,05 para todo) sería US$+52.04._
Brier en 1600 strikes: modelo 0.1384 vs mercado 0.1345.

| Activo | Tipo | Liquidadas | Neto |
|---|---|---|---|
| BTC | above | 57 | US$+35.30 |
| BTC | rango | 93 | US$+28.22 |
| BTC | toca | 117 | US$-56.49 |
| ETH | above | 37 | US$-9.37 |
| ETH | rango | 66 | US$-5.68 |
| ETH | toca | 73 | US$+48.95 |

_Regla fija: comprar el lado que el modelo ve ≥5 puntos más barato, a 48/24/12/6/3/1 h del cierre (18/12/6/3/1 h en 'toca'), 10 acciones al precio real del libro, con comisión. Backtest may-oct: +6,7 % con 1 ¢ de deslizamiento (Ethereum +17 %, Bitcoin ~0 %)._

## Sombra maker (¿y si dejábamos la orden en vez de comprar al toque?)

Cosechador: 4957 cajas muertas ya liquidadas.
- Vender el Yes a 2 ¢: 1964 acciones llenadas, neto **US$+39.29** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 3 ¢: 1290 acciones llenadas, neto **US$+38.72** (0 cajas 'muertas' que terminaron ganando)
- Vender el Yes a 5 ¢: 805 acciones llenadas, neto **US$+40.26** (0 cajas 'muertas' que terminaron ganando)
Prueba SP: 13 operaciones; como maker se habrían llenado 11, neto **US$-12.35** (sin comisión).

## Recompensas de liquidez (estimación, últimas 24 h)

- Buenos Aires: ~US$34/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').
- Sao Paulo: ~US$39/día con 100 acciones a 1 ¢ en todas las cajas del mercado de mañana (sin contar pérdidas por quedar 'tomado').


# Efecto de la comisión nueva en temperatura (corte 2026-11-04 13:41 UTC)

Regla fija: `comision/REGLA.md`. Datos: medidor maker (fotos cada 5 min, llenados simulados). La comisión se prendió para todas las cajas abiertas a la vez, el 1-nov-2026 a las 04:37 UTC (última foto con tasa 0: 04:35Z; primera con 0,05: 04:40Z). Sin comisión = fotos antes de esa hora; con = después. Fechas de evento: 7 sin y 6 con (los eventos del 31-oct al 2-nov tienen fotos en los dos lados; los últimos todavía sin cerrar). Cajas-foto: 841,825 sin / 494,932 con. Chequeo: en 0.0 % de las cajas-foto la tasa no coincide con la fecha del evento.

Diferencias = con comisión − sin comisión, emparejadas por ciudad y tipo; entre corchetes el intervalo del 95 % (bootstrap por fecha de evento). Spread, competencia y pozo: valor de cada fecha (mediana de sus cajas-foto), promediado por ciudad.

## 1. Spread del libro (¢, mediana por caja-foto)

| tipo | tramo | sin | con | diferencia por ciudad |
|---|---|---|---|---|
| máximas | 0-12 h | 3.0 | 3.4 | +0.73 [+0.20, +1.39] |
| máximas | 12-24 h | 3.0 | 3.0 | -0.11 [-0.33, +0.11] |
| máximas | 24-36 h | 3.0 | 3.0 | +0.23 [-0.14, +0.63] |
| máximas | 36-48 h | 4.0 | 5.0 | +3.69 [+0.82, +6.88] |
| mínimas | 0-12 h | 66.0 | 65.0 | +0.96 [-6.96, +7.95] |
| mínimas | 12-24 h | 23.0 | 37.0 | -1.04 [-11.71, +5.21] |
| mínimas | 24-36 h | 12.0 | 28.0 | +1.36 [-0.97, +3.86] |
| mínimas | 36-48 h | 32.0 | 40.0 | +2.84 [-3.11, +9.85] |

Control cripto (comisión igual todo el período): spread mediano 2.0 ¢ antes del 1-nov 04:37Z y 2.0 ¢ después (diferencia -0.0 ¢).

Cajas apretadas (spread ≤ 5 ¢), proporción de cajas-foto:

- máximas: sin 85 %, con 77 %.
- mínimas: sin 15 %, con 10 %.

## 2. Competencia y pozo (máximas, 12–48 h)

- Puntaje de rivales en la zona de recompensa (mediana): sin 64, con 42; diferencia por ciudad -29.58 [-50.23, -10.80].
- Pozo por caja (US$/día): sin 24.3, con 23.0; diferencia por ciudad -2.34 [-4.67, -0.29]. Cajas con pozo: sin 87 %, con 86 %.
- Pozo total por fecha de evento (promedio por foto, todas las cajas vivas):

| fecha | comisión | pozo US$/día |
|---|---|---|
| 27-Oct | no | 4,933 |
| 28-Oct | no | 5,281 |
| 29-Oct | no | 5,258 |
| 30-Oct | no | 4,957 |
| 31-Oct | no | 5,004 |
| 01-Nov | no | 5,172 |
| 01-Nov | sí | 3,942 |
| 02-Nov | no | 4,945 |
| 02-Nov | sí | 5,172 |
| 03-Nov | sí | 5,088 |
| 04-Nov | sí | 5,107 |
| 05-Nov | sí | 4,832 |
| 06-Nov | sí | 3,630 |

## 3. Llenados de la orden simulada (máximas y mínimas, todos los tramos)

| orden | grupo | acciones llenadas por caja-día | resultado a la resolución ¢/acción | reembolso ¢/acción | neto ¢/acción | acciones resueltas |
|---|---|---|---|---|---|---|
| 1 ¢ | sin | 240.2 | -3.87 | 0.00 | -3.87 | 702,023 |
| 1 ¢ | con | 111.7 | -2.60 | 0.20 | -2.40 | 180,559 |
| 2 ¢ | sin | 144.8 | -4.15 | 0.00 | -4.15 | 423,371 |
| 2 ¢ | con | 70.5 | -3.31 | 0.20 | -3.12 | 112,755 |

Diferencia del resultado por acción (orden a 1 ¢): +1.27 [-0.41, +3.72] ¢.

## 4. Neto maker por US$ 100 de capital y día (cajas con spread ≤ 5 ¢, orden a 2 ¢, recompensa pesimista)

| grupo | recompensa | acciones llenadas | resultado llenados | reembolso | neto |
|---|---|---|---|---|---|
| sin comisión | 4.13 | 120.3 | -2.77 | 0.00 | +1.36 |
| con comisión | 4.37 | 68.2 | -1.96 | 0.13 | +2.55 |

Diferencia del neto (con − sin): +1.19 [-1.11, +3.18] US$/día por US$ 100. Las fechas con comisión más recientes todavía no resolvieron, así que el resultado de sus llenados sale de las que sí cerraron.

Límites: pocos días con comisión y sin repetir, la recompensa estimada es optimista (fotos cada 5 min), y los llenados son simulados. Ver `comision/REGLA.md`.

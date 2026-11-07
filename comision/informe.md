# Efecto de la comisión nueva en temperatura (corte 2026-11-07 21:24 UTC)

Regla fija: `comision/REGLA.md`. Datos: medidor maker (fotos cada 5 min, llenados simulados). La comisión se prendió para todas las cajas abiertas a la vez, el 1-nov-2026 a las 04:37 UTC (última foto con tasa 0: 04:35Z; primera con 0,05: 04:40Z). Sin comisión = fotos antes de esa hora; con = después. Fechas de evento: 7 sin y 9 con (los eventos del 31-oct al 2-nov tienen fotos en los dos lados; los últimos todavía sin cerrar). Cajas-foto: 841,825 sin / 839,978 con. Chequeo: en 0.0 % de las cajas-foto la tasa no coincide con la fecha del evento.

Diferencias = con comisión − sin comisión, emparejadas por ciudad y tipo; entre corchetes el intervalo del 95 % (bootstrap por fecha de evento). Spread, competencia y pozo: valor de cada fecha (mediana de sus cajas-foto), promediado por ciudad.

## 1. Spread del libro (¢, mediana por caja-foto)

| tipo | tramo | sin | con | diferencia por ciudad |
|---|---|---|---|---|
| máximas | 0-12 h | 3.0 | 3.4 | +0.74 [+0.35, +1.16] |
| máximas | 12-24 h | 3.0 | 3.0 | -0.08 [-0.28, +0.15] |
| máximas | 24-36 h | 3.0 | 3.0 | +0.29 [-0.02, +0.58] |
| máximas | 36-48 h | 4.0 | 5.0 | +2.68 [+1.44, +3.77] |
| mínimas | 0-12 h | 66.0 | 60.0 | -3.02 [-11.11, +4.79] |
| mínimas | 12-24 h | 23.0 | 31.0 | -2.73 [-11.67, +2.65] |
| mínimas | 24-36 h | 12.0 | 25.0 | -1.76 [-6.02, +2.24] |
| mínimas | 36-48 h | 32.0 | 36.0 | -1.18 [-5.53, +3.39] |

Control cripto (comisión igual todo el período): spread mediano 2.0 ¢ antes del 1-nov 04:37Z y 2.0 ¢ después (diferencia -0.0 ¢).

Cajas apretadas (spread ≤ 5 ¢), proporción de cajas-foto:

- máximas: sin 85 %, con 77 %.
- mínimas: sin 15 %, con 10 %.

## 2. Competencia y pozo (máximas, 12–48 h)

- Puntaje de rivales en la zona de recompensa (mediana): sin 64, con 38; diferencia por ciudad -31.04 [-45.03, -16.33].
- Pozo por caja (US$/día): sin 24.3, con 22.7; diferencia por ciudad -2.25 [-3.87, -0.82]. Cajas con pozo: sin 87 %, con 86 %.
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
| 05-Nov | sí | 5,063 |
| 06-Nov | sí | 5,171 |
| 07-Nov | sí | 5,086 |
| 08-Nov | sí | 5,153 |
| 09-Nov | sí | 3,875 |

## 3. Llenados de la orden simulada (máximas y mínimas, todos los tramos)

Ojo: el medidor no registró llenados del 2-nov 22:25Z al 7-nov 23:20Z (Polymarket retiró la API vieja de operaciones). Esas fotos se sacan de la exposición. Llenados con comisión: del 1-nov 04:37Z en adelante fuera del hueco (01-Nov 04:40 a 02-Nov 22:20 UTC, 313,235 acciones).

| orden | grupo | acciones llenadas por caja-día | resultado a la resolución ¢/acción | reembolso ¢/acción | neto ¢/acción | acciones resueltas |
|---|---|---|---|---|---|---|
| 1 ¢ | sin | 240.2 | -3.87 | 0.00 | -3.87 | 702,023 |
| 1 ¢ | con | 189.1 | -2.69 | 0.20 | -2.49 | 192,003 |
| 2 ¢ | sin | 144.8 | -4.15 | 0.00 | -4.15 | 423,371 |
| 2 ¢ | con | 119.4 | -3.51 | 0.20 | -3.31 | 121,232 |

Diferencia del resultado por acción (orden a 1 ¢): +1.18 [-0.52, +3.18] ¢.

## 4. Neto maker por US$ 100 de capital y día (cajas con spread ≤ 5 ¢, orden a 2 ¢, recompensa pesimista)

| grupo | recompensa | acciones llenadas | resultado llenados | reembolso | neto |
|---|---|---|---|---|---|
| sin comisión | 4.13 | 120.3 | -2.77 | 0.00 | +1.36 |
| con comisión | 4.41 | 113.7 | -3.37 | 0.22 | +1.26 |

Diferencia del neto (con − sin): -0.10 [-2.21, +2.07] US$/día por US$ 100. Las fechas con comisión más recientes todavía no resolvieron, así que el resultado de sus llenados sale de las que sí cerraron.

Límites: pocos días con comisión y sin repetir, la recompensa estimada es optimista (fotos cada 5 min), y los llenados son simulados. Ver `comision/REGLA.md`.

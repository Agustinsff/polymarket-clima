# Pronóstico propio como filtro maker (corte 2026-11-08 14:07 UTC)

Regla fija: `propio_maker/REGLA.md`. Llenados simulados resueltos sobre cajas con probabilidad del modelo (prueba B, día anterior), posteriores a esa probabilidad y fuera del hueco 2-nov 22:25Z → 7-nov 23:20Z: 84,540 llenados, 1,629,085 acciones, 11 fechas de evento, 56 series.

| orden | grupo | llenados | acciones | resultado ¢/acción (con reembolso) | intervalo 95 % |
|---|---|---|---|---|---|
| 1 ¢ | de acuerdo | 27,924 | 530,028 | -3.74 | [-5.67, -2.24] |
| 1 ¢ | en desacuerdo | 24,252 | 470,701 | -3.68 | [-5.22, -2.08] |
| 1 ¢ | todas | 52,176 | 1,000,729 | -3.71 | [-4.44, -3.02] |
| 2 ¢ | de acuerdo | 17,883 | 348,739 | -4.21 | [-5.82, -2.62] |
| 2 ¢ | en desacuerdo | 14,481 | 279,617 | -4.26 | [-6.34, -2.05] |
| 2 ¢ | todas | 32,364 | 628,356 | -4.23 | [-4.66, -3.72] |

- Orden a 1 ¢: de acuerdo − todas = -0.03 ¢/acción [-1.56, +1.26]; de acuerdo − en desacuerdo = -0.06 ¢, P(≤0) = 0.466.
- Orden a 2 ¢: de acuerdo − todas = +0.02 ¢/acción [-1.60, +1.59]; de acuerdo − en desacuerdo = +0.05 ¢, P(≤0) = 0.499.

**Veredicto según la regla: NO SIRVE como filtro** (pide, a 2 ¢, ≥ +1 ¢ sobre todas y P < 5 % contra en desacuerdo).

Límites: llenados simulados (cuenta prudente del medidor), una sola foto del modelo por caja (día anterior), y pocas fechas de evento.

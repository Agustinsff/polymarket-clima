# ¿El precio absorbe tarde las corridas de GFS/ECMWF? Resultados

Generado 2026-10-26 00:21Z con la regla fija de `REGLA.md`. 1140 eventos con precio por minuto (2026-10-09 a 2026-10-23), 77 corridas por modelo, 4572 señales (modelo × corrida × evento) que pasan los filtros.

## Hora en que cada corrida aparece en AWS (mediana, horas después de la hora de la corrida)

| modelo | corrida | h hasta el último paso |
|---|---|---|
| gfs | 00Z | 4.25 |
| gfs | 06Z | 4.18 |
| gfs | 12Z | 4.21 |
| gfs | 18Z | 4.22 |
| ecmwf | 00Z | 7.57 |
| ecmwf | 06Z | 6.45 |
| ecmwf | 12Z | 7.57 |
| ecmwf | 18Z | 6.45 |

## Prueba A: ¿el precio se mueve tarde hacia donde fue la corrida?

E = media del mercado en anchos de caja. Pendiente β de ΔE sobre Δb (cambio del pronóstico entre corridas, en anchos de caja); t = β / error estándar agrupado por evento. β = 1 sería que el mercado copia el cambio entero.

| modelo | tramo | señales | β | t |
|---|---|---|---|---|
| gfs | antes de W (desde corrida+3 h) | 2197 | -0.000 | -0.1 |
| gfs | W → W+1 h | 2197 | +0.014 | +4.5 |
| gfs | W → W+3 h | 2197 | +0.039 | +5.6 |
| gfs | W → W+6 h | 2197 | +0.059 | +5.4 |
| ecmwf | antes de W (desde corrida+3 h) | 2344 | +0.017 | +2.0 |
| ecmwf | W → W+1 h | 2375 | +0.014 | +3.8 |
| ecmwf | W → W+3 h | 2375 | +0.044 | +6.9 |
| ecmwf | W → W+6 h | 2375 | +0.067 | +7.3 |
| ambos | antes de W (desde corrida+3 h) | 4541 | +0.007 | +1.5 |
| ambos | W → W+1 h | 4572 | +0.014 | +5.8 |
| ambos | W → W+3 h | 4572 | +0.041 | +8.7 |
| ambos | W → W+6 h | 4572 | +0.062 | +9.0 |

Δb típico: mediana |Δb| = 0.25; |Δb| ≥ 0,5 en 27% de las señales.

| tipo | señales | β antes de W | β W → W+3 h |
|---|---|---|---|
| highest | 4530 | +0.006 (t +1.4) | +0.041 (t +8.6) |
| lowest | 42 | +0.143 (t +1.1) | +0.211 (t +3.5) |

## Prueba B: comprar la caja vecina hacia donde fue la corrida

| salida | modelo | operaciones | ganancia media | t | 1ª mitad | 2ª mitad |
|---|---|---|---|---|---|---|
| 1 h | ambos | 1193 | -7.5% | -16.0 | -8.4% | -6.5% |
| 1 h | gfs | 544 | -7.5% | -10.2 | -9.2% | -5.6% |
| 1 h | ecmwf | 649 | -7.5% | -13.0 | -7.7% | -7.3% |
| 3 h | ambos | 1193 | -4.0% | -6.0 | -4.1% | -3.8% |
| 3 h | gfs | 544 | -4.5% | -4.5 | -5.2% | -3.7% |
| 3 h | ecmwf | 649 | -3.5% | -4.0 | -3.1% | -3.9% |
| 6 h | ambos | 1193 | -0.8% | -0.9 | -0.4% | -1.3% |
| 6 h | gfs | 544 | -1.6% | -1.2 | -2.3% | -0.8% |
| 6 h | ecmwf | 649 | -0.2% | -0.1 | +1.2% | -1.8% |

Precio de compra con operaciones reales en la ventana: 15%; de venta a 3 h: 27% (el resto, precio ± 1 ¢). Compra media 24.1 ¢ vs precio en W 23.0 ¢.

La misma prueba sin costos (precio en W contra precio a W+3 h): +7.5% (t +10.1, 1193 ops).

## Criterio de éxito

1. Prueba A, β a 3 h > 0 con t ≥ 3: **sí** (β +0.041, t +8.7).
2. Prueba B a 3 h ≥ +2 %, t ≥ 2, ≥ 150 ops, + en las dos mitades: **no** (-4.0%, t -6.0, 1193 ops, mitades -4.1% / -3.8%).


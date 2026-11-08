# Pronóstico propio: validación contra el mercado (paso 3)

Generado 2026-11-08 14:05 UTC con las reglas de REGLAS.md (fijadas el 3-nov-2026) y el método M1 (elegido en resultados_modelo.md). Precio del mercado = punto medio normalizado de la foto; real = METAR de rutina con el redondeo de Polymarket.

## Prueba A: máximas, mismo día a las 9 h local (horizonte 1)

Sin eventos.

## Prueba B: máximas y mínimas, día anterior (horizonte 2)

Días: 16 (2026-10-22 a 2026-11-07); eventos: 810.

| Medida | Modelo | Mercado |
|---|---|---|
| Brier medio (menor es mejor) | 0.7309 | 0.6344 |

- Mejora del modelo sobre el mercado: **-15.2 %** (regla: ≥ +3 %).
- Probabilidad de que el modelo no sea mejor (bootstrap por días): **100.0 %** (regla: < 2,5 %).
- Compras como taker (borde ≥ 3 ¢, ask real, comisión 0,05·p·(1−p)): 1790 compras, ganan 113, costo US$ 135.76, resultado US$ -22.76, **ROI -16.8 %** (regla: > 0).

- Solo máximas: 734 eventos, modelo 0.7378 vs mercado 0.6372 (-15.8 %).
- Solo mínimas: 76 eventos, modelo 0.6638 vs mercado 0.6068 (-9.4 %).
- Eventos descartados: libro incompleto (medios no suman ~1) 594, sin pronostico propio o sin dato real 208.

**Prueba B: NO PASA.**

La prueba A no se pudo hacer: `hoy.csv` guarda las máximas a las 12 y 15 h local y las mínimas a las 9 h, no hay foto de máximas a las 9 h. Fue un error al escribir REGLAS.md.

## Informativo (no decide)

Variantes más generosas con el modelo, para medir la distancia:

- B con horizonte 1 (puede usar corridas que a esa hora quizás no existían): 810 eventos, modelo 0.6968 vs mercado 0.6344 (-9.8 %).
- B con la primera foto del día anterior, horizonte 2: 761 eventos, modelo 0.7358 vs mercado 0.6519 (-12.9 %).
- Máximas a las 12 h local del mismo día, horizonte 1: 747 eventos, modelo 0.6965 vs mercado 0.4881 (-42.7 %).

## Veredicto

**NO PASA**: según la regla, se cierra acá sin prueba en papel.

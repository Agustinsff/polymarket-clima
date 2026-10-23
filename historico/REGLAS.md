# Backtest: promedio de 11 modelos contra precios históricos de Polymarket

Reglas fijadas el 23-oct-2026, **antes de bajar ningún precio**. No se cambian después de ver resultados;
si algo se agrega después, va marcado como "agregado después".

## Datos
- Pronósticos: `modelos/dias.csv.gz` (24-ago a 22-oct-2026, 86 series). Se usan dos:
  - **Promedio**: promedio de los 11 modelos, con el sesgo de cada serie corregido (columna `corr`).
  - **GFS+ECMWF**: la misma cuenta con solo GFS y ECMWF (lo más parecido a la base del bot).
  - El sesgo ya está medido solo con días anteriores a la emisión del pronóstico (no ve el futuro).
- Precios: `clob.polymarket.com/prices-history` de cada caja (Yes), el último punto en las 6 h previas al momento de decisión.
- Resultado: la caja que Polymarket dio por ganadora (gamma, mercado cerrado con precio 1). Días sin ganadora no entran.
- Comisión: 0 (clima tiene zero_fees).

## Momento de decisión (para no usar pronósticos que todavía no existían)
Un pronóstico "a h días" de Open-Meteo para la hora 23 del día D sale de una corrida de hasta ~24·h horas antes,
que se publica unas 4-6 h después. Por eso se decide a las **06:00 hora local del día D − (h − 1)**:
- **h = 2 (principal)**: 06:00 local del día anterior. Máximas y mínimas.
- h = 3: 06:00 local de dos días antes (si ya había mercado).
- h = 1: 06:00 local del mismo día, **solo máximas** (a esa hora la mínima ya casi ocurrió).

## Probabilidad del modelo
- Temperatura ~ Normal(centro = pronóstico corregido, desvío σ). Caja = [lo − 0,5, hi + 0,5] en su unidad (°F en EE.UU.).
- σ de cada serie y horizonte = error cuadrático medio del pronóstico corregido en días con resultado conocido antes de
  la emisión, achicado hacia el de todas las series juntas: σ² = (n·σ_serie² + 10·σ_todas²) / (n + 10). Mínimo 0,5 °C.
- Hacen falta al menos 10 días previos con error en esa serie; si no, el día no entra.

## Precio de ejecución
El precio histórico no es el que se paga. El costo de comprar se mide con lo que anotó el bot del día anterior (`pronostico.csv`,
20 a 23-oct): para cada foto se compara el mejor ask y el mejor bid con el precio histórico de ese momento.
Por tramo de precio (0-10, 10-30, 30-70, 70-90, 90-100 ¢) se usa la **mediana** de (ask − histórico) para comprar Yes y
de (histórico − bid) para comprar No. Además se informa con un costo fijo de 0, 1, 2 y 3 ¢ sobre el histórico.

## Reglas de operación (las mismas que `pronostico.py`)
- Comprar Yes si p_modelo − costo ≥ 10 puntos; comprar No si (1 − p_modelo) − costo_No ≥ 10 puntos.
- Solo si el costo está entre 3 y 90 ¢. 10 acciones por operación. Sin tope por día.
- Secundario: umbral de 5 puntos.

## Medidas
1. Brier y log-score por caja: mercado (precio histórico) vs Promedio vs GFS+ECMWF.
2. λ ("cuánto creerle al modelo"): p = precio + λ·(p_modelo − precio), λ por máxima verosimilitud, con intervalo 95 %.
3. Simulación de operaciones: n, ganancia, ROI = ganancia / plata puesta, y P(ROI < 0) remuestreando **días** (2000 veces).
4. Cortes: por horizonte, máximas/mínimas, primera y segunda mitad de las fechas.

## Criterio de "hay ventaja" (decidido antes)
Para el Promedio a h = 2 con el costo medido: ROI > 0 con P(ROI < 0) < 5 %, **y** λ con intervalo que no incluye 0,
**y** ROI positivo en las dos mitades de las fechas. Si falta cualquiera de las tres: no hay ventaja demostrada.

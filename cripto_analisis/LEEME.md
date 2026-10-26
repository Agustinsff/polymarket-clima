# Prueba cripto desarmada (26-oct-2026)

Regla del análisis: `REGLA.md` (fijada antes de desagregar). Script: `python cripto_analisis/analizar.py`
→ `resultados.md`. No cambia `cripto.py` ni la prueba en curso.

## Conclusión
- Con libro real: 80 ops liquidadas, **+US$ 78 sobre US$ 175** con comisión real; +US$ 70 con 1 ¢ extra.
  Los costos no son el problema (comisión real ≈ 0,1 ¢/acción en opciones baratas).
- **Es casi todo un día**: BTC del 24-oct dio +US$ 104 (BTC cerró debajo de 80.000 cuando el mercado
  daba 84–97 % a 80–82 k). Sin ese bloque, −US$ 26. Mediana por bloque (activo×día): +US$ 0,65.
- Solo hay 6 bloques independientes (3 días × 2 activos). Bootstrap por bloques: P(total ≤ 0) ≈ 0,27.
  Brier modelo vs mercado: modelo apenas mejor, P ≈ 0,27, también todo por BTC 24-oct.
- El patrón es "comprar colas baratas": 33 ops a <10 ¢ dieron +US$ 80 (10 ganadas), 10–30 ¢ −US$ 39.
  Es una apuesta a movimientos grandes: pierde chico seguido y gana grande de vez en cuando. No es una
  ganancia constante por naturaleza.
- El backtest may–oct decía lo contrario por activo (ETH +17 %, BTC ≈ 0); la prueba da BTC +, ETH −.
  Lo que coincide en los dos es que la ganancia viene de las opciones baratas.
- Para que una ventaja del tamaño del backtest (~7 %) se distinga del ruido harían falta ~100+ días;
  si fuera tan grande como lo medido (+45 %), ~26 días (≈52 bloques).

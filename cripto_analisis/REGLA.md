# Análisis de la prueba cripto en papel: regla fijada antes de mirar

Fijada el 26-oct-2026 ~14:25 UTC, **antes de desagregar los resultados** (solo se conocía el total del panel:
+US$ 82 en 73 ops con precio del libro real). No cambia la prueba en curso (`cripto.py` sigue igual).

## Qué ops
- Las de `cripto_ops.csv` desde `desde_libro` (23-oct 00:04 UTC), liquidadas según `cripto_estado.json`.
- Aparte, como referencia, las de antes (precio del 1er escalón) y el backtest may–oct descrito en `cripto.py`.

## Resultado por op
- Ganancia = acciones·(1−p) si gana, −acciones·p si pierde, menos comisión.
- Tres comisiones: (a) la anotada en la fila (lo que usa el panel), (b) la real de cripto 0,07·p·(1−p),
  (c) (b) + 1 ¢ extra de deslizamiento por acción como estrés.

## Cortes (todos se reportan, no se elige el mejor)
activo (BTC/ETH), tipo (above/rango/toca), horizonte (48/24/12/6/3/1 y 18 en toca), lado (Sí/No),
tramo de precio (<10 ¢, 10–30, 30–70, 70–90, >90), tamaño del borde (5–10, 10–20, >20 puntos), día de cierre.

## ¿Es suerte?
- Las ops **no son independientes**: el mismo día y activo comparten el movimiento del precio, y el mismo
  mercado se opera en varios horizontes. Unidad de remuestreo = **(activo, día de cierre)**.
- Bootstrap por bloques (10.000 remuestreos) del total y P(total ≤ 0). También t de Student sobre los bloques.
- Se informa cuántos bloques hacen falta para que una ventaja del tamaño medido dé P < 5 %.

## Qué cuenta como "positivo de verdad"
Total > 0 con comisión real (b) **y** P(≤0) < 5 % por bloques **y** que no lo explique un solo día.

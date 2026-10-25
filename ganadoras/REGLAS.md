# Qué hacen distinto las billeteras ganadoras: reglas fijadas ANTES de mirar resultados (25-oct-2026)

Pedido de Agus (25-oct): no copiar a las ganadoras (eso ya dio ≈0 %, `seguir/`), sino ver si su ventaja sale de
algo **observable sin saber quién apuesta** (momento, precio, tipo de caja) que se pueda convertir en una regla
mecánica. Estas reglas se suben antes de correr `ganadoras/analisis.py`. Si se cambia algo después, se anota abajo
con fecha y motivo y el resultado con las reglas originales se sigue mostrando.

## Datos y partición
Los 30 días de `rivales/datos/` (rama `investigacion-rivales`): operaciones taker de los mercados de temperatura
cerrados. Comisión 0 (tasa real de temperatura). Se parten por **fecha del evento**:
- **Descubrimiento**: la primera mitad de las fechas de evento (se mira todo lo que se quiera).
- **Prueba**: la segunda mitad. Se toca una sola vez, al final, con las reglas candidatas ya elegidas.

## Rasgos (lista cerrada)
Cada apuesta (compra de un lado a precio q; una venta cuenta como compra del otro lado a 1−q) se describe con:
- **momento**: horas respecto del inicio del día local de la ciudad: <−24, −24 a −12, −12 a −6, −6 a 0, 0 a 6, 6 a 12, 12 a 24.
- **precio** q: 5–15, 15–30, 30–50, 50–70, 70–90 ¢ (lo de <5 y >90 ¢ no entra).
- **tipo**: máxima / mínima.
- **lado**: Sí / No.
- **puesto**: puesto de la caja por precio del Sí dentro del evento en ese momento (último precio operado de cada caja):
  1ª (favorita), 2ª, 3ª, 4ª o más.
- **punta**: caja de punta ("or below" / "or higher") o del medio.
- **región**: América / Europa-África / Asia-Oceanía.

## Paso 1: describir (sólo descubrimiento)
- Ganadoras = criterio de `seguir/` (≥ 20 eventos, t ≥ 2,5, PnL/vol ≥ +3 %) calculado con el descubrimiento.
- Para cada rasgo: reparto del volumen de ganadoras vs el resto, y PnL/vol de ganadoras vs el resto en cada valor.
- **Descomposición**: PnL esperado de las ganadoras si en cada celda (momento × precio × lado) ganaran lo mismo que
  el promedio de todos los takers de esa celda. Lo que queda es "elección dentro de la celda" (información propia,
  que no se puede copiar con una regla).

## Paso 2: reglas candidatas (sólo descubrimiento)
Regla mecánica, sin mirar quién opera: en horarios fijos de decisión (−36, −24, −12, −6, 0, +6 y +12 h respecto del
inicio del día local), para cada caja de cada evento y cada lado, se mira el último precio operado de ese lado. Si cae en la
celda de la regla, se compra US$10. **Precio de entrada**: la primera operación real de cualquiera comprando ese lado
después del horario de decisión y dentro de 120 min, **+1 ¢** (igual que `seguir/`). Si no hay, no se compra.
Se queda hasta la resolución.

Celdas posibles: combinaciones de hasta 2 rasgos (momento de decisión cuenta como rasgo). Son candidatas las que en
descubrimiento tengan ≥ 150 eventos distintos, PnL/vol ≥ +3 % y t por evento ≥ 2. Se quedan como máximo las **5**
de mayor t, quitando las que repiten más de la mitad de las compras de una ya elegida.

## Paso 3: prueba (una vez)
Cada candidata se corre en la mitad de prueba con el mismo cálculo. Intervalo por bootstrap por evento.
**Pasa** una regla si en prueba: PnL/vol ≥ +3 % y el límite inferior del intervalo de 98 % (90 % corregido por 5
candidatas) es > 0, y además las dos mitades de la prueba (por fecha) dan positivo. Se informa también el resultado de
todas las candidatas aunque no pasen.

Si ninguna pasa, la conclusión es que la ventaja de las ganadoras es información propia (elección dentro de la celda),
no un patrón mecánico, y se recomienda cerrar la temperatura diaria.

## Cambios
(ninguno)

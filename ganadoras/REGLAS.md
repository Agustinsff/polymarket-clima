# Sacar la regla de las billeteras ganadoras (no copiarlas): reglas fijadas ANTES (25-oct-2026)

Idea: las billeteras que ganan constante en temperatura (`rivales/`) ganan +8 % a su propio precio, pero copiarlas
15 min tarde da ≈0 % (`seguir/`). Acá no se las copia: se mira **qué tipo de apuesta hacen** (horario, ciudad,
máxima/mínima, caja de punta o del medio, anticipación, precio) y se arma una regla mecánica que no necesita saber
qué hacen ellas. Esa regla se prueba en días que no se miraron.

Este archivo se sube **antes** de mirar nada de la mitad de prueba. La regla concreta se agrega abajo (sección
"Regla elegida") en un commit aparte, también antes de correr la prueba. Si después se cambia algo, se anota con fecha
y motivo, y el resultado con lo original se sigue mostrando.

## Datos
Los 30 días de `rivales/datos/` (rama `investigacion-rivales`): 2.790 eventos cerrados de temperatura, fechas
2026-09-23 a 2026-10-23, todas las operaciones taker. Comisión real de temperatura: **0** (tasa que trae gamma,
la que anotan hoy.py y pronostico.py desde el 23-oct). Igual se muestra el resultado con la tasa vieja 0,05·p·(1−p).

## Mitades (por fecha del evento)
- **Diseño**: eventos con fecha 2026-09-23 a 2026-10-07 (15 fechas). Sólo esto se mira para elegir la regla.
- **Prueba**: eventos con fecha 2026-10-08 a 2026-10-23 (16 fechas). No se mira hasta que la regla esté subida.
- El script de diseño filtra las operaciones a los eventos de diseño antes de calcular nada.

## Cómo se arma la regla (en la mitad de diseño)
1. Ganadoras = billeteras con ≥ 20 eventos de diseño, t ≥ 3 y PnL/volumen ≥ +3 % en apuestas de 5–90 ¢ (sin cosecha).
2. Se compara dónde ponen la plata ellas contra el resto (anticipación, hora UTC, hora local, máxima/mínima, ciudad,
   precio, posición de la caja respecto de la favorita, si compran Sí o No, si el precio venía subiendo o bajando).
3. Con lo que más las distingue se arma **una** regla mecánica: momento de decisión fijo, qué caja y qué lado,
   usando sólo precios observables antes de ese momento. Se prueba en el diseño con la misma ejecución de abajo.
   Hay una sola regla principal; si se muestran variantes, no cuentan para el veredicto.

## Ejecución (igual en diseño y prueba)
- Decisión a la hora T con el último precio de cada caja antes de T (de las operaciones de todos).
- **Entrada 15 min tarde**: precio de la primera compra de otra persona del mismo lado hecha entre T+15 y T+75 min,
  **más 1 ¢** (no hay libro histórico; una compra taker se llena contra el ask real, el 1 ¢ cubre profundidad; el
  backtest histórico midió +0,6 a +1,5 ¢ de costo). Si no hay ninguna, no se entra.
- No se entra si ese precio supera en más de 5 ¢ el precio visto en T (límite) o pasa 90 ¢.
- US$ 10 por apuesta, hasta la resolución.

## Veredicto (en la mitad de prueba)
- **Pasa** si PnL/volumen ≥ **+3 %** y el límite inferior del intervalo del 90 % (bootstrap por evento) es > 0.
- Controles: las dos semanas de prueba por separado; lo mismo entrando en T (sin demora) y 60 min tarde.

## Regla elegida
(se completa antes de correr la prueba)

## Cambios
(ninguno)

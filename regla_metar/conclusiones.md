# Conclusiones (se van completando)

## Primer corte, 26-oct-2026 (eventos del 23 al 25-oct, precios de `libros.csv`)

`python regla_metar/analizar.py --libros --iem metar_iem.csv.gz` → `resultados_libros.json`. No decide nada
(REGLA.md): son 3 fechas y el libro de `libros.csv` no tiene las cajas de menos de 3 ¢.

**Brecha de la regla (lo más informativo por ahora).** Con los METAR de aviationweather, la caja de "solo rutina"
y la de "todos los reportes (con SPECI)" difieren en **1 de 243 eventos** (0,4 %). La caja de rutina coincide con la
ganadora de Polymarket en 243/243 (la regla está bien entendida). Antes del 23-oct (IEM, 2.837 eventos del control;
el SPECI se infiere por el minuto del reporte) difieren en 39 (1,4 %), siempre con SPECI más extremo.
O sea: la regla nueva mueve el resultado una caja en ~1 de cada 100 eventos. Aunque el mercado la ignorara del todo,
la caja de arriba estaría cara ~1 punto de probabilidad: menos que el costo de cruzar el libro (1–3 ¢).

**Sesgo y prueba de plata (M1, máximas).** S = −0,08 cajas (78 eventos, 3 fechas; signo contrario a la hipótesis);
control 24-ago a 20-oct S = +0,04 (t 2,3). Comprar el No de la vecina de arriba: −12 % por operación (75 ops);
vecina de abajo −3 % (69). Con 3 fechas el t agrupado no significa nada.

Siguiente corte: ≈ 30-oct con las fotos propias (`datos/fotos.csv`). Final: ≈ 8-nov.

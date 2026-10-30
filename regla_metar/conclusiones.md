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

## Corte parcial, 30-oct-2026 (eventos del 23 al 29-oct, 644 con ganadora)

`resultados.json` (fotos propias: 4 fechas, 26 al 29-oct, porque el recolector arrancó el 26 a las 10:34 UTC) y
`resultados_libros.json` (`libros.csv`: 7 fechas). No decide nada: el criterio se aplica en el corte final.

- **Brecha de la regla**: rutina vs. todos los reportes difieren en **3 de 644 eventos (0,5 %)**; rutina = ganadora
  644/644. Sigue el techo de ~1 punto de probabilidad.
- **Sesgo, máximas en M1**: S = −0,005 cajas (fotos, 161 ev.) / +0,004 (libros, 278 ev.); control +0,037.
  No hay sesgo hacia arriba; si algo, el período nuevo está un poco más abajo que el control (t −0,6).
- **Prueba de plata, máximas en M1**: No de la vecina de arriba −0,9 % (fotos, 143 ops) / −1,2 % (libros, 258 ops);
  vecina de abajo +5,8 % / +1,1 %. Va al revés de la hipótesis y lejos del +2 % con t ≥ 2.
- Mínimas (secundario): S muy negativo en los dos períodos (−0,37 a −0,43 nuevo, −0,23 control), pero en mínimas el
  libro está casi vacío y el medio no es un precio ejecutable: comprar el No de la vecina de abajo pierde −10 %/−11 %.
  No se lee como señal.

Va camino a "Ni 1": el mercado ya descuenta la regla (o el efecto es demasiado chico para verse).

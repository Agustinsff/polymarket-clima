# ¿El precio absorbe tarde las corridas de GFS/ECMWF? Conclusiones (26-oct-2026)

Regla fijada antes en `REGLA.md`. Tablas completas en `informe.md`. Es investigación: no toca ningún bot.

## Veredicto: el precio sí absorbe tarde, pero no alcanza para pagar el spread. No se sigue.

Según la lectura prefijada, se cumple el criterio 1 y no el 2: "el precio absorbe tarde, pero no alcanza
para pagar el cruce del spread".

- **Prueba A (sí):** después de que la corrida aparece en AWS, la media del mercado se mueve hacia donde fue el
  pronóstico: β = +0,041 a 3 h (t 8,7) y +0,062 a 6 h (t 9,0), en los dos modelos. Antes de W casi no se movió
  (β +0,007, t 1,5). O sea, se mueve tarde, pero **muy poco**: por cada caja que cambia el pronóstico, el mercado
  corre 0,04 de caja en 3 h. La mediana del cambio entre corridas es 0,25 de caja.
- **Prueba B (no):** comprar la caja vecina hacia donde fue la corrida y vender a las 3 h pierde **−4,0 %** por
  operación (t −6,0, 1193 ops; −4,1 % y −3,8 % en cada mitad). A 1 h, −7,5 %; a 6 h, −0,8 % (t −0,9).
  Sin costos la misma operación gana +7,5 % a 3 h y +11 % a 6 h: la señal existe, pero la caja vale ~23 ¢ y
  entrar y salir cuesta ~2 ¢ (≈ 9–10 % del precio), que se come todo.

## Datos

- 1140 eventos del 9 al 23-oct (los que tienen precio por minuto en `rivales/datos/`), 42 ciudades.
- 77 corridas de cada modelo (4-oct 18Z a 23-oct 18Z) bajadas de los archivos originales en AWS
  (`noaa-gfs-bdp-pds`, `ecmwf-forecasts`). Sin campos faltantes. `bajar.py` corre desde el contenedor.
- 4572 señales (modelo × corrida × evento) que pasan los filtros. Casi todas son máximas: en mínimas el día anterior
  las cajas casi nunca suman 0,90–1,15 (libro vacío), quedaron 42 señales y 11 operaciones.
- Denver, París y Lucknow quedaron afuera porque sus estaciones (KBKF, LFPB, VILK) no están en `estaciones.json`.
- Hora real en AWS (mediana desde la hora de la corrida): GFS ~4,2 h; ECMWF 7,6 h (00/12Z) y 6,5 h (06/18Z).
  ECMWF se publica antes en sus propios servidores: para ECMWF algunos ven la corrida antes que nosotros
  (eso se nota en β +0,017, t 2,0 antes de W).

## Controles (agregados después, no cambian el veredicto; `controles.py`)

- La caja vecina del lado **contrario** pierde sin costos (−3,9 % a 3 h, t −5,9): no es un rebote del precio.
- Todas las cajas de 5–60 ¢ sin mirar la señal: −0,2 % a 3 h (t −1,0): no hay deriva general.
- Quedarse hasta la resolución (pagando sólo la entrada): +6,5 %, t 0,9: demasiado ruido para decir algo.
- El resultado final también se corre hacia donde fue el pronóstico: β = +0,11 (t 6,9). El mercado subreacciona a
  las corridas, pero el efecto es chico comparado con el ancho del spread en cajas baratas.

## Límites

- Precio ejecutable aproximado: no hay libro histórico. Compra = máx(precio + 1 ¢, mediana de lo que pagaron los
  compradores en 15 min); venta = mín(precio − 1 ¢, mediana de lo que cobraron los vendedores). Sólo 15 % de las
  compras y 27 % de las ventas tuvieron operaciones reales en la ventana; el resto usa ± 1 ¢ (el spread mediano
  medido el día anterior en máximas es ~2 ¢, ver `libros_informe.md`).
- Comisión 0 (la tasa real de temperatura anotada desde el 23-oct es 0,0).
- 15 días. La salida a 6 h queda cerca de cero (−0,8 %): una regla nueva con salida a 6 h o entrada como
  market maker podría quedar en empate, pero eso sería otra prueba (y entrar como maker ya se descartó).

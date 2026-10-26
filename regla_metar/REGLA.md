# ¿La regla nueva de resolución (METAR de rutina) encarece las cajas altas? Regla fija (26-oct-2026)

Escrita el 26-oct-2026 ~01 UTC, **antes de mirar ningún precio ni resultado para esta pregunta**. No se cambia
después de ver datos; lo que se agregue va en `conclusiones.md` marcado como "agregado después".

Es solo medición: no opera ni toca ningún bot ni prueba en curso.

## Pregunta

Desde los mercados del 23-oct Polymarket resuelve la temperatura con los METAR de aviationweather.gov:
solo reportes de rutina (los SPECI no cuentan), grupo T en décimas, .5 hacia arriba, °F convertido.
La máxima de los reportes de rutina tiende a salir algo más baja que la máxima "real" (y la mínima algo más alta).
Si el mercado no lo descuenta, las cajas altas de la máxima (y bajas de la mínima) están caras.
¿Pasa? ¿Alcanza para ganar comprando el No de la caja vecina de arriba de la favorita, con precio y comisión reales?

## Datos

- **Período nuevo**: eventos de temperatura diaria (máxima y mínima) con fecha local del **23-oct al 6-nov-2026**
  inclusive cuya fuente sea aviationweather. Todas las estaciones con METAR (Hong Kong, que resuelve con HKO, no entra).
- **Precio**: foto del libro real de **todas** las cajas del evento (recolector `regla_metar/recolector.py`, cada hora
  desde Actions). Momentos (hora local de la estación, primera foto dentro de la ventana):
  - **M1 = 06:00–07:59 del día D (principal)**;
  - M0 = 06:00–07:59 del día anterior; M2 = 12:00–13:59 del día D (secundarios).
  - Primer corte (23 al ~29-oct): con `libros.csv` (foto por hora, solo cajas entre 3 y 97 ¢; las que faltan
    cuentan 0). No decide nada.
- **Resultado**: la caja que Polymarket da por ganadora (mercado cerrado con precio ≥ 0,99). Días sin ganadora no entran.
- **METAR**: aviationweather (con `metarType`) desde el recolector; antes del 23-oct, la historia de IEM y
  aviationweather de la rama `investigacion-velocidad`. En IEM, que no marca el tipo, SPECI = reporte fuera del minuto
  habitual de la estación (el más frecuente).
- **Control (regla vieja)**: `historico/cache.json.gz` (precio histórico a las 06:00 local del día D y del día anterior,
  ganadora de Polymarket), eventos del 24-ago al 20-oct (Wunderground). Solo eventos cuyas cajas sumen 0,90–1,15.
  El 21 y 22-oct (regla de transición) no entran en ningún lado.

## Medidas

1. **Brecha de la regla** (sin precios). Para cada evento: caja con todos los reportes (rutina + SPECI) contra caja con
   solo rutina (la regla nueva). % de eventos en que difieren y para qué lado. Chequeo: caja de rutina = ganadora.
2. **Sesgo de cajas**. Cajas ordenadas de abajo hacia arriba, posición k = 0, 1, 2…; q_k = precio medio del libro
   normalizado para que el evento sume 1 (en el control, el precio histórico). Ganadora en la posición w.
   **S = Σ q_k · k − w** (en cajas). S > 0 = el mercado esperaba más alto de lo que salió.
   Se espera S > 0 en máximas y S < 0 en mínimas si el mercado no descuenta la regla.
   Media de S con error estándar agrupado por fecha, en el período nuevo y en el control, y la diferencia.
3. **Prueba de plata**. En M1, máximas: comprar **10 acciones del No de la caja vecina de arriba de la más cara**
   (si la más cara no es la de arriba de todo), recorriendo el libro real (vender Sí contra las compras), si el No
   cuesta entre 3 y 97 ¢. Comisión real del mercado (`tasa · p · (1 − p)`; hoy 0 en temperatura).
   Se tiene hasta la resolución. Resultado = (cobro − costo − comisión) / costo.
   **Control**: lo mismo con la vecina de abajo. Secundarios (no deciden): M0, M2 y mínimas al espejo
   (No de la vecina de abajo).

## Criterio de éxito (todo tiene que cumplirse)

1. Máximas en M1: S del período nuevo > 0 con t ≥ 2, **y** S nuevo − S del control > 0 con t ≥ 2.
2. Prueba de plata en M1: ganancia media ≥ +2 % por operación, t ≥ 2 (agrupado por fecha), ≥ 150 operaciones,
   positiva en las dos mitades del período (por fecha) **y** mayor que la de la vecina de abajo.

Lectura:
- 1 y 2 → se le propone a Agus una prueba en papel (sería estrategia nueva: se le consulta antes).
- Sólo 1 → el sesgo existe pero no paga el costo: no se sigue.
- Ni 1 → el mercado ya descuenta la regla: no se sigue.

## Cortes

- Parcial: con los eventos del 23 al 29-oct (≈ 30-oct). Final: cuando resuelvan los del 6-nov (≈ 7/8-nov).
- El recolector deja de sacar fotos sola después del 7-nov.

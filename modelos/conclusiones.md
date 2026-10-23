# Que modelo de pronostico conviene (23-oct-2026)

Datos: 60 dias (24-ago a 22-oct-2026), 86 series (maxima y minima de 45 estaciones; Hong Kong queda
afuera porque no tiene METAR), 11 modelos globales de Open-Meteo, pronosticos hechos 1, 2, 3 y 5 dias
antes. Real = METAR con la misma regla que `calib/` (hilo de calibracion). Tablas completas en
`informe.md`; datos dia por dia en `dias.csv.gz`. Es investigacion: no cambia ningun bot.

## Lo principal

1. **El promedio de los 11 modelos, con el sesgo de cada ciudad corregido, es lo mejor en todos los
   horizontes.** A 1 dia: error medio 0,84 °C contra 0,98 °C de GFS+ECMWF (la base del bot), y cae en
   la caja ganadora el 40% de los dias contra 35%. Le gana a GFS+ECMWF en 77 de 86 series (a 2, 3 y 5
   dias: 65, 70 y 74 de 86). Vale igual para maximas (0,81 vs 0,94) y minimas (0,87 vs 1,03).
2. **El mejor modelo suelto es ECMWF-IA (AIFS)**: 0,93 °C a 1 dia, pero tiene mucho sesgo crudo
   (1,0 °C promedio): sirve solo corrigiendo el sesgo de cada ciudad. Le siguen ICON (0,96) y el ECMWF
   comun (1,03). GFS es de los peores (1,17), junto con GEM, JMA y CMA.
3. **Elegir "el mejor modelo de cada ciudad" no sirve**: elegido con la primera mitad de los dias y
   medido en la segunda, da 0,96 °C, peor que el promedio simple (0,86). El mejor de una mitad quedo
   entre los 3 mejores de la otra solo en 40 de 86 series: es mas ruido que algo propio de la ciudad.
   Elegir un trio por ciudad empata con el promedio, no le gana.
4. **El horizonte importa menos de lo que parece hasta 3 dias**: el promedio corregido pasa de 0,84
   (1 dia) a 0,93 (2) y 1,01 (3); a 5 dias, 1,26.
5. **Corregir el sesgo por ciudad es lo que mas rinde** en casi todos los modelos (ej. ECMWF-IA de
   1,33 a 0,93). Coincide con lo del hilo de calibracion (28% -> 36% de caja exacta).

## Ensambles

Open-Meteo no guarda historia de los ensambles (probado en `sonda.txt`), asi que solo se pueden
comparar con lo que anoto el bot desde el 20-oct: 162 series-dia, sin corregir sesgo. Ahi el ensamble
del bot (1,36 °C) queda parecido a ECMWF (1,33) y peor que ICON (1,09) y el promedio de 11 (1,16). Son
3 dias: no alcanza para concluir; se va a poder repetir con mas dias porque el bot lo sigue anotando.

## Que haria con esto (para la revision del 26-oct, no ahora)

Si se decide tocar el pronostico del bot: usar el promedio de los 11 modelos con sesgo por ciudad
como centro de la distribucion (y el ensamble solo para el ancho). No es una estrategia nueva, es
cambiar el pronostico de `pronostico.py`, que esta en prueba: queda para decidir con Agus.

Para repetir el analisis: workflow `modelos` (a mano), escribe en `modelos/`.

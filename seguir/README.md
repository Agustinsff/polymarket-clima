# Seguir billeteras ganadoras (diseño + backtest, 23-oct-2026)

No opera nada. Pregunta: si copiamos a las billeteras que ganan constante en temperatura, ¿ganamos nosotros?

- `REGLAS.md`: las reglas, fijadas y subidas **antes** de correr el backtest (commit bca451d).
- `backtest.py`: walk-forward sobre los 30 días de `rivales/datos/` (rama `investigacion-rivales`).
  `python seguir/backtest.py RUTA_A_rivales/datos` (tarda ~1 min).
- `informe.md`: el resultado.

## Resultado

**No pasa.** Elegir a las billeteras con el pasado sí funciona: fuera de muestra siguen ganando +8% a su propio
precio (al azar, +1%). Pero esa ventaja está en *el momento y el precio* al que entran: un minuto después el precio ya
se movió ~2,5¢ en contra y copiarlas da 0% (L = 1, 5 o 60 min) y −0,6% con la regla principal (L = 15 min,
intervalo −2,4% a +1,3%). Pasa igual en las dos mitades de los días de prueba y con hello.67, la más grande (−1,9%).

Mirado después (no estaba en las reglas): copiar sólo las apuestas **durante el día** da +2,3% con L = 15, pero el
intervalo incluye 0 (−0,8% a +5,4%) y las dos mitades cambian de signo (−2,2% y +5,7%). Es ruido hasta que se
pruebe aparte.

## Velocidad

Durante el día, el que compra entre 5¢ y 90¢ en los minutos :00–:01 gana +4,8%, en :02–:04 +3,1% y desde :05 ya
nada (0%). Nuestra fuente de METAR más rápida y gratis (`carrera.py`, noaa_txt) tarda una mediana de 250 s, o sea que
llegamos al tramo en el que ya no queda ventaja; copiar a los que entran en :00–:04 dos a diez minutos después pierde
entre −3% y −4%. Un bot de velocidad necesitaría ver el METAR en menos de ~2 min y una máquina prendida todo el
tiempo (GitHub Actions no sirve para eso). No vale la pena con lo que tenemos; el cosechador ya cubre la parte de
velocidad que no depende de llegar primero (cajas imposibles).

## Si algún día se quisiera retomar

La única variante con algo de señal es "copiar apuestas durante el día con ≤15 min". Para tomarla en serio habría que
fijarla como regla nueva y probarla en papel hacia adelante (con el libro real al momento de copiar), no ajustarla con
estos mismos datos. Se decide en la revisión del 26-oct.

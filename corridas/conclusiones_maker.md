# Versión maker de la regla de las corridas. Conclusiones (26-oct-2026)

Regla fijada antes en `REGLA_MAKER.md`; tablas completas en `informe_maker.md`; operación por operación en
`ops_maker.csv.gz`. Es investigación: no toca ningún bot. Se repite con `python corridas/maker.py CARPETA_RIVALES_DATOS`.

## Veredicto: entrar como maker es peor que entrar como taker. Se cierra.

Según la lectura prefijada, no se cumple el criterio 1: "ser maker no arregla la señal de las corridas".

- **Principal** (orden de compra a precio en W − 1 ¢, válida 3 h, venta taker a W + 6 h): se llena el 31 % de
  las veces y las llenadas pierden **−4,3 %** por operación (t −3,0, 373 ops; −2,5 % y −6,4 % por mitad).
  La misma señal entrando como taker y saliendo a 6 h: −0,8 % (t −0,9).
- Da lo mismo cómo se entre o se salga: orden a la par del medio −5,5 %, 2 ¢ abajo −3,5 %, salir 3 h después del
  llenado −6,0 %, salir también como maker −6,1 %. Quedarse hasta la resolución es puro ruido (t −0,6).
- **La causa es selección adversa, y es enorme**: en las 820 señales donde nadie nos vendió, la caja subió
  **+17,4 %** de W a W + 6 h (t +14). En las 373 donde sí nos llenaron, bajó −3,0 %. El maker se queda sólo con
  las cajas que iban para abajo y se pierde todas las que iban para arriba, que es justo donde estaba la ganancia
  de la señal (+7,5 % sin costos). Es exactamente el "makers pierden" del estudio de rivales, ahora con una señal
  a favor y aun así pierde.
- Por precio: 5–20 ¢ −6,8 %, 20–40 ¢ −3,1 %; 40–60 ¢ +5,0 % pero son 11 operaciones. Por modelo no cambia.

## Qué significa para las otras ideas

- Recompensas de liquidez (hilo aparte): el costo de selección adversa de dejar una orden 3 h en una caja de
  máximas el día anterior es del orden de **3–5 % del precio de la caja (≈ 1 ¢ por acción a 23 ¢)**. Cualquier
  recompensa o reembolso tiene que superar eso para que dar liquidez pague. Con los números de los docs (reembolso
  ≈ 0,25 · 0,05 · p(1 − p) ≈ 0,2 ¢ por acción a 23 ¢) el reembolso solo no alcanza ni de cerca; la recompensa
  de liquidez diaria es la única que podría.
- Temperatura diaria: con esto quedan probadas las dos formas de entrar (taker y maker) sobre la única señal
  pública que mostró algo. Refuerza la recomendación de los hilos anteriores de cerrar la temperatura diaria con
  información pública.

## Límites

- No hay libro histórico: "precio en W − 1 ¢" aproxima el mejor precio de compra del libro (spread mediano ~2 ¢).
  Si el libro real estaba más lejos, nuestra orden hubiera estado adelante de la fila y se llenaría más, pero
  también con más selección adversa; la dirección del resultado no cambia.
- Llenado prudente: sólo cuenta operaciones estrictamente por debajo de nuestro precio. Contando también las
  que se hicieron justo a nuestro precio, la tasa de llenado pasa de 31 % a 40 %; el sentido no cambia.
- 14 días (9 a 22-oct), antes de la regla nueva de resolución.

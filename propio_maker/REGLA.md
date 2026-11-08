# Pronóstico propio como filtro maker: regla de medición

Fijada el 8-nov-2026 ~14:15 UTC, **antes de cruzar** las probabilidades del modelo con los llenados (solo se vio que
`propio-datos/probs_cajas.csv.gz` tiene 8.910 filas, prueba B, método M1, del 20-oct al 6-nov, y que el paso 3 del
pronóstico propio NO pasó: Brier 0,731 contra 0,634 del mercado). Solo se mide; no se arma prueba en papel sin Agus.

## Pregunta

Aunque el modelo pierda contra el precio, ¿sirve para elegir **qué** órdenes maker dejar? Si dejamos la orden solo donde
el modelo está de acuerdo, ¿se achica la pérdida de los llenados (selección adversa)?

## Datos

- Probabilidad del modelo por caja: `probs_cajas.csv.gz` (`condition_id`, `momento_utc`, `p_modelo`).
- Llenados simulados del medidor maker (`medidor-maker/maker/datos/llenados.csv`), clima, con resultado (`gano`).
  Se usan solo llenados de fotos **antes del 2-nov 22:25Z o desde el 7-nov 23:20Z** (hueco por la API retirada) y
  **después** del `momento_utc` de la probabilidad de esa caja (el modelo no ve el futuro).
- Cajas con precio de nuestra orden entre 3 y 97 ¢.

## Qué se mide

"De acuerdo": orden de compra del Sí a precio q con `p_modelo > q`; orden de venta del Sí a q con `p_modelo < q`.
Resultado por acción a la resolución (+ reembolso), para órdenes a 1 y 2 ¢ del medio:
de acuerdo, en desacuerdo y todas. Bootstrap 2.000 veces por fecha de evento.

## Qué decide

**Sirve como filtro** si, a 2 ¢, (de acuerdo − todas) ≥ +1 ¢/acción y (de acuerdo − en desacuerdo) > 0 con P < 5 %.
Si sirve, se le propone a Agus sumarlo al bot maker (es cambio de estrategia: no se toca sin su OK).
Si no, se cierra: el modelo no aporta ni como taker ni como maker.

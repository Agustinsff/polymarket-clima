# ¿El precio absorbe tarde las corridas de GFS/ECMWF? Regla fija (26-oct-2026)

Escrita antes de mirar ningún dato de pronóstico ni de precio para esta pregunta. No se cambia después de ver
resultados; si algo se agrega, va en `conclusiones.md` marcado como "agregado después".

Es investigación: no opera ni toca ningún bot.

## Pregunta

Cuando sale una corrida nueva de GFS o ECMWF y cambia el pronóstico de la máxima o mínima de mañana,
¿el precio de las cajas se mueve en esa dirección durante las 1–6 h siguientes (o sea, tarde), lo
suficiente para ganar comprando apenas sale la corrida y vendiendo después, con precio ejecutable y comisión?

## Datos

- **Corridas**: archivos originales de cada corrida, no Open-Meteo.
  - GFS 0,25° (00/06/12/18Z), bucket público `noaa-gfs-bdp-pds` en AWS, temperatura a 2 m por hora.
  - ECMWF IFS 0,25° datos abiertos (00/06/12/18Z), bucket `ecmwf-forecasts` en AWS, temperatura a 2 m cada 3 h.
  - Punto de grilla más cercano a la estación de resolución (`estaciones.json`). Máxima/mínima = máximo/mínimo de
    los valores del día local de la estación, en la unidad del mercado (°F en EE.UU.).
- **Hora en que la corrida está disponible (W)**: la hora `LastModified` del último archivo que hace falta en el
  bucket, más 10 minutos. Si el bucket la publica más tarde que la fuente original, nos perjudica (W más tarde):
  es conservador.
- **Precios**: los de `rivales/datos/` (rama `investigacion-rivales`): precio por minuto de cada caja
  (prices-history) y todas las operaciones con su lado. Período = el que tenga precio por minuto.
- **Mercados**: temperatura diaria, máximas y mínimas, días cuyo comienzo local cae entre 6 h y 48 h después de W
  ("día anterior"). En el momento W las cajas del evento tienen que sumar entre 0,90 y 1,15 (si no, el precio es
  el medio de un libro vacío; ver backtest de `historico/`).

## Señal

Para cada modelo, corrida R, estación y día D: **Δ = pronóstico(R) − pronóstico(R − 6 h)** del mismo modelo,
medido en anchos de caja (Δb = Δ / ancho de caja del evento; 1 °C o 2 °F en general).

## Prueba A: ¿el precio se mueve tarde? (sin costos)

Media del mercado E(t) = Σ precio normalizado × centro de caja (en anchos de caja; las cajas de los extremos
"X o menos"/"X o más" cuentan un ancho más allá del borde). Para h = 1, 3 y 6 h:

    E(W + h) − E(W) = β_h · Δb + error

β_h con error estándar agrupado por evento. También se informa, para ver cuánto ya se absorbió antes de W,
el mismo ajuste con E(W) − E(R + 3 h) (el movimiento desde que arranca la ventana de publicación).

## Prueba B: ¿se puede ganar? (con costos)

- Si |Δb| ≥ 0,5: comprar 10 acciones del **Sí de la caja vecina a la más cara del evento, del lado hacia donde
  se movió el pronóstico** (más cara + 1 si Δ > 0, −1 si Δ < 0), si en W cuesta entre 5 y 60 ¢.
- Salida: vender a las **W + 3 h** (principal). Se informan también 1 h y 6 h, pero no deciden.
- Precio de compra = el mayor entre (precio en W + 1 ¢) y la mediana de lo que pagaron los compradores del Sí
  (taker que compra Sí, o que vende No a 1 − p) en [W, W + 15 min]. Precio de venta = el menor entre
  (precio a la salida − 1 ¢) y la mediana de lo que cobraron los vendedores del Sí en [salida − 15, salida + 15 min].
  Sin operaciones en la ventana se usa sólo precio ± 1 ¢ y se cuenta aparte cuántas fueron así.
- Comisión: la tasa real del mercado (`tasa · p · (1 − p)` en cada lado; en temperatura hoy es 0).
- Resultado por operación = (venta − compra − comisiones) / compra.

## Criterio de éxito (todo tiene que cumplirse)

1. Prueba A: β a 3 h > 0 con t ≥ 3.
2. Prueba B, salida a 3 h: ganancia media ≥ +2 % por operación, t ≥ 2 (agrupado por evento), ≥ 150 operaciones,
   y positiva en las dos mitades del período (por fecha).

Lectura:
- 1 y 2 → vale la pena anotarlo en vivo ~10 días con el libro real desde Actions (sería estrategia nueva: se le
  consulta a Agus antes).
- Sólo 1 → el precio absorbe tarde, pero no alcanza para pagar el cruce del spread: no se sigue.
- Ni 1 → el precio ya incorporó la corrida cuando la vemos: no se sigue.

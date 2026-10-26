# Arbitraje de precios que no suman 1: regla de medición

Fijada el 24-oct-2026 ~22:45 UTC, **antes de mirar ningún dato**. No se cambia después de ver resultados;
si hubiera que cambiar algo se anota abajo con fecha y motivo.

Solo se mide. No se opera ni se toca ninguna prueba en papel.

## Qué mercados

1. **Temperatura**: todos los eventos abiertos de `tag_slug=daily-temperature` (cajas de una ciudad y un día).
   Comisión 0 (o la que traiga el mercado, si cambia).
2. **Otros multi-resultado (negRisk)**: los 40 eventos negRisk abiertos que no son de temperatura con más
   volumen de las últimas 24 h (se re-elige cada 10 min). Comisión real de cada mercado (`feeSchedule.rate`,
   0 si `feesEnabled` es falso).
3. **Control binario Sí+No**: los 20 mercados binarios (evento de un solo mercado) con más volumen de 24 h.

Solo cuentan mercados con libro (`enableOrderBook`), activos y no cerrados.
Eventos negRisk "aumentados" (`negRiskAugmented`, tienen resultados que pueden agregarse después u "Otro")
se miden pero se reportan aparte: ahí comprar todos los Sí **no** garantiza cobrar.

## Las dos jugadas (las únicas que se miden)

En un evento con N resultados abiertos, sale exactamente uno:

- **Comprar todos los Sí**: comprar q acciones de Sí en cada resultado. Cobra q dólares seguro.
- **Comprar todos los No**: comprar q acciones de No en cada resultado. Cobra q·(N−1) dólares seguro.

En el binario es lo mismo con N = 2 (Sí + No).

## Precio

- Precio ejecutable real: se recorre el libro de **cada token que se compra** (asks del token Sí para la primera
  jugada, asks del token No para la segunda), escalón por escalón. No se usan precios medios ni el resumen de gamma.
- Comisión de taker por acción: `tasa · p · (1 − p)`, la misma fórmula del resto del repo, con la tasa de cada mercado.
- Se compran juegos completos (la misma q en todos los resultados) mientras el juego siguiente cueste menos
  de lo que cobra (1 para Sí, N−1 para No). Eso da el **máximo de juegos** y la **ganancia máxima en US$**.
- Si a algún resultado le falta el lado que hay que comprar (libro vacío), esa jugada no existe en esa foto.
- Mínimo de orden: cada pata tiene que tener al menos `orderMinSize` acciones. Si el máximo de juegos rentables
  es menor que el mínimo, no cuenta como oportunidad.
- No se cuenta gas ni costo de capital (la plata queda inmovilizada hasta que se resuelve el evento); se
  comentan en el informe.

## Oportunidad y duración

- **Oportunidad** en una foto: ganancia neta ≥ US$ 0,01 comprando al menos el mínimo de orden en cada pata.
- **Episodio**: fotos seguidas con oportunidad en el mismo evento y la misma jugada. Empieza en la primera foto con
  oportunidad y termina en la primera sin. Duración observada = tiempo entre la primera foto con y la primera sin.
  Si dura una sola foto se reporta como "menos de un intervalo".
- Fotos: lo más seguido posible (objetivo cada 10 s) desde GitHub Actions; se anota la hora real de cada foto.

## Qué se reporta

Por grupo (temperatura, otros negRisk, binarios): % de fotos con oportunidad, episodios por hora, tamaño
(¢ por juego en el mejor escalón, US$ máximos por la profundidad), duración (mediana y percentiles) y qué
fracción de la ganancia total dura más de 15 min (capturable con el cron actual), más de 1 min y más de 10 s
(lo que podría agarrar un servidor rápido, p. ej. en Irlanda).

## Cambios

- 25-oct 22:40 UTC: las corridas de día del 25-oct no salieron (los cron solo corren desde la rama principal). Se lanza una
  segunda corrida de noche (25→26). La regla no cambia.

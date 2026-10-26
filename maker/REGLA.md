# Recompensas de liquidez y reembolsos maker: regla de medición

Fijada el 26-oct-2026 ~14:30 UTC, **antes de mirar ningún dato propio** (solo se leyeron los documentos
oficiales de Polymarket). No se cambia después de ver resultados; si hubiera que cambiar algo se anota
abajo con fecha y motivo.

Solo se mide. No se opera ni se toca ninguna prueba en papel.

## Pregunta

¿Dejar órdenes como maker (sin tomar precio) en los mercados que Polymarket paga da una ganancia chica
y constante, sumando lo que paga Polymarket y restando lo que se pierde cuando alguien nos llena?

## Qué paga Polymarket (docs.polymarket.com, 26-oct-2026)

1. **Recompensas de liquidez**: pozo diario por mercado (`rewardsDailyRate`). Cada minuto Polymarket
   saca una foto del libro y a cada orden le da puntaje `((v − s)/v)² · tamaño` (v = spread máximo
   del mercado, s = distancia al precio medio). Se suma por lado; con el precio entre 10 y 90 ¢ un solo
   lado vale un tercio, fuera de ese rango hace falta tener los dos lados. El pozo del día se reparte
   según el puntaje de cada maker. Tamaño mínimo (`rewardsMinSize`) y spread máximo
   (`rewardsMaxSpread`) los fija cada mercado. Pago diario a las 00 UTC, mínimo US$ 1.
2. **Reembolsos maker**: de la comisión que paga cada taker (`tasa · acciones · p · (1 − p)`), una parte
   vuelve a los makers de ese mercado repartida por el volumen que les llenaron. Clima: tasa 0,05 y
   25 % de reembolso; cripto: 0,07 y 20 %; el resto 0,04–0,05 y 25 %. Los makers no pagan comisión.

## Qué mercados

- **Temperatura**: todos los eventos abiertos de `daily-temperature`, cajas con precio medio entre 3 y 97 ¢.
- **Cripto**: las series que ya sigue `cripto.py` (BTC/ETH above, rango, toca) que vencen en 72 h.
- **Todos los que tienen pozo**: la lista completa de `GET clob/rewards/markets/multi` se guarda en cada
  foto para saber cuánto pozo hay por categoría y cuánta competencia, sin simular en todos.

## Qué se simula (regla fija)

Una orden nuestra de **100 acciones por lado** (compra y venta del Sí; si el mínimo del mercado es mayor,
el mínimo) a **1 ¢ del precio medio** del lado correspondiente, puesta al momento de cada foto y renovada
cada foto (o sea: siempre a 1 ¢ del medio actual, como haría un bot). Variante de control: a 2 ¢.

- **Recompensa estimada por foto** = `pozo · nuestro_puntaje / (nuestro_puntaje + puntaje_competencia)`,
  con la fórmula oficial y la competencia leída del libro real (órdenes del tamaño mínimo o más).
  Es una cota optimista: no vemos a quien entre y salga entre fotos.
- **Llenado**: la orden se considera llenada si, entre esa foto y la siguiente, alguien operó como taker
  (operaciones de `data-api/trades`, `takerOnly=true`) en ese token a un precio **estrictamente peor para
  él** que el nuestro (compró más caro que nuestra venta o vendió más barato que nuestra compra). Si operó
  justo a nuestro precio, suponemos que había otros antes en la fila (cuenta prudente, igual que
  `sombra_maker.py`). Se llena hasta el tamaño operado.
- **Costo del llenado** = lo que vale esa posición **60 minutos después**, al precio medio del libro, menos lo
  que pagamos/cobramos (selección adversa). También se guarda a 5 y 30 min y al cierre (resultado real)
  cuando se sepa. El número principal del informe es el **de la resolución**; 5/30/60 min son para entender.
- **Reembolso** = 25 % (clima) o 20 % (cripto) de la comisión que pagó el taker que nos llenó:
  `pct · tasa · acciones · p · (1 − p)`. Si el mercado tiene tasa 0, reembolso 0.
- **Ganancia neta diaria** = recompensas + reembolsos + resultado de los llenados (sin gas; el capital
  inmovilizado se informa aparte: 100 acciones por lado a p es ≈ 100 dólares por caja).

## Qué se informa

Por grupo (temperatura / cripto), por horas hasta el cierre y por hora local: recompensa diaria estimada,
reembolsos, llenados por día, pérdida por llenado, y el neto. Verdict: **vale la pena** solo si el neto
es positivo con t > 2 después de al menos 7 días completos, y el capital necesario para ganar US$ 5/día
es razonable (< US$ 2.000). Si el neto es negativo o la recompensa depende de estar solos en el libro
(competencia < 10 % del tiempo), **no vale la pena**.

## Límites conocidos

- Vemos el libro cada 5 minutos (reloj), Polymarket cada minuto: la recompensa estimada es optimista.
- No podemos ver quién es el maker en cada operación: el llenado es una simulación prudente.
- No podemos operar desde GitHub Actions (EE.UU.); todo es en papel.
- Las fotos empiezan el 26-oct-2026 y el medidor se apaga solo el 9-nov-2026; corte intermedio el 2-nov.

## Cambios después de fijada la regla

(ninguno)

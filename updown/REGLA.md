# Up or Down de cripto: estudio histórico de calibración (regla)

Fijada el 26-oct-2026 ~14:40 UTC, **antes de bajar ningún precio** (solo se conoce, por notas públicas, que estos
mercados existen en 5 min, 15 min, 1 h, 4 h, 1 día y 1 semana, que resuelven con el precio promedio de Chainlink al
inicio y al fin de la ventana, que cobran comisión al taker desde enero de 2026 y que los bots son el 55–62 % del
volumen en 5 y 15 min). Si algo se agrega después de ver datos, va marcado "agregado después". No se opera.

## Qué mercados
- Bitcoin y Ethereum. Ventanas: **1 h, 4 h y 1 día** (son las que se pueden seguir desde Actions, que corre cada 15 min).
  Las de 15 min entran solo como muestra de comparación (3 días de BTC); las de 5 min no entran.
- Todos los eventos cerrados con ganador de los últimos **60 días** (o los que haya), bajados desde gamma.
- Comisión: la que trae cada mercado (`feeSchedule`), y si falta, 0,07·p·(1−p) como en los demás de cripto.

## Precio
`clob.polymarket.com/prices-history` del token Up, con la mayor resolución que dé la API. De cada ventana se toman
los precios en **5 momentos**: 10 %, 25 %, 50 %, 75 % y 90 % del tiempo transcurrido (el último punto anterior
a ese momento, y no más viejo que 1/10 de la ventana). Un precio histórico es un último pago, no un ask: por eso
todo se informa con costo extra de 0, 1 y 2 ¢ por acción además de la comisión.

## Medidas
1. **Calibración**: en cada momento, por tramo de precio del Up (0–10, 10–20, …, 90–100 ¢), cuántas veces ganó
   Up frente a lo que el precio decía. Lo mismo para Down (= 1 − Up). Intervalo 95 % binomial.
2. **Ganancia de reglas fijas simples**, comprando 10 acciones:
   - "Favorito": comprar el lado que está a ≥ 70 ¢ (y a ≥ 80, ≥ 90).
   - "Cola": comprar el lado que está a ≤ 30 ¢ (y ≤ 20, ≤ 10).
   - "Cincuenta": comprar Up cuando está a 45–55 ¢ (control: debería dar ≈ −comisión).
   En cada momento y cada ventana, con comisión y con costo extra 0/1/2 ¢. ROI = neto / plata puesta.
3. **Deriva**: con qué frecuencia resuelve Up por ventana y activo (debería ser ≈ 50 %).
4. **Independencia**: ventanas del mismo activo que se solapan en el tiempo (p. ej. la de 1 h dentro de la de 4 h)
   se cuentan como un solo bloque = (activo, día). P(ROI ≤ 0) por bootstrap de bloques, 2.000 remuestreos.

## Criterio de "hay algo"
Una regla vale la pena si, con comisión y 1 ¢ de costo extra, da ROI > 0 con P(≤ 0) < 5 % **y** el signo se repite
en las dos mitades de las fechas **y** en BTC y ETH por separado. Si no, se informa como no encontrado y no se
arma medidor en vivo ni bot.

## Lo que este estudio NO mide
La velocidad (si Polymarket va atrás del precio spot dentro de la ventana) y lo que cobra un maker. Las dos
necesitan datos en vivo (libro y spot a la vez) y se deciden después, según lo que dé esto.

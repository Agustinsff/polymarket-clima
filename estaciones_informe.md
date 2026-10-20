# Peculiaridades de las estaciones y prueba con datos históricos (20-oct-2026)

Datos: 1250 mercados cerrados de temperatura (6 al 19-oct, 44 ciudades), todas sus operaciones públicas
(~670.000) y los METAR de cada estación (IEM). Todo en papel.

## 1. ¿El METAR coincide con la resolución oficial?
- En **1142 de 1148** días el máximo (o mínimo) de los METAR cayó dentro de la caja ganadora (99,5 %).
- Las 6 excepciones: el METAR marcó **1 o 2 grados de más** (nunca de menos):
  - Denver KBKF 13 y 14-oct
  - París LFPB 07-oct
  - Chicago KORD 16-oct
  - Miami KMIA (mínima) 17-oct
  - Lucknow VILK 13-oct
- Se excluyen del cosechador LFPB, VILK y **KBKF (nueva)**. KORD y KMIA quedan en vigilancia.

## 2. Cajas muertas (regla del cosechador: 2 observaciones + 1 grado de margen + 4 min de demora)
- 5234 cajas declaradas muertas: **ninguna terminó ganando**. La regla nueva es segura en esta muestra.
- Vender el Yes de esas cajas **como maker** (dejar la orden y esperar): casi nadie compra.
  - Con la orden a 5 ¢: 8 cajas llenadas en 2 semanas, +US$28 en total.
  - Con la orden a 3 ¢: +US$20.
- Los compradores que pagaban 3 a 25 ¢ ya muerta la caja sumaron ~US$575 en 2 semanas en todas las ciudades. Ese es el techo del cosechador taker, y hay que competir por él.

## 3. Comprar colas baratas como maker (orden de compra de Yes a 1–10 ¢)
- En todas las cajas, sin elegir: **pierde entre 60 y 75 %** de lo invertido. Las órdenes que se llenan son justamente las de las cajas que se están muriendo.
- Filtrando solo las cajas todavía posibles según el METAR: sigue perdiendo, entre 59 y 73 %.
- Ninguna combinación de hora del día y distancia al extremo actual dio positiva de forma clara.
- Las billeteras que ganan con colas **eligen bien**:
  - 0xbF26: 303 compras a <10 ¢, ganó el 12 % y sumó ~US$9.300.
  - Lex-tang: 946 compras, ganó el 8 % y sumó ~US$1.400.
- La ventaja está en el pronóstico, no en la orden. Por eso `pronostico.py` registra colas solo cuando el modelo les da ≥2,5 veces el precio.

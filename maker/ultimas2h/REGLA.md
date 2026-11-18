# Medición: cotizar clima solo en las últimas 2 horas antes de que termine el día

Escrita el 18-nov-2026, ANTES de mirar los resultados. Pedido de Agus (18-nov, hilo del maker real: "dale, coordiná
tu recomendación"). Es solo con datos guardados: no toca el bot real ni pone órdenes.

## La idea
En las últimas 2 horas del día local de la ciudad la máxima (o mínima) del día ya casi se conoce. El precio debería
moverse poco y la recompensa de liquidez se sigue pagando. Hoy el bot no entra ahí (solo cajas que cierran en más
de 24 h).

## Datos
- Fotos cada 5 minutos del medidor maker (rama `medidor-maker`, `maker/datos/fotos_*.csv.gz`, 26-oct al 9-nov):
  libro de todas las cajas de temperatura vivas, pozo de recompensa, competencia y la orden simulada a 2 ¢ del medio.
- Llenados simulados del mismo medidor (`maker/datos/llenados.csv`): una orden nuestra se llena solo si un taker
  operó a un precio peor que el nuestro; con el resultado real de la caja (`gano`) y el reembolso de comisión.
- Se usan solo los períodos con llenados válidos (26-oct al 2-nov 22:25Z y desde el 7-nov 23:20Z; en el medio la
  API vieja no devolvía operaciones).

## Ventanas que se comparan
- "Fin del día": la caja en las últimas 2 horas antes de la medianoche local de la ciudad del día del evento.
  (Polymarket pone el fin del evento a las 12:00 UTC del día; la medianoche local se calcula con la hora local de
  cada foto.)
- "Como hoy": la caja a más de 24 h del fin del evento (la regla actual del bot), como referencia.

## Filtros (los del bot)
Libro con spread ≤ 5 ¢, medio entre 0,03 y 0,97, pozo > 0, orden a 2 ¢ del medio, 100 acciones por lado (se escala
después a lo que pone el bot).

## Qué se mide, en cada ventana
- Movimiento del medio en 1 hora (promedio y cuántas veces 6 ¢ o más).
- Recompensa esperada **pesimista** (los rivales copian nuestra orden), en US$ por caja y por hora.
- Resultado de los llenados **a la resolución**: (lo que pagó la caja − nuestro precio) por acción, más el reembolso
  de comisión de maker, en US$ por caja y por hora.
- **Neto por caja-hora** = recompensa pesimista + llenados a la resolución + reembolso.
- Como la fórmula exagera la recompensa (el 12-nov en real pagó el 57 % de lo estimado), también se informa el neto
  con **la mitad** de la recompensa, y ESE es el que decide.

## Regla de aprobado (con la mitad de la recompensa)
- Intervalo del 90 % por bootstrap agrupando por día del evento (los llenados de un mismo día están correlacionados).
- **PASA** (se arma un bot de papel en vivo que cotice solo esas 2 horas, y se mide una semana antes de cualquier
  plata real): neto de la ventana "fin del día" > 0 **y** el límite de abajo del intervalo > 0.
- **DUDOSO** (se arma igual el papel en vivo, pero sin expectativas): neto > 0 con el intervalo cruzando el cero.
- **NO PASA** (se descarta la idea): neto ≤ 0.
- Si la ventana tiene menos de 30 llenados resueltos, no alcanza: se informa "no concluyente" y se decide con
  Agus si vale armar el papel en vivo para juntar más.

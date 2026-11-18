# Últimas 2 horas antes de la medianoche local vs. regla de hoy (clima, orden a 2 ¢, 100 acciones)

Reglas: `maker/ultimas2h/REGLA.md` (escritas antes de ver esto). Datos: fotos cada 5 min del medidor maker (26-oct al 9-nov) y sus llenados simulados (solo los períodos con llenados válidos). Montos en US$ por caja y por hora, para 100 acciones por lado; el bot pone 20–25.

| ventana | caja-horas | días | mov. medio 1 h | horas con salto ≥6 ¢ | recompensa pesimista | llenados (resueltos) | acciones llenadas/h | llenados por acción | llenados | reembolso | neto | **neto con ½ recompensa** | intervalo 90 % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fin del dia (ultimas 2 h) | 8 | 10 | 6.16 ¢ | 4.1 % | +0.570 | 15 (9) | 99.2 | -14.22 ¢ | -8.825 | +0.0590 | -8.196 | **-8.481** | [-21.801, +0.661] |
| como hoy (>24 h al fin) | 34,426 | 11 | 1.72 ¢ | 4.9 % | +0.183 | 5307 (4160) | 3.8 | -1.98 ¢ | -0.059 | +0.0038 | +0.127 | **+0.036** | [-0.003, +0.078] |

**Veredicto según la regla: NO CONCLUYENTE (menos de 30 llenados resueltos en la ventana).**

En las últimas 2 h hay en promedio 7 cajas vivas por foto y 1.3 cumplen los filtros del bot (spread ≤ 5 ¢, medio 0,03–0,97, pozo); el resto ya está casi decidida (medio < 0,03 o > 0,97) o con el libro abierto.


## Complemento con el historial de precios (eventos del 13-16-11-2026)

- Eventos leídos: 316 (3476 cajas con historial).
- Cajas que al empezar las últimas 2 h del día local seguían con precio entre 0,10 y 0,90: 223 (55.8 por día entre todas las ciudades; 6.4 % de las cajas).
- En esas cajas, movimiento medio del precio en 1 h: últimas 2 h 12.14 ¢ (48 % de las horas con 6 ¢ o más) contra 4.54 ¢ en las 22 h anteriores (23 %).

## Lectura (18-nov)
- Según la regla, la medición con las fotos del medidor es **no concluyente**: el medidor casi no sacó fotos de las
  cajas pasado el fin del evento (12:00 UTC), así que de las últimas 2 h quedan solo 8 caja-horas con libro apretado y
  15 llenados. Esos pocos perdieron −14 ¢ por acción, contra −2 ¢ con la regla de hoy.
- El complemento con el historial de precios (4 días, 316 eventos) va **en contra de la idea**: en las últimas 2 h
  casi todas las cajas ya están decididas (precio < 0,10 o > 0,90) y las ~56 por día que siguen abiertas se mueven
  **12 ¢ por hora** (casi la mitad de las horas con saltos de 6 ¢ o más), contra 4,5 ¢ en el resto del día. Son las
  cajas que se definen con el último dato de temperatura, justo donde un taker informado nos llena del lado malo.
- Recomendación: no armar el papel en vivo de las últimas 2 h y descartar la idea, salvo que Agus quiera juntar más datos.

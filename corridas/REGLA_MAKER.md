# Versión maker de la regla de las corridas. Regla fija (26-oct-2026)

Escrita antes de correr nada. No se cambia después de ver resultados; lo que se agregue va en `conclusiones_maker.md`
marcado como "agregado después". Es investigación: no opera ni toca ningún bot.

## Pregunta

La prueba B de `REGLA.md` dio +7,5 % sin costos y −4 % con costos: la señal existe, pero cruzar el spread
(≈ 2 ¢ sobre una caja de ~23 ¢) se la come. ¿Cambia el resultado si, en vez de comprar al precio del libro
(taker), dejamos la orden de compra en el libro y esperamos a que alguien nos venda (maker)?

El problema conocido: en temperatura los makers pierden (estudio `rivales/`), porque te llenan la orden
justo cuando alguien sabe más. Acá la pregunta es si una señal a favor (la corrida) alcanza para compensar eso.

## Datos y señales

Las mismas de `REGLA.md`: mismas corridas, mismo W, mismos eventos y las mismas señales de la prueba B
(|Δb| ≥ 0,5, caja vecina a la más cara del lado del pronóstico, precio en W entre 5 y 60 ¢). Lo único que cambia
es cómo entramos y salimos.

## Entrada como maker

- En W ponemos una orden de compra del Sí de esa caja a **B = precio en W − 1 ¢** (redondeado al centavo). El
  spread mediano medido en máximas el día anterior es ~2 ¢, así que B es aproximadamente el mejor precio de
  compra que ya había en el libro: nos ponemos a la par, no adelante.
- La orden vale **3 h** (hasta W + 3 h). Si no se llena, se cancela y no hay operación.
- Se llena en el primer momento en que algún taker **vendió Sí (o compró No) a un precio estrictamente menor
  que B** (`p_si < B`). Si el precio de esa operación fue justo B, suponemos que había otros antes en la fila
  y no nos llenan (cuenta prudente, igual que `sombra_maker.py`). Precio de compra = B. Sin comisión (los makers
  no pagan; en temperatura hoy es 0 igual).
- Se informa aparte, sin decidir: B = precio en W (a la par del medio, más agresivo) y B = precio en W − 2 ¢.

## Salida

- Principal: **vender como taker a W + 6 h** (precio = mín(precio a W + 6 h − 1 ¢, mediana de lo que cobraron los
  vendedores en ±15 min), igual que `REGLA.md`). Se elige 6 h y no 3 h porque la orden puede llenarse hasta 3 h
  después de W y la deriva medida llega al menos hasta 6 h.
- Se informa también: salir a W + 3 h, salir 3 h después del llenado, y **salida como maker** (orden de venta a
  precio en W + 6 h + 1 ¢, válida 3 h, se llena si un taker compró Sí a más que eso; si no, venta taker a W + 9 h).
- Resultado por operación = (venta − compra) / compra.

## Comparación obligatoria

1. **Mismas señales, versión taker** (compra a precio en W + 1 ¢ o mediana de compradores; salida igual), para
   que la diferencia sea sólo entrar como maker.
2. **Selección adversa**: para las órdenes que NO se llenaron, cuánto subió el precio de W a W + 6 h, contra las
   que sí se llenaron. Si las que no se llenan son las que suben, el maker se queda sólo con las malas.
3. Tasa de llenado por tramo de precio (5–20, 20–40, 40–60 ¢) y por modelo.

## Criterio de éxito (todo tiene que cumplirse, con la entrada principal y la salida principal)

1. Ganancia media ≥ +2 % por operación llenada, t ≥ 2 (agrupado por evento), ≥ 150 operaciones llenadas.
2. Positiva en las dos mitades del período (por fecha).
3. Tasa de llenado ≥ 30 % (si no, por más que ande, no da para una ganancia constante).

Lectura:
- Cumple → vale anotar en vivo ~10 días desde Actions con libro real (sería estrategia nueva: se le consulta a
  Agus antes), y manda información al hilo de recompensas de liquidez.
- Cumple 1 y 2 pero no 3 → pocas operaciones; anotar igual pero como complemento de otra cosa.
- No cumple 1 → ser maker no arregla la señal de las corridas. Cerrar.

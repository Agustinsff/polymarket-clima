# Conclusiones (23-oct-2026)

**No hay ventaja.** Con precios que se podían operar, el promedio de 11 modelos (sesgo corregido) pierde un 3,5 %
el día anterior (h = 2, 2811 operaciones, 41 días) y un 4,6 % el mismo día a las 6 (h = 1, solo máximas).
GFS+ECMWF pierde algo más (−5,5 % y −4,4 %). El mercado pronostica mejor que los dos: Brier 0,060 contra 0,067 del
promedio a h = 2, y λ ("cuánto creerle al modelo por encima del precio") da −0,05, o sea nada.

- El veredicto "SÍ" de la regla fijada antes es **falso**: viene de precios que no existían. En las mínimas el día
  anterior, las cajas de un evento suman 2-4 en vez de 1, porque el "precio" histórico es el medio de un libro vacío
  (bid 1 ¢ / ask 66 ¢ → 33,5 ¢). "Comprar No" a 66 ¢ ahí era imposible. Filtrando esos momentos (cajas que suman
  0,90-1,15, filtro agregado después de ver resultados) la ganancia desaparece.
- Las mínimas casi no tienen libro el día anterior: con libro de verdad quedan 77 operaciones (−2 %).
- A 3 días (h = 3) hay un positivo (+38 %), pero son 79 operaciones en 15 días y con libros finos: es ruido o no se
  puede operar con tamaño. No alcanza para nada.
- El modelo mejorado sí pronostica mejor que GFS+ECMWF, pero el mercado ya lo sabe: ganarle al pronóstico del bot no
  es ganarle al precio. Coincide con Kelly (ventaja 0) y con el MOS de 9 modelos de antes.
- Costo medido de ejecución sobre el precio histórico: +0,6 ¢ en cajas baratas, +1,1 a +1,5 ¢ en el resto.

Lección para próximos backtests: antes de usar un precio histórico, chequear que las cajas del evento sumen ~1.

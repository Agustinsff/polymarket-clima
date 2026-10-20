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

## 4. ¿El mercado del mismo día está bien calibrado? (cajas todavía posibles, precio = última operación)
- Sí, y mucho. En todos los tramos de precio, el % de veces que gana la caja es casi igual al precio:
  - <2 ¢ ganó el 0,3 %;
  - 2–5 ¢, el 2,7 %;
  - 5–10 ¢, el 6,3 %;
  - 20–50 ¢ (precio medio 33,8 ¢), el 33,8 %;
  - 80 ¢ o más, el 96,1 %.
- Un pronóstico armado solo con el historial de la estación (cuánto sube después de las 12 o las 15 en los 75 días anteriores) es **peor que el mercado**: Brier 0,075 contra 0,048. Comprar colas con ese pronóstico perdió el 33 %.
- Dejar órdenes en el libro (maker) también pierde en casi todos los tramos: las que se llenan son las malas.
- **Única anomalía:** las cajas de **10–20 ¢** ganaron el 11,2 % (precio medio 14,2 %), en 1805 casos. Comprar su No dio ~+1,6 % y fue positivo a las 9, 12 y 15 hs y el día anterior. Puede ser casualidad, porque se probaron varios tramos, así que se valida en papel con la regla **no80_90** de `hoy.py`.
- Conclusión: el mercado ya incorpora el pronóstico del día. Para ganar hace falta un pronóstico **mejor que el del mercado** (lo mide `pronostico.py` / `hoy.py`) o más velocidad.

### 4b. La anomalía de 10–20 ¢, revisada (20-oct, más tarde)
- **Con el precio de venta real** (el último que se pagó al vender en la hora previa), dentro de la muestra (6–19 oct): bid medio 13,2 ¢, la caja ganó el 12,2 % y el ROI fue **+0,5 %**. Con 2 ¢ de diferencia entre compra y venta ya no se distingue de cero; con 3 ¢ es negativo.
- **Fuera de muestra** (9 días entre el 22-sep y el 5-oct; 723 mercados que no se habían mirado), en todas las horas: precio 14,4 %, ganó el 14,2 %, ROI **−1,6 %**. Ningún tramo de 5 a 30 ¢ es positivo.
- Con la regla exacta de `hoy.py` (máxima a las 12/15 y mínima a las 9) fuera de muestra: +1,6 % con 1 ¢ de deslizamiento y +0,6 % con el bid real. El intervalo de confianza incluye el cero holgadamente.
- **Conclusión:** no hay anomalía aprovechable. Era sobre todo el margen entre compra y venta más ruido. La regla `no80_90` queda solo como control en papel.

## 5. Ciudades nuevas (20-oct)
- Se agregaron Estambul (LTFM), Taipéi (RCSS), Tel Aviv (LLBG), Moscú (UUWW), Jinan (ZSJN), Zhengzhou (ZHCC) y Hong Kong (Observatorio, HKO).
- El METAR coincidió con la caja ganadora en **152 de 152** días (1 al 19-oct, máxima y mínima) en Estambul, Taipéi, Tel Aviv y Moscú.
- Zhengzhou: 2 de 2. Jinan es nueva y todavía no tiene días cerrados.
- Hong Kong resuelve con el Observatorio, no con un METAR, así que solo entra en el pronóstico del día anterior. No entra en el del mismo día ni en el cosechador.

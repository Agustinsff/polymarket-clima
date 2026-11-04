# Conversión °F/°C en las cajas de EE.UU.: regla de medición

Fijada el 4-nov-2026 ~14:00 UTC, **antes de mirar** frecuencias o precios (solo se hizo la cuenta aritmética de abajo y
se vio que las cajas de EE.UU. son pares par–impar de 2 °F, p. ej. 46-47°F). No se cambia después; cambios abajo con
fecha y motivo. Solo se mide; no toca pruebas en curso ni arma estrategia.

## Idea

Polymarket resuelve con el METAR de rutina: temperatura en décimas de °C (grupo T), y en EE.UU. la pasa a °F y redondea
(.5 hacia arriba). Cada caja de 2 °F junta 11 valores posibles de décimas de °C, salvo **una de cada nueve**, que junta
12: 28-29, 46-47, 64-65, 82-83, 100-101 °F (y −8/−7, 10-11). Si la temperatura real es suave, esas cajas "de 12" salen
≈ 12/11 = +9 % más seguido que sus vecinas. Si el mercado reparte el precio suave (como hace un modelo normal), esas
cajas quedan baratas ≈ 8 % de su precio.

## Prueba A: física (¿pasa en la realidad?)

Datos: `propio-datos/obs_diaria.csv.gz`, estaciones K* (EE.UU.), columna `max` y `min` (solo reportes de rutina),
desde 2023. Se pasa a °F con la regla de Polymarket y se cuenta cuántos días cae en cada caja de 2 °F.
Estadístico: para cada caja de 12 con días en ella y en sus dos vecinas, `log(n_caja / media geométrica de vecinas)`,
promediado; lo mismo para las cajas de 11 (control: la curvatura de la distribución afecta igual a las dos). Diferencia
esperada si es real: log(12/11) ≈ +0,087 (vecinas de 11). Bootstrap por estación-año. **Pasa** si la diferencia es
> 0 con P < 5 %.

## Prueba B: mercado (¿lo cobra el precio?)

Datos: fotos del libro del medidor maker (`medidor-maker/maker/datos`, precio medio, cada 5 min) en las cajas de EE.UU.
con las tres cajas (la de interés y sus dos vecinas) entre 2 y 98 ¢ en la misma foto. Mismo estadístico con los precios.
Bootstrap por evento. **El mercado lo cobra** si el intervalo del 95 % incluye la diferencia física medida en A y excluye
0; **lo ignora** si el intervalo excluye el valor de A.

## Prueba C: plata (solo informativa)

Con `regla_metar/datos/fotos.csv` (libro real, momentos M0/M1/M2) y `resultados.csv`: comprar 10 acciones del Sí de
cada caja de 12 al ask, con comisión 0,05·p(1−p) para todas las fotos. Se informa ROI y n. Con la muestra que hay
(≈ 2 semanas) no alcanza para decidir; no se arma prueba sin pedírselo a Agus.

## Qué decide

- A pasa y B "lo ignora": proponer al hilo del pronóstico propio que `prob_caja` cuente décimas de °C en vez de
  tratar la temperatura como continua (mejora gratis del modelo). La estrategia suelta (comprar cajas de 12) se
  evalúa con la aritmética: si la ventaja estimada (≈ 8 % del precio) no supera spread + comisión (≈ 2,5–3 ¢ a 30 ¢),
  no se propone.
- A no pasa, o B "lo cobra": se cierra.

# ¿Con qué información eligen las ganadoras? Reglas fijadas ANTES de mirar resultados (26-oct-2026)

Sigue a `ganadoras/` (PR #15): el 82 % de la ventaja de las ganadoras es qué caja eligen dentro de la celda. Pregunta
de Agus: qué detalles no estamos viendo. Acá se mide si esas elecciones coinciden con (a) el pronóstico de los modelos
antes del día y (b) la máxima/mínima que ya se registró durante el día. No opera nada.

## Datos
- Apuestas: `rivales/datos/` (30 días, takers), compras entre 5 y 90 ¢ hasta el fin del día medido. Mismas
  ganadoras que `ganadoras/` (elegidas con la primera mitad de fechas). **Todo lo de abajo se mide en la segunda
  mitad** (las apuestas que no se usaron para elegirlas).
- Pronóstico: `modelos/dias.csv.gz`, modelo "Promedio" (promedio de 11, corregido por sesgo de la serie con días
  previos). Horizonte 2 si la apuesta es más de 24 h antes del día, si no horizonte 1.
- Incertidumbre σ: desvío de (real − corregido) de esa serie y horizonte en los días **anteriores** (≥ 5); si no hay,
  la apuesta queda afuera.
- METAR: `metar_iem.csv.gz` de la rama `investigacion-velocidad`; temperatura del grupo T si está, si no la del cuerpo.

## Probabilidad del modelo para una caja
- Antes del día: T ~ Normal(corregido, σ). Caja °C "n": n−0,5 ≤ T < n+0,5. Caja °F "a-b": a−0,5 ≤ T°F < b+0,5.
  Puntas abiertas hacia el lado correspondiente.
- Durante el día (nowcast simple): m = máxima (o mínima) de los METAR del día local hasta 10 min antes de la apuesta.
  Final = max(m, T) para máximas, min(m, T) para mínimas, con el mismo T.
- p del lado: p si compra Sí, 1 − p si compra No. **Ventaja según el modelo** = p_lado − precio pagado.

## Medidas (mitad de prueba)
Por grupo (ganadoras / resto) y fase (antes / durante el día):
1. % del volumen con ventaja según el modelo > 0, y ventaja media ponderada por volumen.
2. PnL/vol de las apuestas a favor y en contra del modelo.
Lectura fijada: las ganadoras "usan esta información" si su % a favor supera al del resto en ≥ 10 puntos. Si no,
usan otra fuente que no tenemos.

## Regla mecánica (se corre siempre, descubrimiento y prueba por separado)
Horarios de decisión respecto del inicio del día local: −24, −12, −6 h (modelo) y +0, +3, +6, +9, +12 h (nowcast).
Para cada caja y lado con último precio operado entre 5 y 90 ¢: comprar US$10 si p_lado − precio ≥ 0,10.
Entrada: primera operación real de cualquiera comprando ese lado dentro de 120 min, +1 ¢. Hasta la resolución.
**Pasa** si en la prueba da PnL/vol ≥ +3 %, el límite inferior del intervalo de 90 % (bootstrap por evento) > 0 y
las dos mitades de la prueba son positivas. Se informa por separado antes del día y durante el día; pasa cualquiera
de las dos con el criterio corregido a 95 % (dos intentos).

## Extra descriptivo
PnL/vol y % a favor del modelo de las ganadoras por país (EE.UU. / resto), para ver si ganan más donde hay modelos
locales de alta resolución que no tenemos (HRRR, NBM).

## Cambios
(ninguno)

# ¿Qué cambió con la comisión nueva en temperatura? Regla de medición

Fijada el 4-nov-2026 ~13:35 UTC, **antes de analizar** los datos (solo se vio que la columna `tasa` existe en
las fotos del medidor maker). No se cambia después; cualquier cambio va abajo con fecha y motivo.
Solo se mide. No toca ninguna prueba en curso.

## Hecho

En gamma, los mercados de temperatura de eventos hasta el 31-oct-2026 tienen `feeSchedule` rate 0 y
rebateRate 0; desde los eventos del 1-nov (creados desde el 30-oct 06:55Z), rate 0,05 y rebateRate 0,25.
Taker paga `0,05 · acciones · p · (1 − p)`; el maker que lo llena cobra el 25 % de eso.

## Datos

Los del medidor maker (rama `medidor-maker`, `maker/datos/`): fotos cada 5 min desde el 26-oct y llenados
simulados con resolución. Grupo **sin comisión** = eventos con fin 26-oct a 31-oct; **con comisión** = eventos
desde el 1-nov (lo que esté resuelto o con fotos al momento del corte). Cripto (comisión 0,07 en todo el
período) sirve de control de cambios generales del mercado.

## Qué se mide

Siempre por tipo (máximas / mínimas) y por tramo de horas hasta el fin del evento (0–12, 12–24, 24–36, 36–48),
con cajas de precio medio entre 3 y 97 ¢:

1. **Spread** del libro (ask − bid) mediano por caja-foto.
2. **Competencia**: puntaje de rivales en la zona de recompensa (`comp`) y pozo por caja (`pozo`).
3. **Llenados** de la orden simulada a 1 y 2 ¢ del medio: llenados por caja-día y resultado a la resolución
   por acción (sin reembolso y con reembolso).
4. **Neto maker** por US$ 100 de capital por día en cajas apretadas (spread ≤ 5 ¢, orden a 2 ¢), con la misma
   cuenta del informe maker del 2-nov, antes y después, sumando el reembolso.

Diferencia = con comisión − sin comisión, emparejada por ciudad y tipo (promedio de las diferencias por ciudad).
Intervalo: bootstrap 2.000 veces por fecha de evento.

## Qué decide

- **Cambió el spread** si la diferencia mediana es ≥ 1 ¢ en los tramos 12–48 h y el intervalo del 95 % no
  cruza 0, y cripto no se movió en la misma dirección más de la mitad de eso.
- Para el viernes 6-nov (decisión maker): el número que importa es el punto 4. Si el neto con comisión
  es mayor que sin comisión, la comisión ayuda al maker; si es menor (más selección adversa, menos takers),
  baja la expectativa de la prueba real.
- Muestra mínima: 3 fechas de evento con comisión. Con menos, se informa pero se dice que no alcanza.

## Límites

- Pocos días con comisión (1-nov a 4-nov) y sin días repetidos: los cambios del mercado en la misma semana
  (clima, nuevas ciudades) se mezclan con la comisión. Por eso el control cripto y el emparejado por ciudad.
- Llenados son simulación prudente (ver `maker/REGLA.md`).

## Cambios después de fijada la regla

- 4-nov-2026 13:45Z, después de la primera corrida: el chequeo de coherencia mostró que la tasa **no** depende de la
  fecha del evento sino de la hora: todas las cajas abiertas pasaron de 0 a 0,05 entre las fotos de 04:35Z y 04:40Z
  del 1-nov-2026 (incluidas las del 31-oct, 1-nov y 2-nov que ya estaban abiertas). Se cambia la división: **sin** =
  fotos antes del 1-nov 04:37Z, **con** = después; el bootstrap remuestrea pares (fecha de evento, sin/con). El control
  cripto se parte a la misma hora. También se corrigió un error de cuenta: la recompensa por foto ya es US$/día (no se
  multiplica por 288). Los criterios de decisión no cambian.

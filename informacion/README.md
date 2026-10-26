# ¿Con qué información eligen las ganadoras? (26-oct-2026)

Reglas fijadas antes: `REGLAS.md`. Tablas: `informe.md`. Para repetir:
`python informacion/analisis.py RUTA/rivales/datos RUTA/velocidad/datos/metar_iem.csv.gz`
(datos crudos en las ramas `investigacion-rivales` e `investigacion-velocidad`; ~1 min). No opera nada.

## Conclusión: usan información que nosotros no tenemos, y es mejor que nuestro modelo.

- **Antes del día no siguen a nuestro modelo** (promedio de 11 corregido): 48 % de su volumen va a favor del modelo,
  contra 53 % del resto. Y donde más ganan es **yendo en contra del modelo: +14,3 %** (a favor: −0,3 %).
  O sea: donde nuestro modelo y el precio no coinciden, ellas saben quién tiene razón, y casi siempre no es el modelo.
- **Durante el día** el nowcast simple (máxima registrada + pronóstico) explica poco: ganadoras 51 % a favor vs 45 % del
  resto (+7 puntos, menos que los 10 fijados). Ganan +9 % igual a favor o en contra.
- EE.UU. no es donde más ganan (+5 % / +6 %); ganan más en el resto del mundo (+8 % / +10 %).
- Regla mecánica (comprar si el modelo ve ≥ 10 puntos de ventaja, al precio real siguiente +1 ¢): antes del día
  +9,3 % en descubrimiento pero **−2,3 %** en prueba; durante el día −5,9 % / **−11,4 %**. No pasa.

Lectura: su ventaja es un pronóstico mejor que el nuestro (o información local), no un patrón del mercado.
Para competir habría que conseguir esa fuente; con los modelos globales públicos no alcanza.

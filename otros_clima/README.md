# Otros mercados de clima más lentos (idea 4, 26-oct-2026)

Pregunta: ¿hay mercados de clima de Polymarket fuera de la temperatura diaria (anomalía global del mes, lluvia,
nieve, tornados, huracanes, hielo ártico, El Niño) donde un dato público casi en tiempo real adelante la
resolución lo suficiente como para ganar con estadística y no con velocidad?

**Conclusión: no vale la pena.** No hay nada que medir en vivo. Razones, de más a menos fuerte:

1. **El volumen se cayó.** La anomalía global del mes movía US$ 1–5 M por mes en 2025; en 2026 bajó a
   US$ 200 k–1 M en el primer semestre y a US$ 3–90 k desde junio (septiembre 2026: US$ 11 k en toda su vida).
   Lluvia mensual por ciudad: US$ 5–90 k por mes y ciudad. Tornados del mes: US$ 4–34 k. El libro de los abiertos tiene
   spread de 1–5 ¢ (sólo market makers), pero detrás hay muy poca gente con quien operar.
2. **Donde el dato público adelanta la resolución, el precio ya lo tiene.** Lluvia: el día 1 del mes siguiente la
   caja ganadora ya está a 99 ¢ (mediana, 40 eventos) y después del fin de mes se compraron apenas US$ 22 por evento
   por debajo de 95 ¢. Nieve y tornados: 97–99 ¢ al día siguiente del fin del período.
3. **Donde todavía hay incertidumbre (anomalía global entre fin de mes y la publicación de NASA, la caja ganadora
   sigue en ~55 ¢), el mercado sabe más que el dato público.** El ERA5 diario de Copernicus (sale con 2 días de demora)
   adelanta a GISTEMP con un error típico de 0,045 °C, y las cajas miden 0,05 °C: informa, pero no decide. Comparado
   en el momento H3 (mitad de camino entre fin de mes y el cierre), el modelo ERA5 tiene Brier 0,135 contra 0,092 del
   mercado (36 cajas), y la regla "comprar si el modelo da 10 puntos más" pierde −55 % (21 operaciones, P(ROI<0) 0,99).
   Lo más probable es que haya quien replica GISTEMP con GHCN + ERSST antes de que NASA publique.
4. **No hay mal calibración clara.** En los tres momentos (F−7 d, F, mitad hacia el cierre) las cajas ganan más o
   menos lo que dice su precio; las tres reglas mecánicas tienen muy pocas operaciones (5–25 por momento, porque en
   la hora previa casi no se opera) y ninguna da positivo con comisión y 1 ¢ en dos familias a la vez.
5. Huracanes, hielo ártico y El Niño son mercados de temporada (uno o dos eventos por año), con muestra para nada.

## Qué hay en la carpeta
- `REGLA.md`: la regla fija, escrita antes de mirar precios y operaciones.
- `bajar.py` (GitHub Actions, workflow `otros_clima`, sólo en la rama `otros-clima`): mercados, libro actual,
  historia de precios y operaciones taker (hasta 4000 por mercado, las más recientes).
- `fuentes.py`: GISTEMP, ERA5 diario (Climate Pulse), NOAA global, NSIDC, lluvia diaria de IEM.
- `analizar.py` → `informe_datos.md` con todas las tablas.

## Cuidados
- El tope de 4000 operaciones por mercado corta los mercados grandes de 2024–2025 (los momentos H1/H2 de esos
  pueden no tener operaciones); no cambia la conclusión, que se apoya en 2026.
- El precio de ejecución es el de la hora anterior a cada momento: pocos mercados tienen operaciones ahí.
- Los datos crudos quedan sólo en la rama `otros-clima`, no en `main`.

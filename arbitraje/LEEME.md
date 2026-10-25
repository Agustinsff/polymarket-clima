# Arbitraje de precios que no suman 1

Investigación del 24–25 oct 2026. Solo mide; no opera ni toca las pruebas en papel.

- `REGLA.md`: regla de medición, fijada antes de ver datos.
- `medir.py`: foto del libro cada 10 s (temperatura, top-40 negRisk, 20 binarios); corre en Actions (`arbitraje.yml`, al empujar a la rama `arbitraje`).
- `analizar.py`: resumen → `informe_datos.md` y `resumen.json`.
- `informe.html`: informe (también en https://claude.ai/artifact/UFjrfgo6DRMUvNByvLE3ZV).
- Los datos crudos (`datos/fotos_*.csv.gz`) quedan solo en la rama `arbitraje`.

Conclusión: no vale la pena. En temperatura, 5 oportunidades en 6 h por US$ 11 en total, duración mediana 20 s, nada dura 15 min.
Depende solo de velocidad. Sí+No de un binario no puede sumar menos de 1 (el libro del No es espejo del Sí).

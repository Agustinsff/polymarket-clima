# Velocidad sobre el METAR (investigación, 23-oct-2026)

¿Vale la pena un bot que compre "No" (o venda "Sí") en la caja que un METAR acaba de matar, antes que los demás?
No opera nada.

- `vivo.py`: mira aviationweather.gov cada ~4 s (y el archivo de ciclo de tgftp cada 10 s). Cuando un METAR de rutina
  mata una caja, anota el libro real del Sí a los 0 s, 10 s, 30 s, 1, 2, 5 y 15 min, y las operaciones de ese mercado.
- `bajar_metar.py`: historia de METAR de las estaciones, con la hora de publicación de aviationweather (`receiptTime`)
  y la de IEM (30+ días).
- `analizar.py`: cruza todo con las operaciones de la investigación de rivales (rama `investigacion-rivales`).
- Workflow `velocidad.yml`: corre una vez por push a la rama `investigacion-velocidad` (~5 h 30 min) y guarda ahí.

# Rivales en mercados de temperatura (investigación, 23-oct-2026)

Quién gana del otro lado, cuándo entra y qué tan rápido se mueve el precio después de cada corrida de GFS/ECMWF.
No opera nada.

- `bajar.py`: baja eventos, operaciones y precios por minuto de Polymarket. Corre en GitHub Actions
  (`rivales.yml`, se dispara con un push a la rama `investigacion-rivales`, en 6 tramos en paralelo).
- `analizar.py`: arma las tablas (`informe_datos.md`) y `billeteras.csv` (las 12.545 billeteras con PnL, estilo y horario).
- Los datos crudos (~350 MB) quedan sólo en la rama `investigacion-rivales`, en `rivales/datos/`, para no inflar `main`.

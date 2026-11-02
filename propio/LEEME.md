# Pronóstico propio de temperatura

Objetivo: un pronóstico de máxima/mínima por estación, ajustado con el historial de error de cada
modelo en esa estación (post-procesamiento tipo MOS/EMOS), para las 47 estaciones con mercado en
Polymarket. Plan acordado con Agus el 2-nov-2026:

1. **Datos** (`datos.py`, workflow `propio`, todos los días 05:40 UTC). Los datos van a la rama
   `propio-datos`, no a main.
2. Modelo por estación.
3. Validación contra los precios del mercado guardados (Brier). Si no le gana por 3–5 puntos, se cierra.
4. Prueba en papel 2–3 semanas (con avisos ntfy).

## Qué hay en la rama `propio-datos`

| Archivo | Qué es |
|---|---|
| `obs/{ICAO}.csv.gz` | Cada METAR desde ene-2023 (IEM): hora UTC, rutina (R) o SPECI (S), temperatura, si vino del grupo T (décimas) o del cuerpo (entero). |
| `obs_diaria.csv.gz` | Máxima y mínima de cada día local: con la regla de hoy (solo rutina) y con la vieja (rutina + SPECI, hasta el 22-oct-2026). Hong Kong: dato oficial del Observatorio. |
| `pron/{ICAO}.csv.gz` | Máxima/mínima del día local según cada modelo de Open-Meteo, corrida del mismo día (h=0) y de 1, 2 y 3 días antes. |
| `mos/{ICAO}.csv.gz` | Solo EE.UU.: pronósticos oficiales por estación archivados por IEM (NBS/NBE = NBM, GFS/MEX = MOS de GFS, NAM). `n_x` = máx/mín en °F. |
| `estado.json`, `log.txt` | Qué se bajó y qué falta; registro de la última corrida. |

## Qué se aprendió de las fuentes (2-nov-2026)

- **Open-Meteo "previous runs"**: los horizontes 1–3 días existen desde ~jul-2024 (GFS desde antes,
  ECMWF-IA desde ~jul-2025, ECMWF 9 km recién desde 2026). Antes solo está la corrida del mismo día,
  por eso los pronósticos se bajan desde jun-2024. h=0 es la corrida más nueva para cada hora, casi
  una observación: no representa lo que se sabía a la hora de operar.
- Modelos que sirven en las 47 estaciones: ECMWF (3 versiones), GFS, ICON, UKMO, Météo-France, GEM,
  JMA, CMA, DMI, KNMI, MET Norway, best_match. HRRR y NBM: las 12 de EE.UU. ICON-EU 11, JMA-MSM 6,
  AROME 5, ICON-D2 4, UKMO 2 km 3, MeteoSwiss 2. Sin historia: KMA, BOM, GraphCast.
- Cupo de Open-Meteo gratis: ~8.000 por día; un mes de las 47 estaciones cuesta ~1.600. La historia
  completa tarda ~4 días en bajar.
- IEM MOS tarda ~10 s por pedido; se bajan 4 estaciones a la vez.

# polymarket-clima

👉 **[Ver el RESUMEN del día](RESUMEN.md)**: estado de las tareas, resultados, prueba de São Paulo, cosechador y liquidez. Se actualiza solo cada 15 minutos.

Experimentos **en papel**, sin dinero real, con los mercados de temperatura de Polymarket (Buenos Aires y São Paulo).
Todo corre solo en GitHub Actions, así que no hace falta tener ninguna PC prendida.

## Qué corre y cuándo (hora de Montevideo)

| Tarea | Cuándo | Qué hace | Archivo |
|---|---|---|---|
| `diario` (lo dispara `reloj`) | 10:05 y 20:05 | Anota los mercados de mañana frente al modelo y completa los resultados de ayer | `registro.csv`, `resultados.csv` |
| `liquidez` (lo dispara `reloj`) | cada 15 min | Foto del libro de órdenes y recompensas estimadas por dar liquidez | `liquidez.csv` |
| `papel_sp14` (lo dispara `reloj`) | 14:12 (reintenta hasta 14:50) | Prueba en papel "São Paulo 14 hs" (regla fija, no se cambia) | `papel_libro.csv`, `papel_operaciones.csv` |
| `cosechador` | siempre (corridas de ~5 h 40 min encadenadas) | Cosechador **en papel** multi-ciudad: "compra" el No de cajas que ya son imposibles cuando alguien todavía paga ≥3 ¢ por el Yes | `cosecha.csv` |
| `multi` (dentro del reloj) | 10:20 y 20:20 | Pronóstico vs. mercado del día siguiente en **todas las ciudades**, con operaciones simuladas *taker* y *maker* | `pronostico.csv`, `pronostico_ops.csv`, `pronostico_estado.json` |
| `sombra_maker` (dentro del reloj) | 10:20 y 20:20 | Qué hubiera pasado si el cosechador y la prueba SP dejaban la orden en el libro en vez de comprar al toque | `sombra_maker.json` |
| `cosechador` | siempre (cadena) | Cajas imposibles en todas las ciudades; anota cada caja que "muere" | `cosecha.csv`, `cosecha_muertas.csv` |
| `carrera` | 08:00-13:50 y 14:00-19:50 | Carrera de fuentes: qué fuente publica primero cada METAR de Ezeiza | `carrera.csv` |

**`reloj`**: corre 24/7 en tandas encadenadas de ~5 h 40 min y lanza liquidez, diario y papel_sp14 en su horario. Los horarios automáticos de GitHub resultaron poco confiables.

Resumen del cosechador: `python cosechador.py resumen`.

Para correr una tarea a mano: pestaña **Actions** → elegir la tarea → **Run workflow**.
Para pausar una tarea: **Actions** → la tarea → menú `...` → **Disable workflow**.

## Archivos de datos fijos
- `historial_sesgo.csv`, `metar_cache.json`, `calibracion.json`: historial del modelo (13-oct-2026).
- `mos_ba.json`: modelo de 9 modelos de Ezeiza.
- `estaciones.py`: zona horaria de cada ciudad, estaciones excluidas y peculiaridades (ver `estaciones_informe.md`).
- `estaciones.json`: coordenadas de cada estación (se completa sola).

El estado de todo está en **[RESUMEN.md](RESUMEN.md)**.

## Aviso
Es un experimento personal. No es una recomendación financiera y no compra nada.

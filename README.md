# polymarket-clima

Experimentos **en papel**, sin dinero real, con los mercados de temperatura de Polymarket (Buenos Aires y São Paulo).
Todo corre solo en GitHub Actions, así que no hace falta tener ninguna PC prendida.

## Qué corre y cuándo (hora de Montevideo)

| Tarea | Cuándo | Qué hace | Archivo |
|---|---|---|---|
| `diario` | 10:05 y 20:05 | Anota los mercados de mañana frente al modelo y completa los resultados de ayer | `registro.csv`, `resultados.csv` |
| `liquidez` | cada 15 min (GitHub a veces se atrasa) | Foto del libro de órdenes y recompensas estimadas por dar liquidez | `liquidez.csv` |
| `papel_sp14` | 14:11 (con reintentos) | Prueba en papel "São Paulo 14 hs" (regla fija, no se cambia) | `papel_libro.csv`, `papel_operaciones.csv` |
| `carrera` | 08:00-13:50 y 14:00-19:50 | Carrera de fuentes: qué fuente publica primero cada METAR de Ezeiza | `carrera.csv` |

Para correr una tarea a mano: pestaña **Actions** → elegir la tarea → **Run workflow**.
Para pausar una tarea: **Actions** → la tarea → menú `...` → **Disable workflow**.

## Archivos de datos fijos
- `historial_sesgo.csv`, `metar_cache.json`, `calibracion.json`: historial del modelo (13-oct-2026).
- `mos_ba.json`: modelo de 9 modelos de Ezeiza.

## Aviso
Es un experimento personal. No es una recomendación financiera y no compra nada.

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
| `hoy` (dentro del reloj, cada 15 min) | 12:00 y 15:00 locales de cada ciudad (máxima), 09:00 (mínima) | Pronóstico del mismo día usando lo que ya marcó la estación, con operaciones simuladas | `hoy.csv`, `hoy_ops.csv` |
| `cripto` (dentro del reloj, cada 15 min) | a 48/24/12/6/3/1 h del cierre | Mercados "Bitcoin/Ethereum above" vs. modelo de opciones (Binance + Deribit), en papel | `cripto.csv`, `cripto_ops.csv` |
| `sombra_maker` (dentro del reloj) | 10:20 y 20:20 | Qué hubiera pasado si el cosechador y la prueba SP dejaban la orden en el libro en vez de comprar al toque | `sombra_maker.json` |
| `cosechador` | siempre (cadena) | Cajas imposibles en todas las ciudades; anota cada caja que "muere" | `cosecha.csv`, `cosecha_muertas.csv` |
| `carrera` | 08:00-13:50 y 14:00-19:50 | Carrera de fuentes: qué fuente publica primero cada METAR de Ezeiza | `carrera.csv` |
| `reglas` | cada 3 h | Saca una huella de cada familia de mercados (fuente de resolución, comisión, orden mínima, texto del reglamento, ciudades, mercados de clima nuevos) y anota lo que cambia. Los cambios de las últimas 48 h salen arriba de RESUMEN.md y el vigía los manda por mail | `reglas_cambios.csv`, `reglas_informe.md`, `reglas_estado.json` |
| `vigia` | cada hora y al terminar cada tanda del reloj o del cosechador | Si algo dejó de andar, abre un aviso (issue con la etiqueta `alerta`) y GitHub te manda un mail. Lo cierra solo cuando todo vuelve a la normalidad | (no guarda datos) |

**`reloj`**: corre 24/7 en tandas encadenadas de ~5 h 40 min y lanza liquidez, diario y papel_sp14 en su horario. Los horarios automáticos de GitHub resultaron poco confiables.

**Avisos**: si un script falla, el reloj lo anota en `fallas.json` y aparece arriba de todo en RESUMEN.md. El `vigia` junta eso, los atrasos (liquidez, monitor, prueba SP, cosechador) y las corridas que terminaron en error, y te avisa por mail a través de un issue. Para dejar de recibirlos: **Actions** → `vigia` → **Disable workflow**.

**Comisiones**: desde el 23-oct-2026 cada operación en papel anota en `tasa_comision` la tasa de comisión que trae su mercado (`feeSchedule` de Polymarket: hoy 0 en temperatura y 0.07 en cripto). Las operaciones anteriores quedan con 0.05, que era lo que suponíamos para todo. RESUMEN.md muestra al lado cuánto daría cada prueba con 0.05 para todo.

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

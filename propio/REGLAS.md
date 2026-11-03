# Pronóstico propio: reglas fijas de los pasos 2 y 3

Escritas el 3-nov-2026, **antes de ajustar ningún modelo y antes de mirar cómo le va contra el mercado**.
No se cambian después de ver resultados. Si hace falta cambiar algo, se escribe una versión nueva con
fecha y motivo, y la validación vuelve a empezar con días nuevos.

## Qué se pronostica

- La máxima y la mínima de cada día local en cada una de las 47 estaciones (`propio/estaciones.json`).
- Lo "real" es lo que usa Polymarket hoy: el máximo/mínimo de los METAR **de rutina** del día local
  (`max`/`min` de `obs_diaria.csv.gz`), en décimas si el METAR trae el grupo T. Hong Kong: el dato
  oficial del Observatorio. Se usa la regla de rutina también para los días viejos (aunque antes del
  23-oct contaban los SPECI), porque es la regla con la que se va a operar.
- Días con menos de 12 METAR de rutina no se usan.

## Paso 2: el modelo

**Datos de entrada**, solo los que existían al momento de pronosticar:
- Pronósticos de cada modelo de Open-Meteo con horizonte 1 o 2 días (`pron/`). El horizonte 0 no se
  usa: es casi una observación.
- En EE.UU., además, NBM y MOS de GFS (`mos/`), de corridas iniciadas antes del momento de operar.
- El error pasado de cada modelo en esa estación, solo con días ya terminados.

**Candidatos** (lista cerrada):
- **M0, promedio corregido**: promedio de todos los modelos disponibles, menos el sesgo medio de los
  últimos 30 días de esa estación, serie y horizonte. El ancho (desvío) es el error cuadrático de esos
  mismos 30 días. Es lo que ya medimos en `modelos/`: sirve de base.
- **M1, EMOS**: la media es una combinación lineal de los modelos (con pesos aprendidos, con
  regularización para que ningún modelo se lleve todo), y el desvío depende de cuánto discrepan los
  modelos entre sí. Se ajusta por estación, serie y horizonte, con los últimos 120 días más la misma
  época (±45 días) de los años anteriores. Se reajusta cada día con datos hasta el día anterior.
- **M1-EEUU**: igual que M1, sumando NBM y MOS como entradas, solo en las 12 estaciones de EE.UU.

**Cómo se elige**: un solo método para todas las estaciones (elegir por ciudad no funcionó en
`modelos/`). Gana el de menor CRPS (error de la distribución completa, la medida estándar) entre el
1-oct-2025 y el 30-sep-2026. Si M1 no le gana a M0 por al menos 2 %, se usa M0. Nada de este paso mira
precios de mercado.

**De temperatura a probabilidad por caja**: la distribución normal del modelo se integra sobre cada
caja con la regla de Polymarket (redondeo al entero, .5 hacia arriba; en °F se convierte antes y las
cajas son de 2 °F; las cajas de los extremos "o menos" / "o más" se llevan las colas). Donde el METAR
solo trae enteros, se integra entre k−0,5 y k+0,5.

## Paso 3: validación contra el mercado

Se compara con los precios que guardaron los bots, con libro real:

- **Prueba A (principal), mismo día**: máximas, la foto de `hoy.csv` de las 9 de la mañana local,
  contra el modelo con horizonte 1 día. (El mercado a esa hora ya sabe la temperatura de la mañana y
  nosotros no: la comparación nos juega en contra.)
- **Prueba B, día anterior**: máximas y mínimas, la última foto de `pronostico.csv` del día anterior,
  contra el modelo con horizonte 2 días (así no usamos ninguna corrida que todavía no existiera).
- Precio del mercado = punto medio entre compra y venta de cada caja, normalizado para que el evento
  sume 1. Solo eventos con todas las cajas y puntos medios que sumen entre 0,90 y 1,15 (lección de
  `historico/`). Se excluyen las estaciones de `EXCLUIR` de estaciones.py.
- Días: desde el 22-oct-2026. Se evalúa con un mínimo de 15 días y 300 eventos por prueba; si no
  llega, se espera.

**Pasa si, en la prueba A o en la B:**
1. El Brier del modelo (suma sobre las cajas del evento) es al menos **3 % menor** que el del mercado, y
2. remuestreando por días (bootstrap, 10.000 veces), la probabilidad de que el modelo **no** sea mejor
   es menor a 2,5 % (2,5 % y no 5 % porque hay dos pruebas), y
3. una simulación de compras como taker da ROI positivo: comprar 1 acción de cada caja donde la
   probabilidad del modelo supera el precio de compra (ask) más la comisión por al menos 3 ¢, al ask
   real de la foto, con la comisión real del mercado (si no está anotada, 0,05·p·(1−p)).

**Si no pasa**: se cierra acá, sin prueba en papel, y queda escrito por qué.
**Si pasa**: paso 4, papel 2–3 semanas con estas mismas reglas y avisos por ntfy; recién después se
habla de plata real.

## Además (informativo, no decide)

- Cuánto le gana el modelo al mercado por estación, por serie y por horizonte.
- Si combinar modelo y mercado mejora al mercado solo (peso del modelo en una mezcla).
- La misma comparación contra los precios históricos de `historico/` (41 días, menos confiables).

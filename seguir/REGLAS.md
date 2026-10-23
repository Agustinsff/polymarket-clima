# Seguir billeteras ganadoras: reglas fijadas ANTES de mirar resultados (23-oct-2026)

Estas reglas se escriben y se suben antes de correr `seguir/backtest.py`. Si después se cambia algo, se anota abajo
con fecha y motivo, y el resultado con las reglas originales se sigue mostrando.

## Datos
Los de la investigación de rivales (rama `investigacion-rivales`, `rivales/datos/`): 30 días de operaciones taker
de todos los mercados de temperatura cerrados (21-sep a 23-oct). Comisión: 0 (tasa real de temperatura).

## Selección (sólo con el pasado: walk-forward)
Para cada día de prueba D (día UTC), se mira sólo lo que ya estaba resuelto: operaciones de eventos con fecha ≤ D−2
y hechas antes del inicio de D. Los primeros 10 días son sólo historia; se prueba desde el día 11.

Cuentan como "apuesta de pronóstico/lectura": compras (o ventas, pasadas a compra del lado contrario a 1−p) a precio
entre 5¢ y 90¢, antes de que termine el día medido. Las de ≥90¢ (cosecha) no cuentan.

Una billetera queda elegida para el día D si, en esas apuestas:
- tiene ≥ 20 eventos distintos,
- t ≥ 2,5 (PnL medio por evento / error estándar),
- PnL/volumen ≥ +3%.
Se toman como máximo las 50 de mayor t.

## Señal y copia
- Señal: la primera apuesta (definición de arriba, de ≥ US$20) de una billetera elegida en cada lado de cada caja
  durante el día D. Agregar más a la misma posición no genera otra señal.
- Copiamos US$10 en el mismo lado y nos quedamos hasta la resolución.
- Precio de entrada con latencia L: el precio de la primera operación de OTRA billetera en la misma dirección
  (comprar ese lado), hecha a partir de T+L y antes de T+L+120 min, **más 1¢** (no vemos el libro histórico; la
  operación de otro es un precio que se llenó de verdad, el 1¢ cubre profundidad y ruido). Si no hay, no se copia.
- No se copia si ese precio pasa 95¢ o supera en más de 10¢ el precio de la billetera (límite).

## Medida principal (decidida ahora)
- **L = 15 min** (lo que se puede lograr hoy con GitHub Actions consultando data-api cada pocos minutos).
  También se muestran L = 0 (el precio de ellos, techo teórico), 1, 5 y 60 min.
- PnL/volumen en todos los días de prueba, intervalo del 90% con bootstrap por evento, y t por día.
- **Pasa** si PnL/volumen ≥ +2% y el límite inferior del intervalo es > 0, con L = 15.
- Comparación: lo mismo copiando billeteras al azar con ≥ 20 eventos (sin filtrar por ganancia), y la
  mitad 1 vs mitad 2 de los días de prueba por separado (que no dependa de una semana).

## Velocidad (investigación aparte, no estrategia)
Medir, en las operaciones durante el día (<90¢), cuánto gana el que entra en cada tramo de minutos después de la hora
en punto (:00–:01, :02–:04, :05–:09, :10–:29, :30–:59), para ver si queda algo para alguien que ve el METAR a los ~4 min
(nuestra mejor fuente gratis, `carrera.py`: mediana 250 s).

## Cambios
(ninguno)

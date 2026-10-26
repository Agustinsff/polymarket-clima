# Up or Down de cripto: estudio histórico (26-oct-2026)

Regla fijada antes de bajar datos: `REGLA.md`. Datos: `bajar.py` (corre en Actions, workflow `updown.yml`,
rama `updown`) → `datos/*.json.gz`. Análisis: `python updown/analizar.py` → `resultados.md`, `resumen.json`.

## Qué son
Mercados "Up or Down" de BTC/ETH (también SOL, XRP, DOGE…) en ventanas de 5 min, 15 min, 1 h, 4 h, 1 día.
Up si el precio al final de la ventana ≥ al del inicio. Los de 5/15 min y 4 h resuelven con el TWAP de Chainlink;
los de 1 h y 1 día con la vela de 1 min de Binance. Comisión taker 0,07·p·(1−p) (≈1,75 ¢ a 50 ¢, 0,9 ¢ a 85 ¢),
20 % vuelve a los makers. Volumen mediano por mercado: BTC 1 h US$ 26 k, ETH 1 h US$ 3,7 k, BTC 15 min US$ 24 k,
BTC 1 día US$ 150 k.

## Datos
60 días (27-ago a 26-oct-2026): BTC y ETH en 1 h (1.439 c/u), 4 h (360 c/u), 1 día (60 c/u); BTC 15 min 3 días (288).
19.842 fotos del precio del Up en 5 momentos de cada ventana (10/25/50/75/90 %).

## Resultado con la regla fija
- Deriva: Up resuelve 50–53 % de las veces. Nada que explotar.
- Calibración: el mercado está bien calibrado en el medio (30–70 ¢: desvíos de ±2 ¢). En los extremos tarde en la
  ventana aparece el sesgo clásico: las colas a 10–30 ¢ ganan **menos** de lo que dice el precio (−3 a −6 ¢) y
  los favoritos a 70–90 ¢ ganan **más** (+4 a +7 ¢). A 90–100 ¢ no hay nada (sin margen).
- De las 109 combinaciones regla×momento×ventana prefijadas pasan el criterio 3, que es lo que pasa por azar con
  109 pruebas al 5 %. Las "cola" pierden en todos lados (−15 a −60 %). "Cincuenta" da ≈ −comisión (control OK).
  Los "favorito" dan +0,5 a +1 % con 1 ¢ de costo extra, demasiado chico para una regla tan amplia.
- **Veredicto con la regla fija: no se encontró una regla simple que pase.**

## Agregado después de ver los datos (no cuenta como hallazgo; es la hipótesis para probar en vivo)
Comprar el lado que está a **70–90 ¢ cuando pasó el 90 % de la ventana de 1 h** (6 min antes del cierre):
545 ops en 61 días (≈ 9 por día), ganó 87 %, ROI +4,8 % con comisión y 1 ¢ extra (+3,6 % con 2 ¢), P(≤0) = 0,005,
positivo en las dos mitades y en BTC (+74) y ETH (+140). Neto US$ 215 en 61 días con 10 acciones (US$ 3,5/día).
Por qué puede ser real: es el sesgo de las colas (la gente paga de más por la chance de que se dé vuelta en 6 min).
Por qué puede no serlo: salió mirando las tablas; el precio histórico es último pago, no el ask; a 6 min del cierre
el libro se mueve rápido y la mitad de la plata está en ETH, cuyos mercados de 1 h mueven solo US$ 3,7 k.

# Medidor de recompensas maker: veredicto final (9-nov-2026)

Medición en papel del 26-oct al 9-nov-2026. La regla está fija en [REGLA.md](REGLA.md) y los números en
[informe_datos.md](informe_datos.md). El informe lo genera `analizar.py`, que lee `maker/datos/` (210 MB, solo en
la rama `medidor-maker`). Pregunta: ¿dejar órdenes maker en las cajas de temperatura que Polymarket premia da una
ganancia chica y constante, sumando recompensa y reembolso y restando lo que se pierde cuando nos llenan?

## Veredicto

**Pasa la regla, por poco, y solo en libros apretados.** Con libros de spread ≤ 5 ¢, órdenes a 2 ¢ del medio y la
recompensa pesimista (los rivales nos copian), el neto es **≈ +0,6 US$/día por cada US$ 100** en los 8 días completos
con llenados medidos (t ≈ 2,1). La regla pedía t > 2 con al menos 7 días completos y menos de US$ 2.000 de capital
para ganar US$ 5/día; da unos US$ 800.

| | corte 2-nov | corte final 9-nov |
|---|---|---|
| días completos con llenados | 7 | 8 (27-oct → 2-nov y 8-nov) |
| neto pesimista por US$ 100 y día | +1,1 | +0,6 (t ≈ 2,1) |
| pozo de clima | ≈ US$ 10.800/día | ≈ US$ 10.700/día en ~460 cajas |
| resultado de los llenados a la resolución | −4,7 ¢/acción | −4,6 ¢/acción a 1 ¢, −5,2 a 2 ¢ (t ≈ −20) |

**Ojo con el +2,18 (t 4,5) de la sección 7 del informe.** Ese número está inflado: incluye del 3 al 7-nov, días en que
el medidor no registró llenados porque Polymarket retiró la API vieja (data-api v1, ~2-nov; arreglado 7-nov). Esos
días suman recompensa sin restar pérdidas. Sacándolos, por día y por US$ 100:

| día | 27-oct | 28-oct | 29-oct | 30-oct | 31-oct | 1-nov | 2-nov | 8-nov |
|---|---|---|---|---|---|---|---|---|
| neto pesimista | +1,23 | +1,05 | +0,65 | +0,29 | +0,38 | +1,16 | +1,30 | −1,14 |

Lo que más pesa:
- **Libros anchos pierden siempre.** Con spread > 5 ¢ el neto pesimista es negativo con cualquier distancia.
- **Los llenados pierden a la resolución** aunque a 60 min parezcan ganar: +3,3 ¢/acción a 60 min contra −4,6 al cierre.
  La marca a 60 min engaña.
- **La comisión del 1-nov** (taker 0,05·p(1−p), reembolso 25 % a makers) no cambió la cuenta: el reembolso suma poco
  (≈ +0,1 por US$ 100).
- **Por horas al cierre** la recompensa por caja se mantiene: 24–36 h 9,6 US$/caja-día, 36–48 h 11,2, contra 11,4 a
  12–24 h. Las cajas de 0–12 h pagan más (17–20), pero en real son donde más se pierde con los llenados.

## Contra lo real (bot en la PC desde el 7-nov, US$ 95,77)

- **Recompensa real ≈ estimada:** 7-nov 2,29 contra 2,43 (94 %); 8-nov 9,95 contra 8,92 (112 %). El medidor no exagera la
  recompensa con 3 cajas.
- **Los llenados reales pierden más que en papel** en las cajas del mismo día (8-nov: Moscú, Múnich, Tokio 14 °C, Seúl).
  Por eso el bot solo opera cajas a más de 24 h desde el 9-nov (PR #72). También canjea pares Sí+No (PR #73) y rota a
  la caja que más paga (PR #74).
- **Cuenta al 9-nov 12Z:** ≈ US$ 95 a precio de mercado, más o menos lo depositado, después de un 8-nov con freno diario.
  Esto incluye US$ 12,24 de recompensa y US$ 4,55 de reembolso.

## Qué sigue

El medidor se apaga solo después del 9-nov y la rama `medidor-maker` queda con los datos. La confirmación es el bot
real: revisión semanal el 14-nov (PR #60) con recompensa contra llenados por caja y por horas al cierre.

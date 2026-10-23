# Promedio de 11 modelos contra precios históricos (backtest)

Reglas fijadas antes de bajar precios: `historico/REGLAS.md`. Generado por `historico/backtest.py`.

Eventos con ganadora y precios: 529; filas (caja × horizonte): 8910.

## Costo de ejecución medido (sobre el precio histórico)

| Tramo | Comprar Yes (ask − hist) | Comprar No (hist − bid) | fotos |
|---|---|---|---|
| 0-10 ¢ | +0.6 ¢ | +0.6 ¢ | 1322 |
| 10-30 ¢ | +1.5 ¢ | +1.5 ¢ | 353 |
| 30-70 ¢ | +1.5 ¢ | +1.1 ¢ | 372 |
| 70-90 ¢ | +1.5 ¢ | +1.5 ¢ | 1 |
| 90-100 ¢ |  |  | 0 |

## Veredicto (criterio fijado antes, h = 2, Promedio, costo medido, umbral 10)

- ROI > 0 y P(ROI<0) < 5 %: no
- λ con intervalo sin 0: no
- ROI positivo en las dos mitades: sí
- **Hay ventaja: NO**

## Horizonte 1 (376 serie-días, 4136 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0588 | 0.1836 | |
| Promedio | 0.0642 | 0.2068 | 0.05 [-0.03, 0.17] |
| GFS+ECMWF | 0.0674 | 0.2203 | 0.00 [-0.05, 0.05] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 574 | 43 | 39% | 2146 | +84.2 | +3.9% | 23% |
| Promedio | 0.1 | medido, highest | 574 | 43 | 39% | 2146 | +84.2 | +3.9% | 23% |
| Promedio | 0.1 | medido, lowest | 0 | | | | | | |
| Promedio | 0.1 | medido, 1a mitad | 282 | 21 | 38% | 1030 | +30.1 | +2.9% | 38% |
| Promedio | 0.1 | medido, 2a mitad | 292 | 22 | 40% | 1116 | +54.2 | +4.9% | 23% |
| Promedio | 0.1 | fijo 0c | 630 | 43 | 40% | 2353 | +176.8 | +7.5% | 4% |
| Promedio | 0.1 | fijo 1c | 587 | 43 | 39% | 2193 | +76.7 | +3.5% | 25% |
| Promedio | 0.1 | fijo 2c | 531 | 43 | 39% | 2030 | +39.8 | +2.0% | 37% |
| Promedio | 0.1 | fijo 3c | 495 | 43 | 38% | 1883 | -22.7 | -1.2% | 60% |
| Promedio | 0.05 | medido | 950 | 43 | 37% | 3479 | +20.6 | +0.6% | 42% |
| Promedio | 0.05 | medido, highest | 950 | 43 | 37% | 3479 | +20.6 | +0.6% | 42% |
| Promedio | 0.05 | medido, lowest | 0 | | | | | | |
| Promedio | 0.05 | medido, 1a mitad | 476 | 21 | 37% | 1749 | +11.3 | +0.7% | 43% |
| Promedio | 0.05 | medido, 2a mitad | 474 | 22 | 37% | 1731 | +9.3 | +0.5% | 46% |
| Promedio | 0.05 | fijo 0c | 1023 | 43 | 39% | 3876 | +113.8 | +2.9% | 18% |
| Promedio | 0.05 | fijo 1c | 981 | 43 | 37% | 3590 | +9.8 | +0.3% | 46% |
| Promedio | 0.05 | fijo 2c | 926 | 43 | 36% | 3335 | -25.2 | -0.8% | 58% |
| Promedio | 0.05 | fijo 3c | 872 | 43 | 35% | 3142 | -121.8 | -3.9% | 85% |
| GFS+ECMWF | 0.1 | medido | 726 | 43 | 39% | 2788 | +42.5 | +1.5% | 35% |
| GFS+ECMWF | 0.1 | medido, highest | 726 | 43 | 39% | 2788 | +42.5 | +1.5% | 35% |
| GFS+ECMWF | 0.1 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 364 | 21 | 40% | 1367 | +93.5 | +6.8% | 12% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 362 | 22 | 38% | 1421 | -51.0 | -3.6% | 76% |
| GFS+ECMWF | 0.1 | fijo 0c | 755 | 43 | 41% | 2952 | +147.9 | +5.0% | 10% |
| GFS+ECMWF | 0.1 | fijo 1c | 744 | 43 | 39% | 2821 | +48.8 | +1.7% | 33% |
| GFS+ECMWF | 0.1 | fijo 2c | 706 | 43 | 38% | 2691 | -11.5 | -0.4% | 54% |
| GFS+ECMWF | 0.1 | fijo 3c | 702 | 43 | 36% | 2563 | -53.2 | -2.1% | 68% |
| GFS+ECMWF | 0.05 | medido | 1021 | 43 | 39% | 3937 | +32.9 | +0.8% | 38% |
| GFS+ECMWF | 0.05 | medido, highest | 1021 | 43 | 39% | 3937 | +32.9 | +0.8% | 38% |
| GFS+ECMWF | 0.05 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 518 | 21 | 39% | 1974 | +35.6 | +1.8% | 33% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 503 | 22 | 39% | 1963 | -2.7 | -0.1% | 52% |
| GFS+ECMWF | 0.05 | fijo 0c | 1066 | 43 | 41% | 4232 | +157.5 | +3.7% | 11% |
| GFS+ECMWF | 0.05 | fijo 1c | 1056 | 43 | 38% | 4016 | +54.5 | +1.4% | 32% |
| GFS+ECMWF | 0.05 | fijo 2c | 1047 | 43 | 36% | 3878 | -58.4 | -1.5% | 70% |
| GFS+ECMWF | 0.05 | fijo 3c | 1108 | 43 | 32% | 3819 | -218.6 | -5.7% | 97% |

## Horizonte 2 (358 serie-días, 3938 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0629 | 0.2018 | |
| Promedio | 0.0681 | 0.2233 | 0.00 [-0.10, 0.12] |
| GFS+ECMWF | 0.0708 | 0.2354 | -0.05 [-0.12, 0.03] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 530 | 41 | 43% | 2250 | +30.0 | +1.3% | 39% |
| Promedio | 0.1 | medido, highest | 530 | 41 | 43% | 2250 | +30.0 | +1.3% | 39% |
| Promedio | 0.1 | medido, lowest | 0 | | | | | | |
| Promedio | 0.1 | medido, 1a mitad | 229 | 19 | 42% | 938 | +11.7 | +1.2% | 43% |
| Promedio | 0.1 | medido, 2a mitad | 301 | 22 | 44% | 1312 | +18.3 | +1.4% | 43% |
| Promedio | 0.1 | fijo 0c | 587 | 41 | 43% | 2487 | +42.7 | +1.7% | 38% |
| Promedio | 0.1 | fijo 1c | 540 | 41 | 43% | 2307 | +33.3 | +1.4% | 38% |
| Promedio | 0.1 | fijo 2c | 495 | 41 | 42% | 2070 | +0.2 | +0.0% | 51% |
| Promedio | 0.1 | fijo 3c | 435 | 41 | 41% | 1868 | -67.9 | -3.6% | 74% |
| Promedio | 0.05 | medido | 924 | 41 | 39% | 3694 | -104.2 | -2.8% | 78% |
| Promedio | 0.05 | medido, highest | 924 | 41 | 39% | 3694 | -104.2 | -2.8% | 78% |
| Promedio | 0.05 | medido, lowest | 0 | | | | | | |
| Promedio | 0.05 | medido, 1a mitad | 434 | 19 | 36% | 1671 | -90.6 | -5.4% | 85% |
| Promedio | 0.05 | medido, 2a mitad | 490 | 22 | 41% | 2024 | -13.7 | -0.7% | 53% |
| Promedio | 0.05 | fijo 0c | 1008 | 41 | 40% | 4072 | -2.0 | -0.1% | 52% |
| Promedio | 0.05 | fijo 1c | 953 | 41 | 39% | 3791 | -111.2 | -2.9% | 79% |
| Promedio | 0.05 | fijo 2c | 884 | 41 | 37% | 3488 | -187.9 | -5.4% | 91% |
| Promedio | 0.05 | fijo 3c | 784 | 41 | 38% | 3202 | -202.4 | -6.3% | 94% |
| GFS+ECMWF | 0.1 | medido | 653 | 41 | 42% | 2770 | -19.7 | -0.7% | 58% |
| GFS+ECMWF | 0.1 | medido, highest | 653 | 41 | 42% | 2770 | -19.7 | -0.7% | 58% |
| GFS+ECMWF | 0.1 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 303 | 19 | 41% | 1249 | -19.4 | -1.6% | 64% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 350 | 22 | 43% | 1520 | -0.2 | -0.0% | 49% |
| GFS+ECMWF | 0.1 | fijo 0c | 704 | 41 | 43% | 3008 | +12.3 | +0.4% | 46% |
| GFS+ECMWF | 0.1 | fijo 1c | 661 | 41 | 43% | 2839 | +11.1 | +0.4% | 46% |
| GFS+ECMWF | 0.1 | fijo 2c | 641 | 41 | 40% | 2688 | -98.0 | -3.6% | 81% |
| GFS+ECMWF | 0.1 | fijo 3c | 599 | 41 | 39% | 2528 | -178.4 | -7.0% | 94% |
| GFS+ECMWF | 0.05 | medido | 1048 | 41 | 40% | 4355 | -124.5 | -2.9% | 82% |
| GFS+ECMWF | 0.05 | medido, highest | 1048 | 41 | 40% | 4355 | -124.5 | -2.9% | 82% |
| GFS+ECMWF | 0.05 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 512 | 19 | 38% | 2055 | -94.8 | -4.6% | 88% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 536 | 22 | 42% | 2300 | -29.7 | -1.3% | 59% |
| GFS+ECMWF | 0.05 | fijo 0c | 1111 | 41 | 42% | 4628 | +12.0 | +0.3% | 48% |
| GFS+ECMWF | 0.05 | fijo 1c | 1077 | 41 | 40% | 4411 | -120.8 | -2.7% | 81% |
| GFS+ECMWF | 0.05 | fijo 2c | 1066 | 41 | 38% | 4243 | -242.9 | -5.7% | 96% |
| GFS+ECMWF | 0.05 | fijo 3c | 1023 | 41 | 36% | 3982 | -281.5 | -7.1% | 99% |

## Horizonte 3 (76 serie-días, 836 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0703 | 0.2418 | |
| Promedio | 0.0673 | 0.2224 | 0.82 [0.62, 0.97] |
| GFS+ECMWF | 0.0717 | 0.2360 | 0.68 [0.42, 0.88] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 166 | 38 | 62% | 865 | +164.8 | +19.1% | 0% |
| Promedio | 0.1 | medido, highest | 166 | 38 | 62% | 865 | +164.8 | +19.1% | 0% |
| Promedio | 0.1 | medido, lowest | 0 | | | | | | |
| Promedio | 0.1 | medido, 1a mitad | 49 | 16 | 59% | 219 | +70.7 | +32.3% | 0% |
| Promedio | 0.1 | medido, 2a mitad | 117 | 22 | 63% | 646 | +94.1 | +14.6% | 2% |
| Promedio | 0.1 | fijo 0c | 200 | 38 | 62% | 1049 | +201.0 | +19.2% | 0% |
| Promedio | 0.1 | fijo 1c | 177 | 38 | 60% | 913 | +157.3 | +17.2% | 0% |
| Promedio | 0.1 | fijo 2c | 154 | 37 | 62% | 809 | +141.4 | +17.5% | 0% |
| Promedio | 0.1 | fijo 3c | 139 | 36 | 60% | 739 | +101.5 | +13.7% | 2% |
| Promedio | 0.05 | medido | 257 | 38 | 58% | 1291 | +199.1 | +15.4% | 0% |
| Promedio | 0.05 | medido, highest | 257 | 38 | 58% | 1291 | +199.1 | +15.4% | 0% |
| Promedio | 0.05 | medido, lowest | 0 | | | | | | |
| Promedio | 0.05 | medido, 1a mitad | 93 | 16 | 53% | 392 | +98.5 | +25.1% | 0% |
| Promedio | 0.05 | medido, 2a mitad | 164 | 22 | 61% | 899 | +100.7 | +11.2% | 4% |
| Promedio | 0.05 | fijo 0c | 296 | 38 | 60% | 1511 | +249.3 | +16.5% | 0% |
| Promedio | 0.05 | fijo 1c | 267 | 38 | 60% | 1373 | +217.2 | +15.8% | 0% |
| Promedio | 0.05 | fijo 2c | 232 | 38 | 61% | 1214 | +206.2 | +17.0% | 0% |
| Promedio | 0.05 | fijo 3c | 212 | 38 | 60% | 1105 | +165.4 | +15.0% | 0% |
| GFS+ECMWF | 0.1 | medido | 187 | 35 | 55% | 930 | +99.6 | +10.7% | 3% |
| GFS+ECMWF | 0.1 | medido, highest | 187 | 35 | 55% | 930 | +99.6 | +10.7% | 3% |
| GFS+ECMWF | 0.1 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 48 | 14 | 46% | 194 | +25.9 | +13.3% | 16% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 139 | 21 | 58% | 736 | +73.7 | +10.0% | 6% |
| GFS+ECMWF | 0.1 | fijo 0c | 218 | 36 | 56% | 1083 | +136.6 | +12.6% | 0% |
| GFS+ECMWF | 0.1 | fijo 1c | 192 | 35 | 55% | 948 | +102.0 | +10.8% | 3% |
| GFS+ECMWF | 0.1 | fijo 2c | 168 | 35 | 56% | 854 | +96.3 | +11.3% | 3% |
| GFS+ECMWF | 0.1 | fijo 3c | 153 | 34 | 60% | 820 | +90.1 | +11.0% | 3% |
| GFS+ECMWF | 0.05 | medido | 286 | 38 | 52% | 1355 | +125.3 | +9.2% | 2% |
| GFS+ECMWF | 0.05 | medido, highest | 286 | 38 | 52% | 1355 | +125.3 | +9.2% | 2% |
| GFS+ECMWF | 0.05 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 99 | 16 | 46% | 416 | +44.3 | +10.7% | 16% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 187 | 22 | 55% | 939 | +80.9 | +8.6% | 5% |
| GFS+ECMWF | 0.05 | fijo 0c | 326 | 38 | 55% | 1613 | +176.6 | +10.9% | 0% |
| GFS+ECMWF | 0.05 | fijo 1c | 297 | 38 | 53% | 1427 | +152.7 | +10.7% | 1% |
| GFS+ECMWF | 0.05 | fijo 2c | 270 | 38 | 52% | 1309 | +91.2 | +7.0% | 6% |
| GFS+ECMWF | 0.05 | fijo 3c | 239 | 37 | 51% | 1153 | +66.9 | +5.8% | 13% |

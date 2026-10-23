# Promedio de 11 modelos contra precios históricos (backtest)

Reglas fijadas antes de bajar precios: `historico/REGLAS.md`. Generado por `historico/backtest.py`.

Eventos con ganadora y precios: 5093; filas (caja × horizonte): 67672.

## Costo de ejecución medido (sobre el precio histórico)

| Tramo | Comprar Yes (ask − hist) | Comprar No (hist − bid) | fotos |
|---|---|---|---|
| 0-10 ¢ | +0.6 ¢ | +0.6 ¢ | 1322 |
| 10-30 ¢ | +1.5 ¢ | +1.5 ¢ | 353 |
| 30-70 ¢ | +1.5 ¢ | +1.1 ¢ | 372 |
| 70-90 ¢ | +1.5 ¢ | +1.5 ¢ | 1 |
| 90-100 ¢ |  |  | 0 |

## Veredicto (criterio fijado antes, h = 2, Promedio, costo medido, umbral 10)

- ROI > 0 y P(ROI<0) < 5 %: sí
- λ con intervalo sin 0: sí
- ROI positivo en las dos mitades: sí
- **Hay ventaja: SÍ**

## Horizonte 1 (1899 serie-días, 20889 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0551 | 0.1725 | |
| Promedio | 0.0644 | 0.2062 | -0.05 [-0.07, -0.03] |
| GFS+ECMWF | 0.0682 | 0.2218 | -0.05 [-0.07, -0.05] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 2954 | 43 | 35% | 10832 | -502.3 | -4.6% | 98% |
| Promedio | 0.1 | medido, highest | 2954 | 43 | 35% | 10832 | -502.3 | -4.6% | 98% |
| Promedio | 0.1 | medido, lowest | 0 | | | | | | |
| Promedio | 0.1 | medido, 1a mitad | 1392 | 21 | 34% | 5048 | -358.1 | -7.1% | 97% |
| Promedio | 0.1 | medido, 2a mitad | 1562 | 22 | 36% | 5784 | -144.2 | -2.5% | 79% |
| Promedio | 0.1 | fijo 0c | 3205 | 43 | 36% | 11722 | -161.7 | -1.4% | 73% |
| Promedio | 0.1 | fijo 1c | 3031 | 43 | 35% | 11078 | -468.1 | -4.2% | 96% |
| Promedio | 0.1 | fijo 2c | 2826 | 43 | 34% | 10368 | -757.6 | -7.3% | 100% |
| Promedio | 0.1 | fijo 3c | 2674 | 43 | 32% | 9610 | -1149.9 | -12.0% | 100% |
| Promedio | 0.05 | medido | 4710 | 43 | 34% | 17099 | -919.2 | -5.4% | 100% |
| Promedio | 0.05 | medido, highest | 4710 | 43 | 34% | 17099 | -919.2 | -5.4% | 100% |
| Promedio | 0.05 | medido, lowest | 0 | | | | | | |
| Promedio | 0.05 | medido, 1a mitad | 2340 | 21 | 33% | 8385 | -565.2 | -6.7% | 100% |
| Promedio | 0.05 | medido, 2a mitad | 2370 | 22 | 35% | 8714 | -354.0 | -4.1% | 97% |
| Promedio | 0.05 | fijo 0c | 5021 | 43 | 36% | 18566 | -456.4 | -2.5% | 94% |
| Promedio | 0.05 | fijo 1c | 4842 | 43 | 34% | 17534 | -914.1 | -5.2% | 100% |
| Promedio | 0.05 | fijo 2c | 4647 | 43 | 33% | 16454 | -1224.3 | -7.4% | 100% |
| Promedio | 0.05 | fijo 3c | 4520 | 43 | 30% | 15484 | -1693.8 | -10.9% | 100% |
| GFS+ECMWF | 0.1 | medido | 3700 | 43 | 37% | 14155 | -625.1 | -4.4% | 100% |
| GFS+ECMWF | 0.1 | medido, highest | 3700 | 43 | 37% | 14155 | -625.1 | -4.4% | 100% |
| GFS+ECMWF | 0.1 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 1820 | 21 | 35% | 6872 | -421.8 | -6.1% | 99% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 1880 | 22 | 38% | 7283 | -203.3 | -2.8% | 91% |
| GFS+ECMWF | 0.1 | fijo 0c | 3888 | 43 | 38% | 15026 | -255.5 | -1.7% | 84% |
| GFS+ECMWF | 0.1 | fijo 1c | 3782 | 43 | 36% | 14355 | -634.8 | -4.4% | 100% |
| GFS+ECMWF | 0.1 | fijo 2c | 3654 | 43 | 35% | 13705 | -935.4 | -6.8% | 100% |
| GFS+ECMWF | 0.1 | fijo 3c | 3703 | 43 | 32% | 13079 | -1318.7 | -10.1% | 100% |
| GFS+ECMWF | 0.05 | medido | 5150 | 43 | 36% | 19540 | -1039.9 | -5.3% | 100% |
| GFS+ECMWF | 0.05 | medido, highest | 5150 | 43 | 36% | 19540 | -1039.9 | -5.3% | 100% |
| GFS+ECMWF | 0.05 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 2590 | 21 | 35% | 9743 | -622.8 | -6.4% | 100% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 2560 | 22 | 37% | 9797 | -417.1 | -4.3% | 100% |
| GFS+ECMWF | 0.05 | fijo 0c | 5398 | 43 | 38% | 20855 | -445.3 | -2.1% | 95% |
| GFS+ECMWF | 0.05 | fijo 1c | 5346 | 43 | 36% | 20020 | -990.2 | -5.0% | 100% |
| GFS+ECMWF | 0.05 | fijo 2c | 5365 | 43 | 33% | 19322 | -1541.7 | -8.0% | 100% |
| GFS+ECMWF | 0.05 | fijo 3c | 5737 | 43 | 29% | 18874 | -2233.9 | -11.8% | 100% |

## Horizonte 2 (3458 serie-días, 38038 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0865 | 0.2809 | |
| Promedio | 0.0670 | 0.2168 | 0.97 [0.97, 0.97] |
| GFS+ECMWF | 0.0702 | 0.2313 | 0.93 [0.93, 0.93] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 12691 | 41 | 80% | 76835 | +25195.4 | +32.8% | 0% |
| Promedio | 0.1 | medido, highest | 2760 | 41 | 39% | 11182 | -381.9 | -3.4% | 95% |
| Promedio | 0.1 | medido, lowest | 9931 | 41 | 92% | 65653 | +25577.3 | +39.0% | 0% |
| Promedio | 0.1 | medido, 1a mitad | 4651 | 19 | 76% | 27864 | +7595.7 | +27.3% | 0% |
| Promedio | 0.1 | medido, 2a mitad | 8040 | 22 | 83% | 48970 | +17599.7 | +35.9% | 0% |
| Promedio | 0.1 | fijo 0c | 13463 | 41 | 80% | 80038 | +26992.1 | +33.7% | 0% |
| Promedio | 0.1 | fijo 1c | 12912 | 41 | 80% | 77947 | +25523.1 | +32.7% | 0% |
| Promedio | 0.1 | fijo 2c | 12304 | 41 | 81% | 75559 | +24180.6 | +32.0% | 0% |
| Promedio | 0.1 | fijo 3c | 11667 | 41 | 82% | 73326 | +22843.8 | +31.1% | 0% |
| Promedio | 0.05 | medido | 16386 | 41 | 73% | 94298 | +25602.0 | +27.2% | 0% |
| Promedio | 0.05 | medido, highest | 4734 | 41 | 37% | 18491 | -870.9 | -4.7% | 100% |
| Promedio | 0.05 | medido, lowest | 11652 | 41 | 88% | 75807 | +26472.8 | +34.9% | 0% |
| Promedio | 0.05 | medido, 1a mitad | 6616 | 19 | 68% | 37069 | +7741.0 | +20.9% | 0% |
| Promedio | 0.05 | medido, 2a mitad | 9770 | 22 | 77% | 57229 | +17861.0 | +31.2% | 0% |
| Promedio | 0.05 | fijo 0c | 17321 | 41 | 73% | 98127 | +27793.4 | +28.3% | 0% |
| Promedio | 0.05 | fijo 1c | 16714 | 41 | 73% | 95710 | +26029.7 | +27.2% | 0% |
| Promedio | 0.05 | fijo 2c | 15965 | 41 | 73% | 92772 | +24078.1 | +25.9% | 0% |
| Promedio | 0.05 | fijo 3c | 15169 | 41 | 74% | 90148 | +22612.2 | +25.1% | 0% |
| GFS+ECMWF | 0.1 | medido | 13467 | 41 | 78% | 80660 | +24180.2 | +30.0% | 0% |
| GFS+ECMWF | 0.1 | medido, highest | 3442 | 41 | 40% | 14440 | -719.7 | -5.0% | 100% |
| GFS+ECMWF | 0.1 | medido, lowest | 10025 | 41 | 91% | 66220 | +24899.9 | +37.6% | 0% |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 4911 | 19 | 73% | 28855 | +6875.3 | +23.8% | 0% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 8556 | 22 | 81% | 51805 | +17304.9 | +33.4% | 0% |
| GFS+ECMWF | 0.1 | fijo 0c | 14183 | 41 | 78% | 83875 | +26075.5 | +31.1% | 0% |
| GFS+ECMWF | 0.1 | fijo 1c | 13666 | 41 | 78% | 81687 | +24443.5 | +29.9% | 0% |
| GFS+ECMWF | 0.1 | fijo 2c | 13202 | 41 | 78% | 79664 | +22826.3 | +28.6% | 0% |
| GFS+ECMWF | 0.1 | fijo 3c | 12617 | 41 | 78% | 77125 | +21384.9 | +27.7% | 0% |
| GFS+ECMWF | 0.05 | medido | 17135 | 41 | 72% | 98570 | +24670.1 | +25.0% | 0% |
| GFS+ECMWF | 0.05 | medido, highest | 5325 | 41 | 38% | 21541 | -1060.6 | -4.9% | 100% |
| GFS+ECMWF | 0.05 | medido, lowest | 11810 | 41 | 87% | 77029 | +25730.7 | +33.4% | 0% |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 6938 | 19 | 66% | 38693 | +6986.9 | +18.1% | 0% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 10197 | 22 | 76% | 59877 | +17683.2 | +29.5% | 0% |
| GFS+ECMWF | 0.05 | fijo 0c | 17961 | 41 | 72% | 102252 | +26938.3 | +26.4% | 0% |
| GFS+ECMWF | 0.05 | fijo 1c | 17484 | 41 | 71% | 99756 | +25023.9 | +25.1% | 0% |
| GFS+ECMWF | 0.05 | fijo 2c | 17052 | 41 | 71% | 97349 | +23101.1 | +23.7% | 0% |
| GFS+ECMWF | 0.05 | fijo 3c | 16537 | 41 | 70% | 95108 | +21312.3 | +22.4% | 0% |

## Horizonte 3 (795 serie-días, 8745 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0980 | 0.3265 | |
| Promedio | 0.0683 | 0.2226 | 0.97 [0.97, 1.00] |
| GFS+ECMWF | 0.0718 | 0.2395 | 0.97 [0.97, 0.97] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 3577 | 38 | 87% | 23034 | +8076.1 | +35.1% | 0% |
| Promedio | 0.1 | medido, highest | 783 | 38 | 66% | 4585 | +574.8 | +12.5% | 0% |
| Promedio | 0.1 | medido, lowest | 2794 | 38 | 93% | 18449 | +7501.3 | +40.7% | 0% |
| Promedio | 0.1 | medido, 1a mitad | 1113 | 16 | 83% | 7303 | +1967.3 | +26.9% | 0% |
| Promedio | 0.1 | medido, 2a mitad | 2464 | 22 | 89% | 15731 | +6108.8 | +38.8% | 0% |
| Promedio | 0.1 | fijo 0c | 3813 | 38 | 86% | 23901 | +8719.1 | +36.5% | 0% |
| Promedio | 0.1 | fijo 1c | 3643 | 38 | 87% | 23348 | +8192.5 | +35.1% | 0% |
| Promedio | 0.1 | fijo 2c | 3475 | 38 | 88% | 22724 | +7706.1 | +33.9% | 0% |
| Promedio | 0.1 | fijo 3c | 3310 | 38 | 89% | 22118 | +7202.4 | +32.6% | 0% |
| Promedio | 0.05 | medido | 4484 | 38 | 80% | 27565 | +8395.3 | +30.5% | 0% |
| Promedio | 0.05 | medido, highest | 1263 | 38 | 57% | 6772 | +428.2 | +6.3% | 0% |
| Promedio | 0.05 | medido, lowest | 3221 | 38 | 89% | 20793 | +7967.1 | +38.3% | 0% |
| Promedio | 0.05 | medido, 1a mitad | 1554 | 16 | 74% | 9340 | +2190.4 | +23.4% | 0% |
| Promedio | 0.05 | medido, 2a mitad | 2930 | 22 | 83% | 18225 | +6204.9 | +34.1% | 0% |
| Promedio | 0.05 | fijo 0c | 4805 | 38 | 79% | 28817 | +9043.2 | +31.4% | 0% |
| Promedio | 0.05 | fijo 1c | 4571 | 38 | 80% | 27956 | +8534.2 | +30.5% | 0% |
| Promedio | 0.05 | fijo 2c | 4327 | 38 | 81% | 27152 | +8088.4 | +29.8% | 0% |
| Promedio | 0.05 | fijo 3c | 4111 | 38 | 82% | 26307 | +7613.2 | +28.9% | 0% |
| GFS+ECMWF | 0.1 | medido | 3610 | 38 | 85% | 23269 | +7550.9 | +32.5% | 0% |
| GFS+ECMWF | 0.1 | medido, highest | 876 | 38 | 61% | 5042 | +317.8 | +6.3% | 0% |
| GFS+ECMWF | 0.1 | medido, lowest | 2734 | 38 | 93% | 18227 | +7233.1 | +39.7% | 0% |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 1046 | 16 | 82% | 6964 | +1635.5 | +23.5% | 0% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 2564 | 22 | 87% | 16305 | +5915.3 | +36.3% | 0% |
| GFS+ECMWF | 0.1 | fijo 0c | 3859 | 38 | 84% | 24349 | +8081.3 | +33.2% | 0% |
| GFS+ECMWF | 0.1 | fijo 1c | 3653 | 38 | 85% | 23483 | +7647.4 | +32.6% | 0% |
| GFS+ECMWF | 0.1 | fijo 2c | 3496 | 38 | 86% | 22934 | +7245.7 | +31.6% | 0% |
| GFS+ECMWF | 0.1 | fijo 3c | 3324 | 38 | 88% | 22257 | +6862.5 | +30.8% | 0% |
| GFS+ECMWF | 0.05 | medido | 4643 | 38 | 78% | 28452 | +7758.2 | +27.3% | 0% |
| GFS+ECMWF | 0.05 | medido, highest | 1433 | 38 | 54% | 7518 | +162.3 | +2.2% | 8% |
| GFS+ECMWF | 0.05 | medido, lowest | 3210 | 38 | 89% | 20934 | +7595.9 | +36.3% | 0% |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 1573 | 16 | 71% | 9468 | +1691.6 | +17.9% | 0% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 3070 | 22 | 82% | 18983 | +6066.6 | +32.0% | 0% |
| GFS+ECMWF | 0.05 | fijo 0c | 4973 | 38 | 77% | 29835 | +8434.7 | +28.3% | 0% |
| GFS+ECMWF | 0.05 | fijo 1c | 4715 | 38 | 78% | 28833 | +7876.9 | +27.3% | 0% |
| GFS+ECMWF | 0.05 | fijo 2c | 4488 | 38 | 79% | 28110 | +7359.7 | +26.2% | 0% |
| GFS+ECMWF | 0.05 | fijo 3c | 4217 | 38 | 80% | 27047 | +6893.1 | +25.5% | 0% |

---

# Agregado después de ver resultados: solo precios con libro de verdad

Las cajas de un evento deberían sumar ~1. En muchas mínimas (y a 3 días) sumaban 2-4: el precio histórico era el medio de un libro casi vacío (ej. bid 1 ¢ / ask 66 ¢ → 33,5 ¢), que no se puede operar. Acá quedan solo los momentos en que las cajas del evento suman entre 0.9 y 1.15 (42185 filas).

## Veredicto con libro de verdad (misma regla)

- ROI > 0 y P(ROI<0) < 5 %: no
- λ con intervalo sin 0: no
- ROI positivo en las dos mitades: no
- **Hay ventaja: NO**

## Horizonte 1 (1899 serie-días, 20889 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0551 | 0.1725 | |
| Promedio | 0.0644 | 0.2062 | -0.05 [-0.07, -0.03] |
| GFS+ECMWF | 0.0682 | 0.2218 | -0.05 [-0.07, -0.05] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 2954 | 43 | 35% | 10832 | -502.3 | -4.6% | 98% |
| Promedio | 0.1 | medido, highest | 2954 | 43 | 35% | 10832 | -502.3 | -4.6% | 98% |
| Promedio | 0.1 | medido, lowest | 0 | | | | | | |
| Promedio | 0.1 | medido, 1a mitad | 1392 | 21 | 34% | 5048 | -358.1 | -7.1% | 97% |
| Promedio | 0.1 | medido, 2a mitad | 1562 | 22 | 36% | 5784 | -144.2 | -2.5% | 79% |
| Promedio | 0.1 | fijo 0c | 3205 | 43 | 36% | 11722 | -161.7 | -1.4% | 73% |
| Promedio | 0.1 | fijo 1c | 3031 | 43 | 35% | 11078 | -468.1 | -4.2% | 96% |
| Promedio | 0.1 | fijo 2c | 2826 | 43 | 34% | 10368 | -757.6 | -7.3% | 100% |
| Promedio | 0.1 | fijo 3c | 2674 | 43 | 32% | 9610 | -1149.9 | -12.0% | 100% |
| Promedio | 0.05 | medido | 4710 | 43 | 34% | 17099 | -919.2 | -5.4% | 100% |
| Promedio | 0.05 | medido, highest | 4710 | 43 | 34% | 17099 | -919.2 | -5.4% | 100% |
| Promedio | 0.05 | medido, lowest | 0 | | | | | | |
| Promedio | 0.05 | medido, 1a mitad | 2340 | 21 | 33% | 8385 | -565.2 | -6.7% | 100% |
| Promedio | 0.05 | medido, 2a mitad | 2370 | 22 | 35% | 8714 | -354.0 | -4.1% | 97% |
| Promedio | 0.05 | fijo 0c | 5021 | 43 | 36% | 18566 | -456.4 | -2.5% | 94% |
| Promedio | 0.05 | fijo 1c | 4842 | 43 | 34% | 17534 | -914.1 | -5.2% | 100% |
| Promedio | 0.05 | fijo 2c | 4647 | 43 | 33% | 16454 | -1224.3 | -7.4% | 100% |
| Promedio | 0.05 | fijo 3c | 4520 | 43 | 30% | 15484 | -1693.8 | -10.9% | 100% |
| GFS+ECMWF | 0.1 | medido | 3700 | 43 | 37% | 14155 | -625.1 | -4.4% | 100% |
| GFS+ECMWF | 0.1 | medido, highest | 3700 | 43 | 37% | 14155 | -625.1 | -4.4% | 100% |
| GFS+ECMWF | 0.1 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 1820 | 21 | 35% | 6872 | -421.8 | -6.1% | 99% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 1880 | 22 | 38% | 7283 | -203.3 | -2.8% | 91% |
| GFS+ECMWF | 0.1 | fijo 0c | 3888 | 43 | 38% | 15026 | -255.5 | -1.7% | 84% |
| GFS+ECMWF | 0.1 | fijo 1c | 3782 | 43 | 36% | 14355 | -634.8 | -4.4% | 100% |
| GFS+ECMWF | 0.1 | fijo 2c | 3654 | 43 | 35% | 13705 | -935.4 | -6.8% | 100% |
| GFS+ECMWF | 0.1 | fijo 3c | 3703 | 43 | 32% | 13079 | -1318.7 | -10.1% | 100% |
| GFS+ECMWF | 0.05 | medido | 5150 | 43 | 36% | 19540 | -1039.9 | -5.3% | 100% |
| GFS+ECMWF | 0.05 | medido, highest | 5150 | 43 | 36% | 19540 | -1039.9 | -5.3% | 100% |
| GFS+ECMWF | 0.05 | medido, lowest | 0 | | | | | | |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 2590 | 21 | 35% | 9743 | -622.8 | -6.4% | 100% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 2560 | 22 | 37% | 9797 | -417.1 | -4.3% | 100% |
| GFS+ECMWF | 0.05 | fijo 0c | 5398 | 43 | 38% | 20855 | -445.3 | -2.1% | 95% |
| GFS+ECMWF | 0.05 | fijo 1c | 5346 | 43 | 36% | 20020 | -990.2 | -5.0% | 100% |
| GFS+ECMWF | 0.05 | fijo 2c | 5365 | 43 | 33% | 19322 | -1541.7 | -8.0% | 100% |
| GFS+ECMWF | 0.05 | fijo 3c | 5737 | 43 | 29% | 18874 | -2233.9 | -11.8% | 100% |

## Horizonte 2 (1859 serie-días, 20449 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0601 | 0.1914 | |
| Promedio | 0.0670 | 0.2172 | -0.05 [-0.07, -0.03] |
| GFS+ECMWF | 0.0702 | 0.2309 | -0.05 [-0.07, -0.03] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 2811 | 41 | 39% | 11356 | -396.0 | -3.5% | 95% |
| Promedio | 0.1 | medido, highest | 2734 | 41 | 39% | 11040 | -389.5 | -3.5% | 95% |
| Promedio | 0.1 | medido, lowest | 77 | 21 | 40% | 316 | -6.5 | -2.0% | 59% |
| Promedio | 0.1 | medido, 1a mitad | 1272 | 19 | 37% | 5064 | -303.6 | -6.0% | 100% |
| Promedio | 0.1 | medido, 2a mitad | 1539 | 22 | 40% | 6292 | -92.3 | -1.5% | 70% |
| Promedio | 0.1 | fijo 0c | 3122 | 41 | 40% | 12715 | -225.0 | -1.8% | 81% |
| Promedio | 0.1 | fijo 1c | 2890 | 41 | 39% | 11641 | -390.7 | -3.4% | 94% |
| Promedio | 0.1 | fijo 2c | 2644 | 41 | 38% | 10668 | -577.5 | -5.4% | 99% |
| Promedio | 0.1 | fijo 3c | 2362 | 41 | 38% | 9786 | -796.3 | -8.1% | 100% |
| Promedio | 0.05 | medido | 4832 | 41 | 37% | 18814 | -934.4 | -5.0% | 100% |
| Promedio | 0.05 | medido, highest | 4673 | 41 | 37% | 18167 | -876.9 | -4.8% | 100% |
| Promedio | 0.05 | medido, lowest | 159 | 23 | 37% | 648 | -57.5 | -8.9% | 89% |
| Promedio | 0.05 | medido, 1a mitad | 2287 | 19 | 35% | 8672 | -681.8 | -7.9% | 100% |
| Promedio | 0.05 | medido, 2a mitad | 2545 | 22 | 39% | 10143 | -252.7 | -2.5% | 89% |
| Promedio | 0.05 | fijo 0c | 5202 | 41 | 39% | 20712 | -362.4 | -1.8% | 87% |
| Promedio | 0.05 | fijo 1c | 4995 | 41 | 37% | 19403 | -902.8 | -4.7% | 100% |
| Promedio | 0.05 | fijo 2c | 4702 | 41 | 36% | 18127 | -1407.1 | -7.8% | 100% |
| Promedio | 0.05 | fijo 3c | 4296 | 41 | 35% | 16816 | -1636.2 | -9.7% | 100% |
| GFS+ECMWF | 0.1 | medido | 3506 | 41 | 40% | 14639 | -799.1 | -5.5% | 100% |
| GFS+ECMWF | 0.1 | medido, highest | 3405 | 41 | 40% | 14222 | -721.7 | -5.1% | 100% |
| GFS+ECMWF | 0.1 | medido, lowest | 101 | 20 | 34% | 417 | -77.4 | -18.6% | 99% |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 1625 | 19 | 38% | 6696 | -556.4 | -8.3% | 100% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 1881 | 22 | 41% | 7943 | -242.7 | -3.1% | 89% |
| GFS+ECMWF | 0.1 | fijo 0c | 3765 | 41 | 41% | 15971 | -421.2 | -2.6% | 95% |
| GFS+ECMWF | 0.1 | fijo 1c | 3583 | 41 | 40% | 14961 | -791.0 | -5.3% | 100% |
| GFS+ECMWF | 0.1 | fijo 2c | 3453 | 41 | 38% | 14176 | -1125.9 | -7.9% | 100% |
| GFS+ECMWF | 0.1 | fijo 3c | 3234 | 41 | 37% | 13197 | -1326.9 | -10.1% | 100% |
| GFS+ECMWF | 0.05 | medido | 5425 | 41 | 38% | 21904 | -1164.3 | -5.3% | 100% |
| GFS+ECMWF | 0.05 | medido, highest | 5245 | 41 | 38% | 21134 | -1054.2 | -5.0% | 100% |
| GFS+ECMWF | 0.05 | medido, lowest | 180 | 23 | 37% | 770 | -110.1 | -14.3% | 99% |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 2624 | 19 | 36% | 10340 | -869.7 | -8.4% | 100% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 2801 | 22 | 40% | 11565 | -294.6 | -2.5% | 92% |
| GFS+ECMWF | 0.05 | fijo 0c | 5694 | 41 | 40% | 23589 | -569.2 | -2.4% | 98% |
| GFS+ECMWF | 0.05 | fijo 1c | 5629 | 41 | 38% | 22345 | -1125.4 | -5.0% | 100% |
| GFS+ECMWF | 0.05 | fijo 2c | 5627 | 41 | 35% | 21485 | -1734.5 | -8.1% | 100% |
| GFS+ECMWF | 0.05 | fijo 3c | 5507 | 41 | 33% | 20584 | -2274.2 | -11.1% | 100% |

## Horizonte 3 (77 serie-días, 847 cajas)

| | Brier | log-score | λ (IC 95 %) |
|---|---|---|---|
| Mercado | 0.0702 | 0.2336 | |
| Promedio | 0.0675 | 0.2192 | 0.90 [0.60, 1.05] |
| GFS+ECMWF | 0.0706 | 0.2331 | 0.57 [0.17, 0.90] |

| Modelo | Umbral | Costo | n | días | acierto | puesto | ganancia | ROI | P(ROI<0) |
|---|---|---|---|---|---|---|---|---|---|
| Promedio | 0.1 | medido | 79 | 15 | 47% | 268 | +101.9 | +38.0% | 0% |
| Promedio | 0.1 | medido, highest | 60 | 14 | 47% | 219 | +61.0 | +27.9% | 1% |
| Promedio | 0.1 | medido, lowest | 19 | 6 | 47% | 49 | +40.9 | +83.4% | 0% |
| Promedio | 0.1 | medido, 1a mitad | 60 | 11 | 52% | 202 | +108.3 | +53.7% | 0% |
| Promedio | 0.1 | medido, 2a mitad | 19 | 4 | 32% | 66 | -6.4 | -9.6% | 76% |
| Promedio | 0.1 | fijo 0c | 101 | 15 | 46% | 327 | +142.9 | +43.7% | 0% |
| Promedio | 0.1 | fijo 1c | 86 | 15 | 46% | 291 | +109.1 | +37.5% | 0% |
| Promedio | 0.1 | fijo 2c | 68 | 14 | 46% | 234 | +76.1 | +32.6% | 2% |
| Promedio | 0.1 | fijo 3c | 57 | 13 | 42% | 200 | +39.7 | +19.8% | 8% |
| Promedio | 0.05 | medido | 177 | 16 | 43% | 606 | +154.1 | +25.4% | 0% |
| Promedio | 0.05 | medido, highest | 124 | 15 | 43% | 445 | +84.8 | +19.1% | 4% |
| Promedio | 0.05 | medido, lowest | 53 | 6 | 43% | 161 | +69.3 | +43.1% | 0% |
| Promedio | 0.05 | medido, 1a mitad | 147 | 12 | 45% | 478 | +182.0 | +38.1% | 0% |
| Promedio | 0.05 | medido, 2a mitad | 30 | 4 | 33% | 128 | -27.9 | -21.8% | 100% |
| Promedio | 0.05 | fijo 0c | 204 | 16 | 44% | 738 | +162.5 | +22.0% | 0% |
| Promedio | 0.05 | fijo 1c | 181 | 16 | 44% | 623 | +167.0 | +26.8% | 0% |
| Promedio | 0.05 | fijo 2c | 159 | 16 | 45% | 565 | +154.6 | +27.3% | 0% |
| Promedio | 0.05 | fijo 3c | 143 | 16 | 47% | 509 | +160.6 | +31.5% | 0% |
| GFS+ECMWF | 0.1 | medido | 75 | 15 | 40% | 270 | +30.0 | +11.1% | 14% |
| GFS+ECMWF | 0.1 | medido, highest | 62 | 13 | 40% | 231 | +19.3 | +8.3% | 23% |
| GFS+ECMWF | 0.1 | medido, lowest | 13 | 5 | 38% | 39 | +10.8 | +27.4% | 3% |
| GFS+ECMWF | 0.1 | medido, 1a mitad | 60 | 11 | 38% | 201 | +29.1 | +14.5% | 11% |
| GFS+ECMWF | 0.1 | medido, 2a mitad | 15 | 4 | 47% | 69 | +0.9 | +1.3% | 48% |
| GFS+ECMWF | 0.1 | fijo 0c | 90 | 16 | 41% | 324 | +46.1 | +14.2% | 5% |
| GFS+ECMWF | 0.1 | fijo 1c | 78 | 16 | 40% | 288 | +22.4 | +7.8% | 23% |
| GFS+ECMWF | 0.1 | fijo 2c | 62 | 15 | 40% | 230 | +20.5 | +8.9% | 22% |
| GFS+ECMWF | 0.1 | fijo 3c | 51 | 14 | 43% | 208 | +12.3 | +5.9% | 28% |
| GFS+ECMWF | 0.05 | medido | 179 | 16 | 41% | 658 | +71.7 | +10.9% | 5% |
| GFS+ECMWF | 0.05 | medido, highest | 132 | 16 | 42% | 495 | +64.8 | +13.1% | 5% |
| GFS+ECMWF | 0.05 | medido, lowest | 47 | 6 | 36% | 163 | +6.9 | +4.2% | 43% |
| GFS+ECMWF | 0.05 | medido, 1a mitad | 148 | 12 | 42% | 533 | +87.3 | +16.4% | 1% |
| GFS+ECMWF | 0.05 | medido, 2a mitad | 31 | 4 | 36% | 126 | -15.6 | -12.4% | 100% |
| GFS+ECMWF | 0.05 | fijo 0c | 218 | 16 | 41% | 797 | +103.0 | +12.9% | 5% |
| GFS+ECMWF | 0.05 | fijo 1c | 190 | 16 | 42% | 698 | +91.5 | +13.1% | 3% |
| GFS+ECMWF | 0.05 | fijo 2c | 167 | 16 | 40% | 629 | +41.5 | +6.6% | 18% |
| GFS+ECMWF | 0.05 | fijo 3c | 143 | 16 | 40% | 553 | +16.6 | +3.0% | 38% |

# Mercados de clima lentos: resultados con la regla fija (REGLA.md)

Mercados cerrados en las familias: 3553 (341 eventos); con F leído: 3456; con operaciones bajadas: 2385.

## Volumen por familia y año (US$ miles)

| fam              |   2022 |   2023 |   2024 |   2025 |   2026 |
|:-----------------|-------:|-------:|-------:|-------:|-------:|
| anomalia_mes     |      0 |      0 |  10127 |  36809 |   2826 |
| hielo            |      0 |      0 |      0 |      0 |    151 |
| huracanes        |      0 |    131 |   5618 |   1676 |   1436 |
| lluvia           |      0 |      0 |      0 |     44 |   3430 |
| mes_mas_caluroso |      0 |      0 |  11233 |   8360 |   6506 |
| nieve            |      3 |      0 |     18 |    392 |   3212 |
| tornados         |      0 |      0 |      0 |     25 |   2055 |

Eventos por familia y año:

| fam              |   2022 |   2023 |   2024 |   2025 |   2026 |
|:-----------------|-------:|-------:|-------:|-------:|-------:|
| anomalia_mes     |      0 |      0 |      8 |     14 |     10 |
| hielo            |      0 |      0 |      0 |      0 |      2 |
| huracanes        |      0 |      2 |      6 |     13 |     31 |
| lluvia           |      0 |      0 |      0 |      1 |    118 |
| mes_mas_caluroso |      0 |      0 |     11 |     15 |     15 |
| nieve            |      1 |      0 |      1 |      6 |     10 |
| tornados         |      0 |      0 |      0 |      1 |     76 |

## 1. Calibración (precio de referencia = última operación antes de H)


### H1

|                                |    n |   precio |   gano |
|:-------------------------------|-----:|---------:|-------:|
| ('anomalia_mes', '0-5')        |   84 |    0.013 |  0.024 |
| ('anomalia_mes', '5-20')       |   34 |    0.108 |  0.029 |
| ('anomalia_mes', '20-50')      |   28 |    0.324 |  0.357 |
| ('anomalia_mes', '50-80')      |   18 |    0.619 |  0.667 |
| ('anomalia_mes', '80-95')      |    5 |    0.87  |  0.6   |
| ('anomalia_mes', '95-100')     |    1 |    0.983 |  1     |
| ('huracanes', '0-5')           |   10 |    0.002 |  0     |
| ('huracanes', '5-20')          |    1 |    0.1   |  0     |
| ('huracanes', '95-100')        |    3 |    0.995 |  1     |
| ('lluvia', '0-5')              |  160 |    0.012 |  0.019 |
| ('lluvia', '5-20')             |   70 |    0.097 |  0.114 |
| ('lluvia', '20-50')            |   45 |    0.316 |  0.244 |
| ('lluvia', '50-80')            |   17 |    0.628 |  0.588 |
| ('lluvia', '80-95')            |    5 |    0.881 |  1     |
| ('lluvia', '95-100')           |    6 |    0.985 |  0.833 |
| ('mes_mas_caluroso', '0-5')    |   45 |    0.011 |  0     |
| ('mes_mas_caluroso', '5-20')   |    4 |    0.076 |  0     |
| ('mes_mas_caluroso', '20-50')  |    2 |    0.415 |  1     |
| ('mes_mas_caluroso', '50-80')  |    4 |    0.552 |  0.5   |
| ('mes_mas_caluroso', '80-95')  |    6 |    0.892 |  1     |
| ('mes_mas_caluroso', '95-100') |   15 |    0.975 |  1     |
| ('nieve', '0-5')               |    7 |    0.008 |  0     |
| ('nieve', '5-20')              |    7 |    0.097 |  0.143 |
| ('nieve', '20-50')             |    2 |    0.261 |  0     |
| ('nieve', '50-80')             |    5 |    0.594 |  0.2   |
| ('nieve', '95-100')            |    1 |    0.95  |  1     |
| ('tornados', '0-5')            | 1351 |    0.003 |  0     |
| ('tornados', '5-20')           |    6 |    0.073 |  0.167 |
| ('tornados', '20-50')          |    6 |    0.294 |  0.167 |
| ('tornados', '50-80')          |    5 |    0.692 |  0.8   |
| ('tornados', '80-95')          |    1 |    0.88  |  0     |
| ('tornados', '95-100')         |    9 |    0.991 |  1     |

### H2

|                                |    n |   precio |   gano |
|:-------------------------------|-----:|---------:|-------:|
| ('anomalia_mes', '0-5')        |   94 |    0.012 |  0     |
| ('anomalia_mes', '5-20')       |   31 |    0.104 |  0.161 |
| ('anomalia_mes', '20-50')      |   24 |    0.301 |  0.333 |
| ('anomalia_mes', '50-80')      |   17 |    0.608 |  0.647 |
| ('anomalia_mes', '80-95')      |    5 |    0.882 |  0.8   |
| ('anomalia_mes', '95-100')     |    2 |    0.973 |  1     |
| ('huracanes', '0-5')           |   11 |    0.002 |  0     |
| ('huracanes', '95-100')        |    3 |    0.999 |  1     |
| ('lluvia', '0-5')              |  259 |    0.004 |  0.004 |
| ('lluvia', '5-20')             |    4 |    0.113 |  0     |
| ('lluvia', '20-50')            |    1 |    0.35  |  0     |
| ('lluvia', '50-80')            |    2 |    0.634 |  0.5   |
| ('lluvia', '80-95')            |    5 |    0.895 |  0.8   |
| ('lluvia', '95-100')           |   37 |    0.991 |  1     |
| ('mes_mas_caluroso', '0-5')    |   44 |    0.009 |  0     |
| ('mes_mas_caluroso', '5-20')   |    5 |    0.107 |  0     |
| ('mes_mas_caluroso', '20-50')  |    4 |    0.312 |  0.75  |
| ('mes_mas_caluroso', '50-80')  |    3 |    0.715 |  0.667 |
| ('mes_mas_caluroso', '80-95')  |    2 |    0.922 |  1     |
| ('mes_mas_caluroso', '95-100') |   18 |    0.977 |  1     |
| ('nieve', '0-5')               |   42 |    0.004 |  0     |
| ('nieve', '5-20')              |    1 |    0.058 |  0     |
| ('nieve', '20-50')             |    1 |    0.48  |  0     |
| ('nieve', '50-80')             |    1 |    0.616 |  1     |
| ('nieve', '95-100')            |    6 |    0.986 |  1     |
| ('tornados', '0-5')            | 1704 |    0.002 |  0     |
| ('tornados', '5-20')           |    5 |    0.081 |  0.4   |
| ('tornados', '20-50')          |    1 |    0.235 |  0     |
| ('tornados', '50-80')          |    1 |    0.654 |  0     |
| ('tornados', '80-95')          |    3 |    0.902 |  0.333 |
| ('tornados', '95-100')         |   16 |    0.99  |  1     |

### H3

|                                |   n |   precio |   gano |
|:-------------------------------|----:|---------:|-------:|
| ('anomalia_mes', '0-5')        | 113 |    0.009 |  0     |
| ('anomalia_mes', '5-20')       |  16 |    0.096 |  0     |
| ('anomalia_mes', '20-50')      |  16 |    0.353 |  0.375 |
| ('anomalia_mes', '50-80')      |  13 |    0.593 |  0.692 |
| ('anomalia_mes', '80-95')      |  10 |    0.906 |  1     |
| ('anomalia_mes', '95-100')     |   5 |    0.983 |  1     |
| ('hielo', '0-5')               |   3 |    0.016 |  0     |
| ('hielo', '5-20')              |   3 |    0.117 |  0.333 |
| ('hielo', '20-50')             |   1 |    0.219 |  0     |
| ('huracanes', '0-5')           |   6 |    0.002 |  0     |
| ('huracanes', '95-100')        |   2 |    0.998 |  1     |
| ('lluvia', '0-5')              | 244 |    0.003 |  0.004 |
| ('lluvia', '5-20')             |   3 |    0.139 |  0     |
| ('lluvia', '20-50')            |   1 |    0.35  |  0     |
| ('lluvia', '50-80')            |   1 |    0.519 |  1     |
| ('lluvia', '80-95')            |   5 |    0.913 |  0.8   |
| ('lluvia', '95-100')           |  34 |    0.992 |  1     |
| ('mes_mas_caluroso', '0-5')    |  46 |    0.007 |  0     |
| ('mes_mas_caluroso', '5-20')   |   4 |    0.096 |  0     |
| ('mes_mas_caluroso', '20-50')  |   3 |    0.383 |  0.333 |
| ('mes_mas_caluroso', '50-80')  |   3 |    0.6   |  1     |
| ('mes_mas_caluroso', '80-95')  |   3 |    0.913 |  1     |
| ('mes_mas_caluroso', '95-100') |  18 |    0.983 |  1     |
| ('nieve', '0-5')               |  33 |    0.004 |  0     |
| ('nieve', '95-100')            |   7 |    0.993 |  1     |
| ('tornados', '0-5')            |  79 |    0.003 |  0     |
| ('tornados', '5-20')           |   3 |    0.079 |  0.333 |
| ('tornados', '20-50')          |   1 |    0.22  |  1     |
| ('tornados', '50-80')          |   1 |    0.75  |  0     |
| ('tornados', '80-95')          |   3 |    0.927 |  1     |
| ('tornados', '95-100')         |   9 |    0.985 |  1     |

## 2. Reglas mecánicas (precio de ejecución de la hora previa + comisión + 1 ¢)

| regla | momento | familia | ops | ROI | P(ROI<0) |
|---|---|---|---|---|---|
| a fav Si | H1 | anomalia_mes | 5 | +35.6% | 0.10 |
| b No 5-30 | H1 | anomalia_mes | 6 | -1.9% | 0.72 |
| c Si 5-30 | H1 | anomalia_mes | 5 | +165.3% | 0.09 |
| a fav Si | H1 | lluvia | 8 | +20.5% | 0.17 |
| b No 5-30 | H1 | lluvia | 9 | -24.8% | 0.91 |
| c Si 5-30 | H1 | lluvia | 11 | -44.8% | 0.77 |
| a fav Si | H1 | mes_mas_caluroso | 1 | +1.8% | 0.00 |
| a fav Si | H1 | nieve | 1 | -100.0% | 1.00 |
| c Si 5-30 | H1 | nieve | 2 | -100.0% | 1.00 |
| a fav Si | H1 | tornados | 2 | +17.8% | 0.00 |
| a fav Si | H1 | TODAS | 17 | +16.3% | 0.13 |
| b No 5-30 | H1 | TODAS | 15 | -15.9% | 0.93 |
| c Si 5-30 | H1 | TODAS | 18 | +1.1% | 0.52 |
| a fav Si | H2 | anomalia_mes | 6 | -18.4% | 0.79 |
| b No 5-30 | H2 | anomalia_mes | 5 | -3.4% | 0.57 |
| c Si 5-30 | H2 | anomalia_mes | 10 | -100.0% | 1.00 |
| a fav Si | H2 | huracanes | 2 | +0.1% | 0.00 |
| a fav Si | H2 | lluvia | 5 | +0.2% | 0.00 |
| a fav Si | H2 | mes_mas_caluroso | 1 | +4.2% | 0.00 |
| b No 5-30 | H2 | mes_mas_caluroso | 1 | +36.7% | 0.00 |
| c Si 5-30 | H2 | mes_mas_caluroso | 1 | -100.0% | 1.00 |
| a fav Si | H2 | nieve | 5 | +8.3% | 0.00 |
| a fav Si | H2 | TODAS | 19 | -2.7% | 0.64 |
| b No 5-30 | H2 | TODAS | 6 | +2.6% | 0.39 |
| c Si 5-30 | H2 | TODAS | 11 | -100.0% | 1.00 |
| a fav Si | H3 | anomalia_mes | 10 | -0.3% | 0.49 |
| b No 5-30 | H3 | anomalia_mes | 6 | -7.6% | 0.66 |
| c Si 5-30 | H3 | anomalia_mes | 5 | +55.7% | 0.30 |
| a fav Si | H3 | huracanes | 1 | +0.1% | 0.00 |
| a fav Si | H3 | lluvia | 4 | -10.9% | 0.68 |
| c Si 5-30 | H3 | lluvia | 1 | -100.0% | 1.00 |
| a fav Si | H3 | mes_mas_caluroso | 1 | +0.1% | 0.00 |
| b No 5-30 | H3 | mes_mas_caluroso | 1 | +5.3% | 0.00 |
| a fav Si | H3 | nieve | 6 | +0.1% | 0.00 |
| a fav Si | H3 | tornados | 3 | -27.6% | 0.70 |
| b No 5-30 | H3 | tornados | 1 | -100.0% | 1.00 |
| a fav Si | H3 | TODAS | 25 | -5.4% | 0.76 |
| b No 5-30 | H3 | TODAS | 8 | -17.8% | 0.91 |
| c Si 5-30 | H3 | TODAS | 6 | +14.2% | 0.44 |

## 3. Anomalía global: modelo ERA5 en H3 (comprar si prob − precio ≥ 0,10)

Cajas con modelo y precio: 36 de 173; operaciones: 21; ROI -55.4%, P(ROI<0) 0.99

Brier en H3 (cajas con precio): modelo 0.1348, mercado 0.0916, n=36

## 4. Cosecha después de F: precio de la caja ganadora y dinero operado por debajo de 95 ¢

| familia | eventos | mediana F+1d | F+3d | F+7d | US$ comprados <95 ¢ después de F | por evento |
|---|---|---|---|---|---|---|
| anomalia_mes | 30 | 0.55 | 0.54 | 0.94 | 547,792 | 18,260 |
| hielo | 2 | – | – | – | 6,339 | 3,170 |
| huracanes | 2 | 1.00 | – | – | 0 | 0 |
| lluvia | 40 | 0.99 | 1.00 | – | 868 | 22 |
| mes_mas_caluroso | 25 | 0.98 | 0.98 | 0.98 | 924,368 | 36,975 |
| nieve | 7 | 0.99 | – | – | 8,777 | 1,254 |
| tornados | 14 | 0.97 | 0.97 | 0.98 | 26,740 | 1,910 |

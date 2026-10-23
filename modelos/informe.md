# Comparacion de modelos de pronostico (2026-08-24 a 2026-10-22)

Error = real (METAR) - pronostico, en °C. EMA = error medio absoluto. 'Corregido' = restando el sesgo
de esa serie medido solo con los dias anteriores. Caja = % de dias en la caja ganadora (1 °C o 2 °F).
Cada serie (ciudad + maxima/minima) pesa igual; todos los modelos se miden sobre los mismos dias.

## Horizonte 1 dia(s)

| Modelo | Series | EMA crudo | EMA corregido | Caja (corr.) | |sesgo| |
|---|---|---|---|---|---|
| Promedio | 86 | 1.08 | 0.84 | 40% | 0.72 |
| ECMWF-IA | 86 | 1.33 | 0.93 | 36% | 1.04 |
| ICON | 86 | 1.08 | 0.96 | 35% | 0.57 |
| GFS+ECMWF | 86 | 1.27 | 0.98 | 35% | 0.87 |
| ECMWF-9km | 86 | 1.24 | 1.02 | 33% | 0.77 |
| ECMWF | 86 | 1.31 | 1.03 | 34% | 0.88 |
| BestMatch | 86 | 1.37 | 1.05 | 33% | 0.93 |
| MeteoFrance | 86 | 1.34 | 1.09 | 32% | 0.81 |
| UKMO | 86 | 1.33 | 1.09 | 31% | 0.86 |
| GEM | 86 | 1.54 | 1.16 | 29% | 1.06 |
| GFS | 86 | 1.53 | 1.17 | 30% | 1.05 |
| JMA | 86 | 1.79 | 1.21 | 28% | 1.40 |
| CMA | 86 | 1.67 | 1.24 | 28% | 1.18 |

Elegir modelo por ciudad (elegido con la 1a mitad, medido en la 2a):

| Regla | Series | EMA corregido | Caja |
|---|---|---|---|
| Promedio | 86 | 0.86 | 37% |
| trio de la 1a mitad | 86 | 0.87 | 37% |
| mejor de la 1a mitad | 86 | 0.96 | 36% |
| GFS+ECMWF | 86 | 1.01 | 34% |
| ECMWF | 86 | 1.04 | 33% |
| GFS | 86 | 1.23 | 29% |

El mejor modelo de la 1a mitad quedo entre los 3 mejores de la 2a en 40 de 86 series.

## Horizonte 2 dia(s)

| Modelo | Series | EMA crudo | EMA corregido | Caja (corr.) | |sesgo| |
|---|---|---|---|---|---|
| Promedio | 86 | 1.14 | 0.93 | 36% | 0.70 |
| ECMWF-IA | 86 | 1.39 | 0.98 | 35% | 1.07 |
| GFS+ECMWF | 86 | 1.30 | 1.07 | 33% | 0.80 |
| ICON | 86 | 1.20 | 1.08 | 32% | 0.61 |
| ECMWF-9km | 86 | 1.33 | 1.12 | 30% | 0.78 |
| ECMWF | 86 | 1.41 | 1.13 | 31% | 0.92 |
| BestMatch | 86 | 1.41 | 1.19 | 29% | 0.87 |
| UKMO | 86 | 1.47 | 1.20 | 28% | 0.93 |
| MeteoFrance | 86 | 1.54 | 1.25 | 26% | 0.97 |
| GFS | 86 | 1.59 | 1.29 | 28% | 1.05 |
| JMA | 86 | 1.84 | 1.31 | 26% | 1.40 |
| GEM | 86 | 1.69 | 1.32 | 26% | 1.10 |
| CMA | 86 | 1.75 | 1.33 | 26% | 1.20 |

Elegir modelo por ciudad (elegido con la 1a mitad, medido en la 2a):

| Regla | Series | EMA corregido | Caja |
|---|---|---|---|
| trio de la 1a mitad | 86 | 0.95 | 34% |
| Promedio | 86 | 0.96 | 33% |
| mejor de la 1a mitad | 86 | 1.03 | 33% |
| GFS+ECMWF | 86 | 1.10 | 32% |
| ECMWF | 86 | 1.14 | 31% |
| GFS | 86 | 1.35 | 26% |

El mejor modelo de la 1a mitad quedo entre los 3 mejores de la 2a en 54 de 86 series.

## Horizonte 3 dia(s)

| Modelo | Series | EMA crudo | EMA corregido | Caja (corr.) | |sesgo| |
|---|---|---|---|---|---|
| Promedio | 86 | 1.21 | 1.01 | 34% | 0.70 |
| ECMWF-IA | 86 | 1.44 | 1.04 | 34% | 1.09 |
| GFS+ECMWF | 86 | 1.34 | 1.16 | 30% | 0.78 |
| ICON | 86 | 1.29 | 1.19 | 29% | 0.60 |
| ECMWF-9km | 86 | 1.39 | 1.20 | 29% | 0.80 |
| ECMWF | 86 | 1.47 | 1.22 | 29% | 0.93 |
| BestMatch | 86 | 1.45 | 1.26 | 28% | 0.86 |
| UKMO | 86 | 1.58 | 1.32 | 27% | 0.98 |
| GFS | 86 | 1.65 | 1.39 | 26% | 1.05 |
| MeteoFrance | 86 | 1.67 | 1.39 | 25% | 0.99 |
| JMA | 86 | 1.99 | 1.44 | 24% | 1.48 |
| GEM | 86 | 1.81 | 1.45 | 24% | 1.15 |
| CMA | 86 | 1.84 | 1.46 | 24% | 1.21 |

Elegir modelo por ciudad (elegido con la 1a mitad, medido en la 2a):

| Regla | Series | EMA corregido | Caja |
|---|---|---|---|
| Promedio | 86 | 1.05 | 32% |
| trio de la 1a mitad | 86 | 1.08 | 32% |
| mejor de la 1a mitad | 86 | 1.16 | 31% |
| GFS+ECMWF | 86 | 1.19 | 30% |
| ECMWF | 86 | 1.22 | 28% |
| GFS | 86 | 1.45 | 26% |

El mejor modelo de la 1a mitad quedo entre los 3 mejores de la 2a en 39 de 86 series.

## Horizonte 5 dia(s)

| Modelo | Series | EMA crudo | EMA corregido | Caja (corr.) | |sesgo| |
|---|---|---|---|---|---|
| Promedio | 86 | 1.40 | 1.26 | 28% | 0.67 |
| ECMWF-IA | 86 | 1.60 | 1.26 | 28% | 1.07 |
| GFS+ECMWF | 86 | 1.58 | 1.42 | 26% | 0.82 |
| ECMWF-9km | 86 | 1.64 | 1.48 | 24% | 0.85 |
| ECMWF | 86 | 1.69 | 1.49 | 25% | 0.94 |
| ICON | 86 | 1.59 | 1.55 | 24% | 0.60 |
| BestMatch | 86 | 1.74 | 1.58 | 22% | 0.93 |
| UKMO | 86 | 1.84 | 1.63 | 21% | 1.00 |
| GFS | 86 | 1.91 | 1.70 | 22% | 1.09 |
| GEM | 86 | 2.07 | 1.72 | 21% | 1.22 |
| JMA | 86 | 2.23 | 1.74 | 22% | 1.49 |

Elegir modelo por ciudad (elegido con la 1a mitad, medido en la 2a):

| Regla | Series | EMA corregido | Caja |
|---|---|---|---|
| Promedio | 86 | 1.30 | 27% |
| trio de la 1a mitad | 86 | 1.31 | 27% |
| mejor de la 1a mitad | 86 | 1.38 | 26% |
| GFS+ECMWF | 86 | 1.45 | 25% |
| ECMWF | 86 | 1.50 | 24% |
| GFS | 86 | 1.76 | 21% |

El mejor modelo de la 1a mitad quedo entre los 3 mejores de la 2a en 52 de 86 series.

## Mejor modelo por serie (horizonte 1 dia, EMA corregido, todos los dias)

| Serie | n | Mejor | EMA | 2o | EMA | GFS+ECMWF | Promedio |
|---|---|---|---|---|---|---|---|
| highest|amsterdam | 54 | ECMWF-9km | 0.59 | UKMO | 0.59 | 0.58 | 0.55 |
| highest|ankara | 54 | ECMWF-IA | 0.79 | GEM | 0.86 | 0.84 | 0.80 |
| highest|atlanta | 54 | ECMWF-IA | 0.65 | ECMWF | 0.73 | 0.73 | 0.61 |
| highest|austin | 54 | ECMWF-IA | 0.76 | GEM | 0.83 | 0.82 | 0.76 |
| highest|beijing | 54 | ICON | 0.83 | ECMWF-IA | 0.85 | 1.06 | 0.81 |
| highest|buenos-aires | 54 | ECMWF | 0.97 | ICON | 0.99 | 1.05 | 0.96 |
| highest|busan | 54 | ECMWF-IA | 0.71 | GEM | 0.82 | 0.92 | 0.70 |
| highest|cape-town | 54 | GFS | 1.17 | MeteoFrance | 1.17 | 1.05 | 0.95 |
| highest|chengdu | 54 | ICON | 1.36 | ECMWF-IA | 1.43 | 1.48 | 1.36 |
| highest|chicago | 54 | ECMWF-IA | 0.90 | ICON | 1.01 | 1.26 | 1.01 |
| highest|chongqing | 54 | ECMWF-IA | 0.85 | GFS | 1.21 | 1.10 | 0.99 |
| highest|dallas | 54 | GEM | 0.90 | UKMO | 0.98 | 0.97 | 0.87 |
| highest|guangzhou | 54 | ECMWF-IA | 0.79 | ECMWF | 0.98 | 0.95 | 0.87 |
| highest|helsinki | 54 | ECMWF-IA | 0.55 | UKMO | 0.55 | 0.58 | 0.50 |
| highest|houston | 54 | ICON | 0.88 | ECMWF-IA | 0.96 | 0.95 | 0.78 |
| highest|istanbul | 54 | ECMWF | 0.71 | MeteoFrance | 0.72 | 0.92 | 0.65 |
| highest|jeddah | 54 | ICON | 0.62 | ECMWF-9km | 0.66 | 0.72 | 0.67 |
| highest|karachi | 54 | ICON | 0.81 | ECMWF-IA | 0.86 | 0.92 | 0.75 |
| highest|kuala-lumpur | 54 | JMA | 0.70 | ECMWF-IA | 0.80 | 0.79 | 0.69 |
| highest|london | 54 | ECMWF-IA | 0.71 | ICON | 0.80 | 0.77 | 0.70 |
| highest|los-angeles | 54 | UKMO | 1.16 | GFS | 1.21 | 1.48 | 1.14 |
| highest|madrid | 54 | ECMWF-IA | 0.72 | ECMWF-9km | 0.73 | 0.73 | 0.72 |
| highest|manila | 54 | ECMWF-IA | 0.92 | MeteoFrance | 0.98 | 0.88 | 0.86 |
| highest|mexico-city | 54 | ECMWF-IA | 0.91 | ICON | 0.92 | 1.03 | 0.75 |
| highest|miami | 54 | ECMWF-IA | 0.78 | ECMWF-9km | 0.80 | 0.90 | 0.71 |
| highest|milan | 54 | BestMatch | 0.66 | ICON | 0.68 | 0.90 | 0.61 |
| highest|moscow | 54 | ECMWF-IA | 0.79 | ICON | 0.84 | 0.93 | 0.83 |
| highest|munich | 54 | ECMWF-IA | 0.80 | MeteoFrance | 0.82 | 0.85 | 0.77 |
| highest|nyc | 54 | ECMWF-IA | 0.79 | ICON | 0.83 | 0.90 | 0.70 |
| highest|panama-city | 53 | ECMWF-IA | 0.75 | JMA | 0.78 | 0.96 | 0.76 |
| highest|qingdao | 54 | ECMWF-IA | 0.61 | ECMWF | 0.67 | 0.66 | 0.54 |
| highest|san-francisco | 54 | ECMWF-IA | 1.13 | MeteoFrance | 1.30 | 1.50 | 1.15 |
| highest|sao-paulo | 54 | ECMWF-IA | 1.41 | ECMWF | 1.49 | 1.58 | 1.41 |
| highest|seattle | 54 | ECMWF-IA | 0.84 | ICON | 0.89 | 0.92 | 0.84 |
| highest|seoul | 54 | ECMWF-IA | 0.67 | ECMWF | 0.81 | 0.91 | 0.87 |
| highest|shanghai | 54 | ECMWF-IA | 0.72 | ICON | 0.75 | 0.74 | 0.74 |
| highest|shenzhen | 54 | ICON | 0.91 | JMA | 0.95 | 0.77 | 0.79 |
| highest|singapore | 54 | JMA | 0.73 | GFS | 0.77 | 0.75 | 0.71 |
| highest|taipei | 54 | ECMWF | 0.91 | ECMWF-IA | 0.94 | 0.88 | 0.84 |
| highest|tel-aviv | 54 | ECMWF-9km | 0.54 | CMA | 0.55 | 0.73 | 0.56 |
| highest|tokyo | 54 | ICON | 0.97 | ECMWF-IA | 0.99 | 0.96 | 0.85 |
| highest|toronto | 54 | ECMWF-IA | 0.86 | ICON | 0.92 | 1.07 | 0.90 |
| highest|warsaw | 54 | ECMWF-IA | 0.73 | UKMO | 0.74 | 0.83 | 0.65 |
| highest|wellington | 54 | ECMWF | 0.67 | ECMWF-9km | 0.69 | 0.63 | 0.64 |
| highest|wuhan | 54 | ECMWF-IA | 0.89 | ICON | 1.11 | 1.22 | 1.17 |
| lowest|amsterdam | 54 | ECMWF-IA | 0.84 | ICON | 0.89 | 0.99 | 0.86 |
| lowest|ankara | 54 | BestMatch | 0.96 | ICON | 1.07 | 2.00 | 1.33 |
| lowest|atlanta | 54 | CMA | 0.70 | ECMWF-9km | 0.79 | 0.79 | 0.77 |
| lowest|austin | 54 | ECMWF-IA | 0.83 | GEM | 0.86 | 1.22 | 1.11 |
| lowest|beijing | 54 | ECMWF-IA | 1.13 | ECMWF-9km | 1.24 | 1.84 | 1.11 |
| lowest|buenos-aires | 54 | ECMWF-IA | 1.55 | GEM | 1.59 | 1.82 | 1.64 |
| lowest|busan | 54 | ECMWF-IA | 0.88 | ECMWF-9km | 0.89 | 0.98 | 0.94 |
| lowest|cape-town | 54 | ICON | 1.12 | ECMWF | 1.19 | 1.36 | 1.08 |
| lowest|chengdu | 54 | ECMWF-IA | 0.65 | CMA | 0.79 | 0.87 | 0.67 |
| lowest|chicago | 54 | ECMWF | 0.80 | GFS | 0.86 | 0.76 | 0.68 |
| lowest|chongqing | 54 | ECMWF-IA | 0.67 | GFS | 0.83 | 0.84 | 0.80 |
| lowest|dallas | 54 | ECMWF | 0.76 | ICON | 0.88 | 0.74 | 0.64 |
| lowest|guangzhou | 54 | ECMWF | 0.84 | ECMWF-IA | 0.92 | 0.87 | 0.97 |
| lowest|helsinki | 54 | ECMWF-IA | 1.19 | GEM | 1.52 | 1.70 | 1.55 |
| lowest|houston | 54 | CMA | 0.68 | ECMWF-9km | 0.78 | 0.74 | 0.66 |
| lowest|istanbul | 54 | ECMWF-9km | 0.82 | ECMWF | 0.84 | 1.19 | 0.96 |
| lowest|jeddah | 54 | ECMWF-IA | 0.46 | ECMWF | 0.54 | 0.51 | 0.49 |
| lowest|karachi | 54 | ECMWF-9km | 0.58 | BestMatch | 0.58 | 0.80 | 0.62 |
| lowest|london | 54 | MeteoFrance | 0.48 | ICON | 0.60 | 0.70 | 0.47 |
| lowest|los-angeles | 54 | UKMO | 0.84 | MeteoFrance | 0.85 | 0.66 | 0.69 |
| lowest|madrid | 54 | ECMWF-IA | 0.69 | UKMO | 0.89 | 1.14 | 0.64 |
| lowest|mexico-city | 54 | ECMWF-9km | 0.82 | BestMatch | 0.82 | 0.87 | 0.78 |
| lowest|miami | 54 | ECMWF | 0.83 | ECMWF-IA | 0.86 | 0.81 | 0.92 |
| lowest|milan | 54 | ICON | 0.97 | ECMWF-IA | 0.99 | 1.43 | 1.00 |
| lowest|moscow | 54 | ECMWF-9km | 1.02 | ECMWF | 1.02 | 1.07 | 0.99 |
| lowest|munich | 54 | ECMWF-IA | 1.05 | MeteoFrance | 1.08 | 1.66 | 1.19 |
| lowest|nyc | 54 | ICON | 0.66 | UKMO | 0.89 | 1.24 | 0.99 |
| lowest|qingdao | 54 | UKMO | 0.97 | ECMWF-9km | 1.01 | 1.24 | 0.91 |
| lowest|san-francisco | 54 | UKMO | 0.77 | GFS | 0.90 | 0.99 | 0.83 |
| lowest|sao-paulo | 54 | ECMWF-IA | 0.55 | ECMWF-9km | 0.76 | 0.79 | 0.65 |
| lowest|seattle | 54 | UKMO | 0.77 | ECMWF | 0.78 | 0.71 | 0.60 |
| lowest|seoul | 54 | ECMWF-IA | 0.61 | ICON | 0.84 | 0.77 | 0.63 |
| lowest|shanghai | 54 | CMA | 0.68 | ECMWF-IA | 0.69 | 0.69 | 0.64 |
| lowest|shenzhen | 54 | ECMWF | 0.79 | ECMWF-IA | 0.90 | 0.76 | 0.97 |
| lowest|taipei | 54 | ICON | 0.83 | GFS | 0.84 | 0.79 | 0.80 |
| lowest|tel-aviv | 54 | ICON | 0.60 | BestMatch | 0.64 | 0.84 | 0.61 |
| lowest|tokyo | 54 | MeteoFrance | 0.80 | ECMWF-IA | 0.86 | 0.87 | 0.88 |
| lowest|toronto | 54 | ECMWF | 0.84 | ECMWF-9km | 0.87 | 0.78 | 0.72 |
| lowest|warsaw | 54 | ECMWF-IA | 0.84 | GEM | 0.99 | 1.44 | 1.08 |
| lowest|wellington | 54 | ICON | 0.92 | ECMWF | 0.95 | 0.85 | 0.92 |
| lowest|wuhan | 54 | ICON | 0.83 | ECMWF-IA | 0.90 | 0.97 | 0.73 |

## Ensamble del bot contra los modelos (mismos dias, sin corregir, desde el 20-oct)

| Modelo | n | EMA crudo |
|---|---|---|
| ICON | 162 | 1.09 |
| Promedio | 162 | 1.16 |
| ECMWF-9km | 162 | 1.21 |
| MeteoFrance | 162 | 1.26 |
| BestMatch | 162 | 1.28 |
| ECMWF | 162 | 1.33 |
| ECMWF-IA | 162 | 1.36 |
| Ensamble del bot | 162 | 1.36 |
| GFS+ECMWF | 162 | 1.41 |
| UKMO | 162 | 1.45 |
| GEM | 162 | 1.62 |
| GFS | 162 | 1.77 |
| JMA | 162 | 1.95 |
| CMA | 162 | 1.99 |

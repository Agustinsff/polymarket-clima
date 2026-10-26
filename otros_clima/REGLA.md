# Regla fija (escrita el 26-oct-2026 03:10Z, antes de mirar precios u operaciones)

Familias (mercados de Polymarket ya resueltos, varias cajas por evento):
anomalía global del mes (GISTEMP), "mes más caluroso" (GISTEMP), lluvia del mes por ciudad (NOAA),
nieve (NOAA), tornados del mes (NCEI), conteo de huracanes/tormentas (NHC), hielo ártico (NSIDC).

Precio: el de ejecución real, sacado de las operaciones taker (`trades.csv.gz`): para comprar el Sí a la hora H,
el precio medio de las compras de Sí (o 1 − ventas de No) de la hora anterior a H; si no hubo, no hay operación.
Comisión: la tasa real del mercado (`comision`, feeSchedule) sobre p·(1−p). Más 1 ¢ de deslizamiento.

Momentos (H), relativos al fin del período medido (fin de mes / fin de semana / fin de temporada = F)
y al cierre del mercado (C = closedTime):
- H1 = F − 7 días
- H2 = F (el dato del período ya casi entero es público: ERA5, lluvia diaria, informes del SPC)
- H3 = F + (C − F)/2 (dato del período completo público, la fuente oficial todavía no publicó)

Medidas:
1. Calibración por familia y momento: precio en cajas de 0–5, 5–20, 20–50, 50–80, 80–95, 95–100 ¢ vs. frecuencia con que ganó.
2. Tres reglas mecánicas, en cada momento:
   a. comprar el Sí de la caja favorita (la más cara) del evento;
   b. comprar el No de toda caja con Sí entre 5 y 30 ¢;
   c. comprar el Sí de toda caja con Sí entre 5 y 30 ¢.
3. Sólo anomalía global: modelo ERA5 (anomalía ERA5 del mes + desvío medio GISTEMP−ERA5 de ese mes del año en los
   10 años previos + desvío medio de los últimos 12 meses; error normal con sd 0,045 °C) en H3. Comprar la caja si
   prob. del modelo − precio ≥ 0,10.
4. Cosecha después de F: precio de la caja ganadora en F+1, F+3, F+7 días y dólares operados en esa caja por debajo de 95 ¢ después de F.

Criterio para seguir: alguna regla con ROI > 0 con comisión y 1 ¢ de deslizamiento en ≥ 2 familias o con
P(ROI<0) < 10 % por bootstrap de eventos, y con volumen suficiente para US$ 50 por evento.

# Conversión °F/°C en cajas de EE.UU. (corte 2026-11-04 13:57 UTC)

Regla fija: `fahrenheit/REGLA.md`. Cajas de 2 °F con 12 décimas de °C (el resto tiene 11): 10-11, 28-29, 46-47, 64-65, 82-83, 100-101 °F. Esperado si la física manda: +0,087 (log 12/11).

## A. Física: ¿las cajas de 12 salen más seguido? (METAR de rutina 2023–2026, estaciones de EE.UU.)

Estaciones: 11, días-estación: 15,444. Diferencia 12 vs 11: **+0.003** [-0.061, +0.068], P(≤0) = 0.452 (cajas-grupo: 251 de 12, 2013 de 11; bootstrap por estación-año).

Por qué: en EE.UU. el sensor ASOS mide en °F enteros y el METAR lo pasa a décimas de °C; al volver a °F, el 99.9 % de las máximas cae exacto en un °F entero. O sea, la conversión es ida y vuelta sin pérdida y todas las cajas de 2 °F tienen el mismo peso: el efecto de las cajas de 12 no existe.

## B. Mercado: ¿el precio ya lo cobra? (fotos del libro cada 5 min, medidor maker, 26-oct en adelante)

Eventos de EE.UU.: 229; con caja de 12 entre vecinas: 85. Diferencia 12 vs 11 en precio: **-0.091** [-0.208, +0.031] (bootstrap por evento).

Veredicto según la regla: física NO PASA; mercado sin decidir (intervalo incluye la física y el 0).

## C. Plata (informativo): comprar 10 acciones del Sí de cada caja de 12 (libro con spread ≤ 5 ¢, precio real de 10 acciones), con comisión 0,05·p(1−p)

| momento | n | ganadas | ask medio | resultado US$ | ROI |
|---|---|---|---|---|---|
| M0 | 55 | 16 | 0.26 | +10.60 | +7.1 % |
| M1 | 57 | 14 | 0.26 | -11.27 | -7.5 % |
| M2 | 24 | 4 | 0.20 | -9.39 | -19.0 % |

Muestra chica: no decide nada (ver regla).


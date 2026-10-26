# Favorito tardío en los Up/Down de 4 horas y 1 día (regla fija)

Fijada el 26-oct-2026 ~18:55 UTC, antes de mirar los resultados de estas ventanas cerca del cierre. Los datos
(60 días, BTC y ETH) ya estaban bajados para el estudio de `REGLA.md`; ese estudio solo miró hasta el 90 % de la
ventana (24 min antes del cierre en 4 h, 2,4 h en 1 día), donde los favoritos dieron +0,5 a +1 % (sin regla que
pase). Acá se mira **6 minutos antes del cierre**, el mismo minuto en que ya opera el bot. No se opera.

## Regla principal (dos pruebas, una por ventana)
- A **6 min del cierre**, con el último precio del Up de los 6 min anteriores (4 h: puntos de 1 min; 1 día: de 5 min):
  si un lado está entre **70 y 90 ¢** (≥ 0,70 y < 0,90), comprar 10 acciones de ese lado.
- Costo: precio + **1 ¢** por acción + comisión del mercado (0,07 si falta).
- **Pasa** (cada ventana por separado) si ROI > 0 con **P(ROI ≤ 0) < 2,5 %** (5 % repartido entre las dos pruebas)
  por bootstrap de bloques (activo, día), **y** positivo en las dos mitades de las fechas **y** en BTC y ETH.
- 1 día tiene ~120 mercados: si da menos de 40 operaciones se informa como "sin datos suficientes", no como hallazgo.

## Se informa además (no decide)
- 0 y 2 ¢ de costo extra; 3 y 10 min antes del cierre; calibración por tramos 60–70 / 70–80 / 80–90 / 90–100 ¢.
- Control: 1 h a 6 min con 1 ¢ tiene que dar 545 ops y +4,8 %.

## Si pasa
Las de 4 h cierran en hora en punto, así que el bot ya está despierto en ese minuto: se sumarían a la misma
estrategia como serie nueva (regla nueva: se consulta a Agus y se prueba en papel antes del real).

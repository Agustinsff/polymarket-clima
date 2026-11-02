# Medidor maker: datos al 2026-11-02 09:24 UTC

Fotos del libro cada 5 min desde 2026-10-26 14:30 UTC: 1974 fotos, 8 días, 1,326,602 cajas-foto con precio entre 3 y 97 ¢ (clima 1,230,819, cripto 95,783). Regla fija: maker/REGLA.md.

## 1. Pozos de recompensa (lo que reparte Polymarket por día)

Promedio por foto (solo cajas cuyo evento todavía no terminó):

| grupo | cajas | con_pozo | pozo |
|---|---|---|---|
| clima | 579 | 409 | 10841 |
| cripto | 49 | 0 | 0 |

`pozo` = suma de US$/día que reparten las cajas vivas de ese grupo entre todos los makers.

## 2. Recompensa estimada si tuviéramos 100 acciones por lado en TODAS las cajas vivas

**Orden a 1 ¢ del medio** (US$/día, suma de todas las cajas vivas; promedio, mediana, mín y máx de las fotos):

| grupo | mean | median | min | max |
|---|---|---|---|---|
| clima | 5130.7 | 4887.8 | 3296.9 | 9962.6 |
| cripto | 0.0 | 0.0 | 0.0 | 0.0 |

**Orden a 2 ¢ del medio** (US$/día, suma de todas las cajas vivas; promedio, mediana, mín y máx de las fotos):

| grupo | mean | median | min | max |
|---|---|---|---|---|
| clima | 4165.8 | 3917.1 | 2340.6 | 9689.7 |
| cripto | 0.0 | 0.0 | 0.0 | 0.0 |

Por caja con pozo (orden a 1 ¢): recompensa media por caja-día, % de fotos en que no hay ningún otro maker dentro del spread premiado (`solos`) y competencia mediana (puntaje de los demás):

| grupo | cajas_con_pozo | rec_media_caja | pct_solos | comp_mediana |
|---|---|---|---|---|
| clima | 2959 | 12.53 | +24.0 % | 42 |

Capital: 100 acciones por lado inmovilizan ≈ US$ 100 por caja. Recompensa por US$ 100 de capital y día = la columna `rec_media_caja`.

Clima, por horas hasta el cierre del evento (orden a 1 ¢, por caja con pozo):

| tramo | cajas_foto | pozo | rec | solos |
|---|---|---|---|---|
| 0-6 h | 53110 | 32.7 | 22.51 | +30.1 % |
| 6-12 h | 85493 | 31.4 | 18.47 | +22.0 % |
| 12-24 h | 188074 | 29.4 | 11.90 | +10.4 % |
| 24-36 h | 199391 | 27.2 | 9.52 | +9.9 % |
| 36-48 h | 205163 | 23.0 | 10.92 | +33.1 % |
| >48 h | 76499 | 16.9 | 12.72 | +68.1 % |

Clima, por hora local de la ciudad:

| hl | cajas_foto | rec | solos |
|---|---|---|---|
| 0-5 h | 203528 | 12.22 | +18.9 % |
| 6-11 h | 201798 | 13.99 | +25.8 % |
| 12-17 h | 202538 | 12.78 | +30.7 % |
| 18-23 h | 199866 | 11.12 | +20.6 % |

Clima, las 12 series con más recompensa por caja (orden a 1 ¢):

| serie | cajas_foto | pozo | rec | solos |
|---|---|---|---|---|
| lowest|hong-kong | 10278 | 26.3 | 21.64 | +56.1 % |
| lowest|wellington | 11460 | 23.5 | 20.35 | +72.6 % |
| lowest|london | 14576 | 24.5 | 18.19 | +57.2 % |
| lowest|los-angeles | 6878 | 21.8 | 18.12 | +74.7 % |
| lowest|madrid | 12489 | 22.5 | 17.80 | +61.8 % |
| lowest|tokyo | 15764 | 21.0 | 16.04 | +63.5 % |
| lowest|nyc | 16308 | 21.4 | 15.48 | +53.9 % |
| lowest|shanghai | 17171 | 18.6 | 15.39 | +75.1 % |
| lowest|warsaw | 11501 | 19.1 | 14.69 | +55.5 % |
| highest|istanbul | 13597 | 28.6 | 14.34 | +25.5 % |
| lowest|seoul | 19115 | 17.6 | 14.33 | +67.9 % |
| lowest|miami | 16290 | 19.6 | 14.07 | +60.8 % |

## 3. Llenados simulados (alguien operó a peor precio que nuestra orden)

94,342 llenados en 8 días; 82,513 ya resueltos. Por grupo y distancia de la orden, por día de medición:

| grupo | dist_c | llenados_d | acciones_d | reembolso_d | pnl_5_d | pnl_60_d | pnl_res_d | pnl_60_acc | pnl_res_acc |
|---|---|---|---|---|---|---|---|---|---|
| clima | 1 | 6920 | 134018 | 43.45 | 5035.0 | 4244.6 | -5332.6 | 3.17 | -4.65 |
| clima | 2 | 4397 | 86773 | 29.46 | 4468.6 | 3776.2 | -3919.5 | 4.35 | -5.24 |
| cripto | 1 | 309 | 13237 | 28.61 | 91.8 | 116.0 | -122.1 | 0.88 | -0.98 |
| cripto | 2 | 166 | 7242 | 17.62 | 97.5 | 124.8 | -190.9 | 1.72 | -2.76 |

`pnl_60_d` = US$/día que vale lo llenado 60 min después (precio medio del libro) menos lo que pagamos; `pnl_res_d` = lo mismo a la resolución, solo de los ya resueltos (`_acc` = centavos por acción).

- clima, orden a 1 ¢: resultado por llenado -17.3 % del capital de esa orden (t = -17.0, n = 48,155).
- clima, orden a 2 ¢: resultado por llenado -19.5 % del capital de esa orden (t = -15.7, n = 30,765).
- cripto, orden a 1 ¢: resultado por llenado -2.2 % del capital de esa orden (t = -0.5, n = 2,323).
- cripto, orden a 2 ¢: resultado por llenado -5.7 % del capital de esa orden (t = -1.1, n = 1,270).

Clima, orden a 1 ¢, resueltos, por lado y precio de nuestra orden:

| lado | tramo_p | n | acc | pnl | pnl_acc | pnl_pct |
|---|---|---|---|---|---|---|
| compra | 3-10 ¢ | 8406 | 151003 | -1985.0 | -1.31 | -14.1 % |
| compra | 10-30 ¢ | 8697 | 145706 | -8954.1 | -6.15 | -30.4 % |
| compra | 30-70 ¢ | 9343 | 151601 | -9562.7 | -6.31 | -16.1 % |
| compra | 70-90 ¢ | 777 | 13615 | -749.1 | -5.50 | -3.9 % |
| compra | 90-97 ¢ | 253 | 5703 | 118.6 | 2.08 | +0.1 % |
| venta | 3-10 ¢ | 2591 | 74586 | -1375.7 | -1.84 | -2.0 % |
| venta | 10-30 ¢ | 6299 | 155665 | -3349.4 | -2.15 | -3.1 % |
| venta | 30-70 ¢ | 9000 | 158666 | -13043.5 | -8.22 | -15.5 % |
| venta | 70-90 ¢ | 1756 | 32445 | -2982.8 | -9.19 | -43.0 % |
| venta | 90-97 ¢ | 1033 | 28797 | -776.9 | -2.70 | -55.3 % |

## 4. Neto diario (recompensa + reembolso + resultado de los llenados)

Con 100 acciones por lado en todas las cajas vivas con precio 3–97 ¢ (es lo que simula la regla), por día de medición:

| grupo | dist_c | recompensa | reembolso | llenados_60min | llenados_resol | neto_60 | neto_resol | cajas | capital |
|---|---|---|---|---|---|---|---|---|---|
| clima | 1 | 5130.7 | 43.45 | 4244.6 | -6229.4 | 9418.8 | -1055.2 | 579 | 57885 |
| clima | 2 | 4165.8 | 29.46 | 3776.2 | -4548.9 | 7971.4 | -353.6 | 579 | 57885 |
| cripto | 1 | 0.0 | 28.61 | 116.0 | -129.8 | 144.6 | -101.1 | 49 | 4852 |
| cripto | 2 | 0.0 | 17.62 | 124.8 | -200.2 | 142.4 | -182.6 | 49 | 4852 |

US$/día. `capital` = colateral inmovilizado (≈ US$ 100 por caja). `neto_resol` usa el resultado por acción de los llenados ya resueltos aplicado a todas las acciones llenadas.

Clima, orden a 1 ¢, día por día (recompensa estimada, llenados a 60 min, neto a 60 min):

| dia | recompensa | acc | reemb | pnl60 | neto_60 |
|---|---|---|---|---|---|
| 2026-10-26 | 4660.3 | 52698 | 0.00 | 244.1 | 4904.4 |
| 2026-10-27 | 5167.9 | 169015 | 0.00 | 4778.7 | 9946.5 |
| 2026-10-28 | 4552.3 | 143939 | 0.00 | 3985.6 | 8537.8 |
| 2026-10-29 | 5294.5 | 167482 | 0.00 | 4722.2 | 10016.7 |
| 2026-10-30 | 5141.4 | 165821 | 0.00 | 7325.5 | 12466.9 |
| 2026-10-31 | 5021.6 | 163312 | 0.00 | 5488.2 | 10509.8 |
| 2026-11-01 | 5482.9 | 148415 | 229.92 | 4523.6 | 10236.4 |
| 2026-11-02 | 5926.8 | 61460 | 117.68 | 2888.8 | 8933.3 |

Neto a 60 min: +9444.0 US$/día, t = 12.3 con 8 días.

## 5. ¿Dónde conviene? Recompensa menos llenados por caja-día (clima, 1 ¢, a 60 min)

Mejores y peores series (neto por caja y día):

| serie | cajas | rec | neto_dia |
|---|---|---|---|
| highest|seoul | 54 | 10.07 | 44.17 |
| highest|hong-kong | 47 | 9.28 | 38.52 |
| highest|guangzhou | 55 | 9.36 | 36.55 |
| highest|shenzhen | 51 | 9.27 | 36.32 |
| highest|tokyo | 60 | 8.82 | 34.89 |
| lowest|hong-kong | 55 | 13.73 | 34.47 |
| highest|busan | 46 | 10.35 | 32.29 |
| highest|chongqing | 51 | 10.62 | 31.81 |
| highest|chicago | 50 | 8.19 | 11.64 |
| highest|dallas | 56 | 8.71 | 10.43 |
| highest|seattle | 53 | 7.32 | 9.72 |
| highest|denver | 46 | 8.84 | 7.29 |
| highest|cape-town | 59 | 8.36 | 7.04 |

58 de 58 series con neto positivo por caja-día.

## 6. Por ancho del libro (spread real bid-ask al momento de poner la orden), clima

Las órdenes a 1 ¢ del medio en un libro de 40 ¢ de ancho quedan muy adentro: el medio no es el precio justo. Esto separa los libros apretados (donde el medio sí vale algo) de los anchos.

**Orden a 1 ¢** (US$/día):

| spread | cajas | capital | recompensa | rec_pes | acciones_d | pnl_res_acc | llenados_resol | reemb | neto | neto_pes | neto_por_100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ≤2 ¢ | 77 | 7748 | 460.2 | 327.5 | 12844 | -1.93 | -247.5 | 3.98 | 216.6 | 84.0 | 2.80 |
| 2-5 ¢ | 250 | 25043 | 2370.2 | 1577.5 | 68918 | -2.62 | -1808.4 | 21.28 | 583.1 | -209.5 | 2.33 |
| 5-10 ¢ | 73 | 7266 | 765.8 | 401.9 | 30742 | -3.82 | -1172.8 | 7.99 | -399.0 | -763.0 | -5.49 |
| 10-20 ¢ | 45 | 4521 | 677.0 | 338.5 | 13403 | -8.03 | -1075.8 | 5.90 | -392.9 | -731.4 | -8.69 |
| >20 ¢ | 133 | 13306 | 857.6 | 428.8 | 8143 | -22.99 | -1872.3 | 4.30 | -1010.5 | -1439.3 | -7.59 |

**Orden a 2 ¢** (US$/día):

| spread | cajas | capital | recompensa | rec_pes | acciones_d | pnl_res_acc | llenados_resol | reemb | neto | neto_pes | neto_por_100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ≤2 ¢ | 77 | 7748 | 289.7 | 223.1 | 5940 | -1.59 | -94.6 | 2.19 | 197.2 | 130.7 | 2.55 |
| 2-5 ¢ | 250 | 25043 | 1628.6 | 1161.4 | 32491 | -2.34 | -760.4 | 10.63 | 878.9 | 411.7 | 3.51 |
| 5-10 ¢ | 73 | 7266 | 713.0 | 380.7 | 27302 | -3.35 | -913.7 | 6.80 | -193.9 | -526.2 | -2.67 |
| 10-20 ¢ | 45 | 4521 | 677.0 | 338.5 | 13000 | -7.50 | -974.4 | 5.64 | -291.8 | -630.3 | -6.45 |
| >20 ¢ | 133 | 13306 | 857.6 | 428.8 | 8043 | -22.16 | -1782.1 | 4.20 | -920.4 | -1349.2 | -6.92 |

`rec_pes` / `neto_pes` = recompensa y neto si los otros makers copian nuestra orden (la competencia suma otro tanto como lo nuestro): es lo que pasa cuando los bots rivales se acomodan. `neto_por_100` = neto diario (optimista) por cada US$ 100 de capital (una caja). Spread mediano del libro en clima: 4.0 ¢; 13 % de las cajas-foto con spread ≤ 2 ¢.

## 7. Día por día: clima, libros con spread ≤ 5 ¢, orden a 2 ¢, recompensa pesimista

| dia | cajas | rec_pes | acc | reemb | llenados_resol | neto_pes | por_100 |
|---|---|---|---|---|---|---|---|
| 2026-10-26 | 352 | 1597.7 | 14829 | 0.00 | -330.2 | 1267.5 | 3.60 |
| 2026-10-27 | 343 | 1559.3 | 46482 | 0.00 | -1035.0 | 524.3 | 1.53 |
| 2026-10-28 | 345 | 1336.7 | 39887 | 0.00 | -888.2 | 448.5 | 1.30 |
| 2026-10-29 | 315 | 1303.6 | 44905 | 0.00 | -999.9 | 303.7 | 0.96 |
| 2026-10-30 | 321 | 1306.2 | 49570 | 0.00 | -1103.8 | 202.4 | 0.63 |
| 2026-10-31 | 325 | 1252.2 | 46140 | 0.00 | -1027.4 | 224.8 | 0.69 |
| 2026-11-01 | 314 | 1430.7 | 46439 | 68.35 | -1034.1 | 465.0 | 1.48 |
| 2026-11-02 | 312 | 1472.9 | 19196 | 34.26 | -427.5 | 1079.8 | 3.47 |

Neto pesimista por US$ 100 de capital: +1.71 US$/día, t = 4.1 con 8 días (el resultado de los llenados usa el promedio por acción de todos los resueltos, -2.23 ¢).

Lo que NO está en estos números: que Polymarket mide cada minuto y nosotros cada 5 (recompensa optimista); que los rivales pueden apretar más que 'copiarnos'; que las fotos son del libro visible (no se ven las órdenes que entran y salen entre fotos); gas y el día que una ciudad se dispute. Lo único que lo confirma es cobrar de verdad.

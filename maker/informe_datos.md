# Medidor maker: datos al 2026-11-09 09:01 UTC

Fotos del libro cada 5 min desde 2026-10-26 14:30 UTC: 3540 fotos, 15 días, 2,458,305 cajas-foto con precio entre 3 y 97 ¢ (clima 2,284,224, cripto 174,081). Regla fija: maker/REGLA.md.

## 1. Pozos de recompensa (lo que reparte Polymarket por día)

Promedio por foto (solo cajas cuyo evento todavía no terminó):

| grupo | cajas | con_pozo | pozo |
|---|---|---|---|
| clima | 598 | 457 | 10723 |
| cripto | 49 | 0 | 0 |

`pozo` = suma de US$/día que reparten las cajas vivas de ese grupo entre todos los makers.

## 2. Recompensa estimada si tuviéramos 100 acciones por lado en TODAS las cajas vivas

**Orden a 1 ¢ del medio** (US$/día, suma de todas las cajas vivas; promedio, mediana, mín y máx de las fotos):

| grupo | mean | median | min | max |
|---|---|---|---|---|
| clima | 5591.6 | 5536.1 | 3296.9 | 9962.6 |
| cripto | 0.0 | 0.0 | 0.0 | 0.0 |

**Orden a 2 ¢ del medio** (US$/día, suma de todas las cajas vivas; promedio, mediana, mín y máx de las fotos):

| grupo | mean | median | min | max |
|---|---|---|---|---|
| clima | 4698.2 | 4648.2 | 2340.6 | 9689.7 |
| cripto | 0.0 | 0.0 | 0.0 | 0.0 |

Por caja con pozo (orden a 1 ¢): recompensa media por caja-día, % de fotos en que no hay ningún otro maker dentro del spread premiado (`solos`) y competencia mediana (puntaje de los demás):

| grupo | cajas_con_pozo | rec_media_caja | pct_solos | comp_mediana |
|---|---|---|---|---|
| clima | 6414 | 12.24 | +35.4 % | 21 |

Capital: 100 acciones por lado inmovilizan ≈ US$ 100 por caja. Recompensa por US$ 100 de capital y día = la columna `rec_media_caja`.

Clima, por horas hasta el cierre del evento (orden a 1 ¢, por caja con pozo):

| tramo | cajas_foto | pozo | rec | solos |
|---|---|---|---|---|
| 0-6 h | 114036 | 27.8 | 20.38 | +45.5 % |
| 6-12 h | 176381 | 27.6 | 17.41 | +34.5 % |
| 12-24 h | 387276 | 26.1 | 11.35 | +21.5 % |
| 24-36 h | 390877 | 24.1 | 9.57 | +21.5 % |
| 36-48 h | 412248 | 20.1 | 11.18 | +46.1 % |
| >48 h | 135823 | 15.2 | 12.09 | +74.8 % |

Clima, por hora local de la ciudad:

| hl | cajas_foto | rec | solos |
|---|---|---|---|
| 0-5 h | 418321 | 12.10 | +32.8 % |
| 6-11 h | 399923 | 13.61 | +36.9 % |
| 12-17 h | 397880 | 12.29 | +39.9 % |
| 18-23 h | 400517 | 10.96 | +32.0 % |

Clima, las 12 series con más recompensa por caja (orden a 1 ¢):

| serie | cajas_foto | pozo | rec | solos |
|---|---|---|---|---|
| lowest|wellington | 19360 | 19.1 | 17.04 | +80.9 % |
| lowest|hong-kong | 20181 | 20.0 | 17.02 | +65.6 % |
| highest|istanbul | 24350 | 28.0 | 15.69 | +33.2 % |
| highest|moscow | 25320 | 26.6 | 15.56 | +33.2 % |
| highest|helsinki | 21222 | 35.3 | 15.37 | +14.2 % |
| lowest|london | 26506 | 19.8 | 15.31 | +64.2 % |
| lowest|madrid | 21813 | 18.7 | 15.10 | +67.6 % |
| lowest|los-angeles | 10712 | 17.3 | 14.83 | +81.4 % |
| lowest|tokyo | 28666 | 17.1 | 13.99 | +73.5 % |
| lowest|shanghai | 29945 | 16.4 | 13.93 | +78.4 % |
| highest|chongqing | 26350 | 25.2 | 13.85 | +28.7 % |
| highest|tel-aviv | 24249 | 29.8 | 13.84 | +19.2 % |

## 3. Llenados simulados (alguien operó a peor precio que nuestra orden)

134,365 llenados en 15 días; 115,510 ya resueltos. Por grupo y distancia de la orden, por día de medición:

| grupo | dist_c | llenados_d | acciones_d | reembolso_d | pnl_5_d | pnl_60_d | pnl_res_d | pnl_60_acc | pnl_res_acc |
|---|---|---|---|---|---|---|---|---|---|
| clima | 1 | 5207 | 99721 | 77.83 | 3927.5 | 3300.9 | -3893.7 | 3.31 | -4.55 |
| clima | 2 | 3354 | 65333 | 53.35 | 3425.0 | 2864.1 | -2961.6 | 4.38 | -5.23 |
| cripto | 1 | 252 | 9888 | 21.54 | -9.6 | 37.0 | -100.5 | 0.37 | -1.17 |
| cripto | 2 | 144 | 5554 | 13.46 | 82.8 | 94.2 | -117.3 | 1.70 | -2.39 |

`pnl_60_d` = US$/día que vale lo llenado 60 min después (precio medio del libro) menos lo que pagamos; `pnl_res_d` = lo mismo a la resolución, solo de los ya resueltos (`_acc` = centavos por acción).

- clima, orden a 1 ¢: resultado por llenado -17.2 % del capital de esa orden (t = -20.1, n = 66,990).
- clima, orden a 2 ¢: resultado por llenado -18.8 % del capital de esa orden (t = -18.0, n = 43,646).
- cripto, orden a 1 ¢: resultado por llenado -3.8 % del capital de esa orden (t = -1.0, n = 3,116).
- cripto, orden a 2 ¢: resultado por llenado -4.8 % del capital de esa orden (t = -1.2, n = 1,758).

Clima, orden a 1 ¢, resueltos, por lado y precio de nuestra orden:

| lado | tramo_p | n | acc | pnl | pnl_acc | pnl_pct |
|---|---|---|---|---|---|---|
| compra | 3-10 ¢ | 11578 | 209379 | -2412.9 | -1.15 | -14.3 % |
| compra | 10-30 ¢ | 12256 | 204465 | -12502.0 | -6.11 | -30.4 % |
| compra | 30-70 ¢ | 12918 | 213156 | -14855.3 | -6.97 | -17.5 % |
| compra | 70-90 ¢ | 1167 | 20146 | -1553.5 | -7.71 | -9.8 % |
| compra | 90-97 ¢ | 366 | 8721 | 19.0 | 0.22 | -2.1 % |
| venta | 3-10 ¢ | 3502 | 98886 | -2322.7 | -2.35 | -2.2 % |
| venta | 10-30 ¢ | 8819 | 217470 | -4233.6 | -1.95 | -2.8 % |
| venta | 30-70 ¢ | 12521 | 224991 | -16326.1 | -7.26 | -15.0 % |
| venta | 70-90 ¢ | 2402 | 44261 | -3453.4 | -7.80 | -36.5 % |
| venta | 90-97 ¢ | 1461 | 41357 | -764.9 | -1.85 | -47.3 % |

## 4. Neto diario (recompensa + reembolso + resultado de los llenados)

Con 100 acciones por lado en todas las cajas vivas con precio 3–97 ¢ (es lo que simula la regla), por día de medición:

| grupo | dist_c | recompensa | reembolso | llenados_60min | llenados_resol | neto_60 | neto_resol | cajas | capital |
|---|---|---|---|---|---|---|---|---|---|
| clima | 1 | 5591.6 | 77.83 | 3300.9 | -4540.2 | 8970.3 | 1129.3 | 598 | 59758 |
| clima | 2 | 4698.2 | 53.35 | 2864.1 | -3416.2 | 7615.7 | 1335.4 | 598 | 59758 |
| cripto | 1 | 0.0 | 21.54 | 37.0 | -115.8 | 58.5 | -94.2 | 49 | 4917 |
| cripto | 2 | 0.0 | 13.46 | 94.2 | -132.6 | 107.6 | -119.1 | 49 | 4917 |

US$/día. `capital` = colateral inmovilizado (≈ US$ 100 por caja). `neto_resol` usa el resultado por acción de los llenados ya resueltos aplicado a todas las acciones llenadas.

Clima, orden a 1 ¢, día por día (recompensa estimada, llenados a 60 min, neto a 60 min):

| dia | recompensa | acc | reemb | pnl60 | neto_60 |
|---|---|---|---|---|---|
| 2026-10-26 | 4660.3 | 52698 | 0.00 | 520.1 | 5180.4 |
| 2026-10-27 | 5167.9 | 169015 | 0.00 | 4544.9 | 9712.8 |
| 2026-10-28 | 4552.3 | 143939 | 0.00 | 3937.0 | 8489.3 |
| 2026-10-29 | 5294.5 | 167482 | 0.00 | 5676.1 | 10970.7 |
| 2026-10-30 | 5141.4 | 165821 | 0.00 | 6964.4 | 12105.8 |
| 2026-10-31 | 5021.6 | 163312 | 0.00 | 5601.4 | 10623.0 |
| 2026-11-01 | 5482.9 | 148415 | 229.92 | 4250.3 | 9963.1 |
| 2026-11-02 | 5743.9 | 136301 | 263.92 | 5553.8 | 11561.6 |
| 2026-11-03 | 5854.0 | 0 | 0.00 | 0.0 | 5854.0 |
| 2026-11-04 | 6170.3 | 0 | 0.00 | 0.0 | 6170.3 |
| 2026-11-05 | 6177.9 | 0 | 0.00 | 0.0 | 6177.9 |
| 2026-11-06 | 5952.1 | 0 | 0.00 | 0.0 | 5952.1 |
| 2026-11-07 | 6376.3 | 4318 | 8.36 | -47.8 | 6336.8 |
| 2026-11-08 | 6408.1 | 255230 | 496.63 | 7734.4 | 14639.1 |
| 2026-11-09 | 6811.1 | 89288 | 168.58 | 4778.4 | 11758.1 |

Neto a 60 min: +9033.0 US$/día, t = 11.9 con 15 días.

## 5. ¿Dónde conviene? Recompensa menos llenados por caja-día (clima, 1 ¢, a 60 min)

Mejores y peores series (neto por caja y día):

| serie | cajas | rec | neto_dia |
|---|---|---|---|
| highest|seoul | 99 | 10.13 | 35.36 |
| highest|guangzhou | 98 | 9.58 | 33.36 |
| highest|wellington | 89 | 10.19 | 31.31 |
| highest|hong-kong | 87 | 9.81 | 31.12 |
| highest|tokyo | 105 | 8.95 | 30.02 |
| highest|kuala-lumpur | 87 | 10.16 | 29.25 |
| highest|nyc | 84 | 7.78 | 28.80 |
| highest|london | 88 | 8.70 | 28.28 |
| lowest|buenos-aires | 35 | 6.93 | 6.36 |
| lowest|mexico-city | 36 | 5.91 | 5.62 |
| lowest|beijing | 51 | 7.17 | 4.67 |
| lowest|ankara | 38 | 6.98 | 4.01 |
| lowest|denver | 22 | 7.47 | 1.76 |

90 de 90 series con neto positivo por caja-día.

## 6. Por ancho del libro (spread real bid-ask al momento de poner la orden), clima

Las órdenes a 1 ¢ del medio en un libro de 40 ¢ de ancho quedan muy adentro: el medio no es el precio justo. Esto separa los libros apretados (donde el medio sí vale algo) de los anchos.

**Orden a 1 ¢** (US$/día):

| spread | cajas | capital | recompensa | rec_pes | acciones_d | pnl_res_acc | llenados_resol | reemb | neto | neto_pes | neto_por_100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ≤2 ¢ | 73 | 7261 | 433.7 | 304.1 | 8889 | -2.44 | -216.4 | 5.68 | 222.9 | 93.4 | 3.07 |
| 2-5 ¢ | 239 | 23873 | 2276.4 | 1492.4 | 50557 | -2.40 | -1214.1 | 36.06 | 1098.3 | 314.3 | 4.60 |
| 5-10 ¢ | 76 | 7644 | 812.5 | 424.5 | 23198 | -3.66 | -849.3 | 16.54 | -20.2 | -408.3 | -0.26 |
| 10-20 ¢ | 55 | 5541 | 818.6 | 409.3 | 10515 | -6.64 | -698.2 | 11.10 | 131.6 | -277.8 | 2.37 |
| >20 ¢ | 154 | 15438 | 1250.4 | 625.2 | 6580 | -23.02 | -1514.8 | 8.45 | -256.0 | -881.2 | -1.66 |

**Orden a 2 ¢** (US$/día):

| spread | cajas | capital | recompensa | rec_pes | acciones_d | pnl_res_acc | llenados_resol | reemb | neto | neto_pes | neto_por_100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ≤2 ¢ | 73 | 7261 | 277.3 | 210.6 | 4089 | -3.05 | -124.7 | 2.85 | 155.4 | 88.8 | 2.14 |
| 2-5 ¢ | 239 | 23873 | 1590.0 | 1116.9 | 24003 | -2.34 | -561.5 | 17.51 | 1046.1 | 572.9 | 4.38 |
| 5-10 ¢ | 76 | 7644 | 761.9 | 404.1 | 20543 | -3.12 | -641.3 | 14.05 | 134.6 | -223.2 | 1.76 |
| 10-20 ¢ | 55 | 5541 | 818.6 | 409.3 | 10182 | -6.16 | -627.4 | 10.61 | 201.8 | -207.5 | 3.64 |
| >20 ¢ | 154 | 15438 | 1250.4 | 625.2 | 6520 | -22.18 | -1445.9 | 8.33 | -187.2 | -812.3 | -1.21 |

`rec_pes` / `neto_pes` = recompensa y neto si los otros makers copian nuestra orden (la competencia suma otro tanto como lo nuestro): es lo que pasa cuando los bots rivales se acomodan. `neto_por_100` = neto diario (optimista) por cada US$ 100 de capital (una caja). Spread mediano del libro en clima: 5.0 ¢; 12 % de las cajas-foto con spread ≤ 2 ¢.

## 7. Día por día: clima, libros con spread ≤ 5 ¢, orden a 2 ¢, recompensa pesimista

| dia | cajas | rec_pes | acc | reemb | llenados_resol | neto_pes | por_100 |
|---|---|---|---|---|---|---|---|
| 2026-10-26 | 352 | 1597.7 | 14829 | 0.00 | -362.7 | 1235.0 | 3.50 |
| 2026-10-27 | 343 | 1559.3 | 46482 | 0.00 | -1136.7 | 422.6 | 1.23 |
| 2026-10-28 | 345 | 1336.7 | 39887 | 0.00 | -975.5 | 361.2 | 1.05 |
| 2026-10-29 | 315 | 1303.6 | 44905 | 0.00 | -1098.1 | 205.5 | 0.65 |
| 2026-10-30 | 321 | 1306.2 | 49570 | 0.00 | -1212.2 | 94.0 | 0.29 |
| 2026-10-31 | 325 | 1252.2 | 46140 | 0.00 | -1128.4 | 123.9 | 0.38 |
| 2026-11-01 | 314 | 1430.7 | 46439 | 68.35 | -1135.7 | 363.4 | 1.16 |
| 2026-11-02 | 297 | 1266.2 | 38876 | 71.97 | -950.7 | 387.4 | 1.30 |
| 2026-11-03 | 282 | 1220.3 | 0 | 0.00 | -0.0 | 1220.3 | 4.33 |
| 2026-11-04 | 295 | 1219.7 | 0 | 0.00 | -0.0 | 1219.7 | 4.13 |
| 2026-11-05 | 310 | 1249.4 | 0 | 0.00 | -0.0 | 1249.4 | 4.03 |
| 2026-11-06 | 302 | 1351.4 | 0 | 0.00 | -0.0 | 1351.4 | 4.47 |
| 2026-11-07 | 299 | 1357.7 | 1511 | 3.00 | -37.0 | 1323.8 | 4.42 |
| 2026-11-08 | 275 | 1246.3 | 68838 | 124.02 | -1683.4 | -313.1 | -1.14 |
| 2026-11-09 | 274 | 1329.4 | 23894 | 38.14 | -584.3 | 783.2 | 2.86 |

Neto pesimista por US$ 100 de capital: +2.18 US$/día, t = 4.5 con 15 días (el resultado de los llenados usa el promedio por acción de todos los resueltos, -2.45 ¢).

Lo que NO está en estos números: que Polymarket mide cada minuto y nosotros cada 5 (recompensa optimista); que los rivales pueden apretar más que 'copiarnos'; que las fotos son del libro visible (no se ven las órdenes que entran y salen entre fotos); gas y el día que una ciudad se dispute. Lo único que lo confirma es cobrar de verdad.

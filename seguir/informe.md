# Seguir billeteras ganadoras: backtest fuera de muestra

Generado 2026-10-23 17:21Z con las reglas de `seguir/REGLAS.md` (fijadas antes). Historia desde 21-Sep; días de prueba 01-Oct a 23-Oct (23 días). Copia de US$10 por señal, +1¢ sobre el precio que consiguió otro, comisión 0.

Billeteras elegidas por día: mínimo 23, mediana 50, máximo 50 (de 2030 con ≥20 eventos).

Señales: 13433 (584 por día), de 86 billeteras.

## 1. ¿Seguirlas habría ganado? (según cuánto tardamos en copiar)

| latencia | copias | llenadas | precio vs el de ellos | PnL US$ | PnL/vol | intervalo 90% | t por día |
|---|---|---|---|---|---|---|---|
| 0 min | 13433 | 100% | +0.0¢ | +10728 | **+8.0%** | +6.4% a +9.6% | 5.8 |
| 1 min | 10386 | 77% | +2.8¢ | -39 | **-0.0%** | -1.9% a +1.9% | -0.0 |
| 5 min | 9885 | 74% | +2.5¢ | -24 | **-0.0%** | -1.8% a +1.8% | -0.0 |
| 15 min **(principal)** | 9488 | 71% | +2.0¢ | -522 | **-0.6%** | -2.4% a +1.3% | -0.5 |
| 60 min | 8749 | 65% | +0.7¢ | -122 | **-0.1%** | -2.3% a +2.0% | -0.1 |

L = 0 es su propio precio +1¢: el techo teórico (ganarías lo que ellos si copiaras al instante y sin moverles el precio).

**Veredicto con la regla fijada (L = 15 min): NO PASA** (PnL/vol -0.6%, límite inferior -2.4%; hacía falta ≥ +2% y > 0).

## 2. Controles

| subconjunto | L=0 | L=1 | L=5 | L=15 | L=60 |
|---|---|---|---|---|---|
| 1ª mitad de los días de prueba | +8.1% (5756) | -0.5% (4543) | -0.5% (4369) | -0.7% (4200) | +0.8% (3841) |
| 2ª mitad | +7.9% (7677) | +0.3% (5843) | +0.4% (5516) | -0.4% (5288) | -0.9% (4908) |
| sólo antes del día (pronóstico) | +7.3% (8828) | -1.1% (6859) | -1.2% (6545) | -2.0% (6310) | -0.3% (5980) |
| sólo durante el día | +9.3% (4605) | +2.0% (3527) | +2.2% (3340) | +2.3% (3178) | +0.3% (2769) |

Copiando billeteras **al azar** (misma cantidad por día, entre las que tienen ≥20 eventos, sin mirar si ganan); 20 sorteos:

| latencia | azar: PnL/vol medio | azar: rango | elegidas |
|---|---|---|---|
| 0 min | +1.3% | -5.6% a +6.0% | +8.0% |
| 15 min | -3.0% | -9.8% a +3.9% | -0.6% |

## 3. Por billetera (L = 15 min, las de más copias)

| billetera | copias | PnL US$ | PnL/vol | precio vs el de ellos |
|---|---|---|---|---|
| hello.67 | 2162 | -403 | -1.9% | +2.8¢ |
| 0xeb1b3e | 907 | -261 | -2.9% | +4.2¢ |
| Cb94C437EA5e6f088c6c0C143c592ab8EFBed | 797 | -364 | -4.6% | +0.3¢ |
| OutOfMemory | 721 | -172 | -2.4% | +2.5¢ |
| 0x65f722 | 703 | +270 | +3.8% | +4.6¢ |
| badatmath. | 535 | +398 | +7.4% | +4.4¢ |
| AuspiciousWolf | 510 | +318 | +6.2% | +2.1¢ |
| Bilberry | 467 | -261 | -5.6% | +2.3¢ |
| 241532532432 | 359 | +183 | +5.1% | +0.3¢ |
| balthazar | 329 | -208 | -6.3% | -1.0¢ |
| yongzhuanziben007 | 303 | +79 | +2.6% | +1.7¢ |
| twobonclay | 195 | -32 | -1.6% | +1.6¢ |
| 0x5356af | 141 | +0 | +0.0% | +2.6¢ |
| MoneyForSky06 | 135 | -169 | -12.5% | +3.5¢ |
| 0x1aBc2b469b5dED495d6C8B21Fc79dcb8d8f345 | 113 | +11 | +1.0% | -0.8¢ |
| haiwenxiang | 109 | -95 | -8.7% | -1.6¢ |
| Qatalyst | 108 | +245 | +22.7% | -1.4¢ |
| 0xb2e42D29690B7B63335a03C0Fd5E64Df0681B7 | 86 | -11 | -1.3% | -1.9¢ |
| Poligarch | 64 | -13 | -2.0% | +0.8¢ |
| CreamCream1215 | 63 | +39 | +6.2% | +1.6¢ |

## 4. Velocidad: ¿queda algo para el que ve el METAR a los ~4 min?

Operaciones durante el día medido, entre 5¢ y 90¢ (las que apuestan a algo que todavía no está decidido), según el minuto de la hora UTC en que entraron. La mayoría de las estaciones informa a la hora en punto; algunas a :20/:50 o :30, eso mezcla un poco los tramos.

| minuto | operaciones | volumen US$ | PnL/vol |
|---|---|---|---|
| :00–:01 | 41446 | 424.990 | +4.8% |
| :02–:04 | 34841 | 372.282 | +3.1% |
| :05–:09 | 53370 | 510.655 | +0.0% |
| :10–:29 | 201985 | 2.218.132 | +1.7% |
| :30–:59 | 252750 | 2.648.402 | +2.0% |

Lo mismo, pero copiando como en la sección 1: si alguien compra entre 5¢ y 90¢ en :00–:04, ¿a qué precio se consigue lo mismo unos minutos después y cuánto deja?

| latencia | copias | precio vs el primero | PnL/vol |
|---|---|---|---|
| 0 min | 5517 | +0.0¢ | +0.2% |
| 2 min | 4577 | -0.4¢ | -3.1% |
| 4 min | 4479 | -0.7¢ | -3.3% |
| 6 min | 4447 | -0.9¢ | -3.5% |
| 10 min | 4356 | -1.4¢ | -4.0% |


## Nota (mirada después de los resultados, no es parte de las reglas)

Sólo las apuestas durante el día, L = 15 min: PnL/vol +2,3%, intervalo 90% −0,8% a +5,4%, t por día 1,1; 1ª mitad
−2,2%, 2ª mitad +5,7%. Con L = 5: +2,2% (−0,7% a +5,2%). No alcanza para decir que hay algo.

# Seguir billeteras ganadoras: backtest fuera de muestra

Generado 2026-10-26 00:36Z con las reglas de `seguir/REGLAS.md` (fijadas antes). Historia desde 21-Sep; días de prueba 01-Oct a 23-Oct (23 días). Copia de US$10 por señal, +1¢ sobre el precio que consiguió otro, comisión 0.

Billeteras elegidas por día: mínimo 24, mediana 50, máximo 50 (de 1930 con ≥20 eventos).

Señales: 12690 (552 por día), de 88 billeteras.

## 1. ¿Seguirlas habría ganado? (según cuánto tardamos en copiar)

| latencia | copias | llenadas | precio vs el de ellos | PnL US$ | PnL/vol | intervalo 90% | t por día |
|---|---|---|---|---|---|---|---|
| 0 min | 12690 | 100% | +0.0¢ | +9381 | **+7.4%** | +5.7% a +9.0% | 6.2 |
| 1 min | 9850 | 78% | +2.8¢ | -820 | **-0.8%** | -2.7% a +1.0% | -0.9 |
| 5 min | 9363 | 74% | +2.4¢ | -844 | **-0.9%** | -2.8% a +0.9% | -0.9 |
| 15 min **(principal)** | 8976 | 71% | +2.0¢ | -1256 | **-1.4%** | -3.2% a +0.3% | -1.2 |
| 60 min | 8230 | 65% | +0.6¢ | -647 | **-0.8%** | -2.9% a +1.5% | -0.7 |

L = 0 es su propio precio +1¢: el techo teórico (ganarías lo que ellos si copiaras al instante y sin moverles el precio).

**Veredicto con la regla fijada (L = 15 min): NO PASA** (PnL/vol -1.4%, límite inferior -3.2%; hacía falta ≥ +2% y > 0).

## 2. Controles

| subconjunto | L=0 | L=1 | L=5 | L=15 | L=60 |
|---|---|---|---|---|---|
| 1ª mitad de los días de prueba | +7.3% (5030) | -1.5% (3979) | -1.6% (3838) | -1.7% (3687) | -0.7% (3338) |
| 2ª mitad | +7.5% (7660) | -0.4% (5871) | -0.4% (5525) | -1.2% (5289) | -0.9% (4892) |
| sólo antes del día (pronóstico) | +6.5% (8276) | -2.4% (6465) | -2.3% (6156) | -3.2% (5927) | -1.6% (5598) |
| sólo durante el día | +9.1% (4414) | +2.2% (3385) | +1.9% (3207) | +2.0% (3049) | +0.9% (2632) |

Copiando billeteras **al azar** (misma cantidad por día, entre las que tienen ≥20 eventos, sin mirar si ganan); 20 sorteos:

| latencia | azar: PnL/vol medio | azar: rango | elegidas |
|---|---|---|---|
| 0 min | +1.9% | -3.3% a +9.2% | +7.4% |
| 15 min | -2.3% | -8.5% a +8.9% | -1.4% |

## 3. Por billetera (L = 15 min, las de más copias)

| billetera | copias | PnL US$ | PnL/vol | precio vs el de ellos |
|---|---|---|---|---|
| hello.67 | 1904 | -607 | -3.2% | +2.7¢ |
| Cb94C437EA5e6f088c6c0C143c592ab8EFBed | 833 | -401 | -4.8% | +0.5¢ |
| 0xeb1b3e | 758 | -443 | -5.8% | +4.2¢ |
| Bilberry | 718 | -346 | -4.8% | +2.4¢ |
| 0x65f722 | 716 | +76 | +1.1% | +4.6¢ |
| OutOfMemory | 627 | -167 | -2.7% | +2.4¢ |
| badatmath. | 535 | +398 | +7.4% | +4.4¢ |
| AuspiciousWolf | 447 | +165 | +3.7% | +1.9¢ |
| balthazar | 329 | -208 | -6.3% | -1.0¢ |
| 241532532432 | 305 | +111 | +3.7% | +0.2¢ |
| MoneyForSky06 | 230 | -110 | -4.8% | +3.2¢ |
| twobonclay | 163 | -63 | -3.9% | +1.4¢ |
| yongzhuanziben007 | 156 | -52 | -3.3% | +2.3¢ |
| Qatalyst | 114 | +270 | +23.7% | -2.2¢ |
| 0x1aBc2b469b5dED495d6C8B21Fc79dcb8d8f345 | 113 | +11 | +1.0% | -0.8¢ |
| haiwenxiang | 112 | -98 | -8.7% | -1.7¢ |
| 0xb2e42D29690B7B63335a03C0Fd5E64Df0681B7 | 97 | -58 | -6.0% | -2.0¢ |
| CreamCream1215 | 65 | +78 | +12.0% | +1.4¢ |
| arsenal85 | 60 | +26 | +4.3% | -1.1¢ |
| 0x3C0B3957f80121d9A9908A68ea3761cddfb1A9 | 51 | -44 | -8.6% | -5.1¢ |

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


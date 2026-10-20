# Otros mercados: Bitcoin/Ethereum y conteo de posts (20-oct-2026)

## Mapa
- ~3.200 eventos abiertos en Polymarket; 84 grupos que se repiten.
- Fuera de deportes y clima, los que más mueven son:
  - Fed (mensual);
  - Bitcoin/Ethereum "above" y "price" (diarios);
  - tweets de Elon (semanal, ~US$0,9M/día);
  - posts de Trump en Truth Social;
  - mercados chicos de datos (Rotten Tomatoes, taquilla, OpenRouter).
- Quedan sin cubrir 7 ciudades de clima: Estambul, Hong Kong, Taipéi, Tel Aviv, Moscú, Jinan y Zhengzhou.

## Bitcoin / Ethereum "above ___ on <fecha>" (vela de 1 min de Binance a las 12:00 ET)
- Modelo: opción digital con el precio de Binance y la volatilidad implícita de Deribit (DVOL). Nada más.
- Datos: may–oct 2026, 294 eventos, ~3.300 strikes y todas sus operaciones.
- Evaluación a 48, 24, 12, 6, 3, 1 y 0,5 h del cierre, con el precio real de ejecución (último pago al comprar / al vender en la hora previa) y comisión.
- **Brier:** modelo ≈ mercado. El mercado ya razona como un modelo de opciones.
- **Regla "comprar el lado que el modelo ve ≥5 puntos más barato":**
  - En total: 796 operaciones en 262 días-activo, **ROI +9,5 %**.
  - Con 1 ¢ de deslizamiento: +6,9 % (P de que sea negativo ≈ 5 %). Con 2 ¢: +4,4 % (P ≈ 14 %).
  - Positivo en los 6 meses combinando BTC y ETH (de +1,5 % a +17 %), y similar en may–jul y ago–oct.
  - BTC solo es más flojo: sep y oct negativos. ETH es más fuerte.
  - La mayor parte viene de las opciones **baratas (<20 ¢)**: +40 % con 1 ¢ de deslizamiento. El mercado parece subvalorar los movimientos grandes.
- **Cuidados:**
  - Se probaron varias variantes, así que puede haber algo de casualidad.
  - Las operaciones de un mismo día están correlacionadas.
  - No sabemos cuánta profundidad tiene el libro.
- → **Prueba en papel con regla fija: `cripto.py`**, desde el 20-oct.

## Tweets de Elon y posts de Trump (calibración del precio)
- Elon (40 semanas, jun–oct): leve sesgo a favor de las cajas improbables.
  - Las cajas a 5–15 ¢ ganaron el 5,2 % (precio 8,8 %); las de 15–35 ¢, el 18,9 % (precio 23,1 %). Comprar el No dio +2,6 a +2,8 ¢ por acción.
  - Las favoritas (65–85 %) ganaron el 79,5 % (precio 72,8 %), pero n = 44.
- Trump: sin un patrón claro.
- Muestra chica (40 eventos) y riesgo de que el propio interesado influya. No se avanza por ahora.

# Bot de Polymarket (esqueleto, 26-oct-2026)

Junta todo lo aprendido en el proyecto en un solo programa que **decide, controla el riesgo, opera y lleva la
cuenta**. Hoy corre solo en **papel** (libro real, sin plata). Pasa a real cuando haya billetera y servidor.

**Desde el 26-oct corre en papel desde el reloj** (minuto 54–58 de cada hora, `python bot/polybot.py una`), con
5 acciones y frenos a la mitad: sirve para probar el bot entero (frenos, órdenes que no llenan, registro) con el
libro real mientras dura la prueba. La prueba oficial del favorito tardío sigue siendo `favorito/` (no se toca) y
es la que decide el 16-nov. Resultados del bot en `bot/resumen_papel.md`. Junto al bot corre `sombra_maker.py` (regla en `SOMBRA_REGLA.md`):
mide si comprar con una orden 1 ¢ abajo, sin comisión, habría rendido más; resultados en `bot/sombra_maker.md`. Plan: pasar a real el 16-nov si la prueba
pasa, con 5 acciones durante 2 semanas y ~US$ 60 en la cuenta.

## Piezas

| archivo | qué hace |
|---|---|
| `config.json` | modo (`papel`/`real`), estrategia, parámetros, límites de riesgo, fecha de apagado |
| `estrategias.py` | decide qué comprar. Hoy: `favorito` (igual a `favorito/REGLA.md`) |
| `ejecutor.py` | `Papel`: simula una orden "todo o nada" releyendo el libro. `Real`: orden FOK con el SDK oficial |
| `mercado.py` | lectura pública (gamma, libro, resultado, control de país) |
| `polybot.py` | el bot: frenos, registro, liquidación, resumen; modos `una`, `bucle`, `resumen` |
| `test_bot.py` | 12 pruebas sin red (`python bot/test_bot.py`) |

## Frenos (cualquiera detiene el bot)
- Archivo `bot/PARAR` (crearlo a mano = botón de apagado; el bot lo crea solo si se activa un freno grave).
- Fecha `apagar_despues_de`.
- Pérdida total ≥ `max_perdida_total` (US$ 25) → crea PARAR.
- `max_errores_seguidos` (5) fallas seguidas de red/API → crea PARAR.
- Por operación: costo ≤ `max_usd_por_op` (US$ 5), ≤ `max_ops_por_dia` (30), pérdida del día < `max_perdida_dia`
  (US$ 10), plata en mercados sin resolver ≤ `max_exposicion_abierta` (US$ 20), una sola op por mercado.
- Órdenes FOK (todo o nada al precio tope o nada): nunca queda una orden colgada si el bot se cae.
- En real, además: no arranca sin `BOT_REAL_CONFIRMO=si` y si `polymarket.com/api/geoblock` dice que el servidor
  está bloqueado.

## Cómo pasar a real (cuando la prueba en papel lo justifique)
1. **Cuenta y billetera**: crear cuenta en polymarket.com (billetera "Deposit Wallet", la de hoy; no paga gas).
   Cargar ~US$ 60 en pUSD (la moneda de Polymarket, respaldada 1:1 por USDC; depositar USDC la convierte sola).
2. **Clave**: exportar la clave privada del firmante o, mejor, crear una **session key** (la doc oficial permite una
   clave aparte que pone y cancela órdenes sin usar la clave dueña; confirmar en la doc qué más puede hacer).
   Esa va al servidor, nunca al repo.
3. **Servidor fuera de EE.UU.**: un VPS chico (US$ 5/mes) en **Irlanda (AWS eu-west-1)**: es la región sin bloqueo más
   cercana a los servidores de Polymarket (Londres). Ojo: Reino Unido, Alemania, Francia, Italia, Polonia, Bélgica,
   EE.UU., Brasil, Australia y otros están bloqueados para operar; Irlanda y Países Bajos solo en la web.
   Argentina y Uruguay no están en la lista.
4. En el servidor: `git clone`, `pip install requests polymarket-client`, y variables
   `POLYMARKET_PRIVATE_KEY=...`, `BOT_REAL_CONFIRMO=si`.
5. Primero **papel desde el servidor** (`modo: papel`, `python bot/polybot.py bucle`) unos días: mide si desde ahí
   el libro se llena igual que en la prueba de Actions.
6. **Primera orden real**: `modo: real`, `acciones: 5`, mirar a mano el resultado en la web. El ejecutor real está
   escrito según la doc oficial pero sin probar: hay que confirmar (a) si estos mercados piden `position_id` en vez de
   `token_id`, (b) qué devuelve el SDK como precio de llenado (hoy se anota el tope, lo peor posible).
7. Las ganadoras se cobran ("redeem") desde la web al principio; automatizarlo después.

## Para sumar otra estrategia
Una función nueva en `estrategias.py` que devuelva señales con el mismo formato. Una estrategia **maker** (órdenes que
esperan en el libro para cobrar recompensas) necesita además: órdenes post-only/GTD, cancelar y reponer, seguir el
libro por WebSocket y un `cancelar_todo` en el freno. Se arma solo si el corte del medidor de recompensas (2-nov)
muestra que el pozo paga más que lo que se pierde por selección adversa (~1 ¢ por acción medido en temperatura).

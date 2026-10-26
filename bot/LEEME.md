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
| `ejecutor.py` | `Papel`: simula una orden "todo o nada" releyendo el libro. `Real`: orden FOK con el SDK oficial y cobro de ganadoras |
| `mercado.py` | lectura pública (gamma, libro, resultado, control de país) |
| `polybot.py` | el bot: frenos, registro, liquidación, resumen; modos `una`, `bucle`, `resumen` |
| `test_bot.py` | 19 pruebas sin red (`python bot/test_bot.py`), incluido el modo real contra un SDK falso |
| `sombra_maker.py`, `fotos_minuto.py` | mediciones para el 17-nov (orden 1 ¢ abajo, minuto de entrada); reglas en `SOMBRA_REGLA.md` |
| `iniciar_bot.cmd`, `parar_bot.cmd`, `secreto_ejemplo.cmd` | para correrlo en Windows |

## Frenos (cualquiera detiene el bot)
- Archivo `bot/PARAR` (botón de apagado manual, frena cualquier modo) o `bot/PARAR_<modo>` (lo crea solo un freno grave).
- Fecha `apagar_despues_de`.
- Pérdida total ≥ `max_perdida_total` (US$ 25) → crea PARAR_<modo>.
- `max_errores_seguidos` (5) fallas seguidas de red/API → crea PARAR_<modo>.
- Por operación: costo ≤ `max_usd_por_op` (US$ 5), ≤ `max_ops_por_dia` (30), pérdida del día < `max_perdida_dia`
  (US$ 10), plata en mercados sin resolver ≤ `max_exposicion_abierta` (US$ 20), una sola op por mercado.
- Órdenes FOK (todo o nada al precio tope o nada): nunca queda una orden colgada si el bot se cae.
- En real, además: no arranca sin `BOT_REAL_CONFIRMO=si` y si `polymarket.com/api/geoblock` dice que el servidor
  está bloqueado.

## Cómo pasar a real en la PC de Agus (plan: 16/17-nov, si la prueba pasa)
1. **Cuenta**: polymarket.com, billetera "Deposit Wallet" (la de hoy; no paga gas). Cargar ~US$ 60 en USDC
   (se convierten solos a pUSD, la moneda de Polymarket).
2. **Python en la PC**: instalar Python 3.12+ y, en la carpeta del repo, `pip install -r bot/requirements_real.txt`.
3. **Secretos**: copiar `bot/secreto_ejemplo.cmd` como `bot/secreto.cmd` y completarlo (clave, billetera, tema de
   avisos). `bot/secreto.cmd` está en `.gitignore`: nunca se sube. Mejor una **clave de sesión** que la clave dueña
   (la doc oficial las permite para que otro programa ponga y cancele órdenes).
4. **Avisos al celular**: instalar la app **ntfy** (gratis, sin cuenta), suscribirse al tema inventado en
   `secreto.cmd` y probar con `python bot\polybot.py probar-aviso`. Avisa: arranque/apagado, cada compra real,
   tope de pérdida del día, cualquier freno, y un resumen diario a las 00 de Uruguay (`resumen_diario_utc`).
5. **Arranque**: doble clic en `bot\iniciar_bot.cmd` (se vuelve a levantar solo si se cae). Para que arranque al
   prender la PC: Programador de tareas → Crear tarea básica → "Al iniciar sesión" → Iniciar un programa →
   `bot\iniciar_bot.cmd`. En Energía, poner "Suspender: Nunca" mientras esté enchufada: si la PC duerme, se
   pierden esas horas (no rompe nada).
6. **Apagar**: doble clic en `bot\parar_bot.cmd` (crea `bot\PARAR`). Si un freno automático lo paró, existe
   `bot\PARAR_real` con el motivo; borrarlo para volver a arrancar.
7. **Primera orden real**: `"modo": "real"` en `config.json` y `BOT_REAL_CONFIRMO=si` en `secreto.cmd`, y mirar en
   la web la primera compra. Lo verificado contra el SDK (`polymarket-client` 0.14.0, sin plata): `token_id` es el
   mismo id de gamma, la respuesta trae pUSD pagados y acciones recibidas (el bot anota precio y acciones reales),
   FOK no llenada vuelve como rechazo `fok_not_filled`, y las ganadoras se cobran solas con `redeem_positions`.
   Falta ver con la primera orden si la comisión sale de lo pagado o de las acciones.
8. Si va bien, se pasa a un servidor fuera de EE.UU. (Irlanda u otro país no bloqueado; Brasil sí está bloqueado).

## Para sumar otra estrategia
Una función nueva en `estrategias.py` que devuelva señales con el mismo formato. Una estrategia **maker** (órdenes que
esperan en el libro para cobrar recompensas) necesita además: órdenes post-only/GTD, cancelar y reponer, seguir el
libro por WebSocket y un `cancelar_todo` en el freno. Se arma solo si el corte del medidor de recompensas (2-nov)
muestra que el pozo paga más que lo que se pierde por selección adversa (~1 ¢ por acción medido en temperatura).

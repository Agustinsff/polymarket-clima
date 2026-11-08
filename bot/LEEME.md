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

## Bot maker (prueba real chica, 3-nov-2026)

`bot/maker.py` es la estrategia que salió del medidor de recompensas (`maker/REGLA.md` e `informe_datos.md` en la
rama `medidor-maker`): dejar órdenes de compra de **Sí y de No a 2 ¢ del precio medio** en **pocas cajas de
temperatura con libro apretado (spread ≤ 5 ¢)** para cobrar las recompensas de liquidez. En papel dio +1 a +1,5 US$
por día por cada US$ 100 aun suponiendo que los rivales copian; la prueba real sirve para ver cuánto paga Polymarket
de verdad (lo único que no se puede medir sin cobrar).

Qué hace cada minuto: elige las `cajas` (3) con más recompensa esperada entre las que cumplen la regla, pone dos
órdenes **post-only** (nunca toman precio, así que nunca pagan comisión) de `acciones_min` (25) acciones por lado,
las renueva solo si el medio se movió, anota cada llenado, cobra las cajas resueltas, y a las 00:30 UTC anota la
recompensa del día anterior que informa Polymarket. Si tiene acciones de un lado, vende esas en vez de comprar el
otro, así el capital no crece. **Al apagarse por cualquier motivo cancela todas las órdenes**, salvo que se le haya
pedido reiniciar (abajo).

Frenos: `bot/PARAR` (manual), `bot/PARAR_maker_<modo>` (automático), fecha `apagar_despues_de`, pérdida del día
≥ US$ 10 (deja de cotizar hasta el día siguiente; cuenta las ventas del día contra el costo medio y las cajas que
resolvieron ese día contra lo que costaban las acciones, aunque se hayan comprado otro día), pérdida total ≥ US$ 30
(cobros − compras + ventas + acciones en cartera al costo), 10 errores seguidos. Capital:
`capital_usd` (150) solo fija el tamaño por caja (una caja con mínimo de recompensa mayor que capital/cajas no se
usa). **Efectivo libre (8-nov-2026, pedido de Agus):** antes de cada compra el bot lee el efectivo real de la cuenta
(real: USDC según el CLOB; papel: capital menos acciones al costo), le resta lo reservado en compras abiertas y solo
pone las compras que entran; las ventas van primero (liberan plata) y las compras se reparten por recompensa esperada.
Una compra que no entra se saltea y se avisa una vez por racha por ntfy (no cuenta como error). No agrega cajas
nuevas que no pueda cotizar entera (≈ tamaño × (1 − 2·distancia)). Sin tope fijo: la billetera es solo del bot y
reinvierte lo que gana (decisión de Agus); los que cuidan la plata son los frenos de pérdida. El resumen y el "sigo
vivo" muestran efectivo, reservado y libre.

**Guardia METAR fina y piso de compra (8-nov-2026, pedido de Agus tras Chengdu 17 °C).** `bot/guardia_metar.py`:
el día del evento (hora local), el bot lee los METAR de la estación (aviationweather, cache 10 min; estaciones de
`propio/estaciones.json`, regla de Polymarket: solo reportes de rutina, grupo T en décimas, .5 arriba, °F convertido)
y, si la temperatura ya observada dejó la caja decidida (máxima observada > caja o ≥ "N or higher"; mínimas al revés),
la suelta, lo anota en el estado (`guardia`) y avisa por ntfy una vez. Una caja donde la observada apenas llegó al
valor NO está decidida (Chengdu 17 °C con 17 observados: puede subir). Config `guardia_metar` (true). Además
`precio_min_compra` (0,10): no compra un lado que cotice por debajo (el otro ya está arriba de 0,90): a ese precio casi
siempre es el lado que ya se sabe que pierde; las ventas del inventario siguen. Esto sí hubiera evitado Chengdu.

**Tope de inventario por lado (8-nov-2026, Moscú 4 °C).** El bot compró 110 No a 0,38 en una sola caja (≈US$ 42, más de
4 veces el freno diario) porque cada lado se decide por separado: mientras tenga No vende No, pero como no tiene Sí sigue
comprando No. Config `max_inventario_lado` (50 = 2 lotes): no pone una compra si lo que ya tiene de ese token más la compra
supera el tope; la venta del inventario sigue y el otro lado también. 0 = sin tope. Es un parámetro de riesgo: lo fija Agus.

**Filtro de movimiento (8-nov-2026, Moscú/Múnich/Tokio 14 °C; Agus lo aprobó 14:42Z).** Con 138 llenados medidos: las compras
hechas con el medio quieto (<4 ¢ de movimiento en la hora previa) rinden +1,4 ¢/acción a la hora; con el medio en movimiento,
−5 ¢. En tendencia el bot compra a medio −2, el medio sigue y vende el inventario a medio +2 por debajo del costo. Regla: por
caja, si el medio se movió `filtro_movimiento_c` (0,06) o más en los últimos `filtro_movimiento_min` (60) minutos, en
cualquier dirección, no se ponen compras en esa caja (las ventas del inventario siguen) hasta que el movimiento de la
ventana vuelva a ser menor. Historia de medios en el estado (`medios`), cajas filtradas en `filtro` y en el resumen.
Costo medido: 22 % de los minutos cotizados sin compras, casi todo en las cajas que perdieron (Tokio 14 °C 81 %, Múnich
76 %) y casi nada en las tranquilas (Tel Aviv 3–7 %). 0 = apagado. Se revisa con el markout el 14-nov.

**Pérdida del día: costo de ese momento y hora de Uruguay (8-nov-2026).** El freno diario saltó a las 17:00Z con "−16,05"
cuando la pérdida real del día era ≈ −5: cada venta se medía contra el costo medio ACTUAL del token, y al recomprar Tokio
14 °C a 0,33 después de haber vendido a 0,12–0,26, las ventas de la mañana pasaron a contar como pérdida. Ahora `pnl(dia)`
repasa las operaciones en orden y mide cada venta contra el costo medio que tenía el token en ese momento (misma cuenta que
`revisar_llenados`). Además el "día" (freno diario, cajas resueltas, aviso "sigo vivo", resumen) es el de Uruguay
(`zona_dia`, America/Montevideo): el freno diario se libera a las 00:00 de Uruguay (03:00Z) y el mensaje lo dice. Los
registros siguen en UTC; la recompensa diaria la informa Polymarket por día UTC (sin cambio). Cuando salta el freno diario
manda un aviso por ntfy (una vez por día).

**Alertas de casos raros (8-nov-2026, pedido de Agus).** Además del aviso de cada llenado, el bot manda por ntfy mensajes que
empiezan con "ALERTA" (solo avisan, no cambian ninguna orden): (1) `alerta_escalera` (3) compras seguidas del mismo token,
cada una más barata que la anterior (medio tick o más, dentro de 3 h; una venta o una compra más cara corta la escalera):
precio en tendencia; avisa en cada escalón nuevo. (2) venta `alerta_venta_bajo_costo_c` (0,05) o más por debajo del costo
medio (los llenados parciales de la misma venta no repiten en 30 min). (3) pérdida del día (hora de Uruguay) en
`alerta_dia_frac` (0,7) del freno diario, una vez por día. `alertas: false` las apaga; cada umbral en 0 apaga el suyo.
Con los llenados del 8-nov hubieran saltado: escalera en Chengdu 17 °C (05:43Z) y Moscú 4 °C (06:34Z), ventas bajo el
costo en Moscú, Múnich y Tokio 14 °C, y la de pérdida del día a las 13:32Z (−7,5), antes del freno.

**Valor a precio de mercado en el resumen (8-nov-2026).** El neto "al costo" del bot (−1,9) y la cartera de la web (−7) no
coincidían: la web valúa las acciones al precio actual del libro. El resumen y el aviso "sigo vivo" muestran ahora también
las acciones al medio actual (`valor_mercado`), los llenados y el neto a mercado y el valor total de la cuenta
(efectivo + acciones), que es lo que muestra polymarket.com. Los frenos siguen midiendo al costo (una caja abierta no es
pérdida hasta que se vende o resuelve).

Archivos: `bot/maker_ops_<modo>.csv` (órdenes puestas, llenados y cobros), `bot/maker_estado_<modo>.json`,
`bot/maker_resumen_<modo>.md`. Pruebas sin red: `python bot/test_maker.py` (42 pruebas, incluido el SDK falso).

**Operarlo sin pausas (8-nov-2026).**
- **Actualizar sin cancelar las órdenes**: doble clic en `bot\actualizar.cmd`. Hace `git pull`, deja `bot\REINICIAR`
  y el bot, en su próxima pasada, sale con código 3 **dejando las órdenes en el libro**; la ventana de
  `iniciar_maker.cmd` lo vuelve a arrancar enseguida y, al arrancar, adopta las órdenes que siguen correspondiendo
  (mismo token, lado y precio), así no pierde el lugar en la fila. `PARAR` y los frenos siguen cancelando todo.
  Si el PR cambió `iniciar_maker.cmd`, cerrar esa ventana y abrirla de nuevo después.
- **Vende lo que queda en cajas soltadas** (8-nov): si el bot dejó una caja (ya no está entre las 3) pero le quedan
  acciones ahí (≥ `acciones_min_venta`, 5), deja una venta post-only al mayor entre el precio de siempre (medio + 2 ¢) y
  el costo + 1 ¢ (nunca vende con pérdida), del tamaño que tenga, para liberar ese capital sin esperar a la resolución. No cuenta como caja ni suma capital; se
  cancela sola si la caja resuelve o el evento terminó.
- **Cambiar la config sin reiniciar**: el bot relee `config.json` en cada ciclo y aplica los cambios de la sección
  `maker` (capital, cajas, distancia, topes…); lo único que no cambia en caliente es `modo`. Lo anota en el log.
- **Cobro automático de cajas ganadas** (billetera proxy, la de login con Google): el `redeem` necesita una clave de
  Relayer. Se crea en polymarket.com → Settings → API Keys → Relayer API Keys; copiar **API Key** y **Signer Address**
  en `bot\secreto.cmd` como `BOT_RELAYER_API_KEY` y `BOT_RELAYER_API_ADDRESS`, y después `actualizar.cmd` (el bot
  relee `secreto.cmd` al arrancar, también en un reinicio sin cancelar). El log dice al arrancar "cobro automatico
  (relayer): si/no". Sin la clave, sigue avisando por ntfy para cobrar a mano en Portfolio → Claim.
- **Avisos al celular (ntfy)**: además de los llenados, el freno y la recompensa de las 00:30 UTC, avisa al llegar a
  3 errores seguidos (`avisar_errores`, una vez por racha, antes del freno de 10) y manda un "sigo vivo" a las
  12:00 UTC (9 de la mañana en Uruguay) con órdenes, cajas y resultado: si no llega, el bot está caído.

**Inventario propio (8-nov-2026).** En real el bot ya no le pregunta a data-api qué acciones tiene (limitaba las
consultas). Lleva la cuenta él mismo con sus llenados, que lee del CLOB ("mis operaciones"): solo cuenta órdenes que
puso él, así que las acciones viejas de la cuenta no se mezclan. La primera vez que arranca con este código rearma todo
desde el 7-nov y anota en `maker_ops_real.csv` los llenados que faltaban (las órdenes que se llenaban enteras no se
anotaban). Las cajas que el bot soltó con acciones se siguen mirando y, al resolver, se cobran; si el cobro automático
falla (billetera proxy), queda anotado y llega un aviso al celular para cobrar a mano en Portfolio → Claim.
Control en solo lectura (no pone ni cancela órdenes, se puede correr con el bot andando):
`python bot\maker.py inventario` compara lo que cree el bot con el saldo de cada token en la billetera.

### Pasos para la prueba real (Agus)
1. **Correrlo en papel primero** en la PC un día: `python bot\maker.py bucle` (o doble clic en `bot\iniciar_maker.cmd`
   con `"modo": "papel"` en la sección `maker` de `config.json`). Mirar `bot/maker_resumen_papel.md`.
2. **Billetera**: en polymarket.com, cargar **US$ 150–200 en USDC** (se convierte solo a pUSD). Es la misma
   Deposit Wallet del bot favorito. Conviene una **clave de sesión** (la doc oficial las permite; el SDK la usa igual
   que la clave dueña).
3. **Secretos**: en `bot\secreto.cmd` (copiar de `secreto_ejemplo.cmd`): `POLYMARKET_PRIVATE_KEY`, `BOT_NTFY_TEMA`
   (avisos al celular) y `BOT_REAL_CONFIRMO=si`. Instalar el SDK: `pip install -r bot\requirements_real.txt`.
4. **Encender**: `"modo": "real"` en la sección `maker` de `config.json` y doble clic en `bot\iniciar_maker.cmd`.
   La PC tiene que quedar prendida (Energía → Suspender: Nunca). Si se apaga, las órdenes quedan en el libro hasta
   que vuelva a arrancar (las cancela al arrancar y las vuelve a poner); si no va a volver, cancelarlas a mano en
   polymarket.com → Portfolio → Open orders.
5. **Qué mirar**: cada mañana `bot/maker_resumen_real.md` (o el aviso de las 00:30 UTC): recompensa cobrada,
   llenados y resultado. La comparación que importa es **recompensa real vs la estimada por fórmula** (misma línea del
   resumen). Si en una semana la real es menos de la mitad de la estimada, la idea no paga; si es parecida, sube de
   capital de a poco.
6. **Apagar**: `bot\parar_bot.cmd`. Cancela todo solo.

Lo que no está probado: ninguna orden real se mandó todavía. El SDK (`polymarket-client` 0.14.0) se leyó para los
nombres (`place_limit_order(..., post_only=True)`, `cancel_orders`, `cancel_all`, `list_open_orders`,
`list_positions`, `get_total_earnings_for_user_for_day`, `redeem_positions`), pero la primera hora real hay que
mirarla en la web.

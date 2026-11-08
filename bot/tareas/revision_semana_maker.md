# Tarea programada: revisión de la semana del bot maker

Tarea programada (Claude Code, scheduled task `maker-revision-semana`) para correr una vez el
2026-11-14 12:00 America/Montevideo en la PC de Agus, solo lectura. Creada el 8-nov-2026 desde la sesión de control
remoto; este archivo es la copia versionada del prompt. Nota: la medición de llenados (markout) también se calcula
afuera del bot, en `markout/informe.md` (workflow diario); si `bot\maker_markout_real.csv` no existe, usar ese informe.

---

Sos el asistente de Agus para su bot maker de Polymarket (mercados de temperatura). Repo local:
C:\Users\Aguwus\Documents\polymarket-clima-repo (rama main). SOLO LECTURA: no toques el bot, no cambies archivos del
repo, no pongas ni canceles órdenes y no leas bot\secreto.cmd. Escribí en español rioplatense, simple y concreto.

Contexto: el 7-nov arrancó el bot maker en real (bot\maker.py) con una "semana de medición". Agus decidió que dos
mejoras queden para DESPUÉS de esa semana, según lo que muestren los datos: (2) Guardia METAR: el día del evento,
sacar las órdenes de las cajas que la temperatura observada (METAR, ver regla_metar\) ya definió, o de todas después
del pico de calor local. (3) WebSocket: escuchar el libro y los llenados en tiempo real para mover las órdenes
enseguida, en vez de cada 60 s.

Tarea:
1. Leé bot\maker_resumen_real.md, bot\maker_ops_real.csv, bot\maker_estado_real.json (sección "recompensas") y, si
   existe, bot\maker_markout_real.csv (movimiento del precio a 5/30/60 min de cada llenado). Leé también bot\LEEME.md.
2. Calculá por día: recompensa real contra estimada, llenados, resultado de los llenados y neto. Calculá el markout
   promedio a 5/30/60 min (¢ a favor o en contra del bot, comparado con la distancia de 2 ¢). Fijate si los peores
   llenados se concentran el día del evento o en cajas que resolvieron en contra (señal para METAR) o justo después
   de movimientos rápidos de precio (señal para WebSocket).
3. Escribí bot\revision_semana_maker.md con los números de la semana y, para (2) y (3), una recomendación clara
   (hacerlo ya / no hace falta / esperar más datos) con la razón en 1 o 2 frases.
4. Avisale a Agus por ntfy: leé solo la línea "set BOT_NTFY_TEMA=" de bot\secreto.cmd con
   findstr /B "set BOT_NTFY_TEMA=" (ninguna otra línea) y hacé POST a https://ntfy.sh/<tema> con 2 o 3 líneas: neto
   de la semana, recompensa real/estimada, y "Revisión lista: bot\revision_semana_maker.md — recomendación:
   METAR <...>, WebSocket <...>".

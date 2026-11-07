#!/bin/bash
# Muestra si el bot corre, las ultimas lineas que escribio y el resumen.
CARPETA=/home/bot/polymarket-clima
systemctl --no-pager status polymarket-maker | head -4
for f in PARAR PARAR_maker_real; do [ -e "$CARPETA/bot/$f" ] && echo "FRENO: bot/$f -> $(cat "$CARPETA/bot/$f")"; done
echo; journalctl -u polymarket-maker -n 20 --no-pager
echo; cat "$CARPETA/bot/maker_resumen_real.md" 2>/dev/null
echo; echo "Geobloqueo: $(curl -fsS --max-time 15 https://polymarket.com/api/geoblock)"

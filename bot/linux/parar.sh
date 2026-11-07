#!/bin/bash
# Apaga el bot: cancela sus ordenes y no lo deja volver a arrancar (ni al reiniciar) hasta borrar bot/PARAR.
# Las acciones compradas quedan en la cuenta.
set -euo pipefail
CARPETA=/home/bot/polymarket-clima
[ "$(id -u)" = 0 ] || { echo "Correr como root (o con sudo)."; exit 1; }
echo "parado a mano $(date -u +%F' '%H:%M)Z" > "$CARPETA/bot/PARAR"
chown bot:bot "$CARPETA/bot/PARAR"
systemctl stop polymarket-maker
journalctl -u polymarket-maker -n 5 --no-pager
echo "Bot apagado. Para volver a prenderlo: rm $CARPETA/bot/PARAR && systemctl start polymarket-maker"

#!/bin/bash
# Actualiza el bot a la ultima version de main: para (cancela ordenes), git pull, revisa inventario, arranca.
set -euo pipefail
CARPETA=/home/bot/polymarket-clima
ENV=/etc/polymarket-maker/secreto.env
[ "$(id -u)" = 0 ] || { echo "Correr como root (o con sudo)."; exit 1; }
systemctl stop polymarket-maker
sudo -u bot git -C "$CARPETA" pull --ff-only \
  || echo "AVISO: git pull fallo (cambios locales?). Sigo con la version que estaba."
sudo -u bot /home/bot/venv/bin/pip install -q -r "$CARPETA/bot/requirements_real.txt"
rm -f "$CARPETA/bot/PARAR" "$CARPETA/bot/PARAR_maker_real"
cd "$CARPETA"
set -a; . "$ENV"; set +a
sudo -u bot --preserve-env=POLYMARKET_PRIVATE_KEY,POLYMARKET_WALLET,BOT_NTFY_TEMA,BOT_REAL_CONFIRMO \
  env PYTHONUTF8=1 /home/bot/venv/bin/python bot/maker.py inventario \
  || echo "AVISO: el inventario no coincide (ver arriba)."
systemctl start polymarket-maker
sleep 10
journalctl -u polymarket-maker -n 10 --no-pager

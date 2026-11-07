#!/bin/bash
# Paso 2: pasa el bot de la PC al servidor y lo arranca.
# Antes: apagar el bot de la PC (parar_bot.cmd y esperar que la ventana diga "Bot maker apagado")
# y copiar desde la PC a /root/migrar/ estos archivos de la carpeta bot\ :
#   secreto.cmd  config.json  maker_estado_real.json  maker_ops_real.csv
# (ver LEEME.md, paso 3). Las claves viajan por scp y nunca se escriben en un chat.
set -euo pipefail
CARPETA=/home/bot/polymarket-clima
M=/root/migrar
ENV=/etc/polymarket-maker/secreto.env
[ "$(id -u)" = 0 ] || { echo "Correr como root (o con sudo)."; exit 1; }

echo "IMPORTANTE: dos bots a la vez con la misma cuenta se pisan (cada uno cancela las ordenes del otro)."
read -r -p "¿El bot de la PC ya esta APAGADO (la ventana dijo 'Bot maker apagado')? Escribi si: " R
[ "$R" = "si" ] || { echo "Nada hecho."; exit 1; }

for f in secreto.cmd config.json; do
  [ -f "$M/$f" ] || { echo "Falta $M/$f (copialo desde la PC, ver LEEME.md)."; exit 1; }
done

echo "== Claves: secreto.cmd -> $ENV (solo root puede leerlo)"
# "set CLAVE=valor" de Windows -> "CLAVE=valor"; saca los \r y las lineas rem/@echo
tr -d '\r' < "$M/secreto.cmd" | sed -n 's/^[[:space:]]*set[[:space:]]\+\([A-Z_]\+\)=\(.*\)$/\1=\2/p' > "$ENV.nuevo"
chmod 600 "$ENV.nuevo"
for k in POLYMARKET_PRIVATE_KEY POLYMARKET_WALLET BOT_NTFY_TEMA; do
  grep -q "^$k=." "$ENV.nuevo" || { echo "secreto.cmd no tiene $k con valor. Nada hecho."; rm -f "$ENV.nuevo"; exit 1; }
done
grep -q '^BOT_REAL_CONFIRMO=si$' "$ENV.nuevo" || { echo "secreto.cmd no dice BOT_REAL_CONFIRMO=si. Nada hecho."; rm -f "$ENV.nuevo"; exit 1; }
mv "$ENV.nuevo" "$ENV"
shred -u "$M/secreto.cmd" 2>/dev/null || rm -f "$M/secreto.cmd"
echo "   OK (se leyeron $(wc -l < "$ENV") lineas; la copia de secreto.cmd se borro)"

echo "== Config y estado del bot"
sudo -u bot git -C "$CARPETA" pull --ff-only || echo "   (git pull fallo; sigo con la version que estaba)"
for f in config.json maker_estado_real.json maker_ops_real.csv; do
  if [ -f "$M/$f" ]; then install -o bot -g bot -m 644 "$M/$f" "$CARPETA/bot/$f"; echo "   copiado $f"; fi
done
python3 -c "import json,sys; c=json.load(open('$CARPETA/bot/config.json')); m=c['maker']; print('   modo', m['modo'], '| capital', m['capital_usd'], '| cajas', m['cajas']); sys.exit(m['modo']!='real')" \
  || { echo "config.json no esta en modo real. Revisalo antes de seguir."; exit 1; }
rm -f "$CARPETA/bot/PARAR" "$CARPETA/bot/PARAR_maker_real"

echo "== Revisar inventario contra la cuenta (solo lectura)"
cd "$CARPETA"
set -a; . "$ENV"; set +a
if ! sudo -u bot --preserve-env=POLYMARKET_PRIVATE_KEY,POLYMARKET_WALLET,BOT_NTFY_TEMA,BOT_REAL_CONFIRMO \
     env PYTHONUTF8=1 /home/bot/venv/bin/python bot/maker.py inventario; then
  read -r -p "El inventario no coincide (ver arriba). ¿Arrancar igual? Escribi si: " R
  [ "$R" = "si" ] || { echo "No se arranco. Revisar y correr de nuevo."; exit 1; }
fi

echo "== Arrancar y dejarlo prendido al reiniciar"
systemctl enable --now polymarket-maker
sleep 15
systemctl --no-pager status polymarket-maker | head -5
journalctl -u polymarket-maker -n 15 --no-pager
echo
echo "Listo: el bot corre en el servidor. Te tiene que llegar 'Maker (real) arrancó' al celular."
echo "NO vuelvas a abrir iniciar_maker.cmd en la PC (se pisarian)."

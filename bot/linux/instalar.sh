#!/bin/bash
# Paso 1: prepara un servidor Ubuntu nuevo para el bot maker. NO lo arranca ni pide claves.
# Uso (como root, en el servidor):
#   curl -fsSL https://raw.githubusercontent.com/Agustinsff/polymarket-clima/main/bot/linux/instalar.sh | bash
# Se puede correr de nuevo sin problema.
set -euo pipefail
REPO=https://github.com/Agustinsff/polymarket-clima
CARPETA=/home/bot/polymarket-clima

[ "$(id -u)" = 0 ] || { echo "Correr como root (o con sudo)."; exit 1; }

echo "== 1/6 ¿Polymarket deja operar desde este servidor?"
GEO=$(curl -fsS --max-time 20 https://polymarket.com/api/geoblock || echo '{}')
echo "   respuesta: $GEO"
if ! echo "$GEO" | grep -q '"blocked":false'; then
  echo "   ALTO: Polymarket bloquea (o no responde) desde este pais. No sirve este servidor."
  echo "   Borralo y crea otro en un pais permitido (Finlandia, Suecia, Espana, Chile...)."
  exit 1
fi

echo "== 2/6 Programas (git, python, reloj en hora)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip curl ca-certificates > /dev/null
timedatectl set-ntp true || true
timedatectl set-timezone UTC || true

echo "== 3/6 Usuario 'bot' (el bot no corre como root)"
id bot > /dev/null 2>&1 || useradd -m -s /bin/bash bot

echo "== 4/6 Copia del repo"
if [ -d "$CARPETA/.git" ]; then
  sudo -u bot git -C "$CARPETA" pull --ff-only
else
  sudo -u bot git clone --depth 50 "$REPO" "$CARPETA"
fi

echo "== 5/6 Librerias de Python"
[ -x /home/bot/venv/bin/python ] || sudo -u bot python3 -m venv /home/bot/venv
sudo -u bot /home/bot/venv/bin/pip install -q --upgrade pip
sudo -u bot /home/bot/venv/bin/pip install -q -r "$CARPETA/bot/requirements_real.txt"
(cd "$CARPETA" && sudo -u bot /home/bot/venv/bin/python bot/test_maker.py > /tmp/test_maker.txt 2>&1) \
  && echo "   pruebas del bot: OK" || { echo "   pruebas del bot FALLARON:"; tail -20 /tmp/test_maker.txt; exit 1; }

echo "== 6/6 Servicio (queda instalado pero APAGADO)"
mkdir -p /etc/polymarket-maker
chmod 700 /etc/polymarket-maker
[ -f /etc/polymarket-maker/secreto.env ] || install -m 600 /dev/null /etc/polymarket-maker/secreto.env
install -m 644 "$CARPETA/bot/linux/polymarket-maker.service" /etc/systemd/system/polymarket-maker.service
for s in pasar_de_la_pc.sh actualizar.sh parar.sh estado.sh; do
  install -m 755 "$CARPETA/bot/linux/$s" /usr/local/bin/maker-${s%.sh}
done
systemctl daemon-reload

echo
echo "Listo. El bot NO esta corriendo. Siguiente paso (el dia del cambio, con el bot de la PC apagado):"
echo "  copiar los archivos de la PC a /root/migrar/ y correr:  maker-pasar_de_la_pc"
echo "Instrucciones completas: $CARPETA/bot/linux/LEEME.md"

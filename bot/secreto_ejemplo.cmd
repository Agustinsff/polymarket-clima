@echo off
rem Copiar este archivo como bot\secreto.cmd y completar. bot\secreto.cmd NO se sube al repo (.gitignore).
rem Clave del firmante o de la clave de sesion (nunca la compartas):
set POLYMARKET_PRIVATE_KEY=
rem Direccion de la billetera de Polymarket (vacio = la Deposit Wallet del firmante):
set POLYMARKET_WALLET=
rem Tema secreto de ntfy.sh para avisos al celular (inventar uno largo, p. ej. agus-bot-7f3k9q2x):
set BOT_NTFY_TEMA=
rem Solo para modo real (ademas de "modo": "real" en bot\config.json):
set BOT_REAL_CONFIRMO=no
rem Opcional, para que el bot maker cobre solo las cajas ganadas (billetera proxy): en polymarket.com -> Settings ->
rem API Keys -> Relayer API Keys -> crear una y copiar "API Key" y "Signer Address":
set BOT_RELAYER_API_KEY=
set BOT_RELAYER_API_ADDRESS=

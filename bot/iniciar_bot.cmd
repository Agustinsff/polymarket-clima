@echo off
rem Arranca el bot y lo vuelve a arrancar si se cae. Para frenarlo: parar_bot.cmd (o crear bot\PARAR).
cd /d "%~dp0.."
set PYTHONUTF8=1
if exist bot\secreto.cmd call bot\secreto.cmd
:otra
python bot\polybot.py bucle
if %errorlevel%==0 goto fin
if exist bot\PARAR goto fin
echo El bot se cerro con un error; vuelve a arrancar en 60 s (cerrar esta ventana para cancelar)...
timeout /t 60 /nobreak >nul
goto otra
:fin
echo Bot apagado. Para volver a arrancar: borrar bot\PARAR o bot\PARAR_real (el que exista; adentro dice el motivo) y abrir iniciar_bot.cmd
pause

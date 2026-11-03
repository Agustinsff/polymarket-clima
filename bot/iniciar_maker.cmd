@echo off
rem Arranca el bot MAKER y lo vuelve a arrancar si se cae. Para frenarlo: parar_bot.cmd (crea bot\PARAR).
cd /d "%~dp0.."
set PYTHONUTF8=1
if exist bot\secreto.cmd call bot\secreto.cmd
:otra
python bot\maker.py bucle
if %errorlevel%==0 goto fin
if exist bot\PARAR goto fin
echo El bot maker se cerro con un error; vuelve a arrancar en 60 s (cerrar esta ventana para cancelar)...
timeout /t 60 /nobreak >nul
goto otra
:fin
echo Bot maker apagado. Para volver a arrancar: borrar bot\PARAR o bot\PARAR_maker_real y abrir iniciar_maker.cmd
pause

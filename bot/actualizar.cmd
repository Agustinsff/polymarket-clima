@echo off
rem Actualiza el bot maker SIN cancelar sus ordenes (no pierde el lugar en la fila):
rem   1. git pull   2. deja bot\REINICIAR   3. el bot que esta corriendo sale con codigo 3 y iniciar_maker.cmd lo
rem   vuelve a arrancar enseguida con el codigo nuevo; al arrancar adopta las ordenes que siguen correspondiendo.
rem Si el bot NO esta corriendo, solo actualiza (y borra el REINICIAR para que no quede colgado).
rem Si el PR cambio iniciar_maker.cmd, cerrar esa ventana y abrirla de nuevo despues de este paso.
cd /d "%~dp0.."
git pull --ff-only
if errorlevel 1 (
  echo No se pudo actualizar (git pull fallo). El bot sigue corriendo como estaba.
  pause
  exit /b 1
)
echo reinicio pedido %date% %time% > bot\REINICIAR
echo Listo: el bot se reinicia en su proxima pasada (menos de un minuto) sin cancelar las ordenes.
echo Si el bot no estaba corriendo, borrar bot\REINICIAR y abrir iniciar_maker.cmd.
pause

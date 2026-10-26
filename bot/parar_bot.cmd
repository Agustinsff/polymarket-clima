@echo off
rem Boton de apagado: el bot termina en su proxima pasada y no vuelve a operar hasta borrar bot\PARAR.
echo parado a mano %date% %time% > "%~dp0PARAR"
echo Listo: el bot se frena en su proxima pasada.
pause

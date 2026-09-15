@echo off
REM Lanzador del sincronizador USB del SGDP (Windows). Requiere Python 3.
python "%~dp0sincronizar_usb.py" %*
echo.
pause

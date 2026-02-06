@echo off
echo ========================================
echo   SISTEMA DE ENGASTADO AUTOMATICO
echo ========================================
echo.
echo Iniciando servidor...
echo.
cd /d %~dp0

REM Obtener la IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%

echo [INFO] El servidor estara disponible en:
echo.
echo   - Local:    http://localhost:5000
echo   - Red:      http://%IP%:5000
echo.
echo Para acceder desde otros dispositivos, usa la IP de red.
echo Presiona Ctrl+C para detener el servidor.
echo.
echo ========================================
echo.

.venv\Scripts\python.exe run.py
pause
@echo off
chcp 65001 >nul
color 0A
title Actualizar App en Raspberry Pi

REM Configurar ruta de Git
set GIT="C:\Users\estebanv\Downloads\PortableGit\cmd\git.exe"

echo.
echo ========================================
echo   ACTUALIZANDO APP EN RASPBERRY PI
echo ========================================
echo.

REM Verificar si hay cambios
%GIT% status --short
if errorlevel 1 (
    echo ERROR: No se pudo verificar el estado de Git
    pause
    exit /b 1
)

echo.
echo [1/4] Agregando archivos modificados...
%GIT% add .

echo.
echo [2/4] Creando commit...
set /p mensaje="Describe los cambios realizados: "
if "%mensaje%"=="" set mensaje=Actualización automática

%GIT% commit -m "%mensaje%"
if errorlevel 1 (
    echo No hay cambios para enviar
    goto ACTUALIZAR_RASPBERRY
)

echo.
echo [3/4] Subiendo cambios a GitHub...
%GIT% push origin main
if errorlevel 1 (
    echo ERROR: No se pudo subir a GitHub
    pause
    exit /b 1
)

:ACTUALIZAR_RASPBERRY
echo.
echo [4/4] Actualizando Raspberry Pi...
ssh ocalab@192.168.1.108 "cd ~/PROYECTO-ENGASTADO1 && git pull origin main && sudo systemctl restart engastado.service"

if errorlevel 1 (
    echo.
    echo ERROR: No se pudo conectar a la Raspberry Pi
    echo Verifica que esté encendida y conectada a la red
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✓ ACTUALIZACIÓN COMPLETADA
echo ========================================
echo.
echo La app en la Raspberry Pi ha sido actualizada
echo Accede a: http://192.168.1.108:5000
echo.
pause

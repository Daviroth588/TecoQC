@echo off
echo ============================================
echo   Tecology TecoQC - Instalacion
echo ============================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Descargue Python 3.10 o superior desde https://www.python.org
    echo Asegurese de marcar "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

echo Python detectado:
python --version
echo.

:: Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR durante la instalacion. Intente ejecutar como Administrador.
    pause
    exit /b 1
)

:: Intentar instalar pythonnet (opcional, para temperaturas con LibreHardwareMonitor)
:: No compatible con Python 3.14+, se omite si falla
echo.
echo Intentando instalar pythonnet (opcional para temperaturas)...
pip install "pythonnet>=3.0.0" >nul 2>&1
if errorlevel 1 (
    echo AVISO: pythonnet no pudo instalarse con esta version de Python.
    echo         Las temperaturas usaran metodos alternativos ^(WMI/OpenHardwareMonitor^).
    echo         Esto es normal con Python 3.14+.
) else (
    echo pythonnet instalado correctamente.
)

echo.
echo ============================================
echo   Instalacion completada exitosamente.
echo   Ejecute run.bat para iniciar TecoQC.
echo ============================================
pause

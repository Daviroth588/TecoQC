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

echo.
echo ============================================
echo   Instalacion completada exitosamente.
echo   Ejecute run.bat para iniciar TecoQC.
echo ============================================
pause

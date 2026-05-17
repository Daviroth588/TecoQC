@echo off
echo ============================================
echo   Tecology TecoQC - Compilando ejecutable
echo ============================================
echo.

:: Verificar que LibreHardwareMonitorLib.dll existe en assets/
if not exist "assets\LibreHardwareMonitorLib.dll" (
    echo ADVERTENCIA: assets\LibreHardwareMonitorLib.dll no encontrado.
    echo Descargue LibreHardwareMonitor desde:
    echo   https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
    echo Extraiga el ZIP y copie LibreHardwareMonitorLib.dll a la carpeta assets\
    echo.
    echo Compilando de todos modos ^(sin sensor de temperatura^)...
    echo.
)

:: Icono es opcional - solo se incluye si existe
set ICON_FLAG=
if exist "assets\logo.ico" (
    set ICON_FLAG=--icon=assets\logo.ico
)

pyinstaller --onefile --windowed --name TecoQC ^
    %ICON_FLAG% ^
    --add-data "assets;assets" ^
    --add-data "report;report" ^
    --hidden-import=wmi ^
    --hidden-import=win32com ^
    --hidden-import=win32com.client ^
    --hidden-import=win32api ^
    --hidden-import=win32con ^
    --hidden-import=psutil ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=reportlab ^
    --hidden-import=reportlab.graphics.barcode ^
    --hidden-import=reportlab.graphics.barcode.code128 ^
    --hidden-import=cv2 ^
    --hidden-import=sounddevice ^
    --hidden-import=numpy ^
    --hidden-import=sqlite3 ^
    --hidden-import=clr ^
    --collect-all reportlab ^
    --collect-all pythonnet ^
    --uac-admin ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: La compilacion fallo. Revisa los mensajes de error arriba.
    echo Causas comunes:
    echo   - pyinstaller no esta instalado: pip install pyinstaller
    echo   - Falta alguna dependencia: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Compilacion completada.
echo Ejecutable generado en: dist\TecoQC.exe
echo.
echo NOTA: El ejecutable pedira permisos de Administrador al iniciar.
echo       Esto es necesario para leer temperaturas de hardware.
pause

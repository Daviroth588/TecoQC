@echo off
echo ============================================
echo   Tecology TecoQC - Compilando ejecutable
echo ============================================
echo.

:: Verificar que LibreHardwareMonitor.dll existe en assets/
if not exist "assets\LibreHardwareMonitor.dll" (
    echo ADVERTENCIA: assets\LibreHardwareMonitor.dll no encontrado.
    echo Descargue LibreHardwareMonitor.dll desde:
    echo   https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
    echo y cópielo a la carpeta assets\ antes de compilar.
    echo.
    echo Compilando de todos modos ^(sin sensor de temperatura^)...
    echo.
)

pyinstaller --onefile --windowed --name TecoQC ^
    --icon=assets\logo.ico ^
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

echo.
echo Compilacion completada.
echo Ejecutable generado en: dist\TecoQC.exe
echo.
echo NOTA: El ejecutable pedira permisos de Administrador al iniciar.
echo       Esto es necesario para leer temperaturas de hardware.
pause

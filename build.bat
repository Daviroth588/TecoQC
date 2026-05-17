@echo off
echo ============================================
echo   Tecology TecoQC - Compilando ejecutable
echo ============================================
echo.

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
    --collect-all reportlab ^
    main.py

echo.
echo Compilacion completada.
echo Ejecutable generado en: dist\TecoQC.exe
pause

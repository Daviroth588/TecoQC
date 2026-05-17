@echo off
echo ============================================
echo   Tecology TecoQC - Compilando ejecutable
echo ============================================
echo.
pyinstaller --onefile --windowed --name TecoQC ^
    --icon=assets\logo.ico ^
    --add-data "assets;assets" ^
    --hidden-import=wmi ^
    --hidden-import=win32com ^
    --hidden-import=win32com.client ^
    --hidden-import=psutil ^
    --hidden-import=PIL ^
    main.py
echo.
echo Compilacion completada. Ejecutable en dist\TecoQC.exe
pause

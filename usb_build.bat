@echo off
echo ============================================
echo   Tecology TecoQC - Preparar USB
echo ============================================
echo.
echo Este script instala dependencias, compila TecoQC.exe
echo y lo copia a la raiz del USB automaticamente.
echo.

:: Detectar Python 3.12 o superior
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    py -3.11 --version >nul 2>&1
    if errorlevel 1 (
        python --version >nul 2>&1
        if errorlevel 1 (
            echo ERROR: No se encontro Python instalado.
            echo Descargue Python 3.12 desde https://www.python.org
            echo Marque "Add Python to PATH" al instalar.
            pause
            exit /b 1
        ) else (
            set PYTHON=python
        )
    ) else (
        set PYTHON=py -3.11
    )
) else (
    set PYTHON=py -3.12
)

echo Python detectado:
%PYTHON% --version
echo.

:: Instalar dependencias
echo [1/3] Instalando dependencias...
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR al instalar dependencias. Intente como Administrador.
    pause
    exit /b 1
)
echo.

:: Compilar ejecutable
echo [2/3] Compilando TecoQC.exe...

set ICON_FLAG=
if exist "assets\logo.ico" (
    set ICON_FLAG=--icon=assets\logo.ico
)

%PYTHON% -m PyInstaller --onefile --windowed --name TecoQC ^
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
    pause
    exit /b 1
)

:: Copiar .exe a la raiz del USB (carpeta padre de donde esta este script)
echo.
echo [3/3] Copiando TecoQC.exe al USB...
copy /Y "dist\TecoQC.exe" "..\TecoQC.exe"
if errorlevel 1 (
    echo AVISO: No se pudo copiar automaticamente.
    echo Copia manualmente: dist\TecoQC.exe  ->  raiz del USB
) else (
    echo TecoQC.exe copiado exitosamente a la raiz del USB.
)

echo.
echo ============================================
echo   LISTO. En la laptop ejecuta TecoQC.exe
echo   como Administrador (clic derecho).
echo ============================================
pause

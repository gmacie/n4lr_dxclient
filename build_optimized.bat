@echo off
echo Building N4LR DX Client...

REM Remove old builds
rmdir /s /q build dist 2>nul

REM Build with PyInstaller
pyinstaller ^
    --name=N4LR-DXClient ^
    --onefile ^
    --windowed ^
    --hidden-import=_cffi_backend ^
    --collect-all flet ^
    --collect-all flet_desktop ^
    --add-data "frontend;frontend" ^
    --add-data "backend;backend" ^
    --exclude-module=PyQt5 ^
    --exclude-module=PyQt6 ^
    --exclude-module=PySide2 ^
    --exclude-module=PySide6 ^
    --clean ^
    run.py

REM Create data structure in dist
mkdir dist\data
mkdir dist\data\static
mkdir dist\data\user

REM Copy static data files
copy data\static\*.json dist\data\static\
copy data\static\*.dat dist\data\static\

echo.
echo Build complete!
echo Exe: dist\N4LR-DXClient.exe
echo Data: dist\data\
echo.
pause
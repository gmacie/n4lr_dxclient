@echo off
REM Build script for N4LR DX Client
echo Building N4LR DX Client for Windows...
echo.

REM Run PyInstaller with exclusions
pyinstaller ^
    --name="N4LR-DXClient" ^
    --onefile ^
    --windowed ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --hidden-import=flet_core ^
    --hidden-import=flet_runtime ^
    --add-data "cty.dat;." ^
    --add-data "dxcc_mapping.json;." ^
    --add-data "challenge_data.json;." ^
    run.py

echo.
echo Build complete! Check the 'dist' folder for N4LR-DXClient.exe
echo.
echo Don't forget to copy these files to the dist folder:
echo   - config.ini (or create new one)
echo   - lotw_users.json (if you have it)
echo.
pause

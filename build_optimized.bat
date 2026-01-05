@echo off
REM Optimized build script for N4LR DX Client
echo Building N4LR DX Client (optimized)...
echo.

REM Clean old builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist N4LR-DXClient.spec del N4LR-DXClient.spec

REM Run PyInstaller with optimizations
pyinstaller ^
    --name="N4LR-DXClient" ^
    --onefile ^
    --windowed ^
    --strip ^
    --noupx ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module scipy ^
    --exclude-module PIL ^
    --exclude-module cv2 ^
    --exclude-module pytest ^
    --exclude-module test ^
    --exclude-module unittest ^
    --add-data "cty.dat;." ^
    --add-data "ffma_grids.json;." ^
    --add-data "dxcc_mapping.json;." ^
    --add-data "dxcc_prefixes.json;." ^
    --add-data "challenge_data.json;." ^
	--add-data "dxcc_entities.json;." ^
	--add-data "dxcc_name_overrides.json;." ^
    run.py

echo.
echo Checking file size...
dir dist\N4LR-DXClient.exe | findstr "N4LR-DXClient.exe"
echo.
echo Build complete! Size before compression shown above.
echo.
echo Now compressing with 7-Zip (if available)...
where 7z >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    7z a -mx=9 dist\N4LR-DXClient.7z dist\N4LR-DXClient.exe
    echo Compressed with 7-Zip!
    dir dist\N4LR-DXClient.7z | findstr ".7z"
) else (
    echo 7-Zip not found - skipping compression
    echo Install 7-Zip from https://www.7-zip.org/ for better compression
)
echo.
echo Don't forget to copy these files to the dist folder:
echo   - config.ini (optional - will be created on first run)
echo   - lotw_users.json will download automatically on first run
echo   - challenge_data.json is embedded but can be updated via Settings
echo.
pause
```

**Key change:** Added line 29:
```
    --add-data "dxcc_prefixes.json;." ^
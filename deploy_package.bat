@echo off
echo Creating distribution package...

REM Build the exe
call build_optimized.bat

REM Create clean distribution folder
rmdir /s /q dist\N4LR_DXClient_Package 2>nul
mkdir dist\N4LR_DXClient_Package
mkdir dist\N4LR_DXClient_Package\data
mkdir dist\N4LR_DXClient_Package\data\static
mkdir dist\N4LR_DXClient_Package\data\user

REM Copy exe
copy dist\N4LR-DXClient.exe dist\N4LR_DXClient_Package\

REM Copy static data files
copy data\static\*.json dist\N4LR_DXClient_Package\data\static\
copy data\static\*.dat dist\N4LR_DXClient_Package\data\static\

REM Create README
echo N4LR DX Client > dist\N4LR_DXClient_Package\README.txt
echo. >> dist\N4LR_DXClient_Package\README.txt
echo Data files are in the data\ folder: >> dist\N4LR_DXClient_Package\README.txt
echo   data\static\ - Reference files (DXCC, CTY.DAT) >> dist\N4LR_DXClient_Package\README.txt
echo   data\user\   - Your settings and logs >> dist\N4LR_DXClient_Package\README.txt

REM Create zip
powershell Compress-Archive -Path dist\N4LR_DXClient_Package\* -DestinationPath dist\N4LR_DXClient.zip -Force

echo.
echo Package created!
echo Folder: dist\N4LR_DXClient_Package\
echo Zip: dist\N4LR_DXClient.zip
echo.
pause
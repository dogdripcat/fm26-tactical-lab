@echo off
cd /d "%~dp0"
echo Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto fail
echo Building EXE...
python -m PyInstaller --onefile --name FM26TacticalLab --add-data "roles.json;." --add-data "role_behaviours.json;." --add-data "role_catalog.json;." fm26lab.py
if errorlevel 1 goto fail
echo.
echo [OK] Built: dist\FM26TacticalLab.exe
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed.
pause
exit /b 1

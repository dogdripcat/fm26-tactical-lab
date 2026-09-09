@echo off
cd /d "%~dp0"
python fm26lab.py init
if errorlevel 1 goto fail
python fm26lab.py tactic-add --file sample_leicester_4231.json
if errorlevel 1 goto fail
python fm26lab.py tactic-list
echo.
echo [OK] Sample tactic registered.
pause
exit /b 0

:fail
echo.
echo [ERROR] Quick start failed.
pause
exit /b 1

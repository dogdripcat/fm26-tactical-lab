@echo off
cd /d "%~dp0"
echo ==========================================
echo FM26 Tactical Lab v0.2.1 - Core Self Test
echo ==========================================
echo.
python --version
if errorlevel 1 goto python_fail
echo.
python fm26lab.py self-test
if errorlevel 1 goto test_fail
echo.
echo [OK] Core self-test completed.
echo You can now run run.bat.
pause
exit /b 0

:python_fail
echo.
echo [ERROR] Python was not found.
echo Check Python installation and PATH.
pause
exit /b 1

:test_fail
echo.
echo [ERROR] Core self-test failed.
echo Please send a screenshot of this window.
pause
exit /b 1

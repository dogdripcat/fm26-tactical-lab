@echo off
cd /d "%~dp0"
python fm26lab.py
if errorlevel 1 (
  echo.
  echo [ERROR] Program stopped with an error.
  echo Please send a screenshot of this window.
  pause
)

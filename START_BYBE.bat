@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 scripts\bybe.py run
) else (
  python scripts\bybe.py run
)
if errorlevel 1 (
  echo.
  echo BYBE Studio failed. See the error above.
  pause
)
endlocal

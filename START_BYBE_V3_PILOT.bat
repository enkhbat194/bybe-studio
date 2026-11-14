@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 studio\server.py
) else (
  python studio\server.py
)
if errorlevel 1 (
  echo.
  echo BYBE V3 pilot stopped with an error. Existing V2 was not changed.
  pause
)
endlocal

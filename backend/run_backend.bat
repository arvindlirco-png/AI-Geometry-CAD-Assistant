@echo off
cd /d %~dp0
set NEED_INSTALL=0
if not exist .venv (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3.11 -m venv .venv
  ) else (
    python -m venv .venv
  )
  set NEED_INSTALL=1
)
if not exist .venv\Scripts\uvicorn.exe set NEED_INSTALL=1
call .venv\Scripts\activate.bat
if "%NEED_INSTALL%"=="1" (
  python -m pip install --upgrade pip
  pip install -r requirements.txt
)
uvicorn app.main:app --host 0.0.0.0 --port 8020 --reload

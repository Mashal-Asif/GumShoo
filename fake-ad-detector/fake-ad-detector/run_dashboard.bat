@echo off
if not exist .venv (
  echo Run run_all.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python fake_ad_dashboard.py dashboard
pause

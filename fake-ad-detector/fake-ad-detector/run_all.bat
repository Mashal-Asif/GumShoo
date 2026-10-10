@echo off
if not exist fake_job_postings.csv (
  echo Put fake_job_postings.csv in this folder first. Download: https://www.kaggle.com/shivamb/real-or-fake-fake-jobposting-prediction
  pause
  exit /b 1
)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python fake_ad_dashboard.py train
python fake_ad_dashboard.py dashboard
pause

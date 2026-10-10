# Fake Ad Detector (with dashboard)

Detects fake / scam ads from their text. Trained on the Kaggle dataset
**Real / Fake Job Posting Prediction** (EMSCAD, ~17.9k ads, ~5% fraudulent).

Model: TF-IDF (words + characters) + hand-made scam signals -> Logistic Regression,
calibrated Linear SVM or Complement Naive Bayes. The script compares all three with
5-fold cross-validation, picks the best by PR-AUC, tunes the threshold on training data,
and tests once on a held-out 20% test set.

## Folder
```
fake-ad-detector/
  fake_ad_dashboard.py   all the code (train, predict, dashboard)
  requirements.txt       libraries
  download_data.py       optional: downloads the dataset via kagglehub
  run_all.bat            Windows: install + train + open dashboard
  run_dashboard.bat      Windows: open dashboard (after training)
  fake_job_postings.csv  <- YOU add this (from Kaggle)
```
After training, these appear: `fake_ad_model_full.joblib` (the trained model) and `results/` (plots, metrics.json, errors.csv, top_fake_words.csv).

## Steps
1. Download `fake_job_postings.csv` from
   https://www.kaggle.com/shivamb/real-or-fake-fake-jobposting-prediction
   and put it in this folder.
2. Windows: double-click `run_all.bat`.
   Manual way:
   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1          (Mac/Linux: source .venv/bin/activate)
   python -m pip install -r requirements.txt
   python fake_ad_dashboard.py train --sample 3000    (quick trial)
   python fake_ad_dashboard.py train                  (full run)
   python fake_ad_dashboard.py dashboard              (opens http://127.0.0.1:8000)
   ```
3. Check one ad from the terminal:
   ```
   python fake_ad_dashboard.py predict "Earn $5000 weekly from home, pay a fee to start!!"
   ```

## Notes
- Report the **fake-class** precision, recall and F1, not accuracy (only ~5% of ads are fake).
- The dataset has job ads from 2012-2014 only, so the model is best at job-scam language.
- Paste full ads (title + company profile + description + requirements) for fair predictions.

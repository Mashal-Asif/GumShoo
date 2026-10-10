"""
OPTIONAL helper: downloads the Kaggle dataset "Real / Fake Job Posting Prediction"
and copies fake_job_postings.csv into this folder.

Needs:  python -m pip install kagglehub
        a Kaggle account (and an API token in ~/.kaggle/kaggle.json if Kaggle asks for one)

If this fails, just download the CSV manually from
https://www.kaggle.com/shivamb/real-or-fake-fake-jobposting-prediction
and put fake_job_postings.csv in this folder.
"""
import glob, os, shutil, sys

try:
    import kagglehub
except ImportError:
    sys.exit("Run first:  python -m pip install kagglehub")

try:
    folder = kagglehub.dataset_download("shivamb/real-or-fake-fake-jobposting-prediction")
except Exception as e:
    sys.exit(f"Download failed: {e}\nDownload the CSV manually from Kaggle (see the top of this file).")

matches = glob.glob(os.path.join(folder, "**", "fake_job_postings.csv"), recursive=True)
if not matches:
    sys.exit(f"fake_job_postings.csv not found in {folder}")
shutil.copy(matches[0], "fake_job_postings.csv")
print("Done -> fake_job_postings.csv copied to this folder")

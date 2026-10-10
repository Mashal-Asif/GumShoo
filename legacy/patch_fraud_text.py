"""
patch_fraud_text.py
Plugs the trained SMS/ad text model (fraud_detection/sms_fraud_model.pkl) into the
Fraud Detection tool in app.py. Your other edits are kept.

Run from the folder that contains app.py (after running train_sms_fraud.py):
    python patch_fraud_text.py
A backup is saved as app_before_fraud_text.py.
"""

import re
import shutil
import sys

with open("app.py", encoding="utf-8") as f:
    s = f.read()

if "_load_text_model" in s:
    sys.exit("app.py already uses the trained text model. Nothing to do.")

NEW = '''@st.cache_resource
def _load_text_model():
    """Trained text model (TF-IDF + classifier), or None if it has not been trained yet."""
    path = Path(__file__).parent / "fraud_detection" / "sms_fraud_model.pkl"
    return joblib.load(path) if path.exists() else None


def predict_fraud(text: str) -> dict:
    """
    INPUT : one text (an ad, job post, message)
    OUTPUT: {"label": "Fraud"/"Legit", "score": P(fraud)}
    Uses the trained model (SMS Spam Collection) together with the rule-based red flags:
    the higher of the two scores wins. For model-only results, delete the rule_score lines.
    """
    rule_score = min(0.95, 0.10 + 0.25 * len(find_red_flags(text)))
    score = rule_score
    model = _load_text_model()
    if model is not None:
        score = max(rule_score, float(model.predict_proba([text])[0, 1]))
    return {"label": "Fraud" if score >= 0.5 else "Legit", "score": score}
'''

pattern = re.compile(
    r'def predict_fraud\(text: str\) -> dict:.*?return \{"label": "Fraud" if score >= 0\.5 else "Legit", "score": score\}\n',
    re.S)
if len(pattern.findall(s)) != 1:
    sys.exit("Could not find predict_fraud in app.py. app.py was NOT changed. Send me this message.")
s = pattern.sub(lambda m: NEW, s)

# imports this code needs
if "import joblib" not in s:
    s = s.replace("import hashlib\n", "import hashlib\nimport joblib\n", 1)
if "from pathlib import Path" not in s:
    s = s.replace("import hashlib\n", "import hashlib\nfrom pathlib import Path\n", 1)

# Fraud is no longer a placeholder tool
s = s.replace("PLACEHOLDER_TOOLS = {FRAUD, PROPAGANDA}", "PLACEHOLDER_TOOLS = {PROPAGANDA}")
s = s.replace("PLACEHOLDER_TOOLS = {DEEPFAKE, FRAUD, PROPAGANDA}", "PLACEHOLDER_TOOLS = {DEEPFAKE, PROPAGANDA}")
s = s.replace("Fraud (text) and Propaganda still use placeholder models.",
              "Fraud uses trained models (transactions, and text trained on the SMS Spam Collection). Propaganda is still a placeholder.")

shutil.copyfile("app.py", "app_before_fraud_text.py")
with open("app.py", "w", encoding="utf-8") as f:
    f.write(s)
print("Patched app.py. Backup saved as app_before_fraud_text.py. Now run: streamlit run app.py")

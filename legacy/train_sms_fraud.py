"""
train_sms_fraud.py
Trains a text classifier (spam/fraud vs normal) on the SMS Spam Collection
and saves it so the app's Fraud Detection tool can use it.

Run from the folder that contains app.py:
    python train_sms_fraud.py
or point it at the dataset file yourself:
    python train_sms_fraud.py "D:\\SCAM_Detect_AI\\sms+spam+collection\\SMSSpamCollection"

Needs:  python -m pip install scikit-learn pandas joblib
Output: fraud_detection/sms_fraud_model.pkl      (the trained model)
        fraud_detection/sms_fraud_metrics.txt    (numbers for your report)
"""

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline

OUT_DIR = Path("fraud_detection")

# A few messages to show what the model does on text it was NOT trained on
SAMPLES = [
    ("Prize SMS", "URGENT! You have won a 1 week FREE membership in our 100,000 Prize Jackpot! Txt the word CLAIM to 81010"),
    ("Friendly SMS", "Ok lar... I will be home soon, do you want me to buy dinner?"),
    ("Job scam ad", "Earn $500 per day from home, no experience needed. Pay a small registration fee and DM us on WhatsApp. Limited slots!"),
    ("Normal job ad", "We are hiring a junior data analyst. Requirements: BSc in statistics. Send your CV to hr@company.com."),
]


def find_dataset() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    for p in Path(".").rglob("SMSSpamCollection*"):
        if p.is_file():
            return p
    sys.exit('Could not find the SMSSpamCollection file. Run:  python train_sms_fraud.py "full\\path\\to\\SMSSpamCollection"')


def load(path: Path) -> pd.DataFrame:
    """Each line is:  label<TAB>text   (label is ham or spam)."""
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            label, sep, text = line.rstrip("\n").partition("\t")
            if sep and label in ("ham", "spam") and text.strip():
                rows.append((int(label == "spam"), text.strip()))
    df = pd.DataFrame(rows, columns=["spam", "text"])
    return df.drop_duplicates("text").reset_index(drop=True)  # duplicates would leak between train and test


def features() -> FeatureUnion:
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, min_df=2)),
    ])


def main():
    path = find_dataset()
    df = load(path)
    n_spam = int(df.spam.sum())
    print(f"Loaded {len(df)} unique messages from {path}  (spam: {n_spam}, normal: {len(df) - n_spam})")

    X_train, X_test, y_train, y_test = train_test_split(
        df.text, df.spam, test_size=0.2, stratify=df.spam, random_state=42)

    candidates = {
        "Naive Bayes": Pipeline([("tfidf", features()), ("clf", MultinomialNB(alpha=0.1))]),
        "Logistic Regression": Pipeline([("tfidf", features()),
                                         ("clf", LogisticRegression(C=10, max_iter=2000, class_weight="balanced"))]),
    }

    print("\nStep 1: compare models with 5-fold cross-validation on the training data (F1 of the spam class)")
    best_name, best_f1 = "", -1.0
    for name, model in candidates.items():
        score = cross_val_score(model, X_train, y_train, cv=5, scoring="f1").mean()
        print(f"  {name:20} F1 = {score:.3f}")
        if score > best_f1:
            best_name, best_f1 = name, score

    print(f"\nStep 2: train the best model ({best_name}) and test it on the 20% of data it has never seen")
    model = candidates[best_name].fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred)
    rec = recall_score(y_test, pred)
    f1 = f1_score(y_test, pred)
    cm = confusion_matrix(y_test, pred)
    print(f"  Accuracy {acc:.3f} | Precision {prec:.3f} | Recall {rec:.3f} | F1 {f1:.3f}")
    print("  Confusion matrix (rows = real, columns = predicted; order: normal, spam):")
    print(cm)
    print(classification_report(y_test, pred, target_names=["normal", "spam"], digits=3))

    print("Step 3: try it on messages that are not from the dataset (probability of fraud):")
    for desc, text in SAMPLES:
        print(f"  {desc:14} {model.predict_proba([text])[0, 1]:.2f}")

    OUT_DIR.mkdir(exist_ok=True)
    joblib.dump(model, OUT_DIR / "sms_fraud_model.pkl")
    report = (
        f"Model: {best_name} (TF-IDF word 1-2 grams + character 2-4 grams)\n"
        f"Dataset: SMS Spam Collection, {len(df)} unique messages ({n_spam} spam), 80/20 stratified split\n"
        f"Cross-validated F1 (training data): {best_f1:.3f}\n"
        f"Test accuracy {acc:.3f}, precision {prec:.3f}, recall {rec:.3f}, F1 {f1:.3f}\n"
        f"Confusion matrix (normal, spam):\n{cm}\n"
    )
    (OUT_DIR / "sms_fraud_metrics.txt").write_text(report, encoding="utf-8")
    print(f"\nSaved: {OUT_DIR / 'sms_fraud_model.pkl'} and {OUT_DIR / 'sms_fraud_metrics.txt'}")


if __name__ == "__main__":
    main()

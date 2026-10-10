"""
Fake Ad Detection - full pipeline on the Kaggle dataset
"Real / Fake Job Posting Prediction" (EMSCAD): fake_job_postings.csv

What this script does (one command):
  1. Loads and cleans the real dataset, prints class balance
  2. Splits into train (80%) / test (20%), stratified
  3. Builds features: word TF-IDF + char TF-IDF + hand-made scam signals
  4. Compares 3 models with 5-fold cross-validation on the TRAIN set only
  5. Picks the best model (by PR-AUC), tunes the decision threshold on train CV predictions
  6. Evaluates ONCE on the untouched test set (precision/recall/F1/ROC-AUC/PR-AUC)
  7. Saves plots, top fake-indicating words, and a list of mistakes to ./results/
  8. Saves the model so you can run `predict`

Usage:
  pip install scikit-learn pandas scipy joblib matplotlib
  python fake_ad_dashboard.py train --data fake_job_postings.csv     # train + test + save results
  python fake_ad_dashboard.py dashboard                              # open the web dashboard (no extra libraries)
  python fake_ad_dashboard.py predict "Earn $5000 weekly from home, pay a fee to start!!"
"""
import argparse, html, json, os, re, sys, time, warnings, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.sparse import hstack, csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, classification_report, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score, recall_score,
                             roc_auc_score, ConfusionMatrixDisplay)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.preprocessing import MaxAbsScaler
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")
SEED = 42
MODEL_PATH = "fake_ad_model_full.joblib"
METRICS_PATH = "results/metrics.json"
RESULTS_DIR = "results"
MAX_CHARS = 2000  # truncate very long ads (keeps training fast)

# ----------------------------------------------------------------------------
# Hand-made scam signals
# ----------------------------------------------------------------------------
URGENCY = r"\b(now|hurry|limited|last chance|only today|expires|act fast|today only|don't miss|urgent|immediately)\b"
TOO_GOOD = r"\b(free|100% free|win|winner|won|giveaway|prize|guaranteed|risk[- ]free|earn \$?\d+|make money|get rich|no investment|no experience)\b"
SHORTENERS = r"(bit\.ly|tinyurl|t\.co|goo\.gl|cutt\.ly|rb\.gy|wa\.me)"
PAYMENT = r"\b(easypaisa|jazzcash|western union|gift card|bitcoin|crypto|advance payment|send money|processing fee|registration fee|wire transfer|money order)\b"
DISCOUNT = r"(\b[5-9]\d ?% ?off\b|\bhalf price\b|\bflash sale\b)"
CLAIMS = r"\b(miracle|cure|lose \d+ ?kg|lose weight fast|doctors hate|secret|breakthrough|work from home|weekly pay|per week|per day)\b"
PERSONAL_INFO = r"\b(bank account|ssn|social security|passport|credit card|send your cv to \S+@(gmail|yahoo|hotmail))"


class ScamFeatures(BaseEstimator, TransformerMixin):
    names = ["urgency", "too_good", "shortener", "payment", "discount", "claims", "personal_info",
             "n_urls", "excl", "caps_ratio", "digit_ratio", "emoji_count", "len_log"]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for t in X:
            tl = t.lower()
            letters = [c for c in t if c.isalpha()]
            caps = sum(c.isupper() for c in letters) / max(len(letters), 1)
            digits = sum(c.isdigit() for c in t) / max(len(t), 1)
            emojis = len(re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", t))
            rows.append([
                len(re.findall(URGENCY, tl)), len(re.findall(TOO_GOOD, tl)),
                len(re.findall(SHORTENERS, tl)), len(re.findall(PAYMENT, tl)),
                len(re.findall(DISCOUNT, tl)), len(re.findall(CLAIMS, tl)),
                len(re.findall(PERSONAL_INFO, tl)),
                len(re.findall(r"https?://|www\.", tl)), t.count("!"),
                caps, digits, emojis, np.log1p(len(t)),
            ])
        return csr_matrix(np.array(rows, dtype=float))


class FeatureBuilder:
    """Word TF-IDF + char TF-IDF + scaled scam signals -> one sparse matrix."""

    def __init__(self):
        self.word = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=150_000,
                                    sublinear_tf=True, stop_words="english")
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 4), min_df=5,
                                    max_features=100_000, sublinear_tf=True)
        self.scam = ScamFeatures()
        self.scaler = MaxAbsScaler()

    def fit_transform(self, texts):
        s = self.scaler.fit_transform(self.scam.fit_transform(texts))
        return hstack([self.word.fit_transform(texts), self.char.fit_transform(texts), s]).tocsr()

    def transform(self, texts):
        s = self.scaler.transform(self.scam.transform(texts))
        return hstack([self.word.transform(texts), self.char.transform(texts), s]).tocsr()

    def feature_names(self):
        return (list(self.word.get_feature_names_out()) + ["char:" + c for c in self.char.get_feature_names_out()]
                + ["signal:" + n for n in ScamFeatures.names])


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
TEXT_COLS = ["title", "company_profile", "description", "requirements", "benefits"]


def load_data(path):
    if not os.path.exists(path):
        sys.exit(f"File not found: {path}\nDownload fake_job_postings.csv from Kaggle "
                 "(shivamb/real-or-fake-fake-jobposting-prediction) and put it in this folder.")
    df = pd.read_csv(path)
    if "fraudulent" not in df.columns:
        sys.exit("Column 'fraudulent' not found - is this the right CSV?")
    cols = [c for c in TEXT_COLS if c in df.columns]
    df["text"] = df[cols].fillna("").astype(str).agg(" ".join, axis=1).str.strip().str.slice(0, MAX_CHARS)
    df["label"] = df["fraudulent"].astype(int)
    n0 = len(df)
    df = df[df["text"].str.len() > 20].drop_duplicates(subset="text").reset_index(drop=True)
    print(f"Loaded {n0} rows -> {len(df)} after removing empty/duplicate ads")
    vc = df["label"].value_counts()
    print(f"Genuine: {vc.get(0, 0)} | Fake: {vc.get(1, 0)} ({vc.get(1, 0) / len(df):.1%} fake)\n")
    return df[["text", "label"]]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def best_threshold(y, scores):
    """Threshold that maximises F1 for the fake class."""
    p, r, t = precision_recall_curve(y, scores)
    f1 = 2 * p[:-1] * r[:-1] / np.clip(p[:-1] + r[:-1], 1e-9, None)
    i = int(np.argmax(f1))
    return float(t[i]), float(f1[i])


def make_models():
    return {
        "LogisticRegression": LogisticRegression(max_iter=3000, class_weight="balanced", C=3.0),
        "LinearSVC (calibrated)": CalibratedClassifierCV(LinearSVC(class_weight="balanced", C=0.5), cv=3),
        "ComplementNB": ComplementNB(alpha=0.3),
    }


def report(name, y, scores, thr):
    pred = (scores >= thr).astype(int)
    print(f"\n===== {name} on TEST set (threshold = {thr:.3f}) =====")
    print(classification_report(y, pred, target_names=["genuine", "fake"], digits=3))
    cm = confusion_matrix(y, pred)
    print("Confusion matrix [[TN FP] [FN TP]]:\n", cm)
    print(f"ROC-AUC: {roc_auc_score(y, scores):.4f} | PR-AUC: {average_precision_score(y, scores):.4f}")
    return pred, cm


# ----------------------------------------------------------------------------
# Train / evaluate
# ----------------------------------------------------------------------------
def train(args):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df = load_data(args.data)
    if args.sample and args.sample < len(df):
        df = df.sample(args.sample, random_state=SEED).reset_index(drop=True)
        print(f"(Using a random sample of {len(df)} ads for a quick run)\n")

    Xtr_t, Xte_t, ytr, yte = train_test_split(df["text"].tolist(), df["label"].values,
                                              test_size=0.2, stratify=df["label"], random_state=SEED)
    print(f"Train: {len(Xtr_t)} ads ({ytr.sum()} fake) | Test: {len(Xte_t)} ads ({yte.sum()} fake)")

    t0 = time.time()
    fb = FeatureBuilder()
    Xtr = fb.fit_transform(Xtr_t)
    Xte = fb.transform(Xte_t)
    print(f"Features built: {Xtr.shape[1]} columns ({time.time() - t0:.0f}s)\n")

    # --- 5-fold CV on TRAIN to compare models --------------------------------
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    print("5-fold cross-validation on the training set (fake class):")
    print(f"{'model':26s} {'PR-AUC':>8s} {'best F1':>8s} {'threshold':>10s}")
    cv_scores, summary = {}, {}
    for name, model in make_models().items():
        oof = cross_val_predict(model, Xtr, ytr, cv=cv, method="predict_proba")[:, 1]
        thr, f1 = best_threshold(ytr, oof)
        pr = average_precision_score(ytr, oof)
        cv_scores[name], summary[name] = oof, (pr, f1, thr)
        print(f"{name:26s} {pr:8.4f} {f1:8.4f} {thr:10.3f}")

    best = max(summary, key=lambda k: summary[k][0])
    thr = summary[best][2]
    print(f"\nBest model by PR-AUC: {best}  (decision threshold {thr:.3f} tuned on train CV)")

    # --- final fit and single evaluation on TEST ------------------------------
    model = make_models()[best]
    model.fit(Xtr, ytr)
    scores = model.predict_proba(Xte)[:, 1]
    pred, cm = report(best, yte, scores, thr)

    # also show the default 0.5 threshold for comparison
    p05 = (scores >= 0.5).astype(int)
    print(f"\n(For comparison, threshold 0.5 -> precision {precision_score(yte, p05, zero_division=0):.3f}, "
          f"recall {recall_score(yte, p05):.3f}, F1 {f1_score(yte, p05):.3f})")

    # --- plots -----------------------------------------------------------------
    p, r, _ = precision_recall_curve(yte, scores)
    plt.figure(figsize=(5.5, 4.5))
    plt.plot(r, p, lw=2)
    plt.xlabel("Recall (fake)"); plt.ylabel("Precision (fake)")
    plt.title(f"Precision-Recall curve - {best}\nPR-AUC = {average_precision_score(yte, scores):.3f}")
    plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/pr_curve.png", dpi=150); plt.close()

    ConfusionMatrixDisplay(cm, display_labels=["genuine", "fake"]).plot(cmap="Blues", values_format="d")
    plt.title("Confusion matrix (test set)"); plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/confusion_matrix.png", dpi=150); plt.close()

    # --- what the model learned (from Logistic Regression) -----------------------
    lr = LogisticRegression(max_iter=3000, class_weight="balanced", C=3.0).fit(Xtr, ytr)
    names = np.array(fb.feature_names())
    coef = lr.coef_[0]
    word_mask = np.array([not n.startswith(("char:", "signal:")) for n in names])
    order = np.argsort(coef)
    top_fake = [(names[i], coef[i]) for i in order[::-1] if word_mask[i]][:25]
    top_real = [(names[i], coef[i]) for i in order if word_mask[i]][:15]
    sig = sorted([(n, c) for n, c in zip(names, coef) if n.startswith("signal:")], key=lambda x: -x[1])
    print("\nTop words/phrases pointing to FAKE:", ", ".join(w for w, _ in top_fake))
    print("Top words/phrases pointing to GENUINE:", ", ".join(w for w, _ in top_real))
    print("Scam-signal weights:", ", ".join(f"{n[7:]}={c:+.2f}" for n, c in sig))
    pd.DataFrame(top_fake, columns=["feature", "weight"]).to_csv(f"{RESULTS_DIR}/top_fake_words.csv", index=False)

    # --- error analysis -------------------------------------------------------------
    err = pd.DataFrame({"text": Xte_t, "label": yte, "score": scores, "pred": pred})
    fp = err[(err.label == 0) & (err.pred == 1)].sort_values("score", ascending=False)
    fn = err[(err.label == 1) & (err.pred == 0)].sort_values("score")
    pd.concat([fp.assign(error="false_positive"), fn.assign(error="false_negative")]).to_csv(
        f"{RESULTS_DIR}/errors.csv", index=False)
    print(f"\nMistakes on test set: {len(fp)} genuine ads flagged as fake, {len(fn)} fake ads missed")
    for title, d in (("Fake ads we MISSED", fn), ("Genuine ads wrongly FLAGGED", fp)):
        print(f"\n{title} (first 3):")
        for _, row in d.head(3).iterrows():
            print(f"  [{row.score:.2f}] {row.text[:150].replace(chr(10), ' ')}...")

    # --- metrics for the dashboard ----------------------------------------------------
    tn, fp_n, fn_n, tp = (int(x) for x in cm.ravel())
    metrics = {
        "dataset": {"rows": int(len(df)), "fake": int(df.label.sum()), "genuine": int((df.label == 0).sum()),
                    "train": len(Xtr_t), "test": len(Xte_t), "test_fake": int(yte.sum())},
        "cv": {k: {"pr_auc": float(v[0]), "f1": float(v[1]), "thr": float(v[2])} for k, v in summary.items()},
        "best": best, "threshold": float(thr),
        "test": {"precision": float(precision_score(yte, pred, zero_division=0)),
                 "recall": float(recall_score(yte, pred)), "f1": float(f1_score(yte, pred)),
                 "accuracy": float((pred == yte).mean()), "roc_auc": float(roc_auc_score(yte, scores)),
                 "pr_auc": float(average_precision_score(yte, scores)),
                 "tn": tn, "fp": fp_n, "fn": fn_n, "tp": tp},
        "top_fake": [[w, float(c)] for w, c in top_fake], "top_real": [[w, float(c)] for w, c in top_real],
        "signals": [[n[7:], float(c)] for n, c in sig],
        "fp_examples": [{"score": float(r.score), "text": r.text[:400]} for _, r in fp.head(8).iterrows()],
        "fn_examples": [{"score": float(r.score), "text": r.text[:400]} for _, r in fn.head(8).iterrows()],
        "trained_at": time.strftime("%Y-%m-%d %H:%M"),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # --- save -----------------------------------------------------------------------
    joblib.dump({"features": fb, "model": model, "threshold": thr, "name": best}, MODEL_PATH)
    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved plots and CSVs -> {RESULTS_DIR}/ (pr_curve.png, confusion_matrix.png, top_fake_words.csv, errors.csv, metrics.json)")
    print("\nNow run:  python fake_ad_dashboard.py dashboard")


# ----------------------------------------------------------------------------
# Predict
# ----------------------------------------------------------------------------
def score_text(bundle, text):
    text = text[:MAX_CHARS]
    score = float(bundle["model"].predict_proba(bundle["features"].transform([text]))[0, 1])
    sig = bundle["features"].scam.transform([text]).toarray()[0]
    found = {n: round(float(v), 2) for n, v in zip(ScamFeatures.names, sig) if v and n != "len_log"}
    return {"score": score, "threshold": bundle["threshold"], "fake": score >= bundle["threshold"],
            "model": bundle["name"], "signals": found}


def predict(args):
    if not os.path.exists(MODEL_PATH):
        sys.exit("No trained model found. Run: python fake_ad_dashboard.py train --data fake_job_postings.csv")
    r = score_text(joblib.load(MODEL_PATH), args.text)
    verdict = "LIKELY FAKE" if r["fake"] else "LIKELY GENUINE"
    print(f"Fake score: {r['score']:.1%} (decision threshold {r['threshold']:.1%}, model: {r['model']}) -> {verdict}")
    print("Signals found:", r["signals"] or "none")


# ----------------------------------------------------------------------------
# Dashboard (pure Python standard library - no Streamlit/Flask needed)
# ----------------------------------------------------------------------------
PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Fake Ad Detector Dashboard</title>
<style>
:root{--bg:#f4f6fb;--card:#fff;--ink:#1b2130;--mut:#667089;--line:#e3e7f0;--acc:#4f46e5;--bad:#dc2626;--good:#16a34a;--warn:#d97706;--chip:#eef0fb}
@media(prefers-color-scheme:dark){:root{--bg:#0e1118;--card:#171b26;--ink:#e8ebf3;--mut:#9aa3b8;--line:#293042;--acc:#818cf8;--bad:#f87171;--good:#4ade80;--warn:#fbbf24;--chip:#222840}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif}
header{padding:28px 32px 8px}h1{margin:0;font-size:26px}header p{margin:4px 0 0;color:var(--mut)}
main{padding:16px 32px 48px;max-width:1200px;margin:auto;display:grid;gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.card h2{margin:0 0 12px;font-size:16px}.grid{display:grid;gap:18px}.g2{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.kpi b{display:block;font-size:26px;color:var(--acc)}.kpi span{color:var(--mut);font-size:13px}
textarea{width:100%;min-height:120px;border:1px solid var(--line);border-radius:10px;padding:10px;background:var(--bg);color:var(--ink);font:inherit;resize:vertical}
button{background:var(--acc);color:#fff;border:0;border-radius:9px;padding:9px 16px;font:inherit;cursor:pointer;margin:8px 8px 0 0}
button.alt{background:var(--chip);color:var(--ink)}
.meter{height:14px;border-radius:99px;background:var(--line);overflow:hidden;margin:10px 0 4px}.meter i{display:block;height:100%}
.verdict{font-size:20px;font-weight:700}.fake{color:var(--bad)}.ok{color:var(--good)}
.chip{display:inline-block;background:var(--chip);border-radius:99px;padding:3px 10px;margin:3px 4px 3px 0;font-size:13px}
.chip.r{background:rgba(220,38,38,.12);color:var(--bad)}.chip.g{background:rgba(22,163,74,.12);color:var(--good)}
.bar{display:grid;grid-template-columns:150px 1fr 70px;gap:10px;align-items:center;margin:6px 0;font-size:13px}
.bar div{height:10px;border-radius:99px;background:var(--acc)}.bar.neg div{background:var(--warn)}
.cm{display:grid;grid-template-columns:auto 1fr 1fr;gap:6px;text-align:center;font-size:14px}
.cm .c{padding:18px 6px;border-radius:10px;font-size:22px;font-weight:700}.cm small{display:block;font-weight:400;font-size:12px;color:var(--mut)}
.tp,.tn{background:rgba(22,163,74,.14)}.fp,.fn{background:rgba(220,38,38,.14)}.h{color:var(--mut);font-size:12px;align-self:center}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
img{max-width:100%;border-radius:10px;border:1px solid var(--line);background:#fff}.mut{color:var(--mut);font-size:13px}
</style></head><body>
<header><h1>Fake Ad Detector</h1><p>Trained on Kaggle "Real / Fake Job Posting Prediction" &middot; best model: <b>__BEST__</b> &middot; trained __WHEN__</p></header>
<main>
<div class="kpis">__KPIS__</div>

<section class="card"><h2>Try it live</h2>
<textarea id="ad" placeholder="Paste a full ad here (title, company profile, description, requirements)..."></textarea>
<div><button onclick="check()">Check ad</button>
<button class="alt" onclick="ex(0)">Example: scam</button><button class="alt" onclick="ex(1)">Example: genuine</button></div>
<div id="out" style="margin-top:14px"></div></section>

<div class="grid g2">
<section class="card"><h2>Test-set confusion matrix</h2>__CM__
<p class="mut">Test set: __TEST_N__ ads (__TEST_FAKE__ fake). Decision threshold: __THR__ (tuned on training cross-validation).</p></section>
<section class="card"><h2>Precision-Recall curve</h2><img src="/results/pr_curve.png" alt="PR curve"></section>
</div>

<div class="grid g2">
<section class="card"><h2>Model comparison (5-fold CV, train set)</h2>__CV__
<p class="mut">Higher PR-AUC is better. The best model was then tested once on the untouched test set.</p></section>
<section class="card"><h2>Dataset</h2>__DATA__</section>
</div>

<div class="grid g2">
<section class="card"><h2>Words pointing to FAKE</h2>__TOPFAKE__<h2 style="margin-top:16px">Words pointing to GENUINE</h2>__TOPREAL__</section>
<section class="card"><h2>Scam-signal weights (Logistic Regression)</h2>__SIGNALS__
<p class="mut">Positive = pushes toward fake. Negative = pushes toward genuine.</p></section>
</div>

<div class="grid g2">
<section class="card"><h2>Fake ads the model MISSED</h2>__FN__</section>
<section class="card"><h2>Genuine ads wrongly FLAGGED</h2>__FP__</section>
</div>
</main>
<script>
const EX=["URGENT hiring! Earn $5000 weekly working from home. No experience needed. Pay a small registration fee via Western Union to start. Limited slots, apply now!!!",
"Software Engineer - Lahore. We are an established company building logistics software. Requirements: BSc Computer Science, 2+ years Python experience. Benefits: health insurance, provident fund. Apply through our careers page."];
function ex(i){document.getElementById('ad').value=EX[i];check();}
async function check(){
 const t=document.getElementById('ad').value.trim();if(!t)return;
 const out=document.getElementById('out');out.textContent='Checking...';
 try{const r=await fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
 const d=await r.json();out.textContent='';
 const v=document.createElement('div');v.className='verdict '+(d.fake?'fake':'ok');
 v.textContent=(d.fake?'LIKELY FAKE':'LIKELY GENUINE')+' - fake score '+(d.score*100).toFixed(1)+'%';out.appendChild(v);
 const m=document.createElement('div');m.className='meter';const b=document.createElement('i');
 b.style.width=(d.score*100)+'%';b.style.background=d.fake?'var(--bad)':'var(--good)';m.appendChild(b);out.appendChild(m);
 const n=document.createElement('div');n.className='mut';n.textContent='Decision threshold '+(d.threshold*100).toFixed(1)+'%';out.appendChild(n);
 const k=Object.keys(d.signals);const s=document.createElement('div');s.style.marginTop='8px';
 if(!k.length){s.textContent='No scam signals found.';s.className='mut';}
 k.forEach(x=>{const c=document.createElement('span');c.className='chip r';c.textContent=x+': '+d.signals[x];s.appendChild(c);});
 out.appendChild(s);}catch(e){out.textContent='Error: '+e;}}
</script></body></html>"""


def _e(x):
    return html.escape(str(x))


def _bars(items, neg_ok=False, fmt="{:+.2f}"):
    if not items:
        return "<p class='mut'>n/a</p>"
    mx = max(abs(v) for _, v in items) or 1
    rows = []
    for k, v in items:
        w = 100 * abs(v) / mx
        rows.append(f"<div class='bar {'neg' if v < 0 else ''}'><span>{_e(k)}</span>"
                    f"<div style='width:{w:.0f}%'></div><span>{fmt.format(v)}</span></div>")
    return "".join(rows)


def _examples(rows):
    if not rows:
        return "<p class='mut'>None - the model made no mistakes of this type on the test set.</p>"
    body = "".join(f"<tr><td>{r['score'] * 100:.0f}%</td><td>{_e(r['text'][:260])}...</td></tr>" for r in rows)
    return f"<table><tr><th>Score</th><th>Ad text</th></tr>{body}</table>"


def build_page(m):
    t, d = m["test"], m["dataset"]
    kp = [("Fake precision", t["precision"]), ("Fake recall", t["recall"]), ("Fake F1", t["f1"]),
          ("PR-AUC", t["pr_auc"]), ("ROC-AUC", t["roc_auc"]), ("Accuracy", t["accuracy"])]
    kpis = "".join(f"<div class='kpi'><b>{v:.1%}</b><span>{k}</span></div>" for k, v in kp)
    cm = ("<div class='cm'><span></span><span class='h'>Predicted genuine</span><span class='h'>Predicted fake</span>"
          f"<span class='h'>Actual<br>genuine</span><div class='c tn'>{t['tn']}<small>true negative</small></div>"
          f"<div class='c fp'>{t['fp']}<small>false positive</small></div>"
          f"<span class='h'>Actual<br>fake</span><div class='c fn'>{t['fn']}<small>false negative (missed)</small></div>"
          f"<div class='c tp'>{t['tp']}<small>true positive</small></div></div>")
    cv = _bars([(k, v["pr_auc"]) for k, v in m["cv"].items()], fmt="{:.3f}")
    data = (f"<table><tr><td>Total ads used</td><td>{d['rows']:,}</td></tr>"
            f"<tr><td>Genuine</td><td>{d['genuine']:,}</td></tr>"
            f"<tr><td>Fake</td><td>{d['fake']:,} ({d['fake'] / d['rows']:.1%})</td></tr>"
            f"<tr><td>Train / test split</td><td>{d['train']:,} / {d['test']:,}</td></tr></table>")
    chips = lambda items, cls: "".join(f"<span class='chip {cls}'>{_e(w)}</span>" for w, _ in items)
    page = (PAGE.replace("__BEST__", _e(m["best"])).replace("__WHEN__", _e(m["trained_at"]))
            .replace("__KPIS__", kpis).replace("__CM__", cm)
            .replace("__TEST_N__", str(d["test"])).replace("__TEST_FAKE__", str(d["test_fake"]))
            .replace("__THR__", f"{m['threshold']:.1%}").replace("__CV__", cv).replace("__DATA__", data)
            .replace("__TOPFAKE__", chips(m["top_fake"], "r")).replace("__TOPREAL__", chips(m["top_real"], "g"))
            .replace("__SIGNALS__", _bars(m["signals"])).replace("__FN__", _examples(m["fn_examples"]))
            .replace("__FP__", _examples(m["fp_examples"])))
    return page.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    bundle, page = None, b""

    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, "text/html; charset=utf-8", self.page)
        if self.path.startswith("/results/"):
            path = os.path.join(RESULTS_DIR, os.path.basename(self.path))
            if path.endswith(".png") and os.path.exists(path):
                with open(path, "rb") as f:
                    return self._send(200, "image/png", f.read())
        self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        if self.path != "/predict":
            return self._send(404, "text/plain", b"Not found")
        try:
            n = int(self.headers.get("Content-Length", 0))
            text = str(json.loads(self.rfile.read(n) or b"{}").get("text", ""))
            body = json.dumps(score_text(self.bundle, text)).encode()
            self._send(200, "application/json", body)
        except Exception as e:  # keep the server alive on bad input
            self._send(400, "application/json", json.dumps({"error": str(e)}).encode())


def dashboard(args):
    if not (os.path.exists(MODEL_PATH) and os.path.exists(METRICS_PATH)):
        sys.exit("Nothing to show yet. Run first: python fake_ad_dashboard.py train --data fake_job_postings.csv")
    with open(METRICS_PATH, encoding="utf-8") as f:
        metrics = json.load(f)
    Handler.bundle = joblib.load(MODEL_PATH)
    Handler.page = build_page(metrics)
    url = f"http://127.0.0.1:{args.port}"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Dashboard running at {url}  (press Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Fake ad detector + dashboard (Kaggle EMSCAD dataset)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train")
    t.add_argument("--data", default="fake_job_postings.csv")
    t.add_argument("--sample", type=int, default=0, help="optional: use only N random ads for a quick test")
    t.set_defaults(fn=train)
    p = sub.add_parser("predict")
    p.add_argument("text")
    p.set_defaults(fn=predict)
    d = sub.add_parser("dashboard", help="open the web dashboard")
    d.add_argument("--port", type=int, default=8000)
    d.add_argument("--no-browser", action="store_true")
    d.set_defaults(fn=dashboard)
    a = ap.parse_args()
    a.fn(a)

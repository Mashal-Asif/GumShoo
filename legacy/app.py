"""
Social Media Safety Detector
-----------------------------
Flow:  Welcome page  ->  Input page (link / file)  ->  Result page

Tools:
  - Deepfake Analyzer     : image is REAL or FAKE
  - Sentiment Analysis    : sentiment breakdown of the text fed in
  - Fraud Detection       : scam / fraudulent ads and messages (text)
  - Propaganda Detection  : propaganda / manipulative text

Status: Sentiment uses the team's real model (tweeteval_sentiment.py: VADER or
RoBERTa). Deepfake uses the trained detector in deepfake_model/. Fraud uses trained models (transactions, and text trained on the SMS Spam Collection). Propaganda is still a placeholder. To plug in
a trained model, edit ONLY its predict_* function in the MODELS section, keep its
input/output format, and remove the tool from PLACEHOLDER_TOOLS.

Run:  streamlit run app.py
"""

import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile

import joblib
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Social Media Safety Detector", layout="centered")

MAX_TEXTS = 500    # cap on how many posts are analysed at once

DEEPFAKE = "Deepfake Analyzer"
SENTIMENT = "Sentiment Analysis"
FRAUD = "Fraud Detection"
PROPAGANDA = "Propaganda Detection"

TOOLS = {
    DEEPFAKE: ("01", "Check whether an image is real or fake (AI-generated or manipulated)."),
    SENTIMENT: ("02", "Analyse the sentiment of posts, tweets or documents."),
    FRAUD: ("03", "Detect scam or fraudulent ads, job offers and messages."),
    PROPAGANDA: ("04", "Detect propaganda and manipulative persuasion in text."),
}

# Tools still using placeholder models (remove a tool from here once its real model is in)
PLACEHOLDER_TOOLS = {PROPAGANDA}


# =============================================================================
# MODELS  (placeholders - replace the bodies with the real trained models)
# =============================================================================

def _fake_score(data: bytes) -> float:
    """Repeatable fake number between 0 and 1. Placeholder only."""
    return int(hashlib.md5(data).hexdigest(), 16) % 100 / 100


# ---- Deepfake: the team's trained detector (deepfake_model/detector.py) ----------
# Ensemble of two Xception models (v2 + v3). Needs: torch, timm (already installed).

@st.cache_resource(show_spinner="Loading deepfake models...")
def load_deepfake_detector():
    """Returns (detector, error_text). Loaded once, then reused."""
    try:
        from deepfake_model.detector import DeepfakeDetector
        return DeepfakeDetector(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def predict_deepfake(image: Image.Image) -> dict:
    """
    INPUT : one PIL image
    OUTPUT: {"label": "Real"/"Fake"/"Uncertain", "score": P(fake), "details": {...}}
    """
    det, error = load_deepfake_detector()
    st.session_state["deepfake_note"] = error
    if det is None:  # model could not load: placeholder so the app still runs
        score = _fake_score(image.resize((32, 32)).tobytes())
        return {"label": "Fake" if score >= 0.5 else "Real", "score": score}
    r = det.predict(image)
    return {"label": r["verdict"].capitalize(), "score": r["p_fake"], "details": r}


# ---- Sentiment: the team's real model (tweeteval_sentiment.py) -------------------
# Needs:  python -m pip install vaderSentiment        (VADER, fast)
#         python -m pip install transformers torch    (RoBERTa, ~500 MB first download)
# Put tweeteval_sentiment.py in the same folder as app.py. If it can't be imported
# (e.g. the `datasets` library is missing), the same two loaders below are used.

SENTIMENT_MODELS = {
    "VADER (fast, rule-based)": "vader",
    "RoBERTa (more accurate, ~500 MB download the first time)": "roberta",
}
ID2LABEL = {0: "negative", 1: "neutral", 2: "positive"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}


def _local_vader():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()

    def predict(texts):
        out = []
        for t in texts:
            c = sia.polarity_scores(t)["compound"]
            out.append(2 if c >= 0.05 else 0 if c <= -0.05 else 1)
        return out
    return predict


def _local_roberta():
    from transformers import pipeline
    clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                   truncation=True, max_length=128)

    def predict(texts):
        return [LABEL2ID[o["label"].lower()] for o in clf(texts, batch_size=32)]
    return predict


@st.cache_resource(show_spinner="Loading sentiment model...")
def load_sentiment_model(name: str):
    """Returns (predict_fn, error_text). predict_fn: list[str] -> list[int] (0 neg, 1 neu, 2 pos)."""
    try:
        try:
            from tweeteval_sentiment import get_model   # the team's module
            return get_model(name), None
        except ImportError:
            return (_local_roberta() if name == "roberta" else _local_vader()), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def predict_sentiment(texts: list, model_name: str = "vader") -> list:
    """INPUT: list of texts.  OUTPUT: list of "Positive"/"Neutral"/"Negative" (same order)."""
    predict, error = load_sentiment_model(model_name)
    st.session_state["sentiment_note"] = error
    if predict is None:  # model could not load: placeholder labels so the app still runs
        scores = [_fake_score(t.encode()) for t in texts]
        return ["Negative" if x < 0.33 else "Neutral" if x < 0.66 else "Positive" for x in scores]
    return [ID2LABEL[i].capitalize() for i in predict(texts)]

# Simple rule-based scam signals. These are REAL checks (not a trained model) and
# are shown in the Fraud results next to the model's verdict.
FLAG_PATTERNS = {
    "Asks for an upfront fee": r"(registration|security|processing|training|joining)\s+fee|pay (a )?(small )?(fee|deposit)|send (money|payment)",
    "Contact via WhatsApp/Telegram": r"whatsapp|telegram|\bdm (us|me)\b|inbox (us|me)",
    "Urgency / pressure": r"limited (seats|slots|spots)|apply (now|today|immediately)|hurry|last chance|act (now|fast)|urgent",
    "Unrealistic earnings": r"earn (up to )?\$?\s?\d|\$\s?\d+\s*(per|/)\s*(day|hour|week)|guaranteed (income|earnings|profit)|get rich|double your",
    "No experience needed": r"no (experience|skills?|qualifications?) (needed|required)|easy money",
    "Asks for personal/bank details": r"\b(cnic|bank account|credit card|otp|password|account number|ssn)\b",
    "Shortened / chat link": r"bit\.ly|tinyurl|t\.me/|wa\.me/",
    "Prize / lottery claim": r"you('ve| have) (won|been selected)|congratulations|lottery|\bprize\b",
}


def find_red_flags(text: str) -> list:
    return [name for name, pattern in FLAG_PATTERNS.items() if re.search(pattern, text, re.I)]


@st.cache_resource
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

@st.cache_resource
def _load_tx_model():
    return joblib.load(Path(__file__).parent / "fraud_detection" / "fraud_detection_model.pkl")


def predict_transaction(tx_type, amount, old_org, new_org, old_dest, new_dest) -> dict:
    row = pd.DataFrame([{
        "type": tx_type, "amount": amount,
        "oldbalanceOrg": old_org, "newbalanceOrig": new_org,
        "oldbalanceDest": old_dest, "newbalanceDest": new_dest,
        "balanceDiffOriginal": old_org - new_org,
        "balanceDiffDestination": new_dest - old_dest,
    }])
    p = float(_load_tx_model().predict_proba(row)[0, 1])
    return {"label": "Fraud" if p >= 0.5 else "Legit", "score": p}


def predict_propaganda(text: str) -> dict:
    """
    INPUT : one text
    OUTPUT: {"label": "Propaganda"/"Not propaganda", "score": P(propaganda),
             "techniques": ["Loaded language", ...]}   <- "techniques" is optional
    TODO  : load the trained propaganda model.
    """
    score = _fake_score(text.encode())
    return {"label": "Propaganda" if score >= 0.5 else "Not propaganda", "score": score, "techniques": []}


# =============================================================================
# READING THE USER'S INPUT (link, image, docx, txt, csv)
# Every reader returns (list_of_images, list_of_texts)
# =============================================================================

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_texts(data: bytes) -> list:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paras = ["".join(t.text or "" for t in p.iter(W + "t")) for p in root.iter(W + "p")]
    return [p.strip() for p in paras if p.strip()]


def docx_images(data: bytes) -> list:
    images = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                try:
                    images.append(Image.open(io.BytesIO(z.read(name))).convert("RGB"))
                except Exception:
                    pass  # skip formats we can't open
    return images


def from_link(url: str):
    r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    if r.headers.get("content-type", "").startswith("image"):
        return [Image.open(io.BytesIO(r.content)).convert("RGB")], []
    html = re.sub(r"(?s)<(script|style).*?</\1>", " ", r.text)
    text = re.sub(r"<[^>]+>", "\n", html)
    return [], [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20]


def from_file(f):
    name, data = f.name.lower(), f.getvalue()
    if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return [Image.open(io.BytesIO(data)).convert("RGB")], []
    if name.endswith(".docx"):
        return docx_images(data), docx_texts(data)
    if name.endswith(".txt"):
        lines = data.decode("utf-8", errors="ignore").splitlines()
        return [], [ln.strip() for ln in lines if ln.strip()]
    if name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(data))
        preferred = ("text", "tweet", "content", "post", "message", "description")
        col = next((c for c in df.columns if str(c).lower() in preferred), None)
        if col is None:
            col = next((c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])), df.columns[0])
        return [], df[col].dropna().astype(str).tolist()
    raise ValueError("Unsupported file type.")


def analyse_texts(module: str, texts: list, model_name: str = "vader") -> pd.DataFrame:
    if module == SENTIMENT:
        return pd.DataFrame({"text": texts, "sentiment": predict_sentiment(texts, model_name)})
    rows = []
    for t in texts:
        if module == FRAUD:
            r = predict_fraud(t)
            rows.append({"text": t, "verdict": r["label"], "risk": r["score"], "red_flags": ", ".join(find_red_flags(t))})
        else:
            r = predict_propaganda(t)
            rows.append({"text": t, "verdict": r["label"], "risk": r["score"], "techniques": ", ".join(r.get("techniques", []))})
    return pd.DataFrame(rows)


# =============================================================================
# NAVIGATION
# =============================================================================

st.session_state.setdefault("page", "home")
st.session_state.setdefault("module", None)
st.session_state.setdefault("result", None)


def go(page: str, **state):
    st.session_state.page = page
    st.session_state.update(state)
    st.rerun()


# =============================================================================
# PAGE 1: WELCOME
# =============================================================================

def home_page():
    st.title("Analysis Tools")
    st.write("Select a tool to begin an analysis.")

    items = list(TOOLS.items())
    for row in (items[:2], items[2:]):
        for col, (name, (icon, desc)) in zip(st.columns(2), row):
            with col.container(border=True):
                st.markdown(f'<div class="eyebrow">Module {icon}</div>', unsafe_allow_html=True)
                st.subheader(name)
                st.write(desc)
                if st.button("Open", key=f"open_{name}"):
                    go("input", module=name, result=None)


# =============================================================================
# PAGE 2: INPUT (same layout for every tool)
# =============================================================================

TX_TYPES = ["PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"]


def transaction_form():
    st.caption("Enter a bank transaction and the trained model will estimate whether it is fraud.")
    tx_type = st.selectbox("Transaction type", TX_TYPES)
    amount = st.number_input("Amount", min_value=0.0, value=1000.0, step=100.0)
    c1, c2 = st.columns(2)
    old_org = c1.number_input("Sender balance before", min_value=0.0, value=5000.0, step=100.0)
    new_org = c1.number_input("Sender balance after", min_value=0.0, value=4000.0, step=100.0)
    old_dest = c2.number_input("Receiver balance before", min_value=0.0, value=2000.0, step=100.0)
    new_dest = c2.number_input("Receiver balance after", min_value=0.0, value=3000.0, step=100.0)
    if st.button("Check transaction", type="primary"):
        try:
            res = predict_transaction(tx_type, amount, old_org, new_org, old_dest, new_dest)
        except Exception as e:
            st.error(f"Could not run the fraud model: {e}")
            return
        details = {"Type": tx_type, "Amount": amount,
                   "Sender before": old_org, "Sender after": new_org,
                   "Receiver before": old_dest, "Receiver after": new_dest}
        go("result", result={"kind": "transaction", **res, "details": details})

def input_page():
    module = st.session_state.module
    is_text = module != DEEPFAKE
    if st.button("Back"):
        go("home")

    st.title(module)
    st.write("Give us the content you want to analyse.")
    if module == FRAUD:
        fraud_kind = st.radio("What do you want to check?", ["A message or ad", "A bank transaction"], horizontal=True)
        if fraud_kind == "A bank transaction":
            transaction_form()
            return

    link = st.text_input("Paste a link", placeholder="https://...")
    st.caption("or")
    file = st.file_uploader("Upload a file (image, docx, txt or csv)", type=["png", "jpg", "jpeg", "webp", "docx", "txt", "csv"])

    mode = None
    if is_text:
        mode = st.radio(
            "Treat the text as",
            ["Separate posts (one per line / paragraph)", "One whole document"],
            index=0 if module == SENTIMENT else 1,
            help="A csv file is always analysed row by row.",
        )

    model_name = "vader"
    if module == SENTIMENT:
        model_name = SENTIMENT_MODELS[st.selectbox("Model", list(SENTIMENT_MODELS))]

    if st.button("Analyse", type="primary"):
        if not link.strip() and file is None:
            st.warning("Please paste a link or upload a file first.")
            return
        try:
            with st.spinner("Analysing..."):
                images, texts = from_file(file) if file is not None else from_link(link.strip())
                if module == DEEPFAKE:
                    if not images:
                        st.error("No image was found in that input. Use an image, a docx containing images, or a direct image link.")
                        return
                    data = [(img, predict_deepfake(img)) for img in images]
                else:
                    is_csv = file is not None and file.name.lower().endswith(".csv")
                    if texts and mode.startswith("One") and not is_csv:
                        texts = ["\n".join(texts)]
                    if not texts:
                        st.error("No text was found in that input. Try a txt, csv, docx file or a link to a page with text.")
                        return
                    data = analyse_texts(module, texts[:MAX_TEXTS], model_name)
        except Exception as e:
            st.error(f"Could not read that input: {e}")
            return
        go("result", result=data)

def transaction_result(d):
    if d["label"] == "Fraud":
        st.error("## Likely fraud")
    else:
        st.success("## Looks legitimate")
    st.progress(float(d["score"]), text=f"Fraud probability: {d['score']:.0%}")
    st.write("**Transaction checked**")
    st.table(pd.DataFrame([d["details"]]))
    st.caption("This is an automated estimate from a trained model, not a final verdict.")


# =============================================================================
# PAGE 3: RESULTS
# =============================================================================

def deepfake_result(data):
    for i, (img, res) in enumerate(data, start=1):
        with st.container(border=True):
            if len(data) > 1:
                st.caption(f"Image {i} of {len(data)}")
            left, right = st.columns([1, 1])
            left.image(img, width=260)
            with right:
                if res["label"] == "Fake":
                    st.error("## Likely FAKE")
                elif res["label"] == "Uncertain":
                    st.warning("## UNCERTAIN")
                    st.caption("The models are not confident, or they disagree. Treat this image with caution.")
                else:
                    st.success("## Appears REAL")
                st.progress(res["score"], text=f"Fake probability: {res['score']:.0%}")
            d = res.get("details")
            if d:
                with st.expander("Details"):
                    st.write(f"Crops analysed: {d['crops']}  |  Spread between crops: {d['spread']}  |  "
                             f"Disagreement between models: {d['model_gap']}")
                    st.table(pd.DataFrame(d["per_model"]).T)
    st.caption("This is an automated estimate, not a final verdict.")


def sentiment_result(df: pd.DataFrame):
    total = len(df)
    counts = df["sentiment"].value_counts()
    values = df["sentiment"].map({"Negative": -1, "Neutral": 0, "Positive": 1})
    overall = counts.idxmax()
    icon = {"Positive": "", "Neutral": "", "Negative": ""}.get(overall, "")

    if total == 1:
        show = {"Positive": st.success, "Neutral": st.info, "Negative": st.error}[overall]
        show(f"## {icon} {overall}")
        return

    st.subheader(f"Overall sentiment: {icon} {overall}")
    cols = st.columns(4)
    cols[0].metric("Posts analysed", total)
    for col, label in zip(cols[1:], ["Positive", "Neutral", "Negative"]):
        n = int(counts.get(label, 0))
        col.metric(label, f"{n / total:.0%}", f"{n} posts", delta_color="off")
    st.write(f"Net sentiment score: **{values.mean():+.2f}** (-1 = all negative, +1 = all positive)")

    st.write("**Sentiment breakdown**")
    st.bar_chart(counts)

    if total >= 5:
        st.write("**Sentiment trend** (rolling average over the posts, in order)")
        st.line_chart(values.rolling(min(20, total), min_periods=1).mean().rename("rolling sentiment"))

    negative = df[df["sentiment"] == "Negative"].head(3)
    if not negative.empty:
        st.write("**Examples of negative posts**")
        for t in negative["text"]:
            st.write(f"- {t[:200]}")

    st.write("**All results**")
    st.dataframe(df)
    st.download_button("Download results (CSV)", df.to_csv(index=False), "sentiment_results.csv", "text/csv")


def risk_result(df: pd.DataFrame, flagged: str, extra_col: str, extra_title: str, filename: str):
    """Shared results page for Fraud and Propaganda detection."""
    total = len(df)
    n_flag = int((df["verdict"] == flagged).sum())

    if total == 1:
        row = df.iloc[0]
        if row["verdict"] == flagged:
            st.error(f"## {row['verdict']}")
        else:
            st.success(f"## {row['verdict']}")
        st.progress(float(row["risk"]), text=f"Risk score: {row['risk']:.0%}")
    else:
        cols = st.columns(3)
        cols[0].metric("Items analysed", total)
        cols[1].metric(f"Flagged as {flagged.lower()}", f"{n_flag / total:.0%}", f"{n_flag} items", delta_color="off")
        cols[2].metric("Average risk score", f"{df['risk'].mean():.0%}")
        st.write("**Verdict breakdown**")
        st.bar_chart(df["verdict"].value_counts())

    found = df[extra_col].str.split(", ").explode()
    found = found[found.fillna("") != ""]
    if not found.empty:
        st.write(f"**{extra_title}**")
        st.bar_chart(found.value_counts())

    if total > 1:
        top = df[df["verdict"] == flagged].sort_values("risk", ascending=False).head(3)
        if not top.empty:
            st.write("**Highest-risk items**")
            for t in top["text"]:
                st.write(f"- {t[:200]}")
        st.write("**All results**")
        st.dataframe(df)
        st.download_button("Download results (CSV)", df.to_csv(index=False), filename, "text/csv")
    st.caption("This is an automated estimate, not a final verdict.")


def result_page():
    module, data = st.session_state.module, st.session_state.result
    if data is None:
        go("home")
    st.title(f"{module}: Results")
    is_tx = isinstance(data, dict) and data.get("kind") == "transaction"
    if module in PLACEHOLDER_TOOLS and not is_tx:
        st.info("Demo mode: this tool uses a placeholder model until the trained one is plugged in.")
    note = st.session_state.get("sentiment_note")
    if module == SENTIMENT and note:
        st.warning(f"The sentiment model could not be loaded, so placeholder results are shown. Reason: {note}")
    dnote = st.session_state.get("deepfake_note")
    if module == DEEPFAKE and dnote:
        st.warning(f"The deepfake model could not be loaded, so placeholder results are shown. Reason: {dnote}")

    if module == DEEPFAKE:
        deepfake_result(data)
    elif module == SENTIMENT:
        sentiment_result(data)
    elif module == FRAUD:
        if is_tx:
            transaction_result(data)
        else:
            risk_result(data, "Fraud", "red_flags", "Red flags found (rule-based)", "fraud_results.csv")
    else:
        risk_result(data, "Propaganda", "techniques", "Techniques detected", "propaganda_results.csv")

    st.divider()
    left, right = st.columns(2)
    if left.button("Analyse something else"):
        go("input", result=None)
    if right.button("Back to home"):
        go("home", result=None)

# =============================================================================
# ROUTER
# =============================================================================

def load_css():
    """Injects style.css (the app's stylesheet) into the page."""
    css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css()
st.markdown('<div class="topbar"><b>Social Media Safety Detector</b><span>Digital Threat Analysis</span></div>',
            unsafe_allow_html=True)

{"home": home_page, "input": input_page, "result": result_page}[st.session_state.page]()

"""
patch_deepfake.py
Plugs the trained deepfake detector (deepfake_model/detector.py) into app.py.
Your other edits in app.py (bank-transaction form, sentiment model, ...) are kept.

Run from the folder that contains app.py:   python patch_deepfake.py
A backup is saved as app_before_deepfake.py.
"""

import shutil
import sys

PATH = "app.py"

with open(PATH, encoding="utf-8") as f:
    s = f.read()

if "load_deepfake_detector" in s:
    sys.exit("app.py already has the deepfake detector. Nothing to do.")


def replace_once(text, old, new, what):
    if text.count(old) != 1:
        sys.exit(f"Could not patch ({what}): the expected code was not found exactly once.\n"
                 "app.py was NOT changed. Send me this message.")
    return text.replace(old, new)


# 1. docstring
s = replace_once(
    s,
    "Deepfake, Fraud and Propaganda still use placeholder models.",
    "Deepfake uses the trained detector in deepfake_model/. Fraud (text) and Propaganda still use placeholder models.",
    "docstring",
)

# 2. deepfake is no longer a placeholder tool
s = replace_once(s, "PLACEHOLDER_TOOLS = {DEEPFAKE, FRAUD, PROPAGANDA}", "PLACEHOLDER_TOOLS = {FRAUD, PROPAGANDA}", "placeholder set")

# 3. the model function
s = replace_once(
    s,
    '''def predict_deepfake(image: Image.Image) -> dict:
    """INPUT: one PIL image.  OUTPUT: {"label": "Real"/"Fake", "score": P(fake)}"""
    score = _fake_score(image.resize((32, 32)).tobytes())
    return {"label": "Fake" if score >= 0.5 else "Real", "score": score}
''',
    '''# ---- Deepfake: the team's trained detector (deepfake_model/detector.py) ----------
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
''',
    "predict_deepfake",
)

# 4. the results page (adds the Uncertain state and a details box)
start = s.index("def deepfake_result(data):")
end = s.index("def sentiment_result(")
s = s[:start] + '''def deepfake_result(data):
    for i, (img, res) in enumerate(data, start=1):
        with st.container(border=True):
            if len(data) > 1:
                st.caption(f"Image {i} of {len(data)}")
            left, right = st.columns([1, 1])
            left.image(img, width=260)
            with right:
                if res["label"] == "Fake":
                    st.error("## ⚠️ Likely FAKE")
                elif res["label"] == "Uncertain":
                    st.warning("## ❓ UNCERTAIN")
                    st.caption("The models are not confident, or they disagree. Treat this image with caution.")
                else:
                    st.success("## ✅ Appears REAL")
                st.progress(res["score"], text=f"Fake probability: {res['score']:.0%}")
            d = res.get("details")
            if d:
                with st.expander("Details"):
                    st.write(f"Crops analysed: {d['crops']}  |  Spread between crops: {d['spread']}  |  "
                             f"Disagreement between models: {d['model_gap']}")
                    st.table(pd.DataFrame(d["per_model"]).T)
    st.caption("This is an automated estimate, not a final verdict.")


''' + s[end:]

# 5. warning if the deepfake model could not load
s = replace_once(
    s,
    '''    if module == SENTIMENT and note:
        st.warning(f"The sentiment model could not be loaded, so placeholder results are shown. Reason: {note}")
''',
    '''    if module == SENTIMENT and note:
        st.warning(f"The sentiment model could not be loaded, so placeholder results are shown. Reason: {note}")
    dnote = st.session_state.get("deepfake_note")
    if module == DEEPFAKE and dnote:
        st.warning(f"The deepfake model could not be loaded, so placeholder results are shown. Reason: {dnote}")
''',
    "result page note",
)

shutil.copyfile(PATH, "app_before_deepfake.py")
with open(PATH, "w", encoding="utf-8") as f:
    f.write(s)
print("Patched OK. Backup saved as app_before_deepfake.py. Now run: streamlit run app.py")

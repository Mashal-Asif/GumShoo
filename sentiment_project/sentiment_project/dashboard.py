"""
Live Brand Sentiment Monitor (Streamlit)
Run:  streamlit run dashboard.py
Needs tweeteval_sentiment.py in the same folder.
"""
import time

import pandas as pd
import streamlit as st

from tweeteval_sentiment import ID2LABEL, get_model, load_tweeteval

st.set_page_config(page_title="Brand Sentiment Monitor", page_icon="📊", layout="wide")

EMOJI = {0: "🔴", 1: "🟡", 2: "🟢"}


# ---------- cached loaders (run once, reused on every rerun) ----------

@st.cache_resource(show_spinner="Loading model...")
def cached_model(name):
    return get_model(name)


@st.cache_data(show_spinner="Loading TweetEval...")
def cached_tweets(n):
    ds = load_tweeteval("test").shuffle(seed=42).select(range(n))
    return list(ds["text"]), list(ds["label"])


# ---------- session state (survives reruns) ----------

s = st.session_state
s.setdefault("running", False)
s.setdefault("idx", 0)
s.setdefault("feed", [])    # list of (label_id, text, was_correct)
s.setdefault("labels", [])  # predicted label ids, in order


def reset():
    s.running, s.idx, s.feed, s.labels = False, 0, [], []


# ---------- sidebar controls ----------

st.sidebar.header("Settings")
model_name = st.sidebar.selectbox("Model", ["roberta", "vader"])
delay = st.sidebar.slider("Seconds between tweets", 0.1, 2.0, 0.5, 0.1)
window = st.sidebar.slider("Rolling window (tweets)", 5, 50, 20)
threshold = st.sidebar.slider("Alert when trend drops below", -1.0, 0.0, -0.3, 0.05)
n_tweets = st.sidebar.slider("Tweets to load", 50, 1000, 300, 50)

c1, c2, c3 = st.sidebar.columns(3)
if c1.button("Start"):
    s.running = True
if c2.button("Stop"):
    s.running = False
if c3.button("Reset"):
    reset()

predict = cached_model(model_name)
texts, truth = cached_tweets(n_tweets)

# ---------- page layout ----------

st.title("📊 Live Brand Sentiment Monitor")
st.caption("Replays TweetEval tweets as a live stream and flags sudden drops in sentiment.")

st.subheader("Try your own text")
user_text = st.text_input("Type a tweet or review:", placeholder="The new update is amazing!")
if user_text:
    label_id = predict([user_text])[0]
    st.write(f"{EMOJI[label_id]} **{ID2LABEL[label_id].upper()}**")

st.divider()

alert_box = st.empty()
m_pos, m_neu, m_neg, m_trend = [col.empty() for col in st.columns(4)]
chart_box = st.empty()
st.subheader("Live feed")
feed_box = st.empty()


def render():
    labels = s.labels
    recent = labels[-window:]
    trend = sum(l - 1 for l in recent) / len(recent) if recent else 0.0

    m_pos.metric("🟢 Positive", labels.count(2))
    m_neu.metric("🟡 Neutral", labels.count(1))
    m_neg.metric("🔴 Negative", labels.count(0))
    m_trend.metric("Trend (-1 to +1)", f"{trend:+.2f}")

    if len(labels) >= 5 and trend <= threshold:
        alert_box.error(f"⚠️ ALERT: negative sentiment spike (trend {trend:+.2f})")
    else:
        alert_box.empty()

    if labels:
        series = [
            sum(l - 1 for l in labels[max(0, i - window + 1): i + 1]) / len(labels[max(0, i - window + 1): i + 1])
            for i in range(len(labels))
        ]
        chart_box.line_chart(pd.DataFrame({"rolling sentiment": series}))

    lines = [
        f"{EMOJI[lab]} **{ID2LABEL[lab]}** {'✅' if ok else '❌'} — {txt[:140]}"
        for lab, txt, ok in reversed(s.feed[-10:])
    ]
    feed_box.markdown("\n\n".join(lines) if lines else "_Press Start in the sidebar._")


render()

# ---------- the live loop ----------

if s.running:
    while s.idx < len(texts):
        pred = predict([texts[s.idx]])[0]
        s.labels.append(pred)
        s.feed.append((pred, texts[s.idx], pred == truth[s.idx]))
        s.idx += 1
        render()
        time.sleep(delay)
    s.running = False
    st.success("Stream finished. Press Reset to run again.")
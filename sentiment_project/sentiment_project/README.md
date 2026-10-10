# Real-Time Sentiment Analysis on TweetEval

A small project that classifies tweets as **negative**, **neutral**, or **positive** in real time, evaluates the models on the TweetEval benchmark, and shows the results in a live Streamlit dashboard.

---

## 1. Project structure

```
sentiment_project/
├── realtime_sentiment.py     # Simple live demo (simulated or typed messages)
├── tweeteval_sentiment.py    # Core code: dataset, models, evaluation, stream replay
├── dashboard.py              # Streamlit live dashboard (imports tweeteval_sentiment.py)
└── README.md                 # This file
```

| File | Purpose | Depends on |
|---|---|---|
| `realtime_sentiment.py` | Minimal real-time scoring in the terminal with a rolling average | VADER / transformers |
| `tweeteval_sentiment.py` | Loads TweetEval, runs models, evaluates accuracy and F1, replays tweets as a stream | `datasets`, `transformers`, `scikit-learn`, `vaderSentiment` |
| `dashboard.py` | Web dashboard with live feed, trend chart, counters, and spike alert | `tweeteval_sentiment.py`, `streamlit`, `pandas` |

`dashboard.py` must be in the same folder as `tweeteval_sentiment.py` because it imports from it.

---

## 2. How it works

```
 TweetEval dataset                   Model
 (tweets + true labels)       (RoBERTa or VADER)
        |                            |
        v                            v
 +-------------+   tweet text   +-----------+
 |  Load data  | -------------> |  Predict  |
 +-------------+                +-----------+
                                      |
              +-----------------------+-----------------------+
              |                       |                       |
              v                       v                       v
        evaluate mode            stream mode            dashboard.py
      accuracy, F1,           one tweet at a time,      live feed, chart,
      confusion matrix        rolling trend             counters, alert
```

### Labels

TweetEval's sentiment task uses three classes:

| ID | Label |
|---|---|
| 0 | negative |
| 1 | neutral |
| 2 | positive |

### Models

| Model | Type | Speed | Accuracy | Download |
|---|---|---|---|---|
| **VADER** | Rule-based lexicon | Very fast | Lower, weak on neutral and sarcasm | None (installed with pip) |
| **RoBERTa** (`cardiffnlp/twitter-roberta-base-sentiment-latest`) | Transformer trained on tweets | Slower | Higher | About 500 MB on first use, then cached |

VADER outputs a compound score from -1 to +1. The code maps it to a class: `>= 0.05` is positive, `<= -0.05` is negative, anything between is neutral.

### Rolling trend

Each prediction is converted to a value (negative = -1, neutral = 0, positive = +1). The **trend** is the average of the last N values (the rolling window). This smooths out single noisy tweets and gives a stable line that moves over time.

### Dataset loading

The dataset is fetched automatically from Hugging Face:

```python
load_dataset("cardiffnlp/tweet_eval", "sentiment", split="test")
```

You never download it manually. The first run needs internet access; afterwards it is read from the local cache (`~/.cache/huggingface/`, or `C:\Users\<you>\.cache\huggingface\` on Windows).

| Split | Size |
|---|---|
| train | 45,615 |
| validation | 2,000 |
| test | 12,284 |

---

## 3. Installation

Requires Python 3.9 or newer. Python 3.11 or 3.12 is the safest choice for compatibility with `torch`.

```bash
python -m pip install datasets transformers torch scikit-learn vaderSentiment streamlit pandas
```

If you only want to try VADER first, a lighter install works:

```bash
python -m pip install datasets scikit-learn vaderSentiment streamlit pandas
```

Optional: use a virtual environment.

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux
```

---

## 4. Usage

### 4.1 `realtime_sentiment.py` (simple demo)

```bash
python realtime_sentiment.py                 # simulated stream, VADER
python realtime_sentiment.py --stdin         # type your own messages
python realtime_sentiment.py --model bert    # transformer model
```

| Option | Default | Description |
|---|---|---|
| `--model` | `vader` | `vader` or `bert` |
| `--stdin` | off | Read messages from the keyboard instead of the simulated stream |
| `--window` | 10 | Rolling average size |

Press `Ctrl+C` to stop and print a summary of counts.

### 4.2 `tweeteval_sentiment.py` (evaluation and stream replay)

```bash
python tweeteval_sentiment.py evaluate --limit 500
python tweeteval_sentiment.py evaluate --model vader --limit 500
python tweeteval_sentiment.py stream --limit 50 --delay 0.3
```

| Option | Default | Description |
|---|---|---|
| `mode` | required | `evaluate` or `stream` |
| `--model` | `roberta` | `roberta` or `vader` |
| `--split` | `test` | `train`, `validation`, or `test` |
| `--limit` | 0 (all) | Use only the first N tweets |
| `--delay` | 0.5 | Seconds between tweets (stream mode) |
| `--window` | 20 | Rolling window size (stream mode) |

**Evaluate mode** prints accuracy, macro F1, a per-class report, and a confusion matrix (rows are true labels, columns are predictions).

**Stream mode** prints one line per tweet:

```
positive [ok ] trend=+0.40 acc=71.00% | I love this new phone!
```

| Part | Meaning |
|---|---|
| `positive` | Predicted label |
| `[ok ]` / `[MISS]` | Whether the prediction matched the true label |
| `trend` | Rolling average of the last N predictions (-1 to +1) |
| `acc` | Running accuracy so far |

### 4.3 `dashboard.py` (Streamlit dashboard)

```bash
python -m streamlit run dashboard.py
```

The app opens at `http://localhost:8501`.

**Sidebar settings**

| Setting | Description |
|---|---|
| Model | `roberta` or `vader` |
| Seconds between tweets | Stream speed |
| Rolling window | Number of tweets in the trend average |
| Alert threshold | Show a red alert when the trend drops to or below this value |
| Tweets to load | Size of the replayed sample |
| Start / Stop / Reset | Control the stream |

**Main page**

- **Try your own text:** type any sentence to see its predicted sentiment instantly.
- **Counters:** totals of positive, neutral, and negative tweets plus the current trend.
- **Line chart:** rolling sentiment over time.
- **Live feed:** the last 10 tweets with their predicted label and whether it was correct.
- **Alert banner:** appears when negative sentiment spikes below the threshold.

---

## 5. Code reference

### `tweeteval_sentiment.py`

| Function | Description |
|---|---|
| `load_tweeteval(split)` | Returns the TweetEval sentiment split as a Hugging Face dataset |
| `load_roberta()` | Returns a `predict(list[str]) -> list[int]` function using RoBERTa |
| `load_vader()` | Returns a `predict(list[str]) -> list[int]` function using VADER |
| `get_model(name)` | Picks the model by name (`roberta` or `vader`) |
| `evaluate(args)` | Runs the model on a split and prints metrics |
| `stream(args)` | Replays tweets one at a time with a live trend and accuracy |
| `main()` | Parses command-line arguments and runs the chosen mode |

Both model loaders return a function with the same shape, so any model can be swapped in without changing the rest of the code.

### `dashboard.py`

| Part | Description |
|---|---|
| `cached_model()` | Loads the model once and reuses it (`st.cache_resource`) |
| `cached_tweets()` | Loads and shuffles the tweets once (`st.cache_data`) |
| `st.session_state` | Stores progress (`running`, `idx`, `feed`, `labels`) between reruns |
| `render()` | Redraws counters, chart, feed, and alert from the current state |
| Live loop | Predicts one tweet, updates state, renders, waits, repeats |

Streamlit reruns the whole script on every click. Progress is kept in `session_state`, and clicking Stop works because the rerun interrupts the loop.

---

## 6. Connecting a real data source

The stream is just a sequence of text. To use live data (API, Reddit, Kafka, a CSV), replace the tweet list with your own generator:

```python
def my_stream():
    while True:
        text = fetch_next_message()   # your API / socket / file reader
        yield text
```

The model functions (`predict([text])`) and the rolling trend logic stay the same.

---

## 7. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'datasets'` | Libraries not installed, or installed into a different Python | `python -m pip install datasets transformers torch scikit-learn vaderSentiment` |
| `ValueError: text input must be of type str...` | Newer `datasets` returns a column object, not a list | Use `list(ds["text"])` (already fixed in the current `tweeteval_sentiment.py`) |
| `pip` not recognized | `pip` not on PATH | Use `python -m pip install ...` |
| `python` not recognized | Python not on PATH | Try `python3` or `py` |
| `ModuleNotFoundError: No module named 'tweeteval_sentiment'` | `dashboard.py` is not next to `tweeteval_sentiment.py` | Put both files in the same folder and run from that folder |
| Very slow first run | Model and dataset downloading | Wait once; later runs use the cache |
| Install problems with `torch` | Very new Python version (e.g. 3.14) | Use Python 3.11 or 3.12 |

---

## 8. Limitations

- Neutral is the hardest class for both models; expect the most errors there.
- Sarcasm and irony are often misclassified.
- VADER is a general lexicon and is noticeably weaker than RoBERTa on tweets.
- The dashboard replays a dataset to simulate a live feed. Connecting a real source needs the changes described in section 6.
- Results on small `--limit` samples vary from the full test set.

---

## 9. Ideas for extension

- Fine-tune your own model on the TweetEval training split and compare it to the pretrained RoBERTa.
- Add multilingual support with a multilingual sentiment model.
- Connect Reddit or a CSV of customer reviews as the live source.
- Add per-topic or per-keyword trend lines to the dashboard.
- Send an email or Slack message when the alert threshold is crossed.

---

## 10. References

- TweetEval benchmark: Barbieri et al., "TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification" (Findings of EMNLP 2020). Dataset: `cardiffnlp/tweet_eval` on Hugging Face.
- Model: `cardiffnlp/twitter-roberta-base-sentiment-latest` on Hugging Face.
- VADER: Hutto and Gilbert, "VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text" (ICWSM 2014).
- Libraries: Hugging Face `transformers` and `datasets`, `scikit-learn`, `streamlit`, `pandas`.

---

## 11. Quick demo script (for presentations)

1. Run `python -m streamlit run dashboard.py` and open the page.
2. Choose `vader`, press **Start**, and explain the feed, chart, and counters.
3. Type a sarcastic sentence into the text box and show where the model struggles.
4. Switch to `roberta` and press **Reset**, then **Start**. Point out the better accuracy.
5. Lower the alert threshold (for example to -0.1) so the red alert appears, and explain the brand-monitoring use case.

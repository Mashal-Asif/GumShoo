"""
Sentiment analysis on the TweetEval dataset (sentiment task).
Labels in TweetEval: 0 = negative, 1 = neutral, 2 = positive

Usage:
    python tweeteval_sentiment.py evaluate                 # accuracy / F1 on test set (RoBERTa)
    python tweeteval_sentiment.py evaluate --model vader   # compare with VADER
    python tweeteval_sentiment.py stream                   # replay test tweets as a live stream
    python tweeteval_sentiment.py stream --delay 0.2 --limit 50
"""
import argparse
import time
from collections import deque

from datasets import load_dataset

ID2LABEL = {0: "negative", 1: "neutral", 2: "positive"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}


# ---------- Step 1: load the dataset ----------

def load_tweeteval(split="test"):
    # splits: train (45,615), validation (2,000), test (12,284)
    return load_dataset("cardiffnlp/tweet_eval", "sentiment", split=split)


# ---------- Step 2: load a model (returns a function: list[str] -> list[int]) ----------

def load_roberta():
    from transformers import pipeline
    clf = pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        truncation=True,
        max_length=128,
    )

    def predict(texts):
        out = clf(texts, batch_size=32)
        return [LABEL2ID[o["label"].lower()] for o in out]
    return predict


def load_vader():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()

    def predict(texts):
        preds = []
        for t in texts:
            c = sia.polarity_scores(t)["compound"]
            preds.append(2 if c >= 0.05 else 0 if c <= -0.05 else 1)
        return preds
    return predict


def get_model(name):
    return load_roberta() if name == "roberta" else load_vader()


# ---------- Step 3a: batch evaluation ----------

def evaluate(args):
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

    ds = load_tweeteval(args.split)
    if args.limit:
        ds = ds.select(range(min(args.limit, len(ds))))

    predict = get_model(args.model)
    texts, y_true = list(ds["text"]), list(ds["label"])

    print(f"Evaluating {args.model} on {len(texts)} tweets ({args.split} split)...")
    y_pred = predict(texts)

    print(f"\nAccuracy : {accuracy_score(y_true, y_pred):.4f}")
    print(f"Macro F1 : {f1_score(y_true, y_pred, average='macro'):.4f}\n")
    print(classification_report(y_true, y_pred, target_names=list(ID2LABEL.values()), digits=3))
    print("Confusion matrix (rows = true, cols = predicted):")
    print(confusion_matrix(y_true, y_pred))


# ---------- Step 3b: real-time replay ----------

COLORS = {"negative": "\033[91m", "neutral": "\033[93m", "positive": "\033[92m"}
RESET = "\033[0m"


def stream(args):
    ds = load_tweeteval(args.split).shuffle(seed=42)
    if args.limit:
        ds = ds.select(range(min(args.limit, len(ds))))

    predict = get_model(args.model)
    window = deque(maxlen=args.window)  # rolling window of values: -1, 0, +1
    correct = 0

    try:
        for i, row in enumerate(ds, 1):
            pred = predict([row["text"]])[0]
            true = row["label"]
            correct += int(pred == true)
            window.append(pred - 1)  # negative=-1, neutral=0, positive=+1
            trend = sum(window) / len(window)

            label = ID2LABEL[pred]
            mark = "ok " if pred == true else "MISS"
            print(
                f"{COLORS[label]}{label:<8}{RESET} [{mark}] "
                f"trend={trend:+.2f} acc={correct / i:.2%} | {row['text'][:90]}"
            )
            time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    print("\nStopped.")


# ---------- CLI ----------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["evaluate", "stream"])
    p.add_argument("--model", choices=["roberta", "vader"], default="roberta")
    p.add_argument("--split", choices=["train", "validation", "test"], default="test")
    p.add_argument("--limit", type=int, default=0, help="use only the first N tweets")
    p.add_argument("--delay", type=float, default=0.5, help="seconds between tweets (stream)")
    p.add_argument("--window", type=int, default=20, help="rolling window size (stream)")
    args = p.parse_args()

    evaluate(args) if args.mode == "evaluate" else stream(args)


if __name__ == "__main__":
    main()
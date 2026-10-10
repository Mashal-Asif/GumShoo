"""
Real-time sentiment analysis
Usage:
    python realtime_sentiment.py                 # simulated stream, VADER (fast)
    python realtime_sentiment.py --stdin         # type messages yourself
    python realtime_sentiment.py --model bert    # transformer model (more accurate)
"""
import argparse
import random
import sys
import time
from collections import deque

# ---------- Step 1: choose the sentiment model ----------

def load_vader():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()

    def score(text):
        c = analyzer.polarity_scores(text)["compound"]  # -1 .. +1
        label = "POSITIVE" if c >= 0.05 else "NEGATIVE" if c <= -0.05 else "NEUTRAL"
        return label, c
    return score


def load_bert():
    from transformers import pipeline
    clf = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
    )

    def score(text):
        r = clf(text[:512])[0]
        s = r["score"] if r["label"] == "POSITIVE" else -r["score"]
        return r["label"], s
    return score


# ---------- Step 2: the data source (a generator = a stream) ----------

SAMPLES = [
    "I love this product, it works perfectly!",
    "Worst customer service I have ever experienced.",
    "The delivery was okay, nothing special.",
    "Absolutely fantastic update, great job team!",
    "App keeps crashing, totally unusable.",
    "Not bad, but could be better.",
    "Thank you so much, problem solved!",
    "I'm very disappointed with the quality.",
]


def simulated_stream(delay=1.0):
    while True:
        yield random.choice(SAMPLES)
        time.sleep(delay)


def stdin_stream():
    print("Type a message and press Enter (Ctrl+C to quit):")
    for line in sys.stdin:
        line = line.strip()
        if line:
            yield line


# ---------- Step 3: process each message as it arrives ----------

COLORS = {"POSITIVE": "\033[92m", "NEGATIVE": "\033[91m", "NEUTRAL": "\033[93m"}
RESET = "\033[0m"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["vader", "bert"], default="vader")
    p.add_argument("--stdin", action="store_true", help="read messages from keyboard")
    p.add_argument("--window", type=int, default=10, help="rolling average size")
    args = p.parse_args()

    score = load_bert() if args.model == "bert" else load_vader()
    stream = stdin_stream() if args.stdin else simulated_stream()

    window = deque(maxlen=args.window)  # last N scores
    counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}

    try:
        for text in stream:
            label, s = score(text)
            label = label.upper()
            counts[label] = counts.get(label, 0) + 1
            window.append(s)
            avg = sum(window) / len(window)

            print(
                f"{COLORS.get(label, '')}{label:<9}{RESET} "
                f"score={s:+.2f}  rolling_avg={avg:+.2f}  | {text}"
            )
    except KeyboardInterrupt:
        total = sum(counts.values()) or 1
        print("\n--- Summary ---")
        for k, v in counts.items():
            print(f"{k:<9} {v:>4}  ({v / total:.0%})")


if __name__ == "__main__":
    main()
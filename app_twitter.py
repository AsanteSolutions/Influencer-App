import os
import re
import pandas as pd
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Your Twitter/X Bearer Token
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

def extract_tweet_id(url):
    """Extract tweet ID from the post URL."""
    match = re.search(r"status/(\d+)", url)
    if match:
        return match.group(1)
    return None


def get_tweet_metrics(tweet_id):
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {
        "tweet.fields": "public_metrics,conversation_id"
    }
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    res = requests.get(url, headers=headers, params=params)

    if res.status_code != 200:
        return {"error": res.text}

    data = res.json().get("data", {})

    metrics = data.get("public_metrics", {})

    return {
        "likes": metrics.get("like_count", 0),
        "replies": metrics.get("reply_count", 0),
        "retweets": metrics.get("retweet_count", 0),
        "quotes": metrics.get("quote_count", 0),
        "conversation_id": data.get("conversation_id")
    }


def get_tweet_replies(conversation_id):
    """
    Fetch actual comments (replies).
    ⚠ Requires Elevated/Enterprise Twitter access.
    """
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"conversation_id:{conversation_id}",
        "tweet.fields": "author_id,created_at,text"
    }
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    res = requests.get(url, headers=headers, params=params)

    if res.status_code != 200:
        return []

    tweets = res.json().get("data", [])
    return [t["text"] for t in tweets]


@app.route("/")
def home():
    return render_template("upload_twitter.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded"

    file = request.files["file"]
    df = pd.read_csv(file)

    if "LINK" not in df.columns or "NAME" not in df.columns:
        return "CSV must contain columns: NAME and LINK"

    results = []

    for index, row in df.iterrows():
        name = row["NAME"]
        link = row["LINK"]

        tweet_id = extract_tweet_id(str(link))
        if not tweet_id:
            results.append({
                "name": name,
                "link": link,
                "likes": "N/A",
                "replies": "N/A",
                "retweets": "N/A",
                "quotes": "N/A",
                "comments": []
            })
            continue

        metrics = get_tweet_metrics(tweet_id)

        comments = []
        if "conversation_id" in metrics:
            comments = get_tweet_replies(metrics["conversation_id"])

        results.append({
            "name": name,
            "link": link,
            "likes": metrics.get("likes", 0),
            "replies": metrics.get("replies", 0),
            "retweets": metrics.get("retweets", 0),
            "quotes": metrics.get("quotes", 0),
            "comments": comments
        })

    return render_template("results_twitter.html", results=results)


if __name__ == "__main__":
    app.run(debug=True, port=5003)

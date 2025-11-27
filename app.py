import os
import re
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Twitter/X Bearer Token
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
# Facebook Access Token
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
# Instagram Access Token
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

# --- Twitter/X Functions ---
def extract_tweet_id(url):
    """Extract tweet ID from the post URL."""
    match = re.search(r"status/(\d+)", url)
    if match:
        return match.group(1)
    return None

def get_tweet_metrics(tweet_id):
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {"tweet.fields": "public_metrics,conversation_id"}
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
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

# --- Facebook Functions ---
def extract_facebook_post_id(url):
    """Extract Facebook post ID from the URL."""
    patterns = [
        r'facebook\.com/[\w.]+/posts/(\d+)',
        r'facebook\.com/[\w.]+/photos/[^/]+/(\d+)',
        r'facebook\.com/permalink\.php\?story_fbid=(\d+)',
        r'facebook\.com/photo\.php\?fbid=(\d+)',
        r'/posts/(\d+)',
        r'/videos/(\d+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_facebook_post_metrics(post_id):
    url = f"https://graph.facebook.com/v18.0/{post_id}"
    params = {
        "fields": "reactions.summary(true),comments.summary(true),shares",
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return {"error": res.text}
    data = res.json()
    return {
        "reactions": data.get("reactions", {}).get("summary", {}).get("total_count", 0),
        "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
        "shares": data.get("shares", {}).get("count", 0),
    }

# --- Instagram Functions ---
def extract_instagram_post_id(url):
    """Extract Instagram post ID or shortcode from the URL."""
    patterns = [
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'instagram\.com/tv/([A-Za-z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def clean_facebook_url(url):
    """Remove query parameters and mobile or tracking parts of a facebook link to normalize it."""
    # Basic cleanup: remove querystrings and tracking parameters
    return url.split('?')[0].replace('m.facebook.com', 'facebook.com')

def get_instagram_post_metrics(media_id):
    """Note: This requires Instagram Business or Creator accounts."""
    url = f"https://graph.instagram.com/{media_id}"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return {"error": res.text}
    data = res.json()
    return {
        "likes": data.get("like_count", 0),
        "comments": data.get("comments_count", 0),
    }

# --- App Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload_facebook", methods=["GET", "POST"])
def upload_facebook():
    if request.method == "POST":
        try:
            if "file" not in request.files:
                return render_template("error_facebook.html",
                                     error="No file uploaded",
                                     message="Please select a file to upload.")

            file = request.files["file"]

            if file.filename == '':
                return render_template("error_facebook.html",
                                     error="No file selected",
                                     message="Please select a valid file.")

            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return render_template("error_facebook.html",
                                     error="Invalid file format",
                                     message="Please upload a CSV or Excel file.")

            df.columns = df.columns.str.strip().str.upper()

            if "LINK" not in df.columns or "NAME" not in df.columns:
                return render_template("error_facebook.html",
                                     error="Missing required columns",
                                     message="Your file must contain columns named 'NAME' and 'LINK'.")

            results = []

            for index, row in df.iterrows():
                name = row["NAME"]
                link = row["LINK"]

                post_id = extract_facebook_post_id(str(link))
                if not post_id:
                    results.append({
                        "name": name,
                        "link": link,
                        "reactions": "N/A",
                        "comments": "N/A",
                        "shares": "N/A",
                    })
                    continue

                metrics = get_facebook_post_metrics(post_id)

                if "error" in metrics:
                    results.append({
                        "name": name,
                        "link": link,
                        "reactions": "N/A",
                        "comments": "N/A",
                        "shares": "N/A",
                    })
                    continue

                results.append({
                    "name": name,
                    "link": link,
                    "reactions": metrics.get("reactions", 0),
                    "comments": metrics.get("comments", 0),
                    "shares": metrics.get("shares", 0),
                })

            return render_template("results_facebook.html", results=results)

        except Exception as e:
            return render_template("error_facebook.html",
                                 error="Processing Error",
                                 message=f"An error occurred while processing your file: {str(e)}")
    return render_template("upload_facebook.html")

def get_instagram_media_id_from_shortcode(shortcode):
    url = f"https://graph.facebook.com/v18.0/ig_shortcode_to_media_id"
    params = {
        "shortcode": shortcode,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None
    data = res.json()
    return data.get("id")


@app.route("/upload_instagram", methods=["GET", "POST"])
def upload_instagram():
    if request.method == "POST":
        try:
            if "file" not in request.files:
                return render_template("error_instagram.html",
                                     error="No file uploaded",
                                     message="Please select a file to upload.")

            file = request.files["file"]

            if file.filename == '':
                return render_template("error_instagram.html",
                                     error="No file selected",
                                     message="Please select a valid file.")

            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return render_template("error_instagram.html",
                                     error="Invalid file format",
                                     message="Please upload a CSV or Excel file.")

            df.columns = df.columns.str.strip().str.upper()

            if "LINK" not in df.columns or "NAME" not in df.columns:
                return render_template("error_instagram.html",
                                     error="Missing required columns",
                                     message="Your file must contain columns named 'NAME' and 'LINK'.")

            results = []

            for index, row in df.iterrows():
                name = row["NAME"]
                link = row["LINK"]

                shortcode = extract_instagram_post_id(str(link))
                if not shortcode:
                    results.append({
                        "name": name,
                        "link": link,
                        "likes": "N/A",
                        "comments": "N/A",
                    })
                    continue

                # Scrape the post directly (Playwright)
                try:
                    import app_instagram
                    scrape_instagram_post = app_instagram.scrape_instagram_post
                except Exception:
                    results.append({
                        "name": name,
                        "link": link,
                        "likes": "N/A",
                        "comments": "N/A",
                    })
                    continue
                metrics = scrape_instagram_post(link)
                if not metrics or "error" in metrics:
                    results.append({
                        "name": name,
                        "link": link,
                        "likes": "N/A",
                        "comments": "N/A",
                    })
                    continue

                results.append({
                    "name": name,
                    "link": link,
                    "likes": metrics.get("likes", 0),
                    "comments": metrics.get("comments", 0),
                })

            return render_template("results_instagram.html", results=results)

        except Exception as e:
            return render_template("error_instagram.html",
                                 error="Processing Error",
                                 message=f"An error occurred while processing your file: {str(e)}")
    return render_template("upload_instagram.html")


@app.route("/upload_twitter", methods=["GET", "POST"])
def upload_twitter():
    if request.method == "POST":
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
                })
                continue

            metrics = get_tweet_metrics(tweet_id)

            results.append({
                "name": name,
                "link": link,
                "likes": metrics.get("likes", 0),
                "replies": metrics.get("replies", 0),
                "retweets": metrics.get("retweets", 0),
                "quotes": metrics.get("quotes", 0),
            })

        return render_template("results_twitter.html", results=results)
    return render_template("upload_twitter.html")


@app.route("/analyze_link", methods=["POST"])
def analyze_link():
    link = request.form.get("link")
    if not link:
        flash("Please enter a link.", "error")
        return redirect(url_for("home"))

    original_link = link  # store for display
    platform = None
    post_id = None
    metrics = {}

    # ---- TWITTER ----
    if "twitter.com" in link or "x.com" in link:
        platform = "Twitter"
        post_id = extract_tweet_id(link)
        if not post_id:
            flash("Could not extract Tweet ID from the link.", "error")
            return redirect(url_for("home"))
        metrics = get_tweet_metrics(post_id)

    # ---- FACEBOOK ----
    elif "facebook.com" in link or "fb.watch" in link:
        platform = "Facebook"
        link = clean_facebook_url(link)
        post_id = extract_facebook_post_id(link)
        if not post_id:
            flash("Could not extract Facebook Post ID from the link.", "error")
            return redirect(url_for("home"))
        metrics = get_facebook_post_metrics(post_id)

    # ---- INSTAGRAM ----
    elif "instagram.com" in link:
        platform = "Instagram"
        try:
            import app_instagram
            scrape_instagram_post = app_instagram.scrape_instagram_post
        except Exception as e:
            flash("Instagram scraper not available: ensure Playwright is installed.", "error")
            return redirect(url_for("home"))

        # Use Playwright scraping method to fetch likes/comments directly by link
        metrics = scrape_instagram_post(link)

    else:
        flash("Unsupported platform. Only Twitter, Facebook, and Instagram links are accepted.", "error")
        return redirect(url_for("home"))

    # ---- Handle API errors ----
    if not metrics or ("error" in metrics):
        flash(f"API Error: {metrics.get('error', 'Unknown error')}", "error")
        return redirect(url_for("home"))

    # Show debug in console
    print("Platform:", platform)
    print("Post ID:", post_id)
    print("Metrics:", metrics)

    return render_template("results.html",
                           link=original_link,
                           platform=platform,
                           metrics=metrics)


if __name__ == "__main__":
    app.run(debug=True)
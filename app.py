import os
import re
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
# Facebook Access Token
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
# NOTE: Playwright is used for Instagram/Twitter/TikTok scraping; no access token is required.

# --- Twitter/X Functions ---
def extract_tweet_id(url):
    """Extract tweet ID from the post URL."""
    match = re.search(r"status/(\d+)", url)
    if match:
        return match.group(1)
    return None



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


def scrape_instagram_post(url):
    """
    Scrape an Instagram post using Playwright (best effort).
    """
    try:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as ie:
            return {"error": "Playwright not installed. Run 'pip install playwright' and 'python -m playwright install chromium'"}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                 "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            context = browser.new_context(user_agent=ua, locale='en-US')
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            try:
                page.wait_for_selector('article', timeout=8000)
            except Exception:
                pass
            likes = 0
            comments_count = 0
            media_type = "N/A"
            comment_list = []
            try:
                ld_json = page.query_selector('script[type="application/ld+json"]')
                if ld_json:
                    json_text = ld_json.inner_text() or ld_json.text_content()
                    obj = json.loads(json_text)
                    if isinstance(obj, dict):
                        inter = obj.get('interactionStatistic')
                        if isinstance(inter, dict):
                            likes = int(inter.get('userInteractionCount', 0))
                        elif isinstance(inter, list):
                            for stat in inter:
                                if stat.get('interactionType', {}).get('name', '').lower().find('like') != -1:
                                    likes = int(stat.get('userInteractionCount', 0))
                                if stat.get('interactionType', {}).get('name', '').lower().find('comment') != -1:
                                    comments_count = int(stat.get('userInteractionCount', 0))
                        media_type = obj.get('uploadDate', media_type) or media_type
            except Exception:
                pass
            if likes == 0 or comments_count == 0:
                try:
                    og_descr = page.query_selector('meta[property="og:description"]')
                    if og_descr:
                        ogc = og_descr.get_attribute('content') or ''
                        m = re.search(r"([\d,\.]+)\s+likes", ogc, re.I)
                        if m:
                            likes = int(m.group(1).replace(',', ''))
                        m2 = re.search(r"([\d,\.]+)\s+comments", ogc, re.I)
                        if m2:
                            comments_count = int(m2.group(1).replace(',', ''))
                except Exception:
                    pass
            if likes == 0:
                try:
                    text = ''
                    try:
                        text = page.text_content('article') or ''
                    except Exception:
                        text = page.content() or ''
                    m = re.search(r"([\d,\.]+)\s+likes", text, re.I)
                    if m:
                        likes = int(m.group(1).replace(',', ''))
                except Exception:
                    pass
            try:
                nodes = page.query_selector_all('div.C4VMK > span')
                for node in nodes:
                    txt = node.inner_text().strip()
                    if txt:
                        comment_list.append(txt)
                if not comment_list:
                    try:
                        li_nodes = page.query_selector_all('article li')
                        for l in li_nodes:
                            txt = l.inner_text().strip()
                            if txt:
                                comment_list.append(txt)
                    except Exception:
                        pass
                comments_count = comments_count or len(comment_list)
            except Exception:
                pass
            try:
                context.close()
                browser.close()
            except Exception:
                pass
            return {
                "likes": int(likes or 0),
                "comments": int(comments_count or 0),
                "comment_list": comment_list[:20],
                "media_type": media_type
            }
    except Exception as e:
        return {"error": str(e)}


def scrape_twitter_post(url):
    """
    Scrape a public Twitter/X post using Playwright.
    Returns: {"likes": int, "replies": int, "retweets": int, "comment_list": [str..]}
    """
    try:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return {"error": "Playwright not installed. Run 'pip install playwright' and 'python -m playwright install chromium'"}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(locale='en-US')
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            try:
                page.wait_for_selector('article', timeout=8000)
            except Exception:
                pass
            likes = 0
            replies = 0
            retweets = 0
            comment_list = []
            try:
                ld_json = page.query_selector('script[type="application/ld+json"]')
                if ld_json:
                    obj = json.loads(ld_json.inner_text() or ld_json.text_content())
                    if isinstance(obj, dict):
                        inter = obj.get('interactionStatistic')
                        if isinstance(inter, dict):
                            likes = int(inter.get('userInteractionCount', 0))
                        elif isinstance(inter, list):
                            for stat in inter:
                                name = stat.get('interactionType', {}).get('name', '').lower()
                                if 'like' in name:
                                    likes = int(stat.get('userInteractionCount', 0))
                                if 'comment' in name:
                                    replies = int(stat.get('userInteractionCount', 0))
                                if 'retweet' in name or 'share' in name:
                                    retweets = int(stat.get('userInteractionCount', 0))
            except Exception:
                pass
            if likes == 0 or replies == 0:
                try:
                    og_descr = page.query_selector('meta[property="og:description"]')
                    if og_descr:
                        ogc = og_descr.get_attribute('content') or ''
                        m = re.search(r"([\d,\.]+)\s+Likes", ogc, re.I)
                        if m:
                            likes = int(m.group(1).replace(',', ''))
                except Exception:
                    pass
            # Attempt to scrape comment texts
            try:
                nodes = page.query_selector_all('div[aria-label="Timeline: Conversation"] div[dir="auto"] span')
                for node in nodes:
                    txt = node.inner_text().strip()
                    if txt:
                        comment_list.append(txt)
                comments_count = len(comment_list)
            except Exception:
                comments_count = 0
            try:
                context.close()
                browser.close()
            except Exception:
                pass
            return {"likes": int(likes or 0), "replies": int(replies or 0), "retweets": int(retweets or 0), "comment_list": comment_list[:20]}
    except Exception as e:
        return {"error": str(e)}


def scrape_tiktok_post(url):
    """
    Scrape a public TikTok video using Playwright (best effort).
    Returns: {"likes": int, "comments": int, "comment_list": [str..]}
    """
    try:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return {"error": "Playwright not installed. Run 'pip install playwright' and 'python -m playwright install chromium'"}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(locale='en-US')
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            try:
                page.wait_for_selector('main', timeout=8000)
            except Exception:
                pass
            likes = 0
            comments = 0
            comment_list = []
            try:
                og_descr = page.query_selector('meta[property="og:description"]')
                if og_descr:
                    ogc = og_descr.get_attribute('content') or ''
                    m = re.search(r"([\d,\.]+)\s+Likes|([\d,\.]+)\s+view", ogc, re.I)
                    if m:
                        # sometimes shows views or likes here
                        likes = int((m.group(1) or m.group(2)).replace(',', ''))
            except Exception:
                pass
            # Grab comments (best-effort)
            try:
                nodes = page.query_selector_all('div.comment-item > p')
                for node in nodes:
                    txt = node.inner_text().strip()
                    if txt:
                        comment_list.append(txt)
                comments = len(comment_list)
            except Exception:
                pass
            try:
                context.close()
                browser.close()
            except Exception:
                pass
            return {"likes": int(likes or 0), "comments": int(comments or 0), "comment_list": comment_list[:20]}
    except Exception as e:
        return {"error": str(e)}

# NOTE: Instagram metrics are retrieved using Playwright scrapers (see scatter functions above).

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

# NOTE: We use Playwright for Instagram scraping. This Graph API helper was removed.


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
                    "comment_list": metrics.get("comment_list", [])
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
            return render_template("error_twitter.html",
                                 error="No file uploaded",
                                 message="Please select a file to upload.")

        file = request.files["file"]
        df = pd.read_csv(file)

        if "LINK" not in df.columns or "NAME" not in df.columns:
            return render_template("error_twitter.html",
                                 error="Missing required columns",
                                 message="Your file must contain columns named 'NAME' and 'LINK'.")

        results = []

        for index, row in df.iterrows():
            name = row["NAME"]
            link = row["LINK"]
            # Use Playwright scraping for Twitter post
            metrics = scrape_twitter_post(link)
            if not metrics or "error" in metrics:
                results.append({
                    "name": name,
                    "link": link,
                    "likes": "N/A",
                    "replies": "N/A",
                    "retweets": "N/A",
                    "quotes": "N/A",
                })
                continue
            results.append({
                "name": name,
                "link": link,
                "likes": metrics.get("likes", 0),
                "replies": metrics.get("replies", 0),
                "retweets": metrics.get("retweets", 0),
                "quotes": metrics.get("quotes", 0),
                "comments": metrics.get("comment_list", [])
            })

        return render_template("results_twitter.html", results=results)
    return render_template("upload_twitter.html")


@app.route("/upload_tiktok", methods=["GET", "POST"])
def upload_tiktok():
    if request.method == "POST":
        try:
            if "file" not in request.files:
                return render_template("error_tiktok.html",
                                     error="No file uploaded",
                                     message="Please select a file to upload.")

            file = request.files["file"]

            if file.filename == '':
                return render_template("error_tiktok.html",
                                     error="No file selected",
                                     message="Please select a valid file.")

            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return render_template("error_tiktok.html",
                                     error="Invalid file format",
                                     message="Please upload a CSV or Excel file.")

            df.columns = df.columns.str.strip().str.upper()

            if "LINK" not in df.columns or "NAME" not in df.columns:
                return render_template("error_tiktok.html",
                                     error="Missing required columns",
                                     message="Your file must contain columns named 'NAME' and 'LINK'.")

            results = []

            for index, row in df.iterrows():
                name = row["NAME"]
                link = row["LINK"]

                # Scrape TikTok post directly
                metrics = scrape_tiktok_post(link)
                if not metrics or "error" in metrics:
                    results.append({
                        "name": name,
                        "link": link,
                        "likes": "N/A",
                        "comments": "N/A",
                        "comment_list": []
                    })
                    continue

                results.append({
                    "name": name,
                    "link": link,
                    "likes": metrics.get("likes", 0),
                    "comments": metrics.get("comments", 0),
                    "comment_list": metrics.get("comment_list", [])
                })

            return render_template("results_tiktok.html", results=results)

        except Exception as e:
            return render_template("error_tiktok.html",
                                 error="Processing Error",
                                 message=f"An error occurred while processing your file: {str(e)}")
    return render_template("upload_tiktok.html")


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
        # Use Playwright scraping instead of API
        try:
            metrics = scrape_twitter_post(link)
        except Exception as e:
            flash("Twitter scraper not available: ensure Playwright is installed.", "error")
            return redirect(url_for("home"))

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
            metrics = scrape_instagram_post(link)
        except Exception:
            flash("Instagram scraper not available: ensure Playwright is installed.", "error")
            return redirect(url_for("home"))

    # ---- TIKTOK ----
    elif "tiktok.com" in link or "vm.tiktok.com" in link:
        platform = "TikTok"
        try:
            metrics = scrape_tiktok_post(link)
        except Exception:
            flash("TikTok scraper not available: ensure Playwright is installed.", "error")
            return redirect(url_for("home"))

    else:
        flash("Unsupported platform. Only Twitter, Facebook, Instagram, and TikTok links are accepted.", "error")
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
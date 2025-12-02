"""
Twitter/X Blueprint - handles Twitter post analysis routes
"""
import re
import pandas as pd
from flask import Blueprint, render_template, request
from playwright.sync_api import sync_playwright

# Create Blueprint
twitter_bp = Blueprint('twitter', __name__, url_prefix='/twitter')


def extract_tweet_id(url: str):
    """Extract tweet ID from the post URL."""
    match = re.search(r"status/(\d+)", url)
    return match.group(1) if match else None


def scrape_tweet(tweet_url):
    """Scrape a public Twitter/X post using Playwright."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(tweet_url, timeout=60000)
            page.wait_for_selector("article", timeout=15000)

            likes_elem = page.locator('[data-testid="like"]')
            replies_elem = page.locator('[data-testid="reply"]')
            retweets_elem = page.locator('[data-testid="retweet"]')

            likes = likes_elem.text_content() if likes_elem.count() > 0 else "0"
            replies = replies_elem.text_content() if replies_elem.count() > 0 else "0"
            retweets = retweets_elem.text_content() if retweets_elem.count() > 0 else "0"

            views = "N/A"
            try:
                views_elem = page.locator("span:below(:text('Views'))").nth(0)
                if views_elem.count() > 0:
                    views = views_elem.text_content()
            except:
                pass

            comments = []
            comment_elements = page.locator('div[data-testid="tweetText"]')
            count = comment_elements.count()
            for i in range(min(count, 20)):
                text = comment_elements.nth(i).text_content()
                if text:
                    comments.append(text)

            browser.close()

            return {
                "likes": likes.strip() if likes else "0",
                "replies": replies.strip() if replies else "0",
                "retweets": retweets.strip() if retweets else "0",
                "views": views,
                "comments": comments
            }

        except Exception as e:
            browser.close()
            return {"error": str(e)}


@twitter_bp.route("/")
def home():
    return render_template("twitter/upload.html")


@twitter_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return render_template("twitter/error.html",
                             error="No file uploaded",
                             message="Please select a file to upload.")

    file = request.files["file"]
    
    if file.filename == '':
        return render_template("twitter/error.html",
                             error="No file selected",
                             message="Please select a valid file.")

    if not file.filename.endswith('.csv'):
        return render_template("twitter/error.html",
                             error="Invalid file format",
                             message="Please upload a CSV file.")

    df = pd.read_csv(file)

    if "LINK" not in df.columns or "NAME" not in df.columns:
        return render_template("twitter/error.html",
                             error="Missing required columns",
                             message="Your file must contain columns named 'NAME' and 'LINK'.")

    results = []

    for _, row in df.iterrows():
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
                "views": "N/A",
                "comments": []
            })
            continue

        metrics = scrape_tweet(link)

        if "error" in metrics:
            results.append({
                "name": name,
                "link": link,
                "likes": "N/A",
                "replies": "N/A",
                "retweets": "N/A",
                "views": "N/A",
                "comments": []
            })
            continue

        results.append({
            "name": name,
            "link": link,
            "likes": metrics.get("likes", "0"),
            "replies": metrics.get("replies", "0"),
            "retweets": metrics.get("retweets", "0"),
            "views": metrics.get("views", "N/A"),
            "comments": metrics.get("comments", [])
            })

    return render_template("twitter/results.html", results=results)
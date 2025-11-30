"""
Archived file: `app_instagram.py` moved to single-app `app.py`.
Use `app.py` as the entrypoint for the consolidated application.
This file is preserved for reference only.
"""

import os
import re
import json
import requests
import pandas as pd
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")  # REQUIRED for Graph API if used

app = Flask(__name__)


def extract_post_id(url):
    """Extract Instagram post ID or shortcode from ANY Instagram URL format."""
    url = url.strip()

    # Normalize URL (remove trailing slash or tracking params)
    url = url.split('?')[0].rstrip('/')

    patterns = [
        r'instagram\.com/p/([^/]+)',
        r'instagram\.com/reel/([^/]+)',
        r'instagram\.com/reels/([^/]+)',
        r'instagram\.com/tv/([^/]+)',
        r'instagram\.com/(?:[^/]+)/([^/]+)'   # fallback for unusual formats
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None



def scrape_instagram_post(url):
    """
    Scrape likes/comments from a PUBLIC IG post using Playwright.
    Returns: {"likes": int, "comments": int, "comment_list": [...], "media_type": str}
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return {"error": "Playwright missing. Run: pip install playwright && playwright install chromium"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)

            try:
                page.wait_for_selector("article", timeout=8000)
            except Exception:
                pass

            likes = 0
            comments_count = 0
            media_type = "N/A"
            comment_list = []

            # Pull metrics from application/ld+json
            try:
                ld_json = page.query_selector('script[type="application/ld+json"]')
                if ld_json:
                    obj = json.loads(ld_json.inner_text())
                    inter = obj.get("interactionStatistic")

                    if isinstance(inter, dict):
                        likes = int(inter.get("userInteractionCount", 0))

                    elif isinstance(inter, list):
                        for item in inter:
                            name = item.get("interactionType", {}).get("name", "").lower()
                            if "like" in name:
                                likes = int(item.get("userInteractionCount", 0))
                            if "comment" in name:
                                comments_count = int(item.get("userInteractionCount", 0))

                    media_type = obj.get("uploadDate", "N/A")

            except Exception:
                pass

            # Try og:description for likes/comments
            try:
                og = page.query_selector('meta[property="og:description"]')
                if og:
                    text = og.get_attribute("content") or ""
                    m = re.search(r"([\d,.,]+)\s+likes", text, re.I)
                    if m:
                        likes = int(m.group(1).replace(",", ""))

                    m2 = re.search(r"([\d,.,]+)\s+comments", text, re.I)
                    if m2:
                        comments_count = int(m2.group(1).replace(",", ""))
            except Exception:
                pass

            # Pull comments directly
            try:
                nodes = page.query_selector_all("div.C4VMK > span")
                for node in nodes:
                    txt = node.inner_text().strip()
                    if txt:
                        comment_list.append(txt)

                if comments_count == 0:
                    comments_count = len(comment_list)
            except Exception:
                pass

            context.close()
            browser.close()

            return {
                "likes": likes,
                "comments": comments_count,
                "comment_list": comment_list[:20],
                "media_type": media_type
            }

    except Exception as e:
        return {"error": str(e)}


@app.route("/")
def home():
    return render_template("upload_instagram.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return render_template("error_instagram.html",
                                   error="No file uploaded",
                                   message="Please upload a CSV or Excel file.")

        file = request.files["file"]

        if file.filename == "":
            return render_template("error_instagram.html",
                                   error="Empty file",
                                   message="Please upload a valid file.")

        # Read file
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return render_template("error_instagram.html",
                                   error="Invalid format",
                                   message="Only CSV or Excel files allowed.")

        df.columns = df.columns.str.strip().str.upper()

        if "NAME" not in df.columns or "LINK" not in df.columns:
            return render_template("error_instagram.html",
                                   error="Invalid columns",
                                   message="Required columns: NAME, LINK")

        results = []

        for _, row in df.iterrows():
            name = row["NAME"]
            link = str(row["LINK"]).strip()

            shortcode = extract_post_id(link)
            if not shortcode:
                results.append({
                    "name": name,
                    "link": link,
                    "likes": "N/A",
                    "comments": "N/A",
                    "media_type": "N/A",
                    "comment_list": []
                })
                continue

            metrics = scrape_instagram_post(link)

            if not metrics or "error" in metrics:
                results.append({
                    "name": name,
                    "link": link,
                    "likes": "N/A",
                    "comments": "N/A",
                    "media_type": "N/A",
                    "comment_list": []
                })
                continue

            results.append({
                "name": name,
                "link": link,
                "likes": metrics["likes"],
                "comments": metrics["comments"],
                "media_type": metrics["media_type"],
                "comment_list": metrics["comment_list"],
            })

        return render_template("results_instagram.html", results=results)

    except Exception as e:
        return render_template("error_instagram.html",
                               error="Processing Error",
                               message=str(e))


if __name__ == "__main__":
    raise SystemExit("Deprecated: run app.py instead of app_instagram.py.")

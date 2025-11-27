import os
import re
import json
import pandas as pd
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv
# Import playwright lazily inside scrape_instagram_post to avoid import errors if not installed.

load_dotenv()

app = Flask(__name__)

# Instagram Access Token (requires Facebook App with Instagram Basic Display or Instagram Graph API)
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

def extract_post_id(url):
    """Extract Instagram post ID or shortcode from the URL."""
    # Matches various Instagram URL formats
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


def scrape_instagram_post(url):
    """
    Scrape likes and comments from a public Instagram post using Playwright.
    Returns a dict: {"likes": int, "comments": int, "comment_list": [str,...], "media_type": str}
    This is a best-effort approach and may fail if Instagram changes markup or the post requires login.
    """
    try:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as ie:
            return {"error": "Playwright not installed. Run 'pip install playwright' and 'playwright install chromium'"}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for the main post article to load
            try:
                page.wait_for_selector('article', timeout=8000)
            except Exception:
                # Continue - sometimes article is present but with a different node
                pass

            content = page.content()

            # 1) Try application/ld+json script for interaction statistics
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
                        # interactionStatistic may be for comments or likes
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

            # 2) Try og:description which sometimes contains likes/comments (e.g., '1,234 likes')
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

            # 3) As a fallback, search for common class selectors for likes
            if likes == 0:
                try:
                    # Some pages show 'Likes' text with a number
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

            # 4) Grab comment nodes (best effort): look for comment containers
            try:
                # Common class for comments & caption: 'C4VMK', fallback to 'ul li' structure
                nodes = page.query_selector_all('div.C4VMK > span')
                for node in nodes:
                    txt = node.inner_text().strip()
                    if txt:
                        comment_list.append(txt)
                # Remove the first one if it looks like caption (author and caption)
                if len(comment_list) > 0:
                    # Usually the caption is first; we leave all since it's helpful
                    pass
                comments_count = comments_count or len(comment_list)
            except Exception:
                pass

            # Close browser
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


def get_post_comments(media_id, limit=10):
    """
    Backwards compatible wrapper that returns comments list by querying Graph API if we have a media_id.
    If you prefer Playwright scraped comments, use scrape_instagram_post(url).
    """
    try:
        url = f"https://graph.instagram.com/{media_id}/comments"
        params = {
            "fields": "text,username,timestamp",
            "limit": limit,
            "access_token": ACCESS_TOKEN
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return []
        data = res.json()
        comments_data = data.get("data", [])
        return [c.get("text", "") for c in comments_data]
    except Exception:
        return []


def shortcode_to_media_id(shortcode):
    """
    Convert Instagram shortcode to media ID.
    Note: For production use, you may need to use the Instagram Basic Display API
    or maintain a mapping of shortcodes to media IDs.
    """
    # This is a simplified approach - in production you'd need proper API calls
    # to convert shortcode to media ID or use the Business Discovery API
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    media_id = 0
    
    for char in shortcode:
        media_id = media_id * 64 + alphabet.index(char)
    
    return str(media_id)


@app.route("/")
def home():
    return render_template("upload_instagram.html")


@app.route("/upload", methods=["POST"])
def upload_file():
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

        # Support both CSV and Excel files
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return render_template("error_instagram.html",
                                 error="Invalid file format",
                                 message="Please upload a CSV or Excel file.")

        # Check for required columns (case-insensitive)
        df.columns = df.columns.str.strip().str.upper()
        
        if "LINK" not in df.columns or "NAME" not in df.columns:
            return render_template("error_instagram.html",
                                 error="Missing required columns",
                                 message="Your file must contain columns named 'NAME' and 'LINK'.")

        results = []

        for index, row in df.iterrows():
            name = row["NAME"]
            link = row["LINK"]

            shortcode = extract_post_id(str(link))
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
            # Use Playwright to scrape the post directly by URL
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
            comment_list = metrics.get("comment_list", []) or []
            results.append({
                "name": name,
                "link": link,
                "likes": metrics.get("likes", 0),
                "comments": metrics.get("comments", 0),
                "media_type": metrics.get("media_type", "N/A"),
                "comment_list": comment_list
            })

        return render_template("results_instagram.html", results=results)
    
    except Exception as e:
        return render_template("error_instagram.html",
                             error="Processing Error",
                             message=f"An error occurred while processing your file: {str(e)}")


if __name__ == "__main__":
    app.run(debug=True, port=5002)

"""
TikTok Blueprint - handles TikTok video analysis routes
"""
import re
import pandas as pd
from flask import Blueprint, render_template, request

# Create Blueprint
tiktok_bp = Blueprint('tiktok', __name__, url_prefix='/tiktok')


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
            browser = p.chromium.launch(
                headless=True, 
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                locale='en-US',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Use domcontentloaded for faster loading
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            try:
                page.wait_for_selector('main', timeout=5000, state='attached')
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
                        likes = int((m.group(1) or m.group(2)).replace(',', ''))
            except Exception:
                pass
            
            # Grab comments (best-effort, limit for speed)
            try:
                nodes = page.query_selector_all('div.comment-item > p')
                for node in nodes[:10]:  # Limit to first 10
                    try:
                        txt = node.inner_text(timeout=2000).strip()
                        if txt:
                            comment_list.append(txt)
                    except:
                        continue
                comments = len(comment_list)
            except Exception:
                pass
            
            try:
                context.close()
                browser.close()
            except Exception:
                pass
            
            return {
                "likes": int(likes or 0),
                "comments": int(comments or 0),
                "comment_list": comment_list[:20]
            }
    except Exception as e:
        return {"error": str(e)}


@tiktok_bp.route("/")
def home():
    return render_template("tiktok/upload.html")


@tiktok_bp.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return render_template("tiktok/error.html",
                                 error="No file uploaded",
                                 message="Please select a file to upload.")

        file = request.files["file"]

        if file.filename == '':
            return render_template("tiktok/error.html",
                                 error="No file selected",
                                 message="Please select a valid file.")

        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return render_template("tiktok/error.html",
                                 error="Invalid file format",
                                 message="Please upload a CSV or Excel file.")

        df.columns = df.columns.str.strip().str.upper()

        if "LINK" not in df.columns or "NAME" not in df.columns:
            return render_template("tiktok/error.html",
                                 error="Missing required columns",
                                 message="Your file must contain columns named 'NAME' and 'LINK'.")

        results = []

        for index, row in df.iterrows():
            name = row["NAME"]
            link = row["LINK"]

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

        return render_template("tiktok/results.html", results=results)

    except Exception as e:
        return render_template("tiktok/error.html",
                             error="Processing Error",
                             message=f"An error occurred while processing your file: {str(e)}")

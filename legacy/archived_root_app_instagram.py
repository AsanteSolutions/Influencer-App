"""
Archived copy of root-level `app_instagram.py` moved into legacy folder as a backup.
"""

# Original content preserved for reference

import re
import json
import requests
import pandas as pd
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


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

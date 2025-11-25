import os
import re
import pandas as pd
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

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


def get_post_metrics(media_id):
    """
    Fetch Instagram post metrics using Instagram Graph API.
    Requires an access token with appropriate permissions.
    Note: This requires Instagram Business or Creator accounts.
    """
    url = f"https://graph.instagram.com/{media_id}"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "access_token": ACCESS_TOKEN
    }

    try:
        res = requests.get(url, params=params)
        
        if res.status_code != 200:
            return {"error": res.text}

        data = res.json()
        
        return {
            "likes": data.get("like_count", 0),
            "comments": data.get("comments_count", 0),
            "media_type": data.get("media_type", "N/A"),
            "media_id": media_id
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_post_comments(media_id, limit=10):
    """
    Fetch comments from an Instagram post.
    """
    url = f"https://graph.instagram.com/{media_id}/comments"
    params = {
        "fields": "text,username,timestamp",
        "limit": limit,
        "access_token": ACCESS_TOKEN
    }

    try:
        res = requests.get(url, params=params)
        
        if res.status_code != 200:
            return []

        data = res.json()
        comments_data = data.get("data", [])
        
        return [c.get("text", "") for c in comments_data]
    
    except Exception as e:
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

            # Convert shortcode to media ID
            media_id = shortcode_to_media_id(shortcode)
            
            metrics = get_post_metrics(media_id)
            
            if "error" in metrics:
                results.append({
                    "name": name,
                    "link": link,
                    "likes": "N/A",
                    "comments": "N/A",
                    "media_type": "N/A",
                    "comment_list": []
                })
                continue

            comment_list = get_post_comments(media_id)

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

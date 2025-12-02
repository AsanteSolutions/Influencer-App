"""
Facebook Blueprint - handles Facebook post analysis routes
"""
import os
import re
import pandas as pd
import requests
from flask import Blueprint, render_template, request
from dotenv import load_dotenv

load_dotenv()

# Create Blueprint
facebook_bp = Blueprint('facebook', __name__, url_prefix='/facebook')

# Facebook Access Token
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

def extract_post_id(url):
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


def get_post_metrics(post_id):
    """
    Fetch Facebook post metrics using Graph API.
    Requires a Page Access Token with appropriate permissions.
    """
    url = f"https://graph.facebook.com/v18.0/{post_id}"
    params = {
        "fields": "reactions.summary(true),comments.summary(true),shares,message,created_time",
        "access_token": ACCESS_TOKEN
    }

    try:
        res = requests.get(url, params=params)
        
        if res.status_code != 200:
            return {"error": res.text}

        data = res.json()
        
        reactions = data.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = data.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = data.get("shares", {}).get("count", 0)
        
        return {
            "reactions": reactions,
            "comments": comments,
            "shares": shares,
            "post_id": post_id
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_post_comments(post_id, limit=10):
    """Fetch comments from a Facebook post."""
    url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
    params = {
        "fields": "message,from",
        "limit": limit,
        "access_token": ACCESS_TOKEN
    }

    try:
        res = requests.get(url, params=params)
        
        if res.status_code != 200:
            return []

        data = res.json()
        comments_data = data.get("data", [])
        
        return [c.get("message", "") for c in comments_data]
    
    except Exception as e:
        return []


@facebook_bp.route("/")
def home():
    return render_template("facebook/upload.html")


@facebook_bp.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return render_template("facebook/error.html", 
                                 error="No file uploaded",
                                 message="Please select a file to upload.")

        file = request.files["file"]
        
        if file.filename == '':
            return render_template("facebook/error.html",
                                 error="No file selected",
                                 message="Please select a valid file.")

        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return render_template("facebook/error.html",
                                 error="Invalid file format",
                                 message="Please upload a CSV or Excel file.")

        df.columns = df.columns.str.strip().str.upper()
        
        if "LINK" not in df.columns or "NAME" not in df.columns:
            return render_template("facebook/error.html",
                                 error="Missing required columns",
                                 message="Your file must contain columns named 'NAME' and 'LINK'.")

        results = []

        for index, row in df.iterrows():
            name = row["NAME"]
            link = row["LINK"]

            post_id = extract_post_id(str(link))
            if not post_id:
                results.append({
                    "name": name,
                    "link": link,
                    "reactions": "N/A",
                    "comments": "N/A",
                    "shares": "N/A",
                    "comment_list": []
                })
                continue

            metrics = get_post_metrics(post_id)
            
            if "error" in metrics:
                results.append({
                    "name": name,
                    "link": link,
                    "reactions": "N/A",
                    "comments": "N/A",
                    "shares": "N/A",
                    "comment_list": []
                })
                continue

            comment_list = get_post_comments(post_id)

            results.append({
                "name": name,
                "link": link,
                "reactions": metrics.get("reactions", 0),
                "comments": metrics.get("comments", 0),
                "shares": metrics.get("shares", 0),
                "comment_list": comment_list
            })

        return render_template("facebook/results.html", results=results)
    
    except Exception as e:
        return render_template("facebook/error.html",
                             error="Processing Error",
                             message=f"An error occurred while processing your file: {str(e)}")

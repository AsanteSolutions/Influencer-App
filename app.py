import os
import re
from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv

# Import blueprints
from blueprints import facebook_bp, twitter_bp, instagram_bp, tiktok_bp
from blueprints.facebook import get_post_metrics as get_facebook_post_metrics, extract_post_id as extract_facebook_post_id
from blueprints.instagram import scrape_instagram_post
from blueprints.twitter import scrape_tweet
from blueprints.tiktok import scrape_tiktok_post

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Register blueprints
app.register_blueprint(facebook_bp)
app.register_blueprint(twitter_bp)
app.register_blueprint(instagram_bp)
app.register_blueprint(tiktok_bp)


# Helper function for Facebook URL cleanup
def clean_facebook_url(url):
    """Remove query parameters and mobile or tracking parts of a facebook link to normalize it."""
    return url.split('?')[0].replace('m.facebook.com', 'facebook.com')


# --- Main Routes ---
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze_link", methods=["POST"])
def analyze_link():
    link = request.form.get("link")
    if not link:
        flash("Please enter a link.", "error")
        return redirect(url_for("home"))

    original_link = link
    platform = None
    post_id = None
    metrics = {}

    # ---- TWITTER ----
    if "twitter.com" in link or "x.com" in link:
        platform = "Twitter"
        try:
            metrics = scrape_tweet(link)
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

    print("Platform:", platform)
    print("Post ID:", post_id)
    print("Metrics:", metrics)

    return render_template("results.html",
                           link=original_link,
                           platform=platform,
                           metrics=metrics)


if __name__ == "__main__":
    app.run(debug=True)
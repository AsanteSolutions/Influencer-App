import re
import asyncio
import pandas as pd
from flask import Flask, render_template, request
from playwright.async_api import async_playwright

app = Flask(__name__)

# ---------------------------------------------------------
# Extract Tweet ID from URL
# ---------------------------------------------------------
def extract_tweet_id(url: str):
    match = re.search(r"status/(\d+)", url)
    return match.group(1) if match else None


# ---------------------------------------------------------
# Playwright scraping function
# ---------------------------------------------------------
async def scrape_tweet(tweet_url):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(tweet_url, timeout=60000)

            # Wait for tweet container
            await page.wait_for_selector("article", timeout=15000)

            # Extract metrics
            likes = await page.locator('[data-testid="like"]').text_content()
            replies = await page.locator('[data-testid="reply"]').text_content()
            retweets = await page.locator('[data-testid="retweet"]').text_content()

            # Extract views if available
            views = "N/A"
            try:
                views = await page.locator("span:below(:text('Views'))").nth(0).text_content()
            except:
                pass

            # Extract comments
            comments = []
            comment_elements = page.locator('div[data-testid="tweetText"]')

            count = await comment_elements.count()
            for i in range(min(count, 20)):  # limit to 20 comments
                comments.append(await comment_elements.nth(i).text_content())

            await browser.close()

            return {
                "likes": likes.strip() if likes else "0",
                "replies": replies.strip() if replies else "0",
                "retweets": retweets.strip() if retweets else "0",
                "views": views,
                "comments": comments
            }

        except Exception as e:
            await browser.close()
            return {"error": str(e)}


# ---------------------------------------------------------
# Flask Routes
# ---------------------------------------------------------
@app.route("/")
def home():
    return render_template("upload_twitter.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded"

    file = request.files["file"]
    df = pd.read_csv(file)

    if "LINK" not in df.columns or "NAME" not in df.columns:
        return "CSV must contain columns: NAME and LINK"

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
                "comments": ["Invalid link"]
            })
            continue

        # Playwright must run inside an event loop
        scrape_result = asyncio.run(scrape_tweet(link))

        results.append({
            "name": name,
            "link": link,
            "likes": scrape_result.get("likes", "0"),
            "replies": scrape_result.get("replies", "0"),
            "retweets": scrape_result.get("retweets", "0"),
            "views": scrape_result.get("views", "N/A"),
            "comments": scrape_result.get("comments", [])
        })

    return render_template("results_twitter.html", results=results)


# ---------------------------------------------------------
# Run app
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5003)

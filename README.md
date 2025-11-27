# Social Media Analytics Dashboard

A professional analytics dashboard for X (Twitter), Facebook, and Instagram influencer campaigns.

## 🚀 Features

- **Unified Interface**: A single dashboard to analyze posts from X (Twitter), Facebook, and Instagram.
- **CSV Upload**: Upload a CSV file with a list of links to get a full report.
- **Single Link Analysis**: Quickly analyze a single post by pasting the link.
- **Modern UI**: A clean and modern interface for a great user experience.
- **Responsive Design**: Works on both desktop and mobile devices.
- **Error Handling**: Clear and user-friendly error messages.

## 📋 Requirements

- Python 3.7+
- Flask
- pandas
- openpyxl
- requests
- python-dotenv

## 🔧 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate  # On Windows
    # source venv/bin/activate  # On macOS/Linux
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    **Install Playwright and browsers** (required for Instagram scraping):
    ```bash
    pip install playwright
    python -m playwright install chromium
    ```

4.  **Create a `.env` file** in the root directory and add your API keys:
    ```
    TWITTER_BEARER_TOKEN=<your_twitter_bearer_token>
    FACEBOOK_ACCESS_TOKEN=<your_facebook_access_token>
    INSTAGRAM_ACCESS_TOKEN=<your_instagram_access_token>
    FLASK_SECRET_KEY=<a_super_secret_key>
    ```

## 🎯 Usage

1.  **Run the application:**
    ```bash
    python app.py
    ```

2.  **Open your browser** and go to `http://127.0.0.1:5000`.

## 📊 How It Works

### CSV Upload
- Click on the button for the social media platform you want to analyze (Facebook, Instagram, or Twitter).
- Upload a CSV file with `NAME` and `LINK` columns.
- The application will process the file and display a table of results.

### Single Link Analysis
- Paste a valid link from Facebook, Instagram, or Twitter into the input box.
- Click "Analyze".
- The application will fetch the metrics for the link and display them.

## 🔑 API Setup

### Twitter/X API
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app
3. Generate a Bearer Token
4. Add to `.env` as `TWITTER_BEARER_TOKEN`

### Facebook API
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app
3. Get a Page Access Token with appropriate permissions
4. Add to `.env` as `FACEBOOK_ACCESS_TOKEN`

### Instagram API
1. Instagram API requires a Facebook app
2. Set up Instagram Graph API or Instagram Basic Display
3. Get an access token (requires Instagram Business/Creator account)
4. Add to `.env` as `INSTAGRAM_ACCESS_TOKEN`

## 📁 Project Structure
```
.
├── app.py                          # Main Flask application
├── app_twitter.py                  # Twitter-specific routes
├── requirements.txt                # Python dependencies
├── .env                            # API credentials (not in repo)
├── templates/
│   ├── index.html                  # Main landing page
│   ├── results.html                # Unified results page for single link analysis
│   ├── upload_facebook.html        # Facebook upload page
│   ├── results_facebook.html       # Facebook results page
│   ├── upload_instagram.html       # Instagram upload page
│   ├── results_instagram.html      # Instagram results page
│   ├── upload_twitter.html         # Twitter upload page
│   ├── results_twitter.html        # Twitter results page
│   ├── error_facebook.html         # Facebook error page
│   └── error_instagram.html        # Instagram error page
└── README.md
```

## ⚠️ Important Notes

- **Rate Limits**: Be aware of API rate limits for each platform.
- **Authentication**: Ensure your access tokens have the required permissions.
- **Instagram**: Requires Business or Creator accounts for analytics.
- **Comments**: Comment fetching may require elevated API access on some platforms.
 - **Playwright**: Instagram scraping uses Playwright; ensure browsers are installed by running `playwright install` and that Playwright is in your virtualenv.

## 📝 License

This project is for internal use. Please ensure compliance with social media platform API terms of service.

# Social Media Analytics Dashboard

A Flask-based web application for analyzing social media post engagement across multiple platforms including Facebook, Instagram, Twitter/X, and TikTok.

## 🚀 Features

- **Multi-Platform Support**: Analyze posts from Facebook, Instagram, Twitter/X, and TikTok
- **CSV Batch Processing**: Upload CSV files with multiple links for bulk analysis
- **Single Link Analysis**: Quick analysis for individual post URLs
- **Comprehensive Metrics**: Track likes, comments, shares, views, and other engagement metrics
- **Modern UI**: Clean, responsive interface with platform-specific styling
- **Blueprint Architecture**: Modular Flask blueprints for scalability and maintainability

## 📋 Requirements

- Python 3.8+
- Flask
- Playwright
- pandas
- requests
- python-dotenv

## 🔧 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd "X Test Run for Influencers"
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

4.  **Install Playwright browsers:**
    ```bash
    python -m playwright install chromium
    ```

5.  **Create a `.env` file** in the root directory with your credentials:
    ```
    FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here
    FLASK_SECRET_KEY=your_secret_key_here
    ```

## 🎯 Usage

1.  **Run the application:**
    ```bash
    python app.py
    ```

2.  **Open your browser** and go to `http://127.0.0.1:5000`

### CSV Upload
1. Click on a platform button (Facebook, Instagram, Twitter, or TikTok)
2. Upload a CSV file with `NAME` and `LINK` columns
3. View comprehensive engagement metrics for all posts

**CSV Format Example:**
```csv
NAME,LINK
John Doe,https://www.facebook.com/user/posts/123456789
Jane Smith,https://twitter.com/user/status/987654321
```

### Single Link Analysis
1. On the home page, scroll to "Analyze Single Link"
2. Paste a post URL from any supported platform
3. Click "Analyze" to view engagement metrics

## 🏗 Architecture

### Blueprint Structure

The application uses Flask Blueprints for modular organization:

```
app.py                          # Main application file
blueprints/
├── __init__.py                 # Blueprint exports
├── facebook.py                 # Facebook routes and Graph API integration
├── twitter.py                  # Twitter/X routes and Playwright scraper
├── instagram.py                # Instagram routes and Playwright scraper
└── tiktok.py                   # TikTok routes and Playwright scraper
```

**Blueprint Routes:**
- Facebook: `/facebook/`
- Twitter: `/twitter/`
- Instagram: `/instagram/`
- TikTok: `/tiktok/`

### Template Organization

Templates are organized by platform:

```
templates/
├── base.html                   # Base template with shared styling
├── results_base.html           # Base template for results pages
├── index.html                  # Home page
├── results.html                # Single link analysis results
├── facebook/
│   ├── upload.html
│   ├── results.html
│   └── error.html
├── twitter/
│   ├── upload.html
│   ├── results.html
│   └── error.html
├── instagram/
│   ├── upload.html
│   ├── results.html
│   └── error.html
└── tiktok/
    ├── upload.html
    ├── results.html
    └── error.html
```

## 🔑 API Setup

### Facebook API
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app or use an existing one
3. Get a Page Access Token with permissions: `pages_read_engagement`, `pages_read_user_content`
4. Add to `.env` as `FACEBOOK_ACCESS_TOKEN`

### Twitter/Instagram/TikTok
These platforms use Playwright for web scraping (no API key required).

## 📊 Scraping Methods

| Platform | Method | Metrics Collected |
|----------|--------|-------------------|
| Facebook | Graph API | Reactions, Comments, Shares, Comment text |
| Twitter/X | Playwright | Likes, Retweets, Replies, Views |
| Instagram | Playwright | Likes, Comments |
| TikTok | Playwright | Likes, Comments, Saves, Shares |

## 🛠 Development

### Adding a New Platform

1. Create a new blueprint file in `blueprints/` (e.g., `linkedin.py`)
2. Implement scraping function or API integration
3. Create templates in `templates/platform_name/`
4. Register the blueprint in `app.py`
5. Add platform button to `templates/index.html`
6. Update the analyze_link function in `app.py`

### Customizing Styling

- Edit `templates/base.html` for global styles
- Override `{% block bg_gradient %}` in platform templates for custom colors

## ⚠️ Important Notes

- **Rate Limits**: Be aware of API rate limits for Facebook
- **Authentication**: Ensure Facebook access token has required permissions
- **Playwright Performance**: Scraping opens headless browsers and can be slow; consider caching results
- **Platform Changes**: Social media platforms may update their HTML structure, requiring scraper updates
- **Terms of Service**: Respect platform Terms of Service when scraping data

## 🐛 Troubleshooting

**Issue: "Playwright not installed" error**
```bash
python -m playwright install chromium
```

**Issue: "Facebook API error"**
- Check your Facebook Access Token in `.env`
- Verify token has necessary permissions
- Ensure token hasn't expired

**Issue: "Scraping fails"**
- Platforms may have updated their HTML structure
- Some posts may require login (not supported by default)
- Check if selectors in scraper functions need updating

## 📝 License

This project is for educational and personal use. Please ensure compliance with social media platform API terms of service.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

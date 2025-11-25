# Social Media Analytics Dashboard

Professional analytics dashboards for X (Twitter), Facebook, and Instagram influencer campaigns.

## 🚀 Features

### X (Twitter) Analytics
- Track tweet metrics (likes, replies, retweets, quotes)
- View comments/replies
- Professional purple gradient theme
- Runs on port 5000

### Facebook Analytics
- Track post metrics (reactions, comments, shares)
- Sample comment display
- Facebook blue theme
- Runs on port 5001

### Instagram Analytics
- Track post metrics (likes, comments)
- Media type identification
- Instagram gradient theme (purple-red-orange)
- Runs on port 5002

## 📋 Requirements

- Python 3.7+
- Flask
- pandas
- openpyxl
- requests
- python-dotenv

## 🔧 Installation

1. Clone or download this project

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the root directory with your API credentials:
```
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token_here
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token_here
```

## 🎯 Usage

### Running X (Twitter) Analytics
```bash
python app.py
```
Visit: http://localhost:5000

### Running Facebook Analytics
```bash
python app_facebook.py
```
Visit: http://localhost:5001

### Running Instagram Analytics
```bash
python app_instagram.py
```
Visit: http://localhost:5002

## 📊 CSV File Format

Your CSV file must contain the following columns:
- **NAME**: Influencer or campaign name
- **LINK**: Social media post URL

Example:
```csv
NAME,LINK
John Doe,https://twitter.com/user/status/1234567890
Jane Smith,https://facebook.com/page/posts/9876543210
Mike Johnson,https://instagram.com/p/ABC123xyz/
```

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

## 🎨 Features

- **Modern UI**: Professional gradient designs for each platform
- **Drag & Drop**: Easy file upload with drag-and-drop support
- **Responsive**: Mobile-friendly design
- **Error Handling**: User-friendly error messages
- **Excel Support**: Works with both CSV and Excel files (.xlsx, .xls)
- **Real-time Stats**: Auto-calculated totals and averages
- **Comment Preview**: Sample comments/replies displayed

## 📁 Project Structure

```
.
├── app.py                          # X/Twitter analytics app
├── app_facebook.py                 # Facebook analytics app
├── app_instagram.py                # Instagram analytics app
├── requirements.txt                # Python dependencies
├── .env                           # API credentials (not in repo)
├── templates/
│   ├── upload.html                # X upload page
│   ├── results.html               # X results page
│   ├── error.html                 # X error page
│   ├── upload_facebook.html       # Facebook upload page
│   ├── results_facebook.html      # Facebook results page
│   ├── error_facebook.html        # Facebook error page
│   ├── upload_instagram.html      # Instagram upload page
│   ├── results_instagram.html     # Instagram results page
│   └── error_instagram.html       # Instagram error page
└── README.md
```

## ⚠️ Important Notes

- **Rate Limits**: Be aware of API rate limits for each platform
- **Authentication**: Ensure your access tokens have the required permissions
- **Instagram**: Requires Business or Creator accounts for analytics
- **Comments**: Comment fetching may require elevated API access

## 🛠️ Troubleshooting

### "No file uploaded" error
- Make sure you're selecting a file before clicking upload

### "Missing required columns" error
- Ensure your CSV has columns named exactly "NAME" and "LINK" (case-insensitive)

### API errors
- Verify your API tokens are correct in the `.env` file
- Check if your tokens have the necessary permissions
- Ensure the post URLs are valid and accessible

## 📝 License

This project is for internal use. Please ensure compliance with social media platform API terms of service.

## 🤝 Support

For issues or questions, contact your development team.

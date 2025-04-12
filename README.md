# URL Indexing Bot

A web application that helps you submit URLs for indexing in Google and Bing search engines. This tool allows you to easily submit URLs to search engines for faster indexing and track the submission history.

![URL Indexing Bot](https://via.placeholder.com/800x400?text=URL+Indexing+Bot)

## Features

- **Multi-Platform Support**: Submit URLs to both Google and Bing search engines
- **Modern UI**: Clean, responsive interface built with Bootstrap and Font Awesome
- **Real-time Status Updates**: Track submission status with visual indicators
- **Submission History**: View and filter your submission history
- **Rate Limiting**: Built-in rate limiting to comply with API quotas
- **Error Handling**: Comprehensive error handling and user feedback
- **Lazy Loading**: Efficient loading of history records for better performance

## Project Structure

```
url-indexing-bot/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── LICENSE                 # MIT License
├── templates/              # HTML templates
│   ├── index.html          # Home page
│   ├── google.html         # Google submission page
│   ├── bing.html           # Bing submission page
│   ├── history.html        # Submission history page
│   └── error.html          # Error page
└── README.md               # This file
```

## Prerequisites

- Python 3.7 or higher
- Google Cloud Console account with Indexing API enabled
- Bing Webmaster Tools account
- API keys for both services

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/url-indexing-bot.git
   cd url-indexing-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your API keys:
   - Copy `.env.example` to `.env`
   - Add your API keys to the `.env` file

## Running the Application

### Windows Users
Simply double-click the `run.bat` file or run:
```bash
run.bat
```

### Linux/macOS Users
Make the script executable and run it:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start
Alternatively, you can start the application manually:
```bash
python run.py
```

The script will:
1. Check and install required dependencies
2. Validate your environment configuration
3. Start the Flask application
4. Open your default web browser to the application

## API Key Configuration

### Google Indexing API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Indexing API
4. Create credentials (API key)
5. Add the API key to your `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
```

### Bing Webmaster Tools
1. Go to [Bing Webmaster Tools](https://www.bing.com/webmasters)
2. Add and verify your site
3. Get your API key
4. Add the API key to your `.env` file:
```
BING_API_KEY=your_api_key_here
```

## Rate Limits

The application includes default rate limits to prevent API quota exhaustion:

- Google: 200 requests per day
- Bing: 10 requests per minute

You can customize these limits in your `.env` file:
```
GOOGLE_RATE_LIMIT=200
BING_RATE_LIMIT=10
```

## Usage

1. **Home Page**: Choose between Google and Bing indexing
2. **Submit URLs**: Enter the URL you want to submit for indexing
3. **View History**: Track your submission history with filtering options
4. **Error Handling**: The application provides clear error messages for invalid URLs or API issues

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: example@email.com 
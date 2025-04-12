import os
import json
import logging
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('bing_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('BingBot')

# Bing API Configuration
BING_API_KEY = "05fc7f0b7d6f453da9331bcb15e8d83e"  # Sabit API anahtarı
BING_API_ENDPOINT = "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch"

class BingURLTracker:
    """URL submission tracking for Bing."""
    
    def __init__(self, file_path: str = 'bing_sent_urls.json'):
        self.file_path = file_path
        self.submitted_urls = self._load_submitted_urls()
    
    def _load_submitted_urls(self) -> Dict[str, str]:
        """Load submitted URLs from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading submitted URLs: {e}")
                return {}
        return {}
    
    def _save_submitted_urls(self):
        """Save submitted URLs to file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.submitted_urls, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving submitted URLs: {e}")
    
    def can_submit_url(self, url: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Check if URL can be submitted."""
        if url not in self.submitted_urls:
            return True, None
        
        last_submission = datetime.fromisoformat(self.submitted_urls[url])
        hours_since_submission = (datetime.now() - last_submission).total_seconds() / 3600
        
        if hours_since_submission >= 24:
            return True, None
        
        remaining_hours = 24 - hours_since_submission
        return False, {
            'last_submission': last_submission.strftime('%d.%m.%Y %H:%M:%S'),
            'remaining_hours': round(remaining_hours, 1)
        }
    
    def mark_url_submitted(self, url: str):
        """Mark URL as submitted."""
        self.submitted_urls[url] = datetime.now().isoformat()
        self._save_submitted_urls()
        logger.info(f"URL marked as submitted: {url}")

def request_bing_indexing(url: str, url_tracker: BingURLTracker) -> Dict[str, Any]:
    """Request URL indexing from Bing."""
    try:
        # Check if URL can be submitted
        can_submit, status_info = url_tracker.can_submit_url(url)
        if not can_submit:
            return {
                'url': url,
                'status': 'skipped',
                'message': f"URL was submitted {status_info['remaining_hours']} hours ago. Please wait {status_info['remaining_hours']} more hours.",
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                'status_info': status_info
            }
        
        # Prepare request
        headers = {
            'Content-Type': 'application/json',
            'charset': 'utf-8'
        }
        
        data = {
            'siteUrl': url,  # Ana site URL'si
            'urlList': [url]  # İndekslenecek URL'ler
        }
        
        # Send request to Bing API
        response = requests.post(
            f"{BING_API_ENDPOINT}?apikey={BING_API_KEY}",
            headers=headers,
            json=data
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            # Check for quota limit
            if 'ErrorCode' in result and result['ErrorCode'] == 'QuotaExceeded':
                return {
                    'url': url,
                    'status': 'error',
                    'error': 'Bing API quota limit exceeded',
                    'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                }
            
            # Mark URL as submitted
            url_tracker.mark_url_submitted(url)
            
            return {
                'url': url,
                'status': 'success',
                'message': 'URL submitted successfully',
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                'response': result
            }
        elif response.status_code == 429:  # Too Many Requests
            return {
                'url': url,
                'status': 'error',
                'error': 'Bing API rate limit exceeded. Please try again later.',
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }
        else:
            error_message = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Error submitting URL to Bing: {error_message}")
            return {
                'url': url,
                'status': 'error',
                'error': error_message,
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in request_bing_indexing: {error_message}")
        return {
            'url': url,
            'status': 'error',
            'error': error_message,
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        }

if __name__ == '__main__':
    # Test the bot
    url_tracker = BingURLTracker()
    test_url = "https://example.com"
    result = request_bing_indexing(test_url, url_tracker)
    print(json.dumps(result, ensure_ascii=False, indent=2)) 
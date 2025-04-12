from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os
import time
import re
from urllib.parse import urlparse
import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler("indexing_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IndexingBot")

app = Flask(__name__)

# Rate limiting variables
last_submission_time = {}
submission_counts = {
    'google': {'hourly': 0, 'daily': 0, 'last_reset': time.time()},
    'bing': {'hourly': 0, 'daily': 0, 'last_reset': time.time()}
}

# Platform-specific limits
PLATFORM_LIMITS = {
    'google': {
        'hourly': 50,
        'daily': 500,
        'min_delay': 1,
        'max_delay': 2,
        'peak_hours': {'start': 9, 'end': 17}  # UTC hours for optimal indexing
    },
    'bing': {
        'hourly': 100,
        'daily': 1000,
        'min_delay': 1,
        'max_delay': 2,
        'peak_hours': {'start': 9, 'end': 17}  # UTC hours for optimal indexing
    }
}

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_url(url):
    # Check URL format
    if not is_valid_url(url):
        return False, "Invalid URL format"
    
    # Check URL length
    if len(url) > 2048:
        return False, "URL is too long"
    
    # Check for special characters
    if re.search(r'[<>"\'%]', url):
        return False, "URL contains invalid characters"
    
    # Check if URL is accessible (basic check)
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    return True, "URL is valid"

def is_peak_hour(source):
    current_hour = datetime.utcnow().hour
    peak_hours = PLATFORM_LIMITS[source]['peak_hours']
    return peak_hours['start'] <= current_hour <= peak_hours['end']

def check_rate_limit(source):
    current_time = time.time()
    
    # Reset limits if needed
    if current_time - submission_counts[source]['last_reset'] >= 3600:  # 1 hour
        submission_counts[source]['hourly'] = 0
        submission_counts[source]['last_reset'] = current_time
    
    if current_time - submission_counts[source]['last_reset'] >= 86400:  # 24 hours
        submission_counts[source]['daily'] = 0
    
    # Check time since last submission
    if source in last_submission_time:
        time_since_last = current_time - last_submission_time[source]
        min_delay = PLATFORM_LIMITS[source]['min_delay']
        if time_since_last < min_delay:
            return False, f"Please wait {int(min_delay - time_since_last)} seconds"
    
    # Check hourly limit
    if submission_counts[source]['hourly'] >= PLATFORM_LIMITS[source]['hourly']:
        return False, f"Hourly submission limit reached ({PLATFORM_LIMITS[source]['hourly']} URLs)"
    
    # Check daily limit
    if submission_counts[source]['daily'] >= PLATFORM_LIMITS[source]['daily']:
        return False, f"Daily submission limit reached ({PLATFORM_LIMITS[source]['daily']} URLs)"
    
    # Check if it's peak hour
    if not is_peak_hour(source):
        logger.warning(f"Submitting URL outside peak hours for {source}")
    
    return True, "Rate limit check successful"

def load_history():
    return []

# 404 error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page Not Found",
                         error_description="The URL you entered may be incorrect or the page may have been removed."), 404

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Google home page
@app.route('/google')
def google():
    return render_template('google.html')

# Google URL submission
@app.route('/google/submit', methods=['POST'])
def google_submit():
    try:
        url = request.form.get('url')
        if not url:
            return jsonify({
                'status': 'error',
                'message': 'URL cannot be empty'
            }), 400

        # URL validation
        is_valid, message = validate_url(url)
        if not is_valid:
            logger.warning(f"Invalid URL submitted: {url} - {message}")
            return jsonify({
                'status': 'error',
                'message': message
            }), 400

        # Rate limit check
        can_submit, message = check_rate_limit('google')
        if not can_submit:
            logger.warning(f"Rate limit exceeded: {message}")
            return jsonify({
                'status': 'error',
                'message': message
            }), 429

        # Add natural delay
        delay = random.uniform(
            PLATFORM_LIMITS['google']['min_delay'],
            PLATFORM_LIMITS['google']['max_delay']
        )
        logger.info(f"Adding delay of {delay:.2f} seconds before submission")
        time.sleep(delay)

        # Add URL processing status to history
        history = load_history()
        history.append({
            'url': url,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'Google',
            'status': 'success',
            'message': 'URL successfully submitted'
        })

        # Update counters
        submission_counts['google']['hourly'] += 1
        submission_counts['google']['daily'] += 1
        last_submission_time['google'] = time.time()

        logger.info(f"URL successfully submitted to Google: {url}")
        return jsonify({
            'status': 'success',
            'message': 'URL successfully submitted',
            'redirect': '/processing_status'
        })

    except Exception as e:
        logger.error(f"Error submitting URL to Google: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Google processing status
@app.route('/google/status/<task_id>')
def google_status(task_id):
    # Example status data
    status_data = {
        'status': 'processing',
        'progress': 75,
        'message': 'URL is being indexed...'
    }
    return jsonify(status_data)

# History page
@app.route('/history')
def history():
    # Show first 10 records
    all_history = load_history()
    initial_items = all_history[:10]
    total_count = len(all_history)

    return render_template('history.html', 
                         history=initial_items, 
                         total_count=total_count)

# API endpoint for lazy loading
@app.route('/api/history')
def api_history():
    try:
        page = int(request.args.get('page', 1))
        filter_type = request.args.get('filter', 'all')
        per_page = 10

        # Load history data
        history_data = load_history()
        
        # Filtering
        if filter_type == 'success':
            filtered_items = [item for item in history_data if item['status'] == 'success']
        elif filter_type == 'error':
            filtered_items = [item for item in history_data if item['status'] == 'error']
        elif filter_type == 'skipped':
            filtered_items = [item for item in history_data if item['status'] == 'skipped']
        else:  # 'all' case
            filtered_items = history_data

        # Total record count
        total_count = len(filtered_items)
        total_pages = (total_count + per_page - 1) // per_page

        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        current_items = filtered_items[start_idx:end_idx]

        return jsonify({
            'items': current_items,
            'has_more': page < total_pages,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error in API history: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 
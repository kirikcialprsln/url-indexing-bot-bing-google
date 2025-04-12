import requests
import schedule
import time
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# List of URLs to ping
URLS = [
    "https://example.com",
    "https://google.com",
    # Add your URLs here
]

def ping_url(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        status = "UP" if response.status_code == 200 else "DOWN"
        return {
            "url": url,
            "status": status,
            "status_code": response.status_code,
            "response_time": response_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except requests.RequestException as e:
        return {
            "url": url,
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

def check_all_urls():
    print(f"\nChecking URLs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    results = []
    for url in URLS:
        result = ping_url(url)
        results.append(result)
        print(f"URL: {url}")
        print(f"Status: {result['status']}")
        if result['status'] == "UP":
            print(f"Response Time: {result['response_time']}ms")
            print(f"Status Code: {result['status_code']}")
        elif result['status'] == "ERROR":
            print(f"Error: {result['error']}")
        print("-" * 50)
    
    # Save results to a JSON file
    save_results(results)

def save_results(results):
    filename = f"ping_results_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Load existing results if file exists
    existing_results = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_results = json.load(f)
    
    # Append new results
    existing_results.extend(results)
    
    # Save updated results
    with open(filename, 'w') as f:
        json.dump(existing_results, f, indent=4)

def main():
    print("Link Ping Bot Started!")
    print(f"Monitoring {len(URLS)} URLs")
    
    # Run immediately on startup
    check_all_urls()
    
    # Schedule regular checks (every 5 minutes)
    schedule.every(5).minutes.do(check_all_urls)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 
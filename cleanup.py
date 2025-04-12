#!/usr/bin/env python
"""
Cleanup script for URL Indexing Bot
This script helps prepare the project for GitHub by removing unnecessary files
and ensuring the project structure is clean.
"""

import os
import shutil
import glob

def main():
    print("Starting cleanup process for URL Indexing Bot...")
    
    # Files to remove (old versions)
    files_to_remove = [
        'web_panel.py',
        'google_indexing_bot.py',
        'bing_indexing_bot.py',
        'link_ping_bot.py',
        'web_panel.log',
        'bing_bot.log',
        'indexing_bot.log',
        'service-account.json'
    ]
    
    # Remove files
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Removed: {file}")
            except Exception as e:
                print(f"Error removing {file}: {e}")
    
    # Remove history files
    history_files = glob.glob('history_*.json')
    for file in history_files:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")
    
    # Remove sent URLs files
    sent_urls_files = glob.glob('*_sent_urls.json')
    for file in sent_urls_files:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")
    
    # Remove URL text files
    url_files = glob.glob('urls_*.txt')
    for file in url_files:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_dir)
                print(f"Removed: {pycache_dir}")
            except Exception as e:
                print(f"Error removing {pycache_dir}: {e}")
    
    print("\nCleanup completed successfully!")
    print("\nProject is now ready for GitHub.")
    print("Make sure to:")
    print("1. Review the .gitignore file")
    print("2. Check that no sensitive information is included")
    print("3. Test the application to ensure it works correctly")
    print("4. Commit your changes with a descriptive message")

if __name__ == "__main__":
    main() 
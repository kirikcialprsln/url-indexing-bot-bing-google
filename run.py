#!/usr/bin/env python
"""
Run script for URL Indexing Bot
This script helps run the application with proper environment setup.
"""

import os
import sys
import subprocess
import webbrowser
from time import sleep

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import dotenv
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install dependencies.")
        return False

def check_env_file():
    """Check if .env file exists, if not create from .env.example"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("Creating .env file from .env.example...")
            try:
                with open(".env.example", "r") as example_file:
                    example_content = example_file.read()
                
                with open(".env", "w") as env_file:
                    env_file.write(example_content)
                
                print(".env file created. Please edit it to add your API keys.")
                return True
            except Exception as e:
                print(f"Error creating .env file: {e}")
                return False
        else:
            print(".env.example file not found. Please create a .env file manually.")
            return False
    return True

def run_app():
    """Run the Flask application"""
    print("Starting URL Indexing Bot...")
    
    # Open browser after a short delay
    def open_browser():
        sleep(2)  # Wait for the server to start
        webbrowser.open("http://localhost:5000")
    
    # Start browser in a separate thread
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run the Flask application
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"Error running application: {e}")

def main():
    print("=" * 50)
    print("URL Indexing Bot - Setup and Run")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("Installing missing dependencies...")
        if not install_dependencies():
            print("Failed to install dependencies. Please install them manually.")
            sys.exit(1)
    
    # Check .env file
    if not check_env_file():
        print("Please create a .env file with your API keys before running the application.")
        sys.exit(1)
    
    # Run the application
    run_app()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python
"""
Git initialization script for URL Indexing Bot
This script helps initialize a Git repository and make the initial commit.
"""

import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error message: {e.stderr}")
        return None

def main():
    print("Initializing Git repository for URL Indexing Bot...")
    
    # Check if Git is installed
    git_version = run_command("git --version")
    if not git_version:
        print("Git is not installed or not in PATH. Please install Git and try again.")
        sys.exit(1)
    
    print(f"Using Git version: {git_version.strip()}")
    
    # Check if already a Git repository
    if os.path.exists(".git"):
        print("This directory is already a Git repository.")
        choice = input("Do you want to reinitialize? (y/n): ")
        if choice.lower() != 'y':
            print("Aborting.")
            sys.exit(0)
    
    # Initialize Git repository
    print("Initializing Git repository...")
    init_result = run_command("git init")
    if not init_result:
        print("Failed to initialize Git repository.")
        sys.exit(1)
    
    # Add all files
    print("Adding files to Git...")
    add_result = run_command("git add .")
    if not add_result:
        print("Failed to add files to Git.")
        sys.exit(1)
    
    # Make initial commit
    print("Making initial commit...")
    commit_result = run_command('git commit -m "Initial commit: URL Indexing Bot"')
    if not commit_result:
        print("Failed to make initial commit.")
        sys.exit(1)
    
    print("\nGit repository initialized successfully!")
    print("\nNext steps:")
    print("1. Create a new repository on GitHub")
    print("2. Add the remote repository:")
    print("   git remote add origin https://github.com/yourusername/url-indexing-bot.git")
    print("3. Push your code:")
    print("   git push -u origin master")
    
    # Ask if user wants to add a remote repository
    add_remote = input("\nDo you want to add a remote repository now? (y/n): ")
    if add_remote.lower() == 'y':
        remote_url = input("Enter the remote repository URL: ")
        remote_result = run_command(f"git remote add origin {remote_url}")
        if remote_result:
            print(f"Remote repository added: {remote_url}")
            
            # Ask if user wants to push to remote
            push_remote = input("Do you want to push to the remote repository now? (y/n): ")
            if push_remote.lower() == 'y':
                push_result = run_command("git push -u origin master")
                if push_result:
                    print("Code pushed to remote repository successfully!")
                else:
                    print("Failed to push code to remote repository.")
        else:
            print("Failed to add remote repository.")

if __name__ == "__main__":
    main() 
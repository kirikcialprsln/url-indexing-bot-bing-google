@echo off
echo Preparing URL Indexing Bot for GitHub...

echo.
echo Step 1: Running cleanup script...
python cleanup.py

echo.
echo Step 2: Initializing Git repository...
python init_git.py

echo.
echo GitHub preparation completed!
echo.
echo Next steps:
echo 1. Create a new repository on GitHub (https://github.com/new)
echo 2. Follow the instructions provided by the init_git.py script
echo 3. Make sure to add a license file if needed
echo 4. Update the README.md with your specific information
echo.
pause 
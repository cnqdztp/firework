@echo off
cd /d "%~dp0"

echo Interactive Fish Tank with Firework Effects
echo -------------------------------------------
echo Starting fish tracking and visual effects...

:: First, create a config.json file from config.ini for the web app
echo Creating config.json from config.ini...
python -c "import configparser, json; config = configparser.ConfigParser(); config.read('config.ini'); result = {s: dict(config.items(s)) for s in config.sections()}; open('config.json', 'w').write(json.dumps(result))"

:: Replace the standard index.html with the fixed version
echo Using fixed version of index.html...
copy /Y index_fixed.html index.html

:: Start the HTTP server
echo Starting web server on port 8080...
start cmd /k "python -m http.server 8080"

:: Wait a moment
timeout /t 2 > nul

:: Start the fish tracker
echo Starting fish tracking...
start cmd /k "python fish_tracker.py"

:: Wait a moment
timeout /t 3 > nul

:: Start Chrome in a new window (not kiosk mode for debugging)
echo Starting browser...
start chrome http://localhost:8080

echo.
echo If you encounter issues:
echo 1. Run python debug_api.py to check if the tracker API is working
echo 2. Press F12 in Chrome to view the browser console for errors
echo 3. Close all windows and try running start_simple.bat again
echo.
echo Fish tank started. Close this window to exit.

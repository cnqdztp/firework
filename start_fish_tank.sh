#!/bin/bash

# Start in background
cd "$(dirname "$0")"

# Start web server for the visual effects
python3 -m http.server 8080 &
HTTP_PID=$!

# Start fish tracker
python3 fish_tracker.py &
TRACKER_PID=$!

# Start browser in fullscreen kiosk mode
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  open -a "Google Chrome" --args --kiosk --incognito http://localhost:8080
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  chromium-browser --kiosk --incognito http://localhost:8080 &
else
  # Windows
  start chrome --kiosk --incognito http://localhost:8080
fi
BROWSER_PID=$!

# Save PIDs for clean shutdown
echo $HTTP_PID > http_server.pid
echo $TRACKER_PID > tracker.pid
echo $BROWSER_PID > browser.pid

echo "Fish tank started. Press Ctrl+C to stop."

# Wait for interrupt
trap "kill $(cat http_server.pid) $(cat tracker.pid) $(cat browser.pid 2>/dev/null); rm *.pid; exit" INT
wait
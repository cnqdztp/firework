#!/bin/bash

# Kill all processes
cd "$(dirname "$0")"
if [ -f http_server.pid ]; then
    kill $(cat http_server.pid) 2>/dev/null
    rm http_server.pid
fi

if [ -f tracker.pid ]; then
    kill $(cat tracker.pid) 2>/dev/null
    rm tracker.pid
fi

if [ -f browser.pid ]; then
    kill $(cat browser.pid) 2>/dev/null
    rm browser.pid
fi

echo "Fish tank stopped."
#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Using virtual environment"
else
    echo "No virtual environment found. Run ./setup.sh first if you haven't already."
fi

# Start the web server
echo "Starting Web Search Agent server..."
python3 web_server.py
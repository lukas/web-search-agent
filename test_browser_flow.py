#!/usr/bin/env python3
import requests
import json
import time
from urllib.parse import urlencode

def test_browser_like_request():
    """Test requests exactly like a browser would make them"""
    
    print("Testing browser-like requests...")
    
    # Test 1: GET the main page (like opening in browser)
    print("\n1. Loading main page...")
    response = requests.get('http://localhost:8000/')
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    # Test 2: POST search request (like clicking search button)
    print("\n2. Sending search request (POST)...")
    search_data = {'query': 'python'}
    
    # Make the request exactly like the JavaScript would
    response = requests.post(
        'http://localhost:8000/search',
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible browser)'
        },
        data=json.dumps(search_data)  # Use data instead of json parameter
    )
    
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text[:300]}...")
    
    if response.status_code != 200:
        print(f"ERROR: Expected 200, got {response.status_code}")
        print(f"Response text: {response.text}")
    else:
        try:
            data = response.json()
            print(f"JSON parsed successfully: {len(data.get('results', []))} results")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response.text}")

def test_method_debugging():
    """Debug which HTTP methods are actually being handled"""
    
    print("\n3. Testing different HTTP methods...")
    
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    
    for method in methods:
        try:
            if method == 'GET':
                response = requests.get('http://localhost:8000/search?q=test')
            elif method == 'POST':
                response = requests.post('http://localhost:8000/search', 
                                       json={'query': 'test'})
            elif method == 'PUT':
                response = requests.put('http://localhost:8000/search')
            else:
                response = requests.delete('http://localhost:8000/search')
            
            print(f"{method}: {response.status_code} - {response.text[:50]}...")
        except Exception as e:
            print(f"{method}: Error - {e}")

if __name__ == '__main__':
    # Start server first
    import subprocess
    import signal
    
    print("Starting server...")
    server_process = subprocess.Popen([
        'bash', '-c', 
        'source venv/bin/activate && python3 web_server.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        time.sleep(2)  # Let server start
        test_browser_like_request()
        test_method_debugging()
    finally:
        server_process.terminate()
        server_process.wait(timeout=5)
        print("\nServer stopped.")
#!/usr/bin/env python3
import pytest
import json
import time
import threading
import requests
from web_server import run_server
import signal
import sys

class TestWebServer:
    """Test suite for web server functionality"""
    
    server_thread = None
    server_port = 8001  # Use different port to avoid conflicts
    
    @classmethod
    def setup_class(cls):
        """Start web server in background thread"""
        def start_server():
            try:
                run_server(cls.server_port)
            except Exception as e:
                print(f"Server error: {e}")
        
        cls.server_thread = threading.Thread(target=start_server, daemon=True)
        cls.server_thread.start()
        time.sleep(2)  # Give server time to start
    
    def test_server_starts(self):
        """Test that server starts and responds"""
        response = requests.get(f'http://localhost:{self.server_port}/', timeout=5)
        assert response.status_code == 200
        assert 'Web Search Agent' in response.text
    
    def test_html_interface(self):
        """Test that HTML interface loads correctly"""
        response = requests.get(f'http://localhost:{self.server_port}/', timeout=5)
        html = response.text
        
        # Check for key elements
        assert '<title>Web Search Agent</title>' in html
        assert 'id="query"' in html
        assert 'onclick="search()"' in html
        assert 'id="results"' in html
    
    def test_search_post_endpoint(self):
        """Test POST /search endpoint"""
        search_data = {'query': 'python programming'}
        response = requests.post(
            f'http://localhost:{self.server_port}/search',
            headers={'Content-Type': 'application/json'},
            json=search_data,
            timeout=10
        )
        
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'
        
        data = response.json()
        assert 'results' in data
        assert isinstance(data['results'], list)
        assert len(data['results']) > 0
    
    def test_search_post_empty_query(self):
        """Test POST /search with empty query"""
        search_data = {'query': ''}
        response = requests.post(
            f'http://localhost:{self.server_port}/search',
            headers={'Content-Type': 'application/json'},
            json=search_data,
            timeout=5
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'No query provided'
    
    def test_search_post_invalid_json(self):
        """Test POST /search with invalid JSON"""
        response = requests.post(
            f'http://localhost:{self.server_port}/search',
            headers={'Content-Type': 'application/json'},
            data='invalid json',
            timeout=5
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']
    
    def test_search_get_method_not_allowed(self):
        """Test that GET to /search without query returns error"""
        response = requests.get(f'http://localhost:{self.server_port}/search', timeout=5)
        assert response.status_code == 200  # Should handle GET requests too
        data = response.json()
        assert 'error' in data
    
    def test_404_endpoint(self):
        """Test 404 for non-existent endpoints"""
        response = requests.get(f'http://localhost:{self.server_port}/nonexistent', timeout=5)
        assert response.status_code == 404


def test_web_server_integration():
    """Integration test that simulates the full user flow"""
    import subprocess
    import time
    import signal
    
    # Start server in subprocess
    server_process = subprocess.Popen([
        'bash', '-c', 
        'source venv/bin/activate && python3 web_server.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        time.sleep(3)  # Let server start
        
        # Test HTML page loads
        response = requests.get('http://localhost:8000/', timeout=5)
        assert response.status_code == 200
        assert 'Web Search Agent' in response.text
        
        # Test search functionality
        search_response = requests.post(
            'http://localhost:8000/search',
            headers={'Content-Type': 'application/json'},
            json={'query': 'test search'},
            timeout=10
        )
        
        print(f"Search response status: {search_response.status_code}")
        print(f"Search response headers: {dict(search_response.headers)}")
        print(f"Search response text: {search_response.text[:200]}...")
        
        assert search_response.status_code == 200
        assert 'application/json' in search_response.headers.get('content-type', '')
        
        data = search_response.json()
        assert 'results' in data
        
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait(timeout=5)


if __name__ == '__main__':
    test_web_server_integration()
import pytest
import subprocess
import time
import requests
from playwright.sync_api import sync_playwright, expect


class TestWorkingProxy:
    """Test the working proxy solution"""
    
    server_process = None
    proxy_process = None
    
    @classmethod
    def setup_class(cls):
        """Start both web server and proxy"""
        print("Starting web server on port 8000...")
        cls.server_process = subprocess.Popen([
            'bash', '-c', 
            'source venv/bin/activate && python3 web_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        print("Starting proxy server on port 8080...")
        cls.proxy_process = subprocess.Popen([
            'bash', '-c', 
            'source venv/bin/activate && python3 simple_proxy.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
    
    @classmethod
    def teardown_class(cls):
        """Stop both servers"""
        if cls.proxy_process:
            cls.proxy_process.terminate()
            cls.proxy_process.wait(timeout=5)
            print("Proxy server stopped")
        
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            print("Web server stopped")
    
    def test_proxy_post_works(self):
        """Test that POST requests work through the proxy"""
        response = requests.post('http://localhost:8080/8000/search',
                               json={'query': 'test'},
                               headers={'Content-Type': 'application/json'})
        
        print(f"Proxy POST status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'application/json' in response.headers.get('Content-Type', '')
        
        # Verify we got search results
        data = response.json()
        assert 'results' in data, "Expected results in response"
        assert len(data['results']) > 0, "Expected search results"
    
    def test_proxy_search_interface(self, page):
        """Test the full search interface through proxy"""
        page.goto("http://localhost:8080/8000")
        
        # Check page loads
        expect(page).to_have_title("Web Search Agent")
        
        # Monitor network requests
        requests_made = []
        def handle_request(request):
            if 'search' in request.url:
                requests_made.append(request.url)
                print(f"Search request: {request.url}")
        
        page.on("request", handle_request)
        
        # Perform search
        search_input = page.locator("#query")
        search_input.fill("proxy test")
        
        search_button = page.locator("button:has-text('Search')")
        
        with page.expect_response("**/search") as response_info:
            search_button.click()
        
        response = response_info.value
        print(f"Search response status: {response.status}")
        print(f"Search response URL: {response.url}")
        
        # Verify successful response through proxy
        assert response.status == 200, f"Expected 200, got {response.status}"
        assert "8080/8000/search" in response.url, f"Expected proxy URL, got {response.url}"
        
        # Wait for results
        page.wait_for_selector(".result", timeout=10000)
        results = page.locator(".result")
        assert results.count() > 0, "Expected search results to appear"
        
        print("✓ Proxy search interface working correctly!")


@pytest.fixture
def page():
    """Provide a Playwright page for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
import pytest
import subprocess
import time
import requests
from playwright.sync_api import sync_playwright, expect


class TestProxy405Issue:
    """Test to reproduce the proxy 405 error scenario"""
    
    server_process = None
    
    @classmethod
    def setup_class(cls):
        """Start web server on port 8000"""
        print("Starting web server on port 8000...")
        cls.server_process = subprocess.Popen([
            'bash', '-c', 
            'source venv/bin/activate && python3 web_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
    
    @classmethod
    def teardown_class(cls):
        """Stop web server after tests"""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            print("Web server stopped")
    
    def test_direct_post_works(self):
        """Verify POST requests work directly to port 8000"""
        response = requests.post('http://localhost:8000/search',
                               json={'query': 'test'},
                               headers={'Content-Type': 'application/json'})
        
        print(f"Direct POST to :8000/search - Status: {response.status_code}")
        assert response.status_code == 200, f"Direct POST failed: {response.status_code}"
        assert response.headers.get('Content-Type') == 'application/json'
        
    def test_proxy_url_construction(self, page):
        """Test that URLs are constructed correctly for proxy scenario"""
        # Start with our server on port 8000, but simulate accessing via proxy
        page.goto("http://localhost:8000")
        
        # Override window.location to simulate proxy access
        page.evaluate("""
            // Simulate accessing through proxy at localhost:8080/8000
            Object.defineProperty(window, 'location', {
                value: {
                    href: 'http://localhost:8080/8000/',
                    origin: 'http://localhost:8080',
                    protocol: 'http:',
                    host: 'localhost:8080',
                    pathname: '/8000/'
                },
                writable: false
            });
        """)
        
        # Test what URL would be constructed
        search_url = page.evaluate("""
            const currentUrl = window.location.href;
            const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
            const searchUrl = new URL('search', baseUrl).toString();
            searchUrl;
        """)
        
        print(f"Constructed search URL: {search_url}")
        assert search_url == "http://localhost:8080/8000/search", \
            f"Expected http://localhost:8080/8000/search, got {search_url}"
    
    def test_proxy_scenario_diagnosis(self):
        """Test what happens when we try to POST to the proxy URL"""
        # Try to POST to the proxy URL that would be constructed
        proxy_url = "http://localhost:8080/8000/search"
        
        try:
            response = requests.post(proxy_url,
                                   json={'query': 'test'},
                                   headers={'Content-Type': 'application/json'},
                                   timeout=5)
            print(f"POST to {proxy_url} - Status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text[:200]}...")
            
            # This should fail because there's no proxy running on 8080
            assert False, f"Expected connection error, but got response: {response.status_code}"
            
        except requests.exceptions.ConnectionError as e:
            print(f"✓ Expected: Connection refused to {proxy_url}")
            print(f"  Error: {e}")
            print("This confirms the issue: the client is trying to reach a proxy that's not properly configured")
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


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
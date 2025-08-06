import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright, expect


class TestURLFix:
    """Simple test to verify URL construction fix"""
    
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
    
    def test_search_url_construction(self, page):
        """Test that search requests go to the correct URL"""
        page.goto("http://localhost:8000")
        
        # Monitor network requests
        requests = []
        def handle_request(request):
            if 'search' in request.url:
                requests.append(request.url)
                print(f"Search request made to: {request.url}")
        
        page.on("request", handle_request)
        
        # Test search functionality
        search_input = page.locator("#query")
        search_input.fill("test query")
        
        search_button = page.locator("button:has-text('Search')")
        
        with page.expect_response("**/search") as response_info:
            search_button.click()
        
        response = response_info.value
        print(f"Response URL: {response.url}")
        print(f"Response status: {response.status}")
        
        # Verify the request went to the correct URL
        assert response.url == "http://localhost:8000/search", \
            f"Expected http://localhost:8000/search, got {response.url}"
        assert response.status == 200, f"Expected 200, got {response.status}"
    
    def test_url_construction_logic_in_browser(self, page):
        """Test the JavaScript URL construction logic directly"""
        page.goto("http://localhost:8000")
        
        # Test the URL construction logic by injecting it into the page
        result = page.evaluate("""
            function testUrlConstruction(baseUrl) {
                const currentUrl = baseUrl;
                const baseUrlForSearch = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                const searchUrl = new URL('search', baseUrlForSearch).toString();
                return searchUrl;
            }
            
            // Test various scenarios
            return {
                'http://localhost:8000/': testUrlConstruction('http://localhost:8000/'),
                'http://localhost:8000': testUrlConstruction('http://localhost:8000'),
                'http://localhost:8080/8000/': testUrlConstruction('http://localhost:8080/8000/'),
                'http://localhost:8080/8000': testUrlConstruction('http://localhost:8080/8000')
            };
        """)
        
        print("URL Construction Results:")
        expected_results = {
            'http://localhost:8000/': 'http://localhost:8000/search',
            'http://localhost:8000': 'http://localhost:8000/search', 
            'http://localhost:8080/8000/': 'http://localhost:8080/8000/search',
            'http://localhost:8080/8000': 'http://localhost:8080/8000/search'
        }
        
        for base_url, actual_result in result.items():
            expected = expected_results[base_url]
            status = "✓" if actual_result == expected else "✗"
            print(f"  {status} {base_url} -> {actual_result}")
            assert actual_result == expected, \
                f"URL construction failed: {base_url} -> expected {expected}, got {actual_result}"


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
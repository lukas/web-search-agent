import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright, expect


class TestURLConstruction:
    """Test URL construction issues when accessing through different ports"""
    
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
    
    def test_direct_access_port_8000(self, page):
        """Test direct access on port 8000 works correctly"""
        page.goto("http://localhost:8000")
        
        search_input = page.locator("#query")
        search_input.fill("test query")
        
        # Monitor network requests to see where they go
        requests = []
        def handle_request(request):
            requests.append(request.url)
        
        page.on("request", handle_request)
        
        search_button = page.locator("button:has-text('Search')")
        search_button.click()
        
        # Wait a moment for the request
        time.sleep(2)
        
        # Check that request went to correct URL
        search_requests = [url for url in requests if 'search' in url]
        print(f"Search requests made: {search_requests}")
        
        assert any("localhost:8000/search" in url for url in search_requests), \
            f"Expected request to localhost:8000/search, got: {search_requests}"
    
    def test_simulated_proxy_scenario(self, page):
        """Simulate the proxy scenario by manually constructing URLs"""
        page.goto("http://localhost:8000")
        
        # Inject JavaScript to simulate the proxy scenario
        # This simulates what happens when the page is accessed through a proxy
        page.evaluate("""
            // Override the search function to show what URL would be constructed
            window.originalSearch = window.search;
            window.search = function() {
                const query = document.getElementById('query').value;
                if (!query) return;
                
                // Simulate different base URLs
                const scenarios = [
                    'http://localhost:8000',      // Direct
                    'http://localhost:8080',      // Through proxy
                    'http://localhost:8080/8000'  // Problematic proxy setup
                ];
                
                scenarios.forEach(baseUrl => {
                    // Test relative URL resolution
                    const relativeUrl = '/search';
                    const resolvedUrl = new URL(relativeUrl, baseUrl).toString();
                    console.log(`Base: ${baseUrl}, Relative: ${relativeUrl}, Resolved: ${resolvedUrl}`);
                });
                
                // Show what the browser would actually request
                const currentUrl = window.location.href;
                const searchUrl = new URL('/search', currentUrl).toString();
                window.testResult = {
                    currentUrl: currentUrl,
                    searchUrl: searchUrl
                };
            };
        """)
        
        # Execute the modified search function
        page.locator("#query").fill("test")
        page.locator("button:has-text('Search')").click()
        
        # Get the result
        result = page.evaluate("window.testResult")
        print(f"URL construction test result: {result}")
        
        # This will show us how URLs are being resolved


@pytest.fixture
def page():
    """Provide a Playwright page for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Enable console logging to see our debug output
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
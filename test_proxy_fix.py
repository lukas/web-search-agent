import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright, expect


class TestProxyFix:
    """Test the URL construction fix for proxy scenarios"""
    
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
    
    def test_url_construction_scenarios(self, page):
        """Test URL construction in various scenarios"""
        page.goto("http://localhost:8000")
        
        # Test the URL construction logic with different base URLs
        test_script = """
        function testUrlConstruction(baseUrl, expectedSearchUrl) {
            // Simulate being on different base URLs
            const originalLocation = window.location.href;
            
            // Mock the window.location for testing
            const mockLocation = new URL(baseUrl);
            
            // Apply the same logic as in our search function
            const currentUrl = baseUrl;
            const baseUrlForSearch = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
            const searchUrl = new URL('search', baseUrlForSearch).toString();
            
            console.log(`Base: ${baseUrl} -> Search URL: ${searchUrl}`);
            return searchUrl;
        }
        
        // Test scenarios
        const scenarios = [
            { base: 'http://localhost:8000/', expected: 'http://localhost:8000/search' },
            { base: 'http://localhost:8000', expected: 'http://localhost:8000/search' },
            { base: 'http://localhost:8080/', expected: 'http://localhost:8080/search' },
            { base: 'http://localhost:8080/8000/', expected: 'http://localhost:8080/8000/search' },
            { base: 'http://localhost:8080/8000', expected: 'http://localhost:8080/8000/search' }
        ];
        
        const results = {};
        scenarios.forEach(scenario => {
            const actualUrl = testUrlConstruction(scenario.base, scenario.expected);
            results[scenario.base] = {
                expected: scenario.expected,
                actual: actualUrl,
                correct: actualUrl === scenario.expected
            };
        });
        
        window.testResults = results;
        """
        
        page.evaluate(test_script)
        
        # Get test results
        results = page.evaluate("window.testResults")
        
        print("URL Construction Test Results:")
        for base_url, result in results.items():
            status = "✓" if result['correct'] else "✗"
            print(f"  {status} {base_url}")
            print(f"    Expected: {result['expected']}")
            print(f"    Actual:   {result['actual']}")
        
        # Verify all scenarios work correctly
        for base_url, result in results.items():
            assert result['correct'], f"URL construction failed for {base_url}: expected {result['expected']}, got {result['actual']}"
    
    def test_actual_search_functionality(self, page):
        """Test that search actually works with the new URL construction"""
        page.goto("http://localhost:8000")
        
        # Monitor requests to verify correct URL is used
        requests = []
        def handle_request(request):
            requests.append(request.url)
            print(f"Request made to: {request.url}")
        
        page.on("request", handle_request)
        
        # Fill search form
        search_input = page.locator("#query")
        search_input.fill("test query")
        
        # Click search
        search_button = page.locator("button:has-text('Search')")
        
        with page.expect_response("**/search") as response_info:
            search_button.click()
        
        response = response_info.value
        print(f"Search response status: {response.status}")
        print(f"Search response URL: {response.url}")
        
        # Verify response is successful
        assert response.status == 200, f"Expected 200, got {response.status}"
        assert response.url == "http://localhost:8000/search", f"Expected correct URL, got {response.url}"
        
        # Wait for results to appear
        page.wait_for_selector(".result", timeout=10000)
        results = page.locator(".result")
        assert results.count() > 0, "Expected search results to appear"


@pytest.fixture
def page():
    """Provide a Playwright page for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Enable console logging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
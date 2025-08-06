import pytest
import subprocess
import time
import requests
from playwright.sync_api import sync_playwright, expect


class TestHTTP405Error:
    """Playwright tests to reproduce and verify HTTP 405 errors"""
    
    server_process = None
    
    @classmethod
    def setup_class(cls):
        """Start web server before tests"""
        print("Starting web server for 405 error tests...")
        cls.server_process = subprocess.Popen([
            'bash', '-c', 
            'source venv/bin/activate && python3 web_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)  # Give server time to start
    
    @classmethod
    def teardown_class(cls):
        """Stop web server after tests"""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            print("Web server stopped")
    
    def test_unsupported_method_put(self):
        """Test PUT request to /search endpoint should return 405"""
        try:
            response = requests.put('http://localhost:8000/search', 
                                  json={'query': 'test'}, 
                                  timeout=5)
            print(f"PUT /search status: {response.status_code}")
            print(f"PUT /search response: {response.text}")
            assert response.status_code == 405, f"Expected 405, got {response.status_code}"
            assert 'Allow' in response.headers, "Expected Allow header in 405 response"
            print(f"Allow header: {response.headers.get('Allow')}")
        except requests.exceptions.RequestException as e:
            print(f"PUT request failed: {e}")
            assert False, "PUT request should have returned 405, not failed"
    
    def test_unsupported_method_delete(self):
        """Test DELETE request to /search endpoint should return 405"""
        try:
            response = requests.delete('http://localhost:8000/search', timeout=5)
            print(f"DELETE /search status: {response.status_code}")
            assert response.status_code == 405, f"Expected 405, got {response.status_code}"
        except requests.exceptions.RequestException as e:
            print(f"DELETE request failed: {e}")
            assert False, "DELETE request should have returned 405, not failed"
    
    def test_unsupported_method_patch(self):
        """Test PATCH request to /search endpoint should return 405"""
        try:
            response = requests.patch('http://localhost:8000/search', 
                                    json={'query': 'test'}, 
                                    timeout=5)
            print(f"PATCH /search status: {response.status_code}")
            assert response.status_code == 405, f"Expected 405, got {response.status_code}"
        except requests.exceptions.RequestException as e:
            print(f"PATCH request failed: {e}")
            assert False, "PATCH request should have returned 405, not failed"
    
    def test_playwright_search_with_method_not_allowed(self, page):
        """Test using Playwright to trigger 405 error through browser behavior"""
        page.goto("http://localhost:8000")
        
        # Inject custom JavaScript to make a PUT request
        script = """
        fetch('/search', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: 'test' })
        })
        .then(response => {
            window.testResult = {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            };
        })
        .catch(error => {
            window.testResult = { error: error.message };
        });
        """
        
        page.evaluate(script)
        
        # Wait for the request to complete
        page.wait_for_function("window.testResult !== undefined")
        
        # Get the result
        result = page.evaluate("window.testResult")
        print(f"Playwright PUT request result: {result}")
        
        # Check if we got a 405 error
        if 'status' in result:
            assert result['status'] == 405, f"Expected 405, got {result['status']}"
        else:
            assert False, f"Request failed: {result.get('error', 'Unknown error')}"
    
    def test_direct_search_works(self, page):
        """Verify normal POST search still works"""
        page.goto("http://localhost:8000")
        
        # Enter search query
        search_input = page.locator("#query")
        search_input.fill("test query")
        
        # Click search button
        search_button = page.locator("button:has-text('Search')")
        
        # Wait for search to complete and results to appear
        with page.expect_response("**/search") as response_info:
            search_button.click()
        
        # Check that we got a successful response
        response = response_info.value
        print(f"Normal search status: {response.status}")
        assert response.status == 200, f"Expected 200, got {response.status}"


@pytest.fixture
def page():
    """Provide a Playwright page for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
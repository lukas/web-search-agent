import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright, expect

class TestFailedFetch:
    """Playwright test specifically for the 'failed to fetch' error"""
    
    server_process = None
    
    @classmethod
    def setup_class(cls):
        """Start web server before tests"""
        print("Starting web server for failed fetch tests...")
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
    
    def test_search_shows_searching_then_results(self, page):
        """Test that search shows 'Searching...' then results"""
        page.goto("http://localhost:8000")
        
        # Enter search query
        search_input = page.locator("#query")
        search_input.fill("python programming")
        
        # Click search button
        search_button = page.locator("button:has-text('Search')")
        search_button.click()
        
        # Should immediately show "Searching..."
        expect(page.locator(".loading")).to_be_visible()
        expect(page.locator(".loading")).to_contain_text("Searching...")
        
        # Wait for search to complete
        page.wait_for_selector(".result", timeout=15000)
        
        # Loading should disappear
        expect(page.locator(".loading")).not_to_be_visible()
        
        # Should have results
        expect(page.locator(".result")).to_be_visible()
    
    def test_search_failed_to_fetch_scenario(self, page):
        """Test scenario that reproduces 'failed to fetch' error"""
        page.goto("http://localhost:8000")
        
        # Monitor network requests
        network_requests = []
        network_responses = []
        
        def handle_request(request):
            network_requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers)
            })
            print(f"Request: {request.method} {request.url}")
        
        def handle_response(response):
            network_responses.append({
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers)
            })
            print(f"Response: {response.status} {response.url}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # Enter search query
        search_input = page.locator("#query")
        search_input.fill("test search")
        
        # Click search and wait for loading
        search_button = page.locator("button:has-text('Search')")
        search_button.click()
        
        # Check for loading state
        expect(page.locator(".loading")).to_be_visible()
        
        # Wait up to 20 seconds for either results or error
        try:
            page.wait_for_selector(".result", timeout=20000)
            print("✓ Results appeared")
            
            # Check if we got results or error
            results = page.locator(".result")
            if results.count() > 0:
                first_result_text = results.first.inner_text()
                if "Error:" in first_result_text:
                    print(f"Got error result: {first_result_text}")
                else:
                    print(f"Got successful results: {results.count()} items")
            
        except Exception as e:
            print(f"Timeout waiting for results: {e}")
            
            # Check what's in the results div
            results_content = page.locator("#results").inner_html()
            print(f"Results div content: {results_content}")
        
        # Print network activity
        print(f"\nNetwork requests: {len(network_requests)}")
        for req in network_requests:
            print(f"  {req['method']} {req['url']}")
            
        print(f"\nNetwork responses: {len(network_responses)}")
        for resp in network_responses:
            print(f"  {resp['status']} {resp['url']}")
            
        # Check for any console errors
        def handle_console(msg):
            print(f"Console {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
    
    def test_server_availability(self, page):
        """Test that server is actually responding"""
        page.goto("http://localhost:8000")
        
        # Page should load
        expect(page).to_have_title("Web Search Agent")
        
        # Test direct API call via page.evaluate
        api_result = page.evaluate("""
            async () => {
                try {
                    const response = await fetch('/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query: 'test'})
                    });
                    
                    return {
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries()),
                        body: await response.text()
                    };
                } catch (error) {
                    return {
                        error: error.message,
                        name: error.name
                    };
                }
            }
        """)
        
        print(f"Direct API test result: {api_result}")
        
        if 'error' in api_result:
            print(f"❌ API call failed: {api_result['error']}")
        else:
            print(f"✓ API call succeeded: {api_result['status']}")
    
    def test_browser_console_errors(self, page):
        """Capture any browser console errors during search"""
        console_messages = []
        
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': f"{msg.location.get('url', '')}:{msg.location.get('line_number', '')}"
            })
        
        page.on("console", handle_console)
        
        page.goto("http://localhost:8000")
        
        # Perform search
        search_input = page.locator("#query")
        search_input.fill("test console errors")
        
        search_button = page.locator("button:has-text('Search')")
        search_button.click()
        
        # Wait a bit for any errors to appear
        time.sleep(5)
        
        # Print all console messages
        print(f"\nConsole messages captured: {len(console_messages)}")
        for msg in console_messages:
            print(f"  {msg['type']}: {msg['text']} at {msg['location']}")
        
        # Check for specific error types
        errors = [msg for msg in console_messages if msg['type'] == 'error']
        if errors:
            print(f"❌ Found {len(errors)} console errors")
            for error in errors:
                print(f"  ERROR: {error['text']}")
        else:
            print("✓ No console errors found")


@pytest.fixture
def page():
    """Provide a Playwright page for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless for container environment
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
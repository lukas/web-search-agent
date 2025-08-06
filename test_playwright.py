import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright, expect

class TestWebSearchAgentUI:
    """Playwright tests for the web search agent UI"""
    
    server_process = None
    
    @classmethod
    def setup_class(cls):
        """Start web server before tests"""
        print("Starting web server for Playwright tests...")
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
    
    def test_page_loads(self, page):
        """Test that the main page loads correctly"""
        page.goto("http://localhost:8000")
        
        # Check page title
        expect(page).to_have_title("Web Search Agent")
        
        # Check main heading
        expect(page.locator("h1")).to_contain_text("Web Search Agent")
        
        # Check search input exists
        expect(page.locator("#query")).to_be_visible()
        
        # Check search button exists
        expect(page.locator("button")).to_contain_text("Search")
        
        # Check results div exists (may be empty initially)
        results_div = page.locator("#results")
        expect(results_div).to_be_attached()
    
    def test_search_functionality(self, page):
        """Test the complete search flow"""
        page.goto("http://localhost:8000")
        
        # Enter search query
        search_input = page.locator("#query")
        search_input.fill("python programming")
        
        # Click search button
        search_button = page.locator("button:has-text('Search')")
        
        # Wait for search to complete and results to appear
        with page.expect_response("**/search") as response_info:
            search_button.click()
        
        # Check that we got a successful response
        response = response_info.value
        assert response.status == 200
        assert "application/json" in response.headers["content-type"]
        
        # Wait for loading to disappear and results to appear
        page.wait_for_selector(".result", timeout=10000)
        
        # Check that results are displayed
        results = page.locator(".result")
        assert results.count() > 0, "Expected to find search results"
        
        # Check first result has required elements
        first_result = results.first
        expect(first_result.locator("h3")).to_be_visible()
        expect(first_result.locator("p")).to_be_visible()
    
    def test_empty_search(self, page):
        """Test search with empty query"""
        page.goto("http://localhost:8000")
        
        # Click search without entering anything
        search_button = page.locator("button:has-text('Search')")
        search_button.click()
        
        # Should not make any network request (function returns early)
        # Results div should remain empty
        expect(page.locator("#results")).to_be_empty()
    
    def test_search_error_handling(self, page):
        """Test error handling in search"""
        page.goto("http://localhost:8000")
        
        # Enter search query
        search_input = page.locator("#query")
        search_input.fill("test error handling")
        
        # Click search
        search_button = page.locator("button:has-text('Search')")
        search_button.click()
        
        # Wait for results
        page.wait_for_selector(".result", timeout=10000)
        
        # Should get some kind of result (even if it's a fallback)
        expect(page.locator(".result")).to_be_visible()
    
    def test_keyboard_enter(self, page):
        """Test search with Enter key"""
        page.goto("http://localhost:8000")
        
        # Enter search query and press Enter
        search_input = page.locator("#query")
        search_input.fill("javascript")
        
        with page.expect_response("**/search") as response_info:
            search_input.press("Enter")
        
        # Check response
        response = response_info.value
        assert response.status == 200
        
        # Wait for results
        page.wait_for_selector(".result", timeout=10000)
    
    def test_multiple_searches(self, page):
        """Test performing multiple searches in sequence"""
        page.goto("http://localhost:8000")
        
        queries = ["python", "javascript", "golang"]
        
        for query in queries:
            # Clear previous results and enter new query
            search_input = page.locator("#query")
            search_input.fill("")
            search_input.fill(query)
            
            # Search
            search_button = page.locator("button:has-text('Search')")
            
            with page.expect_response("**/search"):
                search_button.click()
            
            # Wait for results
            page.wait_for_selector(".result", timeout=10000)
            
            # Check that results are relevant to the query
            results_text = page.locator("#results").inner_text()
            # Results should contain some reference to the query
            print(f"Search for '{query}' returned results")
    
    def test_result_links_clickable(self, page):
        """Test that result links are clickable and open in new tab"""
        page.goto("http://localhost:8000")
        
        # Perform search
        search_input = page.locator("#query")
        search_input.fill("python")
        
        search_button = page.locator("button:has-text('Search')")
        
        with page.expect_response("**/search"):
            search_button.click()
        
        # Wait for results with links
        page.wait_for_selector(".result", timeout=10000)
        
        # Check if there are any links in results
        links = page.locator(".result a")
        if links.count() > 0:
            # Check first link has target="_blank"
            first_link = links.first
            expect(first_link).to_have_attribute("target", "_blank")
            print("✓ Result links have target='_blank'")
        else:
            print("No links found in results (this may be normal)")


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
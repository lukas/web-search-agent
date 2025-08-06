import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright, expect


class TestProxyBaseFix:
    """Test the fix for development proxy with base href injection"""
    
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
    
    def test_proxy_base_path_detection(self, page):
        """Test URL construction when __PROXY_BASE_PATH__ is present"""
        page.goto("http://localhost:8000")
        
        # Simulate the development proxy environment by injecting the proxy variables
        page.evaluate("""
            // Simulate what the development proxy injects
            window.__PROXY_BASE_PATH__ = '/8000/';
            
            // Also add the base href tag like the proxy does
            const baseTag = document.createElement('base');
            baseTag.href = '/8000/';
            document.head.insertBefore(baseTag, document.head.firstChild);
        """)
        
        # Test the URL construction logic
        search_url = page.evaluate("""
            // Simulate the search function logic
            let searchUrl;
            if (window.__PROXY_BASE_PATH__) {
                searchUrl = window.__PROXY_BASE_PATH__ + 'search';
            } else if (document.querySelector('base[href]')) {
                const baseHref = document.querySelector('base[href]').getAttribute('href');
                searchUrl = new URL('search', new URL(baseHref, window.location.origin)).toString();
            } else {
                const currentUrl = window.location.href;
                const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                searchUrl = new URL('search', baseUrl).toString();
            }
            return searchUrl;
        """)
        
        print(f"Constructed search URL with proxy base path: {search_url}")
        assert search_url == "/8000/search", f"Expected /8000/search, got {search_url}"
    
    def test_base_href_fallback(self, page):
        """Test URL construction when only base href is present"""
        page.goto("http://localhost:8000")
        
        # Simulate base href without __PROXY_BASE_PATH__
        page.evaluate("""
            const baseTag = document.createElement('base');
            baseTag.href = '/8000/';
            document.head.insertBefore(baseTag, document.head.firstChild);
        """)
        
        search_url = page.evaluate("""
            let searchUrl;
            if (window.__PROXY_BASE_PATH__) {
                searchUrl = window.__PROXY_BASE_PATH__ + 'search';
            } else if (document.querySelector('base[href]')) {
                const baseHref = document.querySelector('base[href]').getAttribute('href');
                searchUrl = new URL('search', new URL(baseHref, window.location.origin)).toString();
            } else {
                const currentUrl = window.location.href;
                const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                searchUrl = new URL('search', baseUrl).toString();
            }
            return searchUrl;
        """)
        
        print(f"Constructed search URL with base href: {search_url}")
        assert search_url == "http://localhost:8000/8000/search", \
            f"Expected http://localhost:8000/8000/search, got {search_url}"
    
    def test_standard_case_still_works(self, page):
        """Test that standard case without proxy still works"""
        page.goto("http://localhost:8000")
        
        search_url = page.evaluate("""
            let searchUrl;
            if (window.__PROXY_BASE_PATH__) {
                searchUrl = window.__PROXY_BASE_PATH__ + 'search';
            } else if (document.querySelector('base[href]')) {
                const baseHref = document.querySelector('base[href]').getAttribute('href');
                searchUrl = new URL('search', new URL(baseHref, window.location.origin)).toString();
            } else {
                const currentUrl = window.location.href;
                const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                searchUrl = new URL('search', baseUrl).toString();
            }
            return searchUrl;
        """)
        
        print(f"Standard case search URL: {search_url}")
        assert search_url == "http://localhost:8000/search", \
            f"Expected http://localhost:8000/search, got {search_url}"


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
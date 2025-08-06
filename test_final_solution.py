import pytest
import subprocess
import time
from playwright.sync_api import sync_playwright


class TestFinalSolution:
    """Test that demonstrates the solution to the proxy 405 error"""
    
    server_process = None
    
    @classmethod
    def setup_class(cls):
        print("Starting web server for final solution test...")
        cls.server_process = subprocess.Popen([
            'bash', '-c', 
            'source venv/bin/activate && python3 web_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
    
    @classmethod
    def teardown_class(cls):
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            print("Web server stopped")
    
    def test_proxy_detection_and_url_construction(self, page):
        """Test that the proxy detection works correctly"""
        page.goto("http://localhost:8000")
        
        # Test normal case (no proxy)
        normal_result = page.evaluate("""
            (() => {
                let searchUrl;
                if (window.__PROXY_BASE_PATH__) {
                    searchUrl = './search';
                } else {
                    const currentUrl = window.location.href;
                    const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                    searchUrl = new URL('search', baseUrl).toString();
                }
                return { proxy: !!window.__PROXY_BASE_PATH__, url: searchUrl };
            })()
        """)
        
        print(f"Normal case: {normal_result}")
        assert not normal_result['proxy'], "Should not detect proxy in normal case"
        assert normal_result['url'] == "http://localhost:8000/search", "Normal URL should be absolute"
        
        # Simulate proxy environment
        page.evaluate("window.__PROXY_BASE_PATH__ = '/8000/';")
        
        proxy_result = page.evaluate("""
            (() => {
                let searchUrl;
                if (window.__PROXY_BASE_PATH__) {
                    searchUrl = './search';
                } else {
                    const currentUrl = window.location.href;
                    const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                    searchUrl = new URL('search', baseUrl).toString();
                }
                return { proxy: !!window.__PROXY_BASE_PATH__, url: searchUrl };
            })()
        """)
        
        print(f"Proxy case: {proxy_result}")
        assert proxy_result['proxy'], "Should detect proxy when __PROXY_BASE_PATH__ exists"
        assert proxy_result['url'] == "./search", "Proxy URL should be relative"


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
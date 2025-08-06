import pytest
import subprocess
import time
import requests
from playwright.sync_api import sync_playwright, expect


class TestCORSInvestigation:
    """Investigate if CORS is blocking POST requests"""
    
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
    
    def test_cors_preflight_request(self):
        """Test CORS preflight (OPTIONS) request to the proxy endpoint"""
        print("\n=== Testing CORS preflight to proxy URL ===")
        
        try:
            # Test OPTIONS request to the problematic proxy URL
            response = requests.options('http://localhost:8080/8000/search',
                                      headers={
                                          'Origin': 'http://localhost:8080',
                                          'Access-Control-Request-Method': 'POST',
                                          'Access-Control-Request-Headers': 'Content-Type'
                                      })
            
            print(f"OPTIONS to proxy URL - Status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text}")
            
            # Check for CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Allow': response.headers.get('Allow')
            }
            print(f"CORS-related headers: {cors_headers}")
            
        except requests.exceptions.RequestException as e:
            print(f"OPTIONS request failed: {e}")
    
    def test_cors_preflight_direct_server(self):
        """Test CORS preflight to the direct server (port 8000)"""
        print("\n=== Testing CORS preflight to direct server ===")
        
        response = requests.options('http://localhost:8000/search',
                                  headers={
                                      'Origin': 'http://localhost:8080',
                                      'Access-Control-Request-Method': 'POST',
                                      'Access-Control-Request-Headers': 'Content-Type'
                                  })
        
        print(f"OPTIONS to direct server - Status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Our server should support OPTIONS and return CORS headers
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check CORS headers
        assert response.headers.get('Access-Control-Allow-Origin') == '*', \
            f"Expected CORS origin *, got {response.headers.get('Access-Control-Allow-Origin')}"
        assert 'POST' in response.headers.get('Access-Control-Allow-Methods', ''), \
            f"Expected POST in allowed methods, got {response.headers.get('Access-Control-Allow-Methods')}"
    
    def test_cross_origin_post_simulation(self, page):
        """Simulate a cross-origin POST request scenario"""
        print("\n=== Simulating cross-origin POST scenario ===")
        
        # Go to the direct server page
        page.goto("http://localhost:8000")
        
        # Simulate making a cross-origin request (as if from a different domain/port)
        result = page.evaluate("""
            async function testCrossOriginPOST() {
                try {
                    // Simulate the exact scenario: page loaded from 8080, making request to 8080/8000/search
                    const response = await fetch('http://localhost:8080/8000/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Origin': 'http://localhost:8080'
                        },
                        body: JSON.stringify({ query: 'cors test' })
                    });
                    
                    return {
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries()),
                        corsError: false
                    };
                } catch (error) {
                    return {
                        error: error.message,
                        corsError: error.message.includes('CORS') || error.message.includes('fetch')
                    };
                }
            }
            
            return await testCrossOriginPOST();
        """)
        
        print(f"Cross-origin POST result: {result}")
        
        if 'error' in result:
            if result.get('corsError'):
                print("✓ CORS error detected in browser")
            else:
                print(f"Non-CORS error: {result['error']}")
        else:
            print(f"Request succeeded with status: {result['status']}")
    
    def test_same_origin_vs_cross_origin(self, page):
        """Compare same-origin vs cross-origin behavior"""
        print("\n=== Comparing same-origin vs cross-origin ===")
        
        page.goto("http://localhost:8000")
        
        # Test same-origin request (should work)
        same_origin_result = page.evaluate("""
            fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: 'same origin test' })
            })
            .then(response => ({ status: response.status, success: true }))
            .catch(error => ({ error: error.message, success: false }));
        """)
        
        page.wait_for_function("arguments[0]", same_origin_result)
        same_origin_final = page.evaluate("arguments[0]", same_origin_result)
        
        print(f"Same-origin request: {same_origin_final}")


@pytest.fixture
def page():
    """Provide a Playwright page for tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Enable console logging for debugging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        yield page
        browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
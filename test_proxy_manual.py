#!/usr/bin/env python3
"""
Manual test to demonstrate the URL construction fix for proxy scenarios
"""

def test_url_construction():
    """Test the URL construction logic that's now used in the web interface"""
    
    def construct_search_url(base_url):
        """Simulate the JavaScript URL construction logic"""
        from urllib.parse import urljoin
        
        # Simulate JavaScript: baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/'
        if base_url.endswith('/'):
            base_for_search = base_url
        else:
            base_for_search = base_url + '/'
        
        # Simulate JavaScript: new URL('search', baseUrl).toString()
        search_url = urljoin(base_for_search, 'search')
        return search_url
    
    # Test scenarios
    test_cases = [
        ("http://localhost:8000", "http://localhost:8000/search"),
        ("http://localhost:8000/", "http://localhost:8000/search"), 
        ("http://localhost:8080", "http://localhost:8080/search"),
        ("http://localhost:8080/", "http://localhost:8080/search"),
        ("http://localhost:8080/8000", "http://localhost:8080/8000/search"),
        ("http://localhost:8080/8000/", "http://localhost:8080/8000/search"),
        ("https://example.com/proxy/app", "https://example.com/proxy/app/search"),
        ("https://example.com/proxy/app/", "https://example.com/proxy/app/search"),
    ]
    
    print("URL Construction Test Results:")
    print("=" * 60)
    
    all_passed = True
    for base_url, expected in test_cases:
        actual = construct_search_url(base_url)
        passed = actual == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        
        print(f"{status} | {base_url:<35} -> {actual}")
        if not passed:
            print(f"      | Expected: {expected}")
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All URL construction tests PASSED")
        print("\nThe fix should resolve the proxy URL issue where requests were going to:")
        print("  http://localhost:8080/search (incorrect)")
        print("instead of:")
        print("  http://localhost:8080/8000/search (correct when accessing via proxy)")
    else:
        print("✗ Some tests FAILED")
    
    return all_passed

if __name__ == "__main__":
    test_url_construction()
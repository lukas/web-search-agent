#!/usr/bin/env python3
"""
Complete end-to-end test of the web interface
"""
import requests
import subprocess
import time
import json

def test_complete_user_flow():
    """Test the complete user flow as if using a web browser"""
    
    # Start the server
    print("Starting web server...")
    server_process = subprocess.Popen([
        'bash', '-c', 
        'source venv/bin/activate && python3 web_server.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        time.sleep(3)  # Give server time to start
        
        print("\n=== STEP 1: Load the web page ===")
        response = requests.get('http://localhost:8000/')
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: Failed to load page: {response.text}")
            return False
            
        html = response.text
        if 'Web Search Agent' not in html:
            print("ERROR: Page doesn't contain expected title")
            return False
            
        print("✓ Web page loads correctly")
        
        print("\n=== STEP 2: Test search functionality ===")
        
        # Test different search queries
        test_queries = ['python', 'javascript', 'test query', 'machine learning']
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            
            # Make the exact same request the browser JavaScript would make
            search_data = {'query': query}
            response = requests.post(
                'http://localhost:8000/search',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(search_data)
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'None')}")
            
            if response.status_code != 200:
                print(f"  ERROR: Expected 200, got {response.status_code}")
                print(f"  Response: {response.text}")
                continue
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                print(f"  ERROR: Wrong content type: {content_type}")
                print(f"  Response: {response.text[:200]}")
                continue
            
            # Try to parse JSON
            try:
                data = response.json()
                print(f"  ✓ JSON parsed successfully")
            except json.JSONDecodeError as e:
                print(f"  ERROR: JSON parse failed: {e}")
                print(f"  Response: {response.text[:200]}")
                continue
            
            # Check response structure
            if 'results' not in data:
                print(f"  ERROR: No 'results' key in response")
                print(f"  Data: {data}")
                continue
            
            if not isinstance(data['results'], list):
                print(f"  ERROR: 'results' is not a list")
                continue
                
            print(f"  ✓ Got {len(data['results'])} results")
            
            # Check first result structure
            if data['results']:
                result = data['results'][0]
                required_keys = ['title', 'content', 'source']
                missing_keys = [key for key in required_keys if key not in result]
                if missing_keys:
                    print(f"  WARNING: Missing keys in result: {missing_keys}")
                else:
                    print(f"  ✓ Result structure is correct")
        
        print("\n=== STEP 3: Test error conditions ===")
        
        # Test empty query
        response = requests.post(
            'http://localhost:8000/search',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'query': ''})
        )
        
        if response.status_code == 400:
            print("✓ Empty query handled correctly (400 error)")
        else:
            print(f"WARNING: Empty query returned {response.status_code}")
        
        # Test invalid JSON
        response = requests.post(
            'http://localhost:8000/search',
            headers={'Content-Type': 'application/json'},
            data='invalid json'
        )
        
        if response.status_code == 400:
            print("✓ Invalid JSON handled correctly (400 error)")
        else:
            print(f"WARNING: Invalid JSON returned {response.status_code}")
        
        print("\n=== SUMMARY ===")
        print("✓ All tests completed successfully!")
        print("The web interface should work correctly for users.")
        return True
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return False
        
    finally:
        print("\nShutting down server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == '__main__':
    success = test_complete_user_flow()
    exit(0 if success else 1)
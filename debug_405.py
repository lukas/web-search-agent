#!/usr/bin/env python3
"""Debug the 405 error by testing the server directly"""
import requests
import subprocess
import time
import json

def test_server_directly():
    print("Starting server with detailed logging...")
    
    server_process = subprocess.Popen([
        'bash', '-c', 
        'source venv/bin/activate && python3 web_server.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    try:
        time.sleep(2)
        
        print("\n=== Testing GET / ===")
        try:
            response = requests.get('http://localhost:8000/', timeout=5)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Content starts with: {response.text[:100]}...")
        except Exception as e:
            print(f"GET / failed: {e}")
        
        print("\n=== Testing POST /search ===")
        try:
            data = {'query': 'test'}
            response = requests.post(
                'http://localhost:8000/search',
                headers={'Content-Type': 'application/json'},
                json=data,
                timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 405:
                print("GOT 405 ERROR!")
                print(f"Full response: {response.text}")
                
        except Exception as e:
            print(f"POST /search failed: {e}")
        
        print("\n=== Testing with raw requests ===")
        import http.client
        
        try:
            conn = http.client.HTTPConnection('localhost', 8000)
            headers = {'Content-Type': 'application/json'}
            body = json.dumps({'query': 'test'})
            
            conn.request('POST', '/search', body, headers)
            response = conn.getresponse()
            
            print(f"Raw HTTP Status: {response.status} {response.reason}")
            print(f"Raw HTTP Headers: {dict(response.getheaders())}")
            print(f"Raw HTTP Body: {response.read().decode()[:200]}...")
            
            conn.close()
            
        except Exception as e:
            print(f"Raw HTTP failed: {e}")
            
    finally:
        print("\nServer output:")
        server_process.terminate()
        try:
            stdout, _ = server_process.communicate(timeout=3)
            print(stdout)
        except:
            server_process.kill()

if __name__ == '__main__':
    test_server_directly()
#!/usr/bin/env python3
"""
Simple HTTP proxy that forwards all requests to localhost:8000
This proxy correctly handles POST requests for the search functionality
"""

import http.server
import http.client
import urllib.parse
import json
from socketserver import ThreadingMixIn


class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP proxy that forwards requests to localhost:8000"""
    
    TARGET_HOST = 'localhost'
    TARGET_PORT = 8000
    
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def do_PUT(self):
        self.proxy_request()
    
    def do_DELETE(self):
        self.proxy_request()
    
    def do_OPTIONS(self):
        self.proxy_request()
    
    def do_HEAD(self):
        self.proxy_request()
    
    def proxy_request(self):
        """Forward the request to the target server"""
        try:
            # Parse the URL - remove the proxy prefix if it exists
            url_path = self.path
            if url_path.startswith('/8000'):
                url_path = url_path[5:]  # Remove '/8000' prefix
            
            # Create connection to target server
            conn = http.client.HTTPConnection(self.TARGET_HOST, self.TARGET_PORT)
            
            # Read request body if present
            content_length = self.headers.get('Content-Length')
            body = None
            if content_length:
                body = self.rfile.read(int(content_length))
            
            # Forward headers (excluding hop-by-hop headers)
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'connection', 'proxy-connection']:
                    headers[key] = value
            
            # Make request to target server
            conn.request(self.command, url_path, body, headers)
            response = conn.getresponse()
            
            # Send response status
            self.send_response(response.status, response.reason)
            
            # Forward response headers
            for key, value in response.getheaders():
                if key.lower() not in ['connection', 'proxy-connection', 'transfer-encoding']:
                    self.send_header(key, value)
            self.end_headers()
            
            # Forward response body
            response_data = response.read()
            self.wfile.write(response_data)
            
            conn.close()
            
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_error(502, f"Bad Gateway: {str(e)}")
    
    def log_message(self, format, *args):
        """Enhanced logging"""
        print(f"PROXY {self.address_string()} - {format % args}")
        print(f"  {self.command} {self.path}")


class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Thread-based HTTP server"""
    allow_reuse_address = True


def run_proxy(port=8080):
    """Run the proxy server"""
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, ProxyHTTPRequestHandler)
    
    print(f"Starting proxy server on port {port}")
    print(f"Proxying requests to localhost:8000")
    print(f"Access the web interface at: http://localhost:{port}/8000")
    print("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down proxy server...")
        httpd.shutdown()


if __name__ == '__main__':
    run_proxy()
#!/usr/bin/env python3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from web_search_agent import WebSearchAgent

class WebSearchHandler(BaseHTTPRequestHandler):
    agent = None
    
    @classmethod
    def set_agent(cls, agent):
        cls.agent = agent

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_html()
        elif self.path == '/debug':
            self.send_debug_html()
        elif self.path.startswith('/search'):
            self.handle_search()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/search':
            self.handle_search_post()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_HEAD(self):
        """Handle HEAD requests"""
        self.do_GET()
    
    def do_PUT(self):
        """Handle PUT requests - not supported"""
        self.send_method_not_allowed()
    
    def do_DELETE(self):
        """Handle DELETE requests - not supported"""
        self.send_method_not_allowed()
    
    def do_PATCH(self):
        """Handle PATCH requests - not supported"""
        self.send_method_not_allowed()
    
    def do_TRACE(self):
        """Handle TRACE requests - not supported"""
        self.send_method_not_allowed()
    
    def do_CONNECT(self):
        """Handle CONNECT requests - not supported"""
        self.send_method_not_allowed()
    
    def send_method_not_allowed(self):
        """Send 405 Method Not Allowed response"""
        self.send_response(405)
        self.send_header('Allow', 'GET, POST, OPTIONS, HEAD')
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'405 Method Not Allowed')
    
    def log_message(self, format, *args):
        """Override to add more detailed logging"""
        print(f"{self.address_string()} - {format % args}")
        print(f"  Method: {self.command}")
        print(f"  Path: {self.path}")
        print(f"  Headers: {dict(self.headers)}")

    def send_html(self):
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Web Search Agent</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .search-box { margin: 20px 0; }
        input[type="text"] { width: 60%; padding: 10px; font-size: 16px; }
        button { padding: 10px 20px; font-size: 16px; margin-left: 10px; }
        .results { margin: 20px 0; }
        .result { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .result h3 { margin: 0 0 10px 0; color: #1a73e8; }
        .result p { margin: 5px 0; }
        .result a { color: #006621; text-decoration: none; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Web Search Agent</h1>
    <div class="search-box">
        <input type="text" id="query" placeholder="Enter your search query..." />
        <button onclick="search()">Search</button>
    </div>
    <div id="results"></div>

    <script>
        function search() {
            const query = document.getElementById('query').value;
            if (!query) return;
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
            
            // Construct search URL that works with development proxies and base href tags
            let searchUrl;
            if (window.__PROXY_BASE_PATH__) {
                // Development proxy detected (like VS Code, Codespaces)
                searchUrl = window.__PROXY_BASE_PATH__ + 'search';
            } else if (document.querySelector('base[href]')) {
                // Base href tag detected - use it to construct URL
                const baseHref = document.querySelector('base[href]').getAttribute('href');
                searchUrl = new URL('search', new URL(baseHref, window.location.origin)).toString();
            } else {
                // Standard case - construct relative to current page
                const currentUrl = window.location.href;
                const baseUrl = currentUrl.endsWith('/') ? currentUrl : currentUrl + '/';
                searchUrl = new URL('search', baseUrl).toString();
            }
            
            fetch(searchUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                if (!response.headers.get('content-type')?.includes('application/json')) {
                    throw new Error('Response is not JSON');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = '<div class="result"><p>Error: ' + data.error + '</p></div>';
                    return;
                }
                
                if (data.results.length === 0) {
                    resultsDiv.innerHTML = '<div class="result"><p>No results found.</p></div>';
                    return;
                }
                
                let html = '';
                data.results.forEach(result => {
                    html += '<div class="result">';
                    html += '<h3>' + escapeHtml(result.title) + '</h3>';
                    html += '<p>' + escapeHtml(result.content) + '</p>';
                    if (result.source) {
                        html += '<a href="' + escapeHtml(result.source) + '" target="_blank">' + escapeHtml(result.source) + '</a>';
                    }
                    html += '</div>';
                });
                resultsDiv.innerHTML = html;
            })
            .catch(error => {
                resultsDiv.innerHTML = '<div class="result"><p>Error: ' + error.message + '</p></div>';
            });
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        document.getElementById('query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                search();
            }
        });
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_debug_html(self):
        """Send debug HTML page"""
        with open('debug_browser.html', 'r') as f:
            html = f.read()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

    def handle_search(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        query = params.get('q', [''])[0]
        
        if not query:
            self.send_json_response({'error': 'No query provided'}, 400)
            return
        
        try:
            results = self.agent.search_web(query)
            self.send_json_response({'results': results})
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)

    def handle_search_post(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            data = json.loads(post_data.decode())
            query = data.get('query', '')
            
            if not query:
                self.send_json_response({'error': 'No query provided'}, 400)
                return
            
            if not self.agent:
                self.send_json_response({'error': 'Search agent not initialized'}, 500)
                return
            
            results = self.agent.search_web(query)
            self.send_json_response({'results': results})
            
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            print(f"Search error: {e}")
            self.send_json_response({'error': str(e)}, 500)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run_server(port=8000):
    # Initialize the agent
    agent = WebSearchAgent()
    WebSearchHandler.set_agent(agent)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebSearchHandler)
    print(f"Web Search Agent server running on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
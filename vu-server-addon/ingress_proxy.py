#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import sys
import os

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def do_PUT(self):
        self.proxy_request()
    
    def do_DELETE(self):
        self.proxy_request()
    
    def proxy_request(self):
        target_port = sys.argv[1] if len(sys.argv) > 1 else "5340"
        target_url = f"http://127.0.0.1:{target_port}{self.path}"
        
        try:
            # Prepare request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(target_url, data=post_data, method=self.command)
            
            # Copy relevant headers
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    req.add_header(header, value)
            
            # Make request
            with urllib.request.urlopen(req) as response:
                # Copy response status
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Proxy Error: {str(e)}".encode())

if __name__ == "__main__":
    PORT = 8099
    target_port = sys.argv[1] if len(sys.argv) > 1 else "5340"
    print(f"Starting Ingress proxy on port {PORT}, forwarding to localhost:{target_port}")
    
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        httpd.serve_forever()
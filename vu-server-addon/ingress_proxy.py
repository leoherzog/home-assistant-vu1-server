#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - PROXY - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to use our logger instead of stderr
        logger.info(f"{self.address_string()} - {format % args}")
    
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
        
        logger.info(f"Proxying {self.command} {self.path} -> {target_url}")
        
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
                logger.info(f"Response: {response.status} for {self.path}")
                
                # Copy response headers
                for header, value in response.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code} for {self.path}: {e.reason}")
            self.send_response(e.code)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"HTTP Error {e.code}: {e.reason}".encode())
        except urllib.error.URLError as e:
            logger.error(f"URL Error for {self.path}: {e.reason}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Connection Error: {e.reason}".encode())
        except Exception as e:
            logger.error(f"Proxy Error for {self.path}: {str(e)}")
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
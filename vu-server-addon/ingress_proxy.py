#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import sys
import logging
import re

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
        # Restrict access to Home Assistant Ingress IP only
        client_ip = self.client_address[0]
        if client_ip != "172.30.32.2":
            logger.warning(f"Access denied for IP: {client_ip}")
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "fail", "message": "Access denied"}')
            return
        
        target_port = sys.argv[1] if len(sys.argv) > 1 else "5340"
        target_url = f"http://127.0.0.1:{target_port}{self.path}"
        
        # Get the Ingress path from headers for path rewriting
        ingress_path = self.headers.get('X-Ingress-Path', '')
        
        logger.info(f"Proxying {self.command} {self.path} -> {target_url} (Ingress: {ingress_path})")
        logger.info(f"Request headers: {dict(self.headers)}")
        
        try:
            # Prepare request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(target_url, data=post_data, method=self.command)
            
            # Copy relevant headers, but skip cache headers for HTML to ensure fresh content
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    # Skip cache-related headers for HTML requests to force fresh content
                    if (self.path == '/' or self.path.endswith('.html')) and header.lower() in ['if-modified-since', 'if-none-match']:
                        logger.info(f"Skipping cache header {header} for HTML request")
                        continue
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
                
                # Copy response body with path rewriting for HTML content
                content = response.read()
                content_type = response.headers.get('Content-Type', '')
                
                if content_type.startswith('text/html') and ingress_path:
                    # Rewrite HTML content to work with Ingress paths
                    logger.info(f"Rewriting HTML content for {self.path} with ingress path: {ingress_path}")
                    content = self.rewrite_html_content(content, ingress_path)
                
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            # For HTML requests, we want fresh content, so treat 304 as an error and retry without cache headers
            if e.code == 304 and (self.path == '/' or self.path.endswith('.html')):
                logger.info(f"Got 304 for HTML {self.path}, retrying without cache headers")
                try:
                    # Retry without cache headers
                    req_fresh = urllib.request.Request(target_url, data=post_data, method=self.command)
                    for header, value in self.headers.items():
                        if header.lower() not in ['host', 'content-length', 'if-modified-since', 'if-none-match']:
                            req_fresh.add_header(header, value)
                    
                    with urllib.request.urlopen(req_fresh) as response:
                        self.send_response(response.status)
                        logger.info(f"Fresh response: {response.status} for {self.path}")
                        
                        for header, value in response.headers.items():
                            self.send_header(header, value)
                        self.end_headers()
                        
                        content = response.read()
                        content_type = response.headers.get('Content-Type', '')
                        
                        if content_type.startswith('text/html') and ingress_path:
                            content = self.rewrite_html_content(content, ingress_path)
                        
                        self.wfile.write(content)
                        return
                except Exception as retry_e:
                    logger.error(f"Retry failed for {self.path}: {retry_e}")
            
            # Handle other 304s or errors normally
            if e.code == 304:
                logger.info(f"304 Not Modified for {self.path}")
                self.send_response(304)
                for header, value in e.headers.items():
                    self.send_header(header, value)
                self.end_headers()
            else:
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
    
    def rewrite_html_content(self, content, ingress_path):
        """Rewrite HTML content to work properly with Home Assistant Ingress"""
        try:
            html = content.decode('utf-8')
            
            # Convert absolute API paths to relative so <base> tag will handle them
            # Change /api/v0/ to api/v0/ (relative)
            html = re.sub(r'"/api/v0/', '"api/v0/', html)
            html = re.sub(r"'/api/v0/", "'api/v0/", html)
            
            # Add base tag to handle all relative paths (assets + API)
            # Ensure ingress_path ends with / for proper relative path resolution
            base_path = ingress_path.rstrip('/') + '/' if ingress_path else '/'
            base_tag = f'<base href="{base_path}">'
            logger.info(f"Adding base tag: {base_tag}")
            
            original_head_count = len(re.findall(r'<head[^>]*>', html, flags=re.IGNORECASE))
            html = re.sub(r'(<head[^>]*>)', r'\1\n    ' + base_tag, html, flags=re.IGNORECASE)
            logger.info(f"Found {original_head_count} head tags, added base tag")
            
            return html.encode('utf-8')
        except Exception as e:
            logger.error(f"Error rewriting HTML content: {e}")
            return content

if __name__ == "__main__":
    PORT = 8099
    target_port = sys.argv[1] if len(sys.argv) > 1 else "5340"
    print(f"Starting Ingress proxy on port {PORT}, forwarding to localhost:{target_port}")
    
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        httpd.serve_forever()
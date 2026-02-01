#!/usr/bin/env python3
import http.server
import ipaddress
import socketserver
import urllib.request
import sys
import logging
import re
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PROXY - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Module-level target port (set in __main__)
TARGET_PORT = "5340"

def is_allowed_ip(ip_str):
    """Check if IP is in Home Assistant supervisor network or loopback."""
    try:
        ip = ipaddress.ip_address(ip_str)
        supervisor_network = ipaddress.ip_network("172.30.0.0/16")
        return ip in supervisor_network or ip.is_loopback
    except ValueError:
        return False

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
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
        # Security check - allow Home Assistant supervisor network range
        client_ip = self.client_address[0]
        if not is_allowed_ip(client_ip):
            logger.warning(f"Access denied for IP: {client_ip}")
            self.send_error(403, "Access denied")
            return
        
        target_url = f"http://127.0.0.1:{TARGET_PORT}{self.path}"
        ingress_path = self.headers.get('X-Ingress-Path', '')
        
        logger.info(f"Proxying {self.command} {self.path} -> {target_url}")
        
        try:
            # Prepare request
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            req = urllib.request.Request(target_url, data=post_data, method=self.command)
            
            # Copy headers, skip cache headers for HTML to prevent 304s
            is_html_request = self.path == '/' or self.path.endswith('.html')
            skip_headers = ['host', 'content-length', 'accept-encoding']
            if is_html_request:
                skip_headers.extend(['if-modified-since', 'if-none-match'])
            
            for header, value in self.headers.items():
                if header.lower() not in skip_headers:
                    req.add_header(header, value)
            
            # Make request and process response (30 second timeout)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                content_type = response.headers.get('Content-Type', '')
                
                # Rewrite content if needed
                content = self.rewrite_content(content, content_type, ingress_path)
                
                # Send response
                self.send_response(response.status)
                self.copy_headers(response.headers, len(content))
                self.end_headers()
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code} for {self.path}: {e.reason}")
            if e.code == 304:
                self.send_response(304)
                for header, value in e.headers.items():
                    self.send_header(header, value)
                self.end_headers()
            else:
                self.send_error(e.code, f"HTTP Error: {e.reason}")
        except Exception as e:
            logger.error(f"Proxy Error for {self.path}: {str(e)}")
            self.send_error(502, f"Proxy Error: {str(e)}")
    
    def rewrite_content(self, content, content_type, ingress_path):
        """Rewrite content based on type"""
        if content_type.startswith('text/html') and ingress_path:
            return self.rewrite_html_content(content, ingress_path)
        elif 'javascript' in content_type:
            return self.rewrite_js_content(content)
        return content
    
    def rewrite_html_content(self, content, ingress_path):
        """Add base tag and fix API paths in HTML using BeautifulSoup"""
        try:
            html = content.decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Add base tag to head
            head = soup.find('head')
            if head:
                base_tag = soup.new_tag('base', href=f"{ingress_path.rstrip('/')}/")
                head.insert(0, base_tag)
            
            # Fix relative URLs in various attributes
            self._fix_relative_urls(soup)
            
            # Remove external font imports from style tags and link tags
            self._remove_external_fonts(soup)
            
            # Add hash link fix script
            self._add_hash_link_fix(soup)
            
            return str(soup).encode('utf-8')
        except Exception as e:
            logger.error(f"Error rewriting HTML with BeautifulSoup: {e}")
            return content
    
    def _fix_relative_urls(self, soup):
        """Fix relative URLs in HTML elements"""
        # Fix href attributes in links
        for tag in soup.find_all(['a', 'link'], href=True):
            href = tag['href']
            if href.startswith('/') and not href.startswith('//'):
                # Convert absolute paths to relative (remove leading /)
                tag['href'] = href[1:] if len(href) > 1 else ''
            elif href.startswith('http'):
                # Only convert to relative if it's pointing to localhost (same server)
                parsed = urlparse(href)
                local_hosts = ('localhost', '127.0.0.1', f'localhost:{TARGET_PORT}', f'127.0.0.1:{TARGET_PORT}')
                if parsed.netloc in local_hosts and parsed.path:
                    tag['href'] = parsed.path[1:] if parsed.path.startswith('/') else parsed.path
        
        # Fix src attributes in scripts, images, etc.
        for tag in soup.find_all(['script', 'img', 'iframe', 'source'], src=True):
            src = tag['src']
            if src.startswith('/') and not src.startswith('//'):
                tag['src'] = src[1:] if len(src) > 1 else ''
        
        # Fix action attributes in forms
        for tag in soup.find_all('form', action=True):
            action = tag['action']
            if action.startswith('/') and not action.startswith('//'):
                tag['action'] = action[1:] if len(action) > 1 else ''
    
    def _remove_external_fonts(self, soup):
        """Remove external font imports that fail in ingress proxy"""
        # Remove external font links
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href') and ('inter' in link['href'].lower() or 'font' in link['href'].lower()):
                if link['href'].startswith('http'):
                    link.decompose()
        
        # Remove external font imports from style tags
        for style in soup.find_all('style'):
            if style.string:
                # Remove @import statements for external fonts
                cleaned_css = re.sub(r'@import\s+url\(["\']?https?://[^"\']*inter[^"\']*["\']?\);', '', style.string, flags=re.IGNORECASE)
                cleaned_css = re.sub(r'@import\s+url\(["\']?https?://[^"\']*font[^"\']*["\']?\);', '', cleaned_css, flags=re.IGNORECASE)
                style.string = cleaned_css
    
    def _add_hash_link_fix(self, soup):
        """Add JavaScript to fix hash links in ingress proxy environment"""
        body = soup.find('body')
        if body:
            script_content = '''
            // Fix for hash links in Home Assistant ingress proxy environment
            // Wait for jQuery and DOM to be ready before setting up event handlers
            (function checkAndInit() {
                if (typeof $ !== 'undefined') {
                    $(document).ready(function() {
                        // Use event delegation to prevent default navigation behavior for hash links
                        $(document).on('click', 'a[href="#"]', function(e) {
                            console.log('Hash link click prevented by ingress proxy fix');
                            e.preventDefault();
                            e.stopPropagation();
                        });
                    });
                } else {
                    setTimeout(checkAndInit, 50);
                }
            })();
            '''
            script_tag = soup.new_tag('script')
            script_tag.string = script_content
            body.append(script_tag)
    
    def rewrite_js_content(self, content):
        """Fix API paths and redirects in JavaScript"""
        try:
            js = content.decode('utf-8')
            # Convert absolute API paths to relative
            js = re.sub(r'["\']\/api\/v0\/', lambda m: m.group(0)[0] + 'api/v0/', js)
            
            # Fix absolute redirects in JavaScript (like window.location.replace("/index.html"))
            # Convert "/path" to "path" to work with base tag
            js = re.sub(r'(window\.location\.(?:replace|href|assign)\s*\(\s*["\'])\/([^"\']+)', r'\1\2', js)
            
            return js.encode('utf-8')
        except Exception as e:
            logger.error(f"Error rewriting JavaScript: {e}")
            return content
    
    def copy_headers(self, response_headers, content_length):
        """Copy response headers, updating content-length and removing content-encoding"""
        for header, value in response_headers.items():
            if header.lower() == 'content-length':
                self.send_header(header, str(content_length))
            elif header.lower() not in ('content-encoding', 'transfer-encoding'):  # Skip content/transfer encoding
                self.send_header(header, value)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Multi-threaded TCP server to handle concurrent requests"""
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    PORT = 8099
    TARGET_PORT = sys.argv[1] if len(sys.argv) > 1 else "5340"
    print(f"Starting Ingress proxy on port {PORT}, forwarding to localhost:{TARGET_PORT}")

    with ThreadedTCPServer(("", PORT), ProxyHandler) as httpd:
        httpd.serve_forever()

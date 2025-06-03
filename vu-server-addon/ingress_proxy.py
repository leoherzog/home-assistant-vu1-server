#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import sys
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PROXY - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        if not (client_ip.startswith("172.30.") or client_ip == "127.0.0.1" or client_ip == "::1"):
            logger.warning(f"Access denied for IP: {client_ip}")
            self.send_error(403, "Access denied")
            return
        
        target_port = sys.argv[1] if len(sys.argv) > 1 else "5340"
        target_url = f"http://127.0.0.1:{target_port}{self.path}"
        ingress_path = self.headers.get('X-Ingress-Path', '')
        
        logger.info(f"Proxying {self.command} {self.path} -> {target_url}")
        
        try:
            # Prepare request
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            req = urllib.request.Request(target_url, data=post_data, method=self.command)
            
            # Copy headers, skip cache headers for HTML to prevent 304s
            is_html_request = self.path == '/' or self.path.endswith('.html')
            skip_headers = ['host', 'content-length']
            if is_html_request:
                skip_headers.extend(['if-modified-since', 'if-none-match'])
            
            for header, value in self.headers.items():
                if header.lower() not in skip_headers:
                    req.add_header(header, value)
            
            # Make request and process response
            with urllib.request.urlopen(req) as response:
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
        """Add base tag and fix API paths in HTML"""
        try:
            html = content.decode('utf-8')
            
            # Temporarily protect inline SVGs and their preceding comments from path rewriting
            svg_placeholders = {}
            
            # Protect SVG elements along with any preceding HTML comments (especially tabler-icons.io references)
            svg_with_comments_matches = re.findall(r'(?:<!--.*?-->\s*)?<svg[^>]*>.*?</svg>', html, re.DOTALL | re.IGNORECASE)
            for i, match in enumerate(svg_with_comments_matches):
                placeholder = f'SVG_PLACEHOLDER_{i}'
                svg_placeholders[placeholder] = match
                html = html.replace(match, placeholder)
            
            # Convert all absolute paths to relative (except external URLs and protocol-relative URLs)
            html = re.sub(r'(["\'])\/(?!\/|http|https)', r'\1', html)
            
            # Restore SVGs and their comments
            for placeholder, original in svg_placeholders.items():
                html = html.replace(placeholder, original)
            
            # Fix absolute URLs that point to the same host (Home Assistant external URLs)
            # Replace https://domain/path with relative path
            html = re.sub(r'(["\'])https?://[^/]+(/[^"\']*)', r'\1\2', html)

            # Fix CSS imports and links such as @import url('/inter/inter.css');
            html = re.sub(r'@import\s+url\(["\']?\/([^"\')]+)["\']?\);', r'@import url("\1");', html)
            
            # Add base tag
            base_tag = f'<base href="{ingress_path.rstrip("/")}/">'
            html = re.sub(r'(<head[^>]*>)', f'\\1\n    {base_tag}', html, flags=re.IGNORECASE)
            
            # Add JavaScript to prevent default behavior for hash links
            # This fixes buttons that don't work properly in the ingress proxy environment
            hash_link_fix_script = '''
    <script>
    // Fix for hash links in Home Assistant ingress proxy environment
    // Use event delegation to prevent default navigation behavior for hash links
    $(document).on('click', 'a[href="#"]', function(e) {
        e.preventDefault();
    });
    </script>'''
            
            # Inject the script before the closing </head> tag
            html = re.sub(r'(</head>)', f'    {hash_link_fix_script}\n\\1', html, flags=re.IGNORECASE)
            
            return html.encode('utf-8')
        except Exception as e:
            logger.error(f"Error rewriting HTML: {e}")
            return content
    
    def rewrite_js_content(self, content):
        """Fix API paths in JavaScript"""
        try:
            js = content.decode('utf-8')
            # Convert absolute API paths to relative
            js = re.sub(r'["\']\/api\/v0\/', lambda m: m.group(0)[0] + 'api/v0/', js)
            return js.encode('utf-8')
        except Exception as e:
            logger.error(f"Error rewriting JavaScript: {e}")
            return content
    
    def copy_headers(self, response_headers, content_length):
        """Copy response headers, updating content-length and removing content-encoding"""
        for header, value in response_headers.items():
            if header.lower() == 'content-length':
                self.send_header(header, str(content_length))
            elif header.lower() != 'content-encoding':  # Skip content-encoding
                self.send_header(header, value)

if __name__ == "__main__":
    PORT = 8099
    target_port = sys.argv[1] if len(sys.argv) > 1 else "5340"
    print(f"Starting Ingress proxy on port {PORT}, forwarding to localhost:{target_port}")
    
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        httpd.serve_forever()
#!/usr/bin/env python3
import http.server
import ipaddress
import socketserver
import urllib.request
import urllib.error
import sys
import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PROXY - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Upstream VU-Server (set in __main__ for the port).
TARGET_HOST = "127.0.0.1"
TARGET_PORT = "5340"

# Allowlist: only Home Assistant's Supervisor ingress gateway plus loopback.
# The full 172.30.0.0/16 hassio network would expose us to every other add-on.
SUPERVISOR_INGRESS_IP = ipaddress.ip_address("172.30.32.2")

# Hop-by-hop headers (RFC 7230 6.1) must never be forwarded by a proxy; they
# apply to a single transport-level connection, not the end-to-end message.
HOP_BY_HOP_HEADERS = frozenset({
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
})


def is_allowed_ip(ip_str):
    """Allow only the Supervisor ingress gateway and loopback."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return ip == SUPERVISOR_INGRESS_IP or ip.is_loopback


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Stop urllib from auto-following redirects so we can forward 3xx.

    Returning ``None`` from ``redirect_request`` makes urllib surface the
    redirect as an ``HTTPError`` (handled exactly like any other non-2xx
    response below), letting us rewrite and forward ``Location`` ourselves.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# Custom opener that does not follow redirects.
_OPENER = urllib.request.build_opener(_NoRedirectHandler)


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    # Enable keep-alive. Every response path below emits a correct
    # Content-Length (or uses send_error, which sends Connection: close),
    # so the client always knows where each message ends.
    # NOTE: streaming/long-poll endpoints are unsupported — responses are
    # fully buffered (this is why the add-on's ingress_stream option was
    # removed).
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

    def proxy_request(self):
        # Only the Supervisor ingress gateway (and loopback) may reach us.
        client_ip = self.client_address[0]
        if not is_allowed_ip(client_ip):
            logger.warning(f"Access denied for IP: {client_ip}")
            self.send_error(403, "Access denied")
            return

        # We length-delimit request bodies via Content-Length; we cannot
        # re-chunk to the backend, so reject chunked uploads explicitly.
        if 'chunked' in self.headers.get('Transfer-Encoding', '').lower():
            logger.warning(f"Rejecting chunked request body for {self.path}")
            self.send_error(411, "Length Required")
            return

        target_url = f"http://{TARGET_HOST}:{TARGET_PORT}{self.path}"
        ingress_path = self.headers.get('X-Ingress-Path', '')

        logger.info(f"Proxying {self.command} {self.path} -> {target_url}")

        try:
            content_length = int(self.headers.get('Content-Length', 0) or 0)
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            req = urllib.request.Request(target_url, data=post_data, method=self.command)

            # Forward request headers, dropping hop-by-hop and a few we
            # regenerate (Host/Content-Length) or refuse (Accept-Encoding,
            # so the backend never compresses content we need to rewrite).
            skip_request_headers = {'host', 'content-length', 'accept-encoding'}
            skip_request_headers |= HOP_BY_HOP_HEADERS
            if self.is_html_request():
                # Avoid 304s on HTML we rewrite; force a full body.
                skip_request_headers |= {'if-modified-since', 'if-none-match'}
            for header, value in self.headers.items():
                if header.lower() not in skip_request_headers:
                    req.add_header(header, value)

            with _OPENER.open(req, timeout=30) as response:
                self.forward_response(response.status, response.headers,
                                      response.read(), ingress_path)
        except urllib.error.HTTPError as e:
            # Non-2xx (and, thanks to _NoRedirectHandler, 3xx) responses.
            # These are deliberate backend responses — JSON error bodies,
            # redirects, 304s — so forward them verbatim (status + body),
            # not as our own HTML error page.
            logger.info(f"Upstream returned HTTP {e.code} for {self.path}: {e.reason}")
            body = b'' if e.code == 304 else e.read()
            self.forward_response(e.code, e.headers, body, ingress_path)
        except Exception as e:
            logger.error(f"Proxy Error for {self.path}: {e}")
            self.send_error(502, f"Proxy Error: {e}")

    # GET/POST cover the JSON API and web UI; HEAD is served by the backend's
    # StaticFileHandler. The backend implements no other verbs.
    do_GET = do_POST = do_HEAD = proxy_request

    def forward_response(self, status, headers, body, ingress_path):
        """Relay an upstream response to the ingress client."""
        if self.command == 'HEAD':
            # No body to rewrite; preserve the upstream Content-Length and
            # send headers only. (Per RFC 7230, a HEAD response carries no
            # body regardless of Content-Length, so keep-alive stays sane.)
            self.send_response(status)
            self.copy_headers(headers, ingress_path, content_length=None)
            self.end_headers()
            return

        content_type = headers.get('Content-Type', '')
        body = self.rewrite_content(body, content_type, ingress_path)
        self.send_response(status)
        self.copy_headers(headers, ingress_path, content_length=len(body))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def is_html_request(self):
        """True for the HTML documents we rewrite (ignoring query strings)."""
        path = urlparse(self.path).path
        return path == '/' or path.endswith('.html')

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

    def copy_headers(self, response_headers, ingress_path, content_length=None):
        """Relay upstream response headers to the client.

        Drops hop-by-hop headers, Content-Encoding (we always emit identity),
        and Date/Server (BaseHTTPRequestHandler emits its own). Rewrites
        Location for forwarded redirects. When ``content_length`` is given we
        emit it as the authoritative body length; when it is ``None`` (HEAD)
        the upstream Content-Length is passed through unchanged.
        """
        for header, value in response_headers.items():
            name = header.lower()
            if name in HOP_BY_HOP_HEADERS or name == 'content-encoding':
                continue
            if name in ('date', 'server'):
                continue
            if name == 'content-length':
                if content_length is None:
                    self.send_header(header, value)
                continue
            if name == 'location':
                value = self.rewrite_location(value, ingress_path)
            self.send_header(header, value)
        if content_length is not None:
            self.send_header('Content-Length', str(content_length))

    def rewrite_location(self, location, ingress_path):
        """Rewrite a redirect Location so it stays inside the ingress mount.

        - Absolute-path Locations (``/foo``) get the ingress path prefixed.
        - Absolute URLs pointing at the backend host get rewritten to the
          prefixed path.
        - Everything else (relative paths, foreign hosts) is left as-is.
        """
        prefix = ingress_path.rstrip('/')
        parsed = urlparse(location)

        if not parsed.scheme and not parsed.netloc:
            # Relative Location.
            if location.startswith('/') and not location.startswith('//'):
                return f"{prefix}{location}" if prefix else location
            return location

        # Absolute URL — only rewrite if it targets our backend.
        backend_hosts = ('127.0.0.1', 'localhost')
        try:
            same_backend = (parsed.hostname in backend_hosts and
                            parsed.port in (int(TARGET_PORT), None))
        except ValueError:
            same_backend = False
        if same_backend:
            rest = parsed.path or '/'
            if parsed.query:
                rest += '?' + parsed.query
            if parsed.fragment:
                rest += '#' + parsed.fragment
            return f"{prefix}{rest}" if prefix else rest
        return location


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

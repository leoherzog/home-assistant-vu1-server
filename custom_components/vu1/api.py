import requests

class StreacomVU1API:
    """Simple client for Streacom VU-Server REST API (no MQTT)."""
    def __init__(self, host, port, api_key):
        self.base_url = f"http://{host}:{port}/api/v0"
        self.api_key = api_key

    def list_dials(self):
        """Retrieve list of dials from VU-Server."""
        url = f"{self.base_url}/dial/list?key={self.api_key}"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def set_value(self, dial_uid, value):
        """Set the needle value (0-100%) for a given dial via REST API."""
        url = f"{self.base_url}/dial/{dial_uid}/set?key={self.api_key}&value={int(value)}"
        requests.get(url)  # non-blocking in integration (could use async calls)

    def set_backlight(self, dial_uid, r, g, b):
        """Set the backlight RGB (0-100 each channel) for a given dial."""
        url = (f"{self.base_url}/dial/{dial_uid}/backlight?key={self.api_key}"
               f"&red={r}&green={g}&blue={b}")
        requests.get(url)

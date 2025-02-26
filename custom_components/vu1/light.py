from homeassistant.components.light import LightEntity, ColorMode
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up light entities for each dial's backlight."""
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    dials = api.list_dials()
    lights = []
    for dial in dials:
        lights.append(VUMeterBacklightLight(api, dial))
    async_add_entities(lights)

class VUMeterBacklightLight(LightEntity):
    """Light entity to control the RGB backlight of a VU1 dial."""
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, api, dial_info):
        self._api = api
        self._uid = dial_info["uid"]
        name = dial_info.get("dial_name", "VU Dial")
        self._attr_name = f"{name} Backlight"
        self._attr_unique_id = f"{self._uid}_backlight"
        # Initialize color from dial info (values 0-100)
        rgb = dial_info.get("backlight", {})
        # Store internal state in 0-255 scale for HA
        r = int(rgb.get("red", 0) * 255 / 100)
        g = int(rgb.get("green", 0) * 255 / 100)
        b = int(rgb.get("blue", 0) * 255 / 100)
        self._attr_rgb_color = (r, g, b)
        self._attr_is_on = (r+g+b) > 0

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._uid)},
            "name": f"VU1 Dial - {self._attr_name}",
            "manufacturer": "Streacom",
            "model": "VU1 Analogue Dial"
        }

    def turn_on(self, **kwargs):
        """Turn on or adjust the dial backlight."""
        r, g, b = self._attr_rgb_color  # current color (0-255)
        if "rgb_color" in kwargs:
            r, g, b = kwargs["rgb_color"]
        # Send new color to dial (convert 0-255 to 0-100 scale)
        self._api.set_backlight(self._uid, int(r*100/255), int(g*100/255), int(b*100/255))
        self._attr_rgb_color = (r, g, b)
        self._attr_is_on = True

    def turn_off(self, **kwargs):
        """Turn off the dial backlight."""
        self._api.set_backlight(self._uid, 0, 0, 0)
        self._attr_rgb_color = (0, 0, 0)
        self._attr_is_on = False

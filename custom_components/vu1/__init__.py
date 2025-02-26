"""Streacom VU1 Integration - Initialize integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Streacom VU1 from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Initialize API client for VU-Server
    from .api import StreacomVU1API
    conf = entry.data
    api = StreacomVU1API(conf["host"], conf["port"], conf["api_key"])
    hass.data[DOMAIN][entry.entry_id] = {"api": api}
    # Set up platform entities (sensor for dial value, light for backlight)
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    await hass.config_entries.async_forward_entry_setup(entry, "light")
    _LOGGER.info("Streacom VU1 integration setup complete")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Streacom VU1 config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "light")
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True

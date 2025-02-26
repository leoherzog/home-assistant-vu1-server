import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN

class StreacomVU1ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Streacom VU1 integration."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input["host"]
            port = user_input["port"]
            api_key = user_input["api_key"]
            # Test connection to VU-Server by calling the dial list API
            import aiohttp
            url = f"http://{host}:{port}/api/v0/dial/list?key={api_key}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            errors["base"] = "cannot_connect"
                        else:
                            data = await resp.json()
                            if data.get("status") != "ok":
                                errors["base"] = "invalid_auth"
                            else:
                                # Connection successful
                                return self.async_create_entry(
                                    title="Streacom VU-Server",
                                    data={"host": host, "port": port, "api_key": api_key}
                                )
            except Exception:
                errors["base"] = "cannot_connect"
        # Show form (initial setup)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host", default="localhost"): str,
                vol.Required("port", default=5340): int,
                vol.Required("api_key"): str
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return StreacomVU1OptionsFlow(config_entry)


class StreacomVU1OptionsFlow(config_entries.OptionsFlow):
    """Handle options for Streacom VU1 integration (per-device settings)."""
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Save the options (min, max, color, sensor selection)
            return self.async_create_entry(title="", data=user_input)
        # Show options form for configuring the dial (single-dial example for simplicity)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("sensor_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("min_value", default=0): vol.Coerce(float),
                vol.Optional("max_value", default=100): vol.Coerce(float),
                vol.Optional("color", default=[100, 100, 100]): selector.ColorRGBSelector()
            })
        )

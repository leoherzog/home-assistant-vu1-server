from homeassistant.core import HomeAssistant

from .ha_integration import HAIntegration
from VU-Server.server_dial_handler import ServerDialHandler
from VU-Server.dial_driver import DialSerialDriver

class VU1Addon:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.dial_driver = DialSerialDriver()
        self.dial_handler = ServerDialHandler(self.dial_driver)
        self.ha_integration = HAIntegration(hass, self.dial_handler)

    async def setup(self):
        await self.ha_integration.setup()
        self.hass.bus.async_listen("state_changed", self.state_changed_listener)

    async def state_changed_listener(self, event):
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")

        if entity_id.startswith(f"{DOMAIN}.") and new_state:
            dial_uid = entity_id.split(".")[1].split("_")[0]
            value = float(new_state.state)
            await self.update_dial_value(dial_uid, value)

    async def update_dial_value(self, dial_uid, value):
        # Update the physical dial
        self.dial_handler.dial_set_percent(dial_uid, value)
        # Update the Home Assistant entity
        await self.ha_integration.update_dial_value(dial_uid, value)
from homeassistant.const import (
    ATTR_MIN, ATTR_MAX,
    DEVICE_CLASS_SENSOR
)
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN

class HAIntegration:
    def __init__(self, hass: HomeAssistant, dial_handler):
        self.hass = hass
        self.dial_handler = dial_handler
        self.default_min = self.hass.data[DOMAIN].get("default_min_value", 0)
        self.default_max = self.hass.data[DOMAIN].get("default_max_value", 100)

    async def register_devices_and_entities(self):
        dev_reg = device_registry.async_get(self.hass)
        ent_reg = entity_registry.async_get(self.hass)

        for dial_uid, dial_info in self.dial_handler.get_dial_info().items():
            device = dev_reg.async_get_or_create(
                config_entry_id=DOMAIN,
                identifiers={(DOMAIN, dial_uid)},
                name=f"{dial_info['dial_name']} VU1",
                model="VU1 Dynamic Analogue Dial",
                manufacturer="Streacom",
            )

            ent_reg.async_get_or_create(
                DOMAIN,
                DEVICE_CLASS_SENSOR,
                f"{dial_uid}_value",
                device_id=device.id,
                name=f"{dial_info['dial_name']} Value",
                original_name=f"{dial_info['dial_name']} Value",
                unit_of_measurement="%",
                suggested_display_precision=0,
            )

            ent_reg.async_get_or_create(
                NUMBER_DOMAIN,
                DOMAIN,
                f"{dial_uid}_min",
                device_id=device.id,
                name=f"{dial_info['dial_name']} Min Value",
                original_name=f"{dial_info['dial_name']} Min Value",
            )

            ent_reg.async_get_or_create(
                NUMBER_DOMAIN,
                DOMAIN,
                f"{dial_uid}_max",
                device_id=device.id,
                name=f"{dial_info['dial_name']} Max Value",
                original_name=f"{dial_info['dial_name']} Max Value",
            )

            # Set initial states
            await self.hass.states.async_set(f"{DOMAIN}.{dial_uid}_value", 0, {
                ATTR_MIN: self.default_min,
                ATTR_MAX: self.default_max,
            })
            await self.hass.states.async_set(f"{NUMBER_DOMAIN}.{DOMAIN}_{dial_uid}_min", self.default_min)
            await self.hass.states.async_set(f"{NUMBER_DOMAIN}.{DOMAIN}_{dial_uid}_max", self.default_max)

    async def update_dial_value(self, dial_uid, value):
        min_value = float(self.hass.states.get(f"{NUMBER_DOMAIN}.{DOMAIN}_{dial_uid}_min").state)
        max_value = float(self.hass.states.get(f"{NUMBER_DOMAIN}.{DOMAIN}_{dial_uid}_max").state)
        
        # Scale the value to the dial's range
        scaled_value = (value - min_value) / (max_value - min_value) * 100
        
        await self.hass.states.async_set(f"{DOMAIN}.{dial_uid}_value", scaled_value, {
            ATTR_MIN: min_value,
            ATTR_MAX: max_value,
        })
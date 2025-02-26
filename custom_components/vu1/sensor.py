from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up VU Meter sensor entities for each dial."""
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    options = {**entry.data, **entry.options}  # combine config data and runtime options
    sensor_entity_id = options.get("sensor_entity_id")
    min_val = options.get("min_value", 0.0)
    max_val = options.get("max_value", 100.0)
    dials = api.list_dials()
    entities = []
    for dial in dials:
        entities.append(VUMeterDialSensor(api, dial, sensor_entity_id, min_val, max_val))
    async_add_entities(entities)

class VUMeterDialSensor(SensorEntity):
    """Sensor entity that reflects the value of a VU1 dial (as percentage)."""
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:gauge"

    def __init__(self, api, dial_info, sensor_entity_id, min_val, max_val):
        self._api = api
        self._uid = dial_info["uid"]
        self._name = dial_info.get("dial_name", "VU Dial")
        self._sensor_entity_id = sensor_entity_id
        self._min = min_val
        self._max = max_val
        self._attr_name = f"{self._name} Needle"
        self._attr_unique_id = f"{self._uid}_needle"

    @property
    def device_info(self):
        # Link this entity to a device (the dial) in Home Assistant
        return {
            "identifiers": {(DOMAIN, self._uid)},
            "name": f"VU1 Dial - {self._name}",
            "manufacturer": "Streacom",
            "model": "VU1 Analogue Dial"
        }

    def update(self):
        """Update the dial reading based on the linked sensor value."""
        # Get the current state of the selected HA sensor
        state = self.hass.states.get(self._sensor_entity_id)
        if state and state.state not in (None, ""):
            try:
                value = float(state.state)
            except ValueError:
                return  # non-numeric state
            # Linear scaling of sensor value to 0-100%
            if value <= self._min:
                perc = 0
            elif value >= self._max:
                perc = 100
            else:
                perc = (value - self._min) / (self._max - self._min) * 100.0
            perc = max(0, min(100, perc))
            # Send the value to the VU1 dial via REST API
            self._api.set_value(self._uid, perc)
            self._attr_native_value = round(perc, 2)
        else:
            self._attr_native_value = None

import asyncio
from homeassistant.core import HomeAssistant

from .addon import VU1AddOn

async def main(hass: HomeAssistant):
    addon = VU1Addon(hass)
    await addon.setup()

    # Keep the add-on running
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    hass = HomeAssistant()
    asyncio.run(main(hass))
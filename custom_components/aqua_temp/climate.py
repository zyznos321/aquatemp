"""Platform for climate integration."""
from abc import ABC
import logging
import sys

from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription
from homeassistant.components.climate.const import (
    DOMAIN as CLIMATE_DOMAIN,
    FAN_AUTO,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .common.consts import (
    BINARY_SENSOR_CONFIG,
    DOMAIN,
    FAN_MODE_MAPPING,
    HVAC_MODE_MAPPING,
    HVAC_MODE_MAX_TEMP,
    HVAC_MODE_MIN_TEMP,
    HVAC_PC_MAPPING,
    MANUAL_MUTE_MAPPING,
    POWER_MODE_MAPPING,
    PROTOCOL_CODE_CURRENT_TEMP,
    PROTOCOL_CODE_FAN_MODE,
    PROTOCOL_CODE_HVAC_MODE,
    PROTOCOL_CODE_POWER,
)
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up the climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    climate_entities = [
        AquaTempClimateEntity(device_code, coordinator)
        for device_code in coordinator.api_data
    ]

    _LOGGER.debug(f"Setting up climate entities: {climate_entities}")

    async_add_entities(climate_entities, True)


class AquaTempClimateEntity(CoordinatorEntity, ClimateEntity, ABC):
    """Representation of a climate entity."""

    _attributes: dict

    def __init__(self, device_code: str, coordinator: AquaTempCoordinator):
        """Initialize the climate entity."""
        super().__init__(coordinator)

        self._api_data = coordinator.api_data[device_code]
        self._config_data = coordinator.config_data

        device_info = coordinator.get_device(device_code)
        device_name = device_info.get("name")

        entity_name = device_name

        device_id = self._api_data.get("device_id")
        slugify_uid = slugify(f"{CLIMATE_DOMAIN}_{device_id}")

        entity_description = ClimateEntityDescription(slugify_uid)
        entity_description.name = entity_name

        self.entity_description = entity_description

        self._device_code = device_code

        self._attributes = {}

        self._attr_device_info = device_info
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
        self._attr_fan_modes = list(FAN_MODE_MAPPING.keys())
        self._attr_hvac_modes = list(HVAC_MODE_MAPPING.keys())

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = FAN_AUTO

        self._attr_temperature_unit = self.coordinator.get_temperature_unit(device_code)
        self._attr_name = entity_name
        self._attr_unique_id = slugify_uid

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get("temperature")

        try:
            await self.coordinator.set_temperature(
                self._device_code, self.hvac_mode, temperature
            )

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        try:
            await self.coordinator.set_hvac_mode(self._device_code, hvac_mode)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        try:
            await self.coordinator.set_fan_mode(self._device_code, fan_mode)

            await self.coordinator.async_request_refresh()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(f"{ex}, Line: {line_number}")

    def _handle_coordinator_update(self) -> None:
        """Fetch new state data for the sensor."""
        mode = self._api_data.get(PROTOCOL_CODE_HVAC_MODE)
        power = self._api_data.get(PROTOCOL_CODE_POWER)
        manual_mute = self._api_data.get(PROTOCOL_CODE_FAN_MODE)
        current_temperature = self._api_data.get(PROTOCOL_CODE_CURRENT_TEMP)

        power_config = BINARY_SENSOR_CONFIG.get(PROTOCOL_CODE_POWER)
        power_on_value = power_config.get("value")

        is_power_on = power == power_on_value

        hvac_mode = HVAC_PC_MAPPING.get(mode) if is_power_on else HVACMode.OFF

        min_temp_key = HVAC_MODE_MIN_TEMP.get(hvac_mode)
        max_temp_key = HVAC_MODE_MAX_TEMP.get(hvac_mode)

        min_temp = self._api_data.get(min_temp_key, 0)
        max_temp = self._api_data.get(max_temp_key, 0)

        hvac_mode_code = HVAC_MODE_MAPPING.get(hvac_mode)
        hvac_mode_param = f"R0{hvac_mode_code}"
        hvac_mode_temperature_value = self._api_data.get(hvac_mode_param)

        target_temperature = None
        if is_power_on and hvac_mode_temperature_value is not None:
            target_temperature = float(hvac_mode_temperature_value)

        self._attr_hvac_mode = hvac_mode
        self._attr_fan_mode = MANUAL_MUTE_MAPPING.get(manual_mute)
        self._attr_target_temperature = float(str(target_temperature))
        self._attr_min_temp = float(str(min_temp))
        self._attr_max_temp = float(str(max_temp))

        if current_temperature is not None:
            self._attr_current_temperature = float(str(current_temperature))

        _LOGGER.debug(f"{PROTOCOL_CODE_HVAC_MODE}: {mode}")
        _LOGGER.debug(f"{PROTOCOL_CODE_POWER}: {power}")
        _LOGGER.debug(f"{PROTOCOL_CODE_FAN_MODE}: {manual_mute}")
        _LOGGER.debug(f"{PROTOCOL_CODE_CURRENT_TEMP}: {current_temperature}")
        _LOGGER.debug(f"is_power_on: {is_power_on}")

        _LOGGER.debug(f"_attr_hvac_mode: {self._attr_hvac_mode}")
        _LOGGER.debug(f"_attr_target_temperature: {self._attr_target_temperature}")
        _LOGGER.debug(f"_attr_fan_mode: {self._attr_fan_mode}")
        _LOGGER.debug(f"_attr_min_temp: {self._attr_min_temp}")
        _LOGGER.debug(f"_attr_max_temp: {self._attr_max_temp}")

        self.async_write_ha_state()

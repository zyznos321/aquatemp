from custom_components.aqua_temp.common.protocol_codes import ProtocolCode
from homeassistant.components.climate import HVACMode

MODE_TEMPERATURE_COOL = "0"
MODE_TEMPERATURE_HEAT = "1"
MODE_TEMPERATURE_AUTO = "2"

HVAC_MODE_MAPPING = {
    HVACMode.OFF: None,
    HVACMode.COOL: MODE_TEMPERATURE_COOL,
    HVACMode.HEAT: MODE_TEMPERATURE_HEAT,
    HVACMode.AUTO: MODE_TEMPERATURE_AUTO,
}

HVAC_MODE_TARGET_TEMPERATURE = {
    HVACMode.COOL: ProtocolCode.TARGET_TEMPERATURE_COOL,
    HVACMode.HEAT: ProtocolCode.TARGET_TEMPERATURE_HEAT,
    HVACMode.AUTO: ProtocolCode.TARGET_TEMPERATURE_AUTO,
}

HVAC_MODE_MINIMUM_TEMPERATURE = {
    HVACMode.COOL: ProtocolCode.MINIMUM_TEMPERATURE_COOL,
    HVACMode.HEAT: ProtocolCode.MINIMUM_TEMPERATURE_HEAT,
}

HVAC_MODE_MAXIMUM_TEMPERATURE = {
    HVACMode.COOL: ProtocolCode.MAXIMUM_TEMPERATURE_COOL,
    HVACMode.HEAT: ProtocolCode.MAXIMUM_TEMPERATURE_HEAT,
}
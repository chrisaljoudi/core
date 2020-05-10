"""Component for interacting with a Lutron Caseta system."""
import logging

from pylutron_caseta.smartbridge import Smartbridge

from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import Entity

from .const import CONF_CA_CERTS, CONF_CERTFILE, CONF_KEYFILE

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lutron_caseta"
DATA_BRIDGE_CONFIG = "lutron_caseta_bridges"

LUTRON_CASETA_COMPONENTS = ["light", "switch", "cover", "scene", "fan", "binary_sensor"]


async def async_setup(hass, base_config):
    """Set up the Lutron component."""

    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass, config_entry):
    """Set up a bridge from a config entry."""

    host = config_entry.data[CONF_HOST]
    keyfile = config_entry.data[CONF_KEYFILE]
    certfile = config_entry.data[CONF_CERTFILE]
    ca_certs = config_entry.data[CONF_CA_CERTS]

    bridge = Smartbridge.create_tls(
        hostname=host, keyfile=keyfile, certfile=certfile, ca_certs=ca_certs
    )

    await bridge.connect()
    if not bridge.is_connected():
        _LOGGER.error("Unable to connect to Lutron Caseta bridge at %s", host)
        return False

    _LOGGER.debug("Connected to Lutron Caseta bridge at %s", host)

    # Store this bridge (keyed by entry_id) so it can be retrieved by the
    # components we're setting up.
    hass.data[DOMAIN][config_entry.entry_id] = bridge

    for component in LUTRON_CASETA_COMPONENTS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True


class LutronCasetaDevice(Entity):
    """Common base class for all Lutron Caseta devices."""

    def __init__(self, device, bridge):
        """Set up the base class.

        [:param]device the device metadata
        [:param]bridge the smartbridge object
        """
        self._device = device
        self._smartbridge = bridge

    async def async_added_to_hass(self):
        """Register callbacks."""
        self._smartbridge.add_subscriber(self.device_id, self.async_write_ha_state)

    @property
    def device_id(self):
        """Return the device ID used for calling pylutron_caseta."""
        return self._device["device_id"]

    @property
    def name(self):
        """Return the name of the device."""
        return self._device["name"]

    @property
    def serial(self):
        """Return the serial number of the device."""
        return self._device["serial"]

    @property
    def unique_id(self):
        """Return the unique ID of the device (serial)."""
        return str(self.serial)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attr = {"device_id": self.device_id, "zone_id": self._device["zone"]}
        return attr

    @property
    def should_poll(self):
        """No polling needed."""
        return False

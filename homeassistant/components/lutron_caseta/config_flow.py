"""Config flow for Lutron Caseta."""
import logging

from pylutron_caseta.smartbridge import Smartbridge
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from . import DOMAIN  # pylint: disable=unused-import
from .const import (
    ABORT_REASON_ALREADY_CONFIGURED,
    CONF_CA_CERTS,
    CONF_CERTFILE,
    CONF_KEYFILE,
    ERROR_CANNOT_CONNECT,
)

_LOGGER = logging.getLogger(__name__)

ENTRY_DEFAULT_TITLE = "Caséta bridge"


class LutronCasetaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Lutron Caseta config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize a Lutron Caseta flow."""
        self.data = {}

    async def async_step_user(self, user_input=None):
        """Configure and connect to a Caseta bridge."""
        errors = {}
        if user_input:
            # Abort if existing entry with matching host exists.
            host = user_input[CONF_HOST]
            if any(
                host == entry.data[CONF_HOST] for entry in self._async_current_entries()
            ):
                return self.async_abort(reason=ABORT_REASON_ALREADY_CONFIGURED)

            # Store the imported config for other steps in this flow to access.
            self.data[CONF_HOST] = host
            self.data[CONF_KEYFILE] = user_input[CONF_KEYFILE]
            self.data[CONF_CERTFILE] = user_input[CONF_CERTFILE]
            self.data[CONF_CA_CERTS] = user_input[CONF_CA_CERTS]

            if not await self.async_validate_connectable_bridge_config():
                errors["base"] = ERROR_CANNOT_CONNECT
            else:
                return self.async_create_entry(
                    title=ENTRY_DEFAULT_TITLE, data=self.data
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_KEYFILE): str,
                    vol.Required(CONF_CERTFILE): str,
                    vol.Required(CONF_CA_CERTS): str,
                }
            ),
            errors=errors,
        )

    async def async_validate_connectable_bridge_config(self):
        """Check if we can connect to the bridge with the current config."""

        try:
            bridge = Smartbridge.create_tls(
                hostname=self.data[CONF_HOST],
                keyfile=self.data[CONF_KEYFILE],
                certfile=self.data[CONF_CERTFILE],
                ca_certs=self.data[CONF_CA_CERTS],
            )

            await bridge.connect()
            if not bridge.is_connected():
                return False

            await bridge.close()
            return True
        except (KeyError, ValueError):
            _LOGGER.error("Unexpected error while connecting to Caseta bridge")
            return False

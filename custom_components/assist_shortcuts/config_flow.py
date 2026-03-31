"""Config flow for Assist Shortcuts."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_DOMAINS, CONTROLLABLE_DOMAINS, DEFAULT_DOMAINS, DOMAIN


def _domain_schema(defaults: list[str]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_DOMAINS, default=defaults): cv.multi_select(
                {d: d.replace("_", " ").title() for d in CONTROLLABLE_DOMAINS}
            )
        }
    )


class AssistShortcutsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(
                title="Assist Shortcuts",
                data={},
                options={CONF_DOMAINS: user_input[CONF_DOMAINS]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_domain_schema(DEFAULT_DOMAINS),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AssistShortcutsOptionsFlow:
        return AssistShortcutsOptionsFlow(config_entry)


class AssistShortcutsOptionsFlow(OptionsFlow):
    """Handle options (reconfigure domains)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_DOMAINS: user_input[CONF_DOMAINS]})

        current = self._config_entry.options.get(CONF_DOMAINS, DEFAULT_DOMAINS)
        return self.async_show_form(
            step_id="init",
            data_schema=_domain_schema(current),
        )

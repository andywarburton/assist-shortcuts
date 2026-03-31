"""Assist Shortcuts — natural shorthand voice commands for Home Assistant Assist."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DOMAINS, DEFAULT_DOMAINS, DOMAIN
from .intent_handler import AssistShortcutsIntentManager

_LOGGER = logging.getLogger(__name__)

type AssistShortcutsConfigEntry = ConfigEntry[AssistShortcutsIntentManager]


async def async_setup_entry(hass: HomeAssistant, entry: AssistShortcutsConfigEntry) -> bool:
    """Set up Assist Shortcuts from a config entry."""
    domains: list[str] = entry.options.get(CONF_DOMAINS, DEFAULT_DOMAINS)

    manager = AssistShortcutsIntentManager(hass, domains)
    await manager.async_setup()

    entry.runtime_data = manager

    # Re-register intents if options change (user updates domain list)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: AssistShortcutsConfigEntry
) -> None:
    """Reload the integration when options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: AssistShortcutsConfigEntry
) -> bool:
    """Unload Assist Shortcuts and deregister all intents."""
    manager: AssistShortcutsIntentManager = entry.runtime_data
    manager.async_unload()
    return True

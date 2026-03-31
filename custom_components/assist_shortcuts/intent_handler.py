"""Intent handlers for Assist Shortcuts."""
from __future__ import annotations

import logging
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, intent
from homeassistant.helpers import floor_registry as fr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

INTENT_TURN_ON = "AssistShortcutTurnOn"
INTENT_TURN_OFF = "AssistShortcutTurnOff"

TARGET_ENTITY = "entity"
TARGET_AREA = "area"
TARGET_FLOOR = "floor"


def _slugify(text) -> str:
    """Lower-case and collapse non-alphanumeric runs to a single space."""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _build_lookup(hass: HomeAssistant) -> dict[str, tuple[str, str]]:
    """
    Build a mapping of slugified name -> (target_type, target_id).

    Priority: floors < areas < entities, so more specific targets win.
    """
    lookup: dict[str, tuple[str, str]] = {}

    floor_reg = fr.async_get(hass)
    area_reg = ar.async_get(hass)
    entity_reg = er.async_get(hass)

    # Floors (lowest priority)
    for floor in floor_reg.floors.values():
        for raw in [floor.name] + list(floor.aliases or []):
            slug = _slugify(raw)
            if slug:
                lookup[slug] = (TARGET_FLOOR, floor.floor_id)

    # Areas
    for area in area_reg.areas.values():
        slug = _slugify(area.name)
        if slug:
            lookup[slug] = (TARGET_AREA, area.id)
        for alias in area.aliases or []:
            slug = _slugify(str(alias))
            if slug:
                lookup[slug] = (TARGET_AREA, area.id)

    # Entities (highest priority)
    for entry in entity_reg.entities.values():
        if entry.hidden_by or entry.disabled_by:
            continue
        for raw in [entry.name, entry.original_name] + list(entry.aliases or []):
            if raw:
                slug = _slugify(str(raw))
                if slug:
                    lookup[slug] = (TARGET_ENTITY, entry.entity_id)

    _LOGGER.debug("Assist Shortcuts: built lookup table with %d entries", len(lookup))
    return lookup


class _ShortcutHandler(intent.IntentHandler):
    """Handles AssistShortcutTurnOn / AssistShortcutTurnOff intents."""

    slot_schema = {
        "shortcut_name": intent.non_empty_string,
    }

    def __init__(self, intent_type: str, action: str, domains: list[str]) -> None:
        self.intent_type = intent_type
        self._action = action  # "turn_on" or "turn_off"
        self._domains = domains

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)
        raw_name: str = slots["shortcut_name"]["value"]
        slug = _slugify(raw_name)

        lookup = _build_lookup(hass)
        match = lookup.get(slug)

        if match is None:
            _LOGGER.debug("Assist Shortcuts: no match for '%s'", slug)
            raise intent.IntentHandleError(
                f"Sorry, I don't know what '{raw_name}' refers to."
            )

        target_type, target_id = match
        service = self._action

        try:
            if target_type == TARGET_ENTITY:
                await hass.services.async_call(
                    "homeassistant",
                    service,
                    {"entity_id": target_id},
                    blocking=True,
                )
                _LOGGER.debug("Assist Shortcuts: %s entity %s", service, target_id)

            elif target_type == TARGET_AREA:
                for domain in self._domains:
                    await hass.services.async_call(
                        domain,
                        service,
                        {"area_id": target_id},
                        blocking=True,
                    )
                _LOGGER.debug(
                    "Assist Shortcuts: %s area %s (domains: %s)",
                    service, target_id, self._domains,
                )

            elif target_type == TARGET_FLOOR:
                area_reg = ar.async_get(hass)
                for area in area_reg.areas.values():
                    if area.floor_id == target_id:
                        for domain in self._domains:
                            await hass.services.async_call(
                                domain,
                                service,
                                {"area_id": area.id},
                                blocking=True,
                            )
                _LOGGER.debug(
                    "Assist Shortcuts: %s floor %s (domains: %s)",
                    service, target_id, self._domains,
                )

        except intent.IntentHandleError:
            raise
        except Exception as err:
            _LOGGER.error("Assist Shortcuts error calling %s on %s: %s", service, target_id, err)
            raise intent.IntentHandleError(
                f"Something went wrong trying to {service.replace('_', ' ')} '{raw_name}'."
            ) from err

        verb = "on" if service == "turn_on" else "off"
        response = intent_obj.create_response()
        response.async_set_speech(f"OK, turning {raw_name} {verb}.")
        return response


class AssistShortcutsIntentManager:
    """Registers and unregisters the two shortcut intent handlers."""

    def __init__(self, hass: HomeAssistant, domains: list[str]) -> None:
        self._hass = hass
        self._domains = domains
        self._handlers: list[_ShortcutHandler] = []

    async def async_setup(self) -> None:
        """Register the on/off intent handlers."""
        for intent_type, action in (
            (INTENT_TURN_ON, "turn_on"),
            (INTENT_TURN_OFF, "turn_off"),
        ):
            handler = _ShortcutHandler(intent_type, action, self._domains)
            intent.async_register(self._hass, handler)
            self._handlers.append(handler)
            _LOGGER.debug("Assist Shortcuts: registered handler for %s", intent_type)

        _LOGGER.info("Assist Shortcuts: ready (domains: %s)", self._domains)

    def async_unload(self) -> None:
        """Unregister all intent handlers."""
        for handler in self._handlers:
            intent.async_unregister(self._hass, handler.intent_type)
        self._handlers.clear()
        _LOGGER.debug("Assist Shortcuts: handlers unregistered")

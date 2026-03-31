"""Intent handlers for Assist Shortcuts."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, intent
from homeassistant.helpers import floor_registry as fr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Slots injected into every intent so handlers know what to do
SLOT_ACTION = "action"
SLOT_TARGET_ID = "target_id"
SLOT_TARGET_TYPE = "target_type"  # "entity" | "area" | "floor"

TARGET_ENTITY = "entity"
TARGET_AREA = "area"
TARGET_FLOOR = "floor"


def _slugify(text: str) -> str:
    """Lower-case and collapse non-alphanumeric runs to a single space."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _names_for_entity(entry: er.RegistryEntry) -> list[str]:
    """Return all distinct slugified names we should register for an entity."""
    names: set[str] = set()

    # Friendly name (display name in HA UI)
    if entry.name:
        names.add(_slugify(entry.name))

    # Original name provided by the device integration
    if entry.original_name:
        names.add(_slugify(entry.original_name))

    # Aliases set by the user in the UI
    for alias in entry.aliases or []:
        if alias:
            names.add(_slugify(alias))

    # Filter out empty strings
    return [n for n in names if n]


class _ShortcutIntentHandler(intent.IntentHandler):
    """A single on/off intent handler for one target (entity, area, or floor)."""

    intent_type: str
    slot_schema = {}  # we don't parse slots from speech; they're baked into the handler

    def __init__(
        self,
        intent_type: str,
        target_type: str,
        target_id: str,
        action: str,
        domains: list[str],
    ) -> None:
        self.intent_type = intent_type
        self._target_type = target_type
        self._target_id = target_id
        self._action = action  # "turn_on" or "turn_off"
        self._domains = domains

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        hass = intent_obj.hass
        service = self._action  # "turn_on" / "turn_off"

        try:
            if self._target_type == TARGET_ENTITY:
                await hass.services.async_call(
                    "homeassistant",
                    service,
                    {"entity_id": self._target_id},
                    blocking=True,
                )
                _LOGGER.debug(
                    "Assist Shortcuts: %s entity %s", service, self._target_id
                )

            elif self._target_type == TARGET_AREA:
                for domain in self._domains:
                    await hass.services.async_call(
                        domain,
                        service,
                        {"area_id": self._target_id},
                        blocking=True,
                    )
                _LOGGER.debug(
                    "Assist Shortcuts: %s area %s (domains: %s)",
                    service,
                    self._target_id,
                    self._domains,
                )

            elif self._target_type == TARGET_FLOOR:
                # HA services don't accept floor_id directly; resolve areas first
                area_reg = ar.async_get(hass)
                for area in area_reg.areas.values():
                    if area.floor_id == self._target_id:
                        for domain in self._domains:
                            await hass.services.async_call(
                                domain,
                                service,
                                {"area_id": area.id},
                                blocking=True,
                            )
                _LOGGER.debug(
                    "Assist Shortcuts: %s floor %s (domains: %s)",
                    service,
                    self._target_id,
                    self._domains,
                )

        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Assist Shortcuts error: %s", err)
            raise RuntimeError(f"Could not {service} {self._target_id}") from err

        response = intent_obj.create_response()
        response.async_set_speech(
            f"OK, {'turning on' if service == 'turn_on' else 'turning off'} {self._target_id.replace('_', ' ')}."
        )
        return response


class AssistShortcutsIntentManager:
    """Builds and registers all shortcut intents, and tears them down on unload."""

    def __init__(self, hass: HomeAssistant, domains: list[str]) -> None:
        self._hass = hass
        self._domains = domains
        self._registered: list[str] = []  # intent type names we've registered

    async def async_setup(self) -> None:
        """Register one on+off intent pair per entity name / area / floor."""
        hass = self._hass
        registered_sentences: set[str] = set()

        entity_reg = er.async_get(hass)
        area_reg = ar.async_get(hass)
        floor_reg = fr.async_get(hass)

        idx = 0

        # ── Entities ──────────────────────────────────────────────────────────
        for entry in entity_reg.entities.values():
            if entry.hidden_by or entry.disabled_by:
                continue
            for name in _names_for_entity(entry):
                if not name:
                    continue
                for action, verb in (("turn_on", "on"), ("turn_off", "off")):
                    sentence = f"{name} {verb}"
                    if sentence in registered_sentences:
                        continue
                    registered_sentences.add(sentence)
                    intent_type = f"{DOMAIN}_e{idx}_{verb}"
                    idx += 1
                    handler = _ShortcutIntentHandler(
                        intent_type=intent_type,
                        target_type=TARGET_ENTITY,
                        target_id=entry.entity_id,
                        action=action,
                        domains=self._domains,
                    )
                    intent.async_register(hass, handler)
                    self._registered.append(intent_type)
                    # Register the sentence that triggers this intent
                    intent.async_register_sentences(
                        hass, DOMAIN, {intent_type: {"data": [{"sentences": [sentence]}]}}
                    )

        # ── Areas ─────────────────────────────────────────────────────────────
        for area in area_reg.areas.values():
            name = _slugify(area.name)
            if not name:
                continue
            for action, verb in (("turn_on", "on"), ("turn_off", "off")):
                sentence = f"{name} {verb}"
                if sentence in registered_sentences:
                    continue
                registered_sentences.add(sentence)
                intent_type = f"{DOMAIN}_a{idx}_{verb}"
                idx += 1
                handler = _ShortcutIntentHandler(
                    intent_type=intent_type,
                    target_type=TARGET_AREA,
                    target_id=area.id,
                    action=action,
                    domains=self._domains,
                )
                intent.async_register(hass, handler)
                self._registered.append(intent_type)
                intent.async_register_sentences(
                    hass, DOMAIN, {intent_type: {"data": [{"sentences": [sentence]}]}}
                )

        # ── Floors ────────────────────────────────────────────────────────────
        for floor in floor_reg.floors.values():
            for raw in [floor.name] + list(floor.aliases or []):
                name = _slugify(raw)
                if not name:
                    continue
                for action, verb in (("turn_on", "on"), ("turn_off", "off")):
                    sentence = f"{name} {verb}"
                    if sentence in registered_sentences:
                        continue
                    registered_sentences.add(sentence)
                    intent_type = f"{DOMAIN}_f{idx}_{verb}"
                    idx += 1
                    handler = _ShortcutIntentHandler(
                        intent_type=intent_type,
                        target_type=TARGET_FLOOR,
                        target_id=floor.floor_id,
                        action=action,
                        domains=self._domains,
                    )
                    intent.async_register(hass, handler)
                    self._registered.append(intent_type)
                    intent.async_register_sentences(
                        hass, DOMAIN, {intent_type: {"data": [{"sentences": [sentence]}]}}
                    )

        _LOGGER.info(
            "Assist Shortcuts: registered %d intent sentences across %d intents",
            len(registered_sentences),
            len(self._registered),
        )

    def async_unload(self) -> None:
        """Unregister all intents we registered."""
        for intent_type in self._registered:
            intent.async_unregister(self._hass, intent_type)
        self._registered.clear()
        _LOGGER.debug("Assist Shortcuts: all intents unregistered")

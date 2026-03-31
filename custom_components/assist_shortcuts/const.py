"""Constants for Assist Shortcuts."""

DOMAIN = "assist_shortcuts"

CONF_DOMAINS = "domains"

# Domains that support turn_on / turn_off
CONTROLLABLE_DOMAINS = [
    "light",
    "switch",
    "fan",
    "cover",
    "media_player",
    "climate",
    "input_boolean",
    "automation",
    "script",
    "vacuum",
    "humidifier",
    "water_heater",
    "lock",
]

DEFAULT_DOMAINS = ["light", "switch"]

# Intent name prefixes
INTENT_ENTITY_ON = "AssistShortcutEntityOn"
INTENT_ENTITY_OFF = "AssistShortcutEntityOff"
INTENT_AREA_ON = "AssistShortcutAreaOn"
INTENT_AREA_OFF = "AssistShortcutAreaOff"
INTENT_FLOOR_ON = "AssistShortcutFloorOn"
INTENT_FLOOR_OFF = "AssistShortcutFloorOff"

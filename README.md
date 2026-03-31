# Assist Shortcuts

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/andywarburton/assist-shortcuts.svg)](https://github.com/andywarburton/assist-shortcuts/releases)

Natural shorthand voice commands for Home Assistant Assist.

Say **"living room off"** instead of **"turn off the lights in the living room"**.  
Say **"cloud off"** instead of **"turn off the cloud light"**.

---

## How it works

On startup, Assist Shortcuts reads all your entities (including friendly names and aliases), areas, and floors and automatically registers a pair of `on` / `off` voice sentences for each one:

| You say | What happens |
|---|---|
| `cloud off` | Turns off the entity whose name/alias is "cloud" |
| `living room on` | Turns on all configured domains in the Living Room area |
| `upstairs off` | Turns off all configured domains on the Upstairs floor |

There is no fuzzy matching or AI involved — every sentence is an exact registered intent, so response time is identical to built-in Assist commands.

> **Note:** Adding a new device or area requires reloading the integration (or restarting Home Assistant) for the new shortcut to be registered.

---

## Installation

### Via HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Click **Custom repositories** and add:
   - **Repository:** `https://github.com/andywarburton/assist-shortcuts`
   - **Type:** Integration
3. Search for **Assist Shortcuts** in HACS and install it.
4. Restart Home Assistant.

### Manual

1. Copy the `custom_components/assist_shortcuts` folder into your `<config>/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

After installation, add the integration via **Settings → Devices & Services → Add Integration → Assist Shortcuts**.

You will be prompted to select which **domains** are controlled when you say an area or floor name (e.g. `living room off`). The default is **Light** and **Switch**.

Available domains:

| Domain | Controls |
|---|---|
| `light` | Lights |
| `switch` | Switches |
| `fan` | Fans |
| `cover` | Covers / blinds |
| `media_player` | Media players |
| `climate` | Climate devices |
| `input_boolean` | Input booleans |
| `lock` | Locks |
| `vacuum` | Vacuums |
| `humidifier` | Humidifiers |

Entity-level commands (e.g. `cloud off`) always target that specific entity only, regardless of domain settings.

### Changing the domain selection

Go to **Settings → Devices & Services → Assist Shortcuts → Configure** and update your domain selection. The integration will reload automatically.

---

## Examples

Given a setup with:
- An entity with friendly name **"Cloud"** in the **Living Room** area
- A floor called **"Upstairs"** containing the **Bedroom** and **Office** areas
- Domains configured as **light** and **switch**

The following voice commands will work:

```
cloud on          → turns on the Cloud entity
cloud off         → turns off the Cloud entity
living room on    → turns on all lights and switches in Living Room
living room off   → turns off all lights and switches in Living Room
upstairs on       → turns on all lights and switches in Bedroom and Office
upstairs off      → turns off all lights and switches in Bedroom and Office
```

---

## Troubleshooting

**My new device isn't recognised**  
Reload the integration: **Settings → Devices & Services → Assist Shortcuts → ⋮ → Reload**, or restart Home Assistant.

**A name with special characters doesn't work**  
Names are normalised to lowercase letters and numbers only. Accented characters and punctuation are replaced with spaces. If your entity is named `Björn's Light`, say `bjorns light on` or add a plain alias in the entity settings.

**Two entities have the same name**  
The first one registered wins. Add distinct aliases to your entities via **Settings → Devices & Services → [Device] → [Entity] → ⚙ → Aliases**.

---

## Contributing

Pull requests and issues are welcome at [github.com/andywarburton/assist-shortcuts](https://github.com/andywarburton/assist-shortcuts).

---

## License

MIT

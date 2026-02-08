# Quick Installation Guide

## Prerequisites

- Home Assistant Core or Home Assistant OS
- Python scripts integration enabled
- All required climate entities configured
- Heating switch (`switch.sonoff_10017fadeb`) configured
- Graceful shutdown button (`input_button.wylacznik_pompy`) configured

## Installation Steps

### 1. Copy Files

```bash
# Create directories if they don't exist
mkdir -p /config/python_scripts
mkdir -p /config/automations

# Copy the heating manager script
cp python_scripts/heating_manager.py /config/python_scripts/

# Copy automation configuration
cp automations/heating_automations.yaml /config/automations/

# Copy input helpers
cp config/input_helpers.yaml /config/
```

### 2. Update configuration.yaml

Add to your `/config/configuration.yaml`:

```yaml
# Enable Python scripts
python_script:

# Include automations (choose one method)
# Method 1: Include file directly
automation: !include automations/heating_automations.yaml

# Method 2: Merge with existing automations
# automation: !include_dir_merge_list automations/

# Include input helpers
# You need to manually copy the contents of input_helpers.yaml into your
# configuration.yaml under the appropriate sections (input_text, input_boolean, etc.)
# OR split the file and include separately. See configuration.yaml.example for details.
```

**Important**: The `input_helpers.yaml` file contains all four helper types. You must either:
1. Copy the contents manually into your `configuration.yaml`
2. Split it into separate files (one per helper type) and include each separately

### 3. Verify Entity Names

Ensure these entities exist in your Home Assistant:

**Climate entities:**
- `climate.gabinet_ani`
- `climate.lazienka_parter`
- `climate.salon`
- `climate.sypialnia`
- `climate.lazienka_pietro`
- `climate.pokoj_z_oknem_naroznym`
- `climate.pokoj_z_tarasem`

**Control entities:**
- `switch.sonoff_10017fadeb`
- `input_button.wylacznik_pompy`

If your entity names are different, edit `python_scripts/heating_manager.py` and `automations/heating_automations.yaml` to match your configuration.

### 4. Check Configuration

```bash
# Check configuration for errors
ha core check
```

### 5. Restart Home Assistant

```bash
# Restart Home Assistant
ha core restart
```

Or use the UI: **Settings** → **System** → **Restart**

### 6. Verify Installation

1. Go to **Developer Tools** → **States**
2. Search for `input_text.heating_runtime_data` - should exist
3. Search for `input_boolean.heating_system_enabled` - should exist
4. Go to **Settings** → **Automations & Scenes**
5. Verify these automations are loaded:
   - Heating: Enable on Low Temperature
   - Heating: Disable on High Temperature
   - Heating: Periodic System Check
   - Heating: Temperature Change Monitor
   - Heating: Runtime Limit Check
   - Heating: Daily Runtime Reset

### 7. Initial Setup

1. Enable the heating automation:
   - Toggle `input_boolean.heating_system_enabled` to ON
2. Set desired thresholds:
   - `input_number.heating_target_temperature` = 19°C
   - `input_number.heating_enable_threshold` = 17°C
   - `input_number.heating_disable_threshold` = 19°C

## Testing

### Manual Test

1. Check current temperatures of all climate entities
2. If any room is below 17°C, the system should automatically enable heating
3. Monitor the logbook for heating system events
4. Verify that only one floor is being heated at a time

### Troubleshooting

**Python script not loading:**
- Check Home Assistant logs: `ha core logs`
- Verify python_script integration is enabled
- Check file permissions on `/config/python_scripts/heating_manager.py`

**Automations not triggering:**
- Check automation states in **Settings** → **Automations**
- Verify entity names match your configuration
- Check traces in automation details

**Runtime data not saving:**
- Verify `input_text.heating_runtime_data` exists
- Check that it has max length of at least 2048 characters
- Review Home Assistant logs for errors

## Post-Installation

1. Monitor system operation for 24 hours
2. Adjust thresholds if needed
3. Review logbook entries for any issues
4. Fine-tune room priorities if necessary

## Need Help?

- Check the main README.md for detailed troubleshooting
- Review Home Assistant logs
- Verify all entities are available and responding

# Home Assistant Heating Automation

A comprehensive Home Assistant automation system for managing a multi-room heating system with intelligent room prioritization, floor-based heating control, and runtime management.

## Features

- **Automatic Temperature Control**: Enable heating when any room drops below 17°C, disable when all rooms exceed 19°C
- **Room Priority System**: Prioritize heating based on temperature delta to 19°C target
- **Bathroom Priority**: Bathrooms receive heating preference for occupant comfort
- **Floor-Based Control**: Heat only one floor at a time to optimize energy usage
- **Runtime Management**: 
  - Maximum 18 hours of continuous system operation
  - Maximum 3 hours per room heating session
  - Minimum 3-hour cycles to prevent frequent on/off switching
- **Graceful Shutdown**: Uses `input_button.wylacznik_pompy` for proper system shutdown
- **Daily Reset**: Automatic runtime counter reset at midnight

## System Architecture

### Entities

#### Climate Entities (7 rooms across 2 floors)

**Ground Floor:**
- `climate.gabinet_ani` - Office
- `climate.lazienka_parter` - Ground floor bathroom
- `climate.salon` - Living room

**First Floor:**
- `climate.sypialnia` - Bedroom
- `climate.lazienka_pietro` - First floor bathroom
- `climate.pokoj_z_oknem_naroznym` - Corner window room
- `climate.pokoj_z_tarasem` - Terrace room

#### Control Entities
- `switch.sonoff_10017fadeb` - Main heating system switch
- `input_button.wylacznik_pompy` - Graceful shutdown button

## Installation

### Step 1: Copy Files to Home Assistant

Copy the files to your Home Assistant configuration directory:

```bash
# Copy Python script
cp python_scripts/heating_manager.py /config/python_scripts/

# Copy automation configuration
cp automations/heating_automations.yaml /config/automations/

# Copy input helpers configuration
cp config/input_helpers.yaml /config/
```

### Step 2: Enable Python Scripts

Add to your `configuration.yaml`:

```yaml
# Enable Python scripts
python_script:

# Include automation configuration
automation: !include automations/heating_automations.yaml
```

For the input helpers, you need to manually copy the contents of `input_helpers.yaml` into your `configuration.yaml` file, placing each section under the appropriate key (`input_text:`, `input_boolean:`, `input_number:`, `input_datetime:`). See the Configuration section below for details.

### Step 3: Restart Home Assistant

Restart Home Assistant to load the new configuration:
- Go to **Settings** → **System** → **Restart**
- Or use the command: `ha core restart`

### Step 4: Verify Setup

1. Check that all climate entities are available
2. Verify the heating switch (`switch.sonoff_10017fadeb`) is accessible
3. Confirm the shutdown button (`input_button.wylacznik_pompy`) exists
4. Check that input helpers were created successfully

## Configuration

### Adjustable Parameters

The system has several configurable parameters in `input_helpers.yaml`:

- **Target Temperature**: Default 19°C (adjustable via `input_number.heating_target_temperature`)
- **Enable Threshold**: Default 17°C (adjustable via `input_number.heating_enable_threshold`)
- **Disable Threshold**: Default 19°C (adjustable via `input_number.heating_disable_threshold`)

### Customization

To customize the heating logic, edit `python_scripts/heating_manager.py`:

```python
# Temperature thresholds
ENABLE_THRESHOLD = 17.0
DISABLE_THRESHOLD = 19.0
TARGET_TEMP = 19.0

# Runtime limits (in hours)
SYSTEM_MAX_RUNTIME = 18
ROOM_MAX_RUNTIME = 3
MIN_CYCLE_TIME = 3
```

## Operation

### Automatic Operation

The system operates automatically based on the following rules:

1. **Enable Heating**: Triggered when any room temperature falls below 17°C
2. **Disable Heating**: Triggered when all rooms exceed 19°C
3. **Room Selection**: Every 5 minutes, the system evaluates which room needs heating most
4. **Floor Alternation**: Only one floor is heated at a time, alternating as needed
5. **Runtime Tracking**: System monitors and enforces runtime limits

### Manual Control

You can manually control the system:

- **Enable Heating**: Turn on `switch.sonoff_10017fadeb`
- **Disable Heating**: Press `input_button.wylacznik_pompy` (graceful shutdown)
- **Pause System**: Toggle `input_boolean.heating_system_enabled` to disable automations

### Monitoring

Monitor the system through:

- **Logbook**: All heating events are logged
- **Developer Tools → States**: Check `input_text.heating_runtime_data` for runtime statistics
- **Climate Entity States**: Monitor current and target temperatures

## Operational Rules

### Priority Logic

Rooms are prioritized for heating based on:

1. **Temperature Delta**: Rooms further from 19°C target get priority
2. **Bathroom Bonus**: Bathrooms receive a +0.5°C bonus in priority calculation
3. **Floor Constraints**: Only one floor heated at a time
4. **Runtime Limits**: Rooms that reached 3-hour limit are excluded

### Runtime Management

- **System Maximum**: 18 hours continuous operation per day
- **Room Maximum**: 3 hours per room per heating session
- **Minimum Cycle**: 3 hours minimum between on/off cycles
- **Daily Reset**: All counters reset at midnight

### Floor Heating Strategy

The system alternates between floors based on:
- Current floor being heated
- Available rooms needing heat on each floor
- Temperature priorities

When the current floor has no rooms needing heat, the system switches to the other floor.

## Troubleshooting

### Heating Not Enabling

1. Check that `input_boolean.heating_system_enabled` is ON
2. Verify at least one room temperature is below 17°C
3. Check that system hasn't reached 18-hour runtime limit
4. Review logbook for error messages

### Rooms Not Heating

1. Verify room climate entity is available
2. Check that room hasn't exceeded 3-hour runtime limit
3. Confirm the room's floor is currently selected for heating
4. Check that room temperature is actually below target

### Frequent On/Off Cycling

The system has built-in protection against frequent cycling:
- Minimum 3-hour active periods
- Minimum 3-hour inactive periods

If cycling still occurs, check:
- Temperature sensor accuracy
- Thermostat calibration
- Room insulation issues

### System Won't Disable

1. Check that all rooms are above 19°C
2. Verify minimum cycle time (3 hours) has elapsed
3. Manually press `input_button.wylacznik_pompy`
4. Check logbook for error messages

## Maintenance

### Daily Tasks
- Monitor system operation through logbook
- Check that temperatures are within expected ranges

### Weekly Tasks
- Review runtime statistics in `input_text.heating_runtime_data`
- Verify all climate entities are responding correctly

### Monthly Tasks
- Calibrate temperature sensors if needed
- Review and adjust thresholds based on seasonal changes
- Check for any automation errors in Home Assistant logs

## Advanced Configuration

### Custom Floor Configuration

To modify floor assignments, edit `python_scripts/heating_manager.py`:

```python
GROUND_FLOOR_ROOMS = [
    "climate.your_room_1",
    "climate.your_room_2",
]

FIRST_FLOOR_ROOMS = [
    "climate.your_room_3",
    "climate.your_room_4",
]
```

### Custom Bathroom Priority

To change which rooms get bathroom priority:

```python
BATHROOMS = [
    "climate.your_bathroom_1",
    "climate.your_bathroom_2"
]
```

### Automation Frequency

To change how often the system checks room priorities, edit `automations/heating_automations.yaml`:

```yaml
- id: heating_periodic_check
  trigger:
    - platform: time_pattern
      minutes: "/5"  # Change this value (every 5 minutes)
```

## Safety Features

- **Graceful Shutdown**: Always uses `input_button.wylacznik_pompy` instead of direct switch toggle
- **Runtime Limits**: Prevents excessive continuous operation
- **Minimum Cycles**: Prevents equipment wear from frequent switching
- **Daily Reset**: Ensures fresh start each day
- **Error Handling**: Robust null checks and error handling in Python script

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Home Assistant logs for errors
3. Open an issue on the GitHub repository

## Acknowledgments

Developed for managing multi-room heating systems in Home Assistant with intelligent prioritization and energy-efficient operation.
# Architecture and Design Document

## Overview

This document describes the architecture and design decisions for the Home Assistant Heating Automation system.

## System Components

### 1. Python Script (heating_manager.py)

The core logic is implemented as a Home Assistant Python script that manages:

- **Temperature Monitoring**: Reads current temperatures from climate entities
- **Priority Calculation**: Determines which rooms need heating most
- **Floor Management**: Ensures only one floor is heated at a time
- **Runtime Tracking**: Monitors and enforces time limits
- **Control Actions**: Manages heating system switch and climate entity targets

#### Key Functions

```python
should_enable_heating(hass)
# Returns True if any room < 17°C

should_disable_heating(hass)
# Returns True if all rooms > 19°C

calculate_temperature_delta(hass, entity_id)
# Returns difference between current temp and 19°C target

select_priority_room(hass, available_rooms)
# Selects room with highest priority (delta + bathroom bonus)

manage_heating_system(hass, action)
# Main entry point: 'check', 'enable', or 'disable'
```

### 2. Automations (heating_automations.yaml)

Six automations coordinate system operation:

1. **Enable on Low Temperature**: Triggers when any room < 17°C
2. **Disable on High Temperature**: Triggers when all rooms > 19°C
3. **Periodic System Check**: Runs every 5 minutes to adjust priorities
4. **Temperature Change Monitor**: Triggers on any temperature change
5. **Runtime Limit Check**: Hourly verification of runtime limits
6. **Daily Runtime Reset**: Resets counters at midnight

### 3. Input Helpers (input_helpers.yaml)

State storage and configuration:

- **input_text.heating_runtime_data**: JSON storage for runtime tracking
- **input_boolean.heating_system_enabled**: Master enable/disable
- **input_number**: Configurable thresholds and targets
- **input_datetime**: Timestamp tracking

## Data Flow

```
Temperature Sensors (Climate Entities)
    ↓
Automation Triggers
    ↓
Python Script (heating_manager.py)
    ↓
Decision Logic (priority, floor, runtime)
    ↓
Actions (switch, climate targets, logging)
    ↓
State Storage (input_text.heating_runtime_data)
```

## Design Decisions

### 1. Single Floor Heating

**Decision**: Heat only one floor at a time

**Rationale**:
- Optimizes energy usage
- Prevents overload on heating system
- Allows focused heating for better efficiency

**Implementation**:
- Track current floor in runtime data
- Filter available rooms by floor
- Alternate floors when switching

### 2. Priority Calculation

**Decision**: Use temperature delta with bathroom bonus

**Rationale**:
- Objective measurement of heating need
- Bathrooms prioritized for comfort
- Simple, transparent algorithm

**Implementation**:
```python
delta = TARGET_TEMP - current_temp
if room in BATHROOMS:
    delta += 0.5
```

### 3. Runtime Tracking

**Decision**: Store runtime data in JSON within input_text

**Rationale**:
- No external database required
- Persists across restarts
- Easy to inspect and debug

**Limitations**:
- 2048 character limit
- Manual serialization required
- No historical data beyond current state

### 4. Graceful Shutdown

**Decision**: Use input_button.wylacznik_pompy instead of direct switch

**Rationale**:
- Allows heating system to complete current cycle
- Prevents abrupt shutdowns
- Hardware-specific requirement

**Implementation**:
- All disable actions use the button
- Never toggle switch directly for disable

### 5. Minimum Cycle Time

**Decision**: 3-hour minimum on/off cycles

**Rationale**:
- Prevents equipment wear
- Reduces energy waste from frequent cycling
- Allows rooms to reach stable temperatures

**Implementation**:
- Track last cycle start time
- Block enable/disable if minimum time not elapsed

## Error Handling

### Temperature Sensor Failures

```python
temp = get_room_temperature(hass, entity_id)
if temp is None:
    return None  # Skip this room
```

### JSON Parse Errors

```python
try:
    return json.loads(state.state)
except json.JSONDecodeError:
    return default_data  # Use defaults
```

### Missing Entities

```python
state = hass.states.get(entity_id)
if state is None:
    return None  # Safely handle missing
```

## Performance Considerations

### 1. Automation Frequency

- Periodic check: Every 5 minutes (configurable)
- Temperature triggers: On change (could be frequent)
- Runtime check: Every hour

**Trade-off**: Responsiveness vs. system load

### 2. Room Iteration

- O(n) for room temperature checks
- O(n) for priority calculation
- With 7 rooms, performance is not a concern

### 3. State Storage

- JSON serialization on every update
- 2048 character limit is sufficient for current data
- No cleanup or archival needed (daily reset)

## Scalability

### Adding Rooms

1. Add climate entity to appropriate floor list
2. Update automation triggers
3. No changes to core logic needed

### Adding Floors

1. Define new floor in FLOOR_ROOMS arrays
2. Update floor selection logic
3. May need to adjust alternation strategy

### Configuration Changes

- Thresholds: Change in Python script or via input_number
- Runtime limits: Change constants in Python script
- Automation frequency: Modify time_pattern in YAML

## Testing Strategy

### Unit Testing (Manual)

Test individual functions with known inputs:
- Temperature reading
- Delta calculation
- Priority selection
- Runtime tracking

### Integration Testing

Test full system with simulated conditions:
- Create test climate entities
- Set specific temperatures
- Verify correct actions taken

### Operational Testing

Monitor live system:
- Check logbook entries
- Verify expected behavior
- Measure actual runtime

## Future Enhancements

### Possible Improvements

1. **Historical Data**: Store daily/weekly statistics
2. **Learning System**: Adjust based on heating patterns
3. **Weather Integration**: Adjust thresholds based on outdoor temperature
4. **Energy Monitoring**: Track actual energy consumption
5. **Notifications**: Alert on anomalies or maintenance needs
6. **Multi-Zone**: Support heating zones beyond floors
7. **Schedule Integration**: Coordinate with occupancy schedules

### Technical Debt

1. **Hardcoded Constants**: Move to configuration
2. **Limited Storage**: Consider using database for history
3. **Error Logging**: Enhance logging and diagnostics
4. **Unit Tests**: Add automated test coverage

## Security Considerations

### Access Control

- Python scripts run with full Home Assistant privileges
- No user input validation needed (internal only)
- State data is trusted

### Data Privacy

- Only temperature data stored
- No personal information collected
- Runtime data visible to all HA users

### Safety

- Runtime limits prevent excessive operation
- Graceful shutdown protects equipment
- Multiple failsafes (automations + manual control)

## Dependencies

- Home Assistant Core (tested on 2024.x)
- Python 3.x (provided by HA)
- Climate integration (various, entity-specific)
- Switch integration (Sonoff device)

## Maintenance

### Regular Tasks

- Monitor logbook for errors
- Verify automation execution
- Check runtime data integrity

### Updates

- Test on Home Assistant updates
- Review deprecated API calls
- Update documentation

### Debugging

1. Enable debug logging for automations
2. Check Developer Tools → States
3. Review Home Assistant logs
4. Trace automation execution

## Conclusion

This architecture provides a robust, maintainable solution for multi-room heating automation with intelligent prioritization and safety features. The design balances simplicity with functionality, making it easy to understand, modify, and extend.

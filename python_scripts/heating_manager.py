"""
Home Assistant Heating System Manager

This script manages a multi-room heating system with the following rules:
- Enable heating if any room falls below 17°C
- Disable heating if all rooms exceed 19°C
- Heat only one floor at a time
- Prioritize rooms by temperature delta to 19°C
- Prefer bathrooms for comfort
- Enforce runtime limits: 3 hours per room, 18 hours system max
- Minimize on/off cycling with 3-hour minimum runtime periods
"""

import json
from datetime import datetime, timedelta

# Room definitions by floor
GROUND_FLOOR_ROOMS = [
    "climate.gabinet_ani",
    "climate.lazienka_parter",
    "climate.salon"
]

FIRST_FLOOR_ROOMS = [
    "climate.sypialnia",
    "climate.lazienka_pietro",
    "climate.pokoj_z_oknem_naroznym",
    "climate.pokoj_z_tarasem"
]

ALL_ROOMS = GROUND_FLOOR_ROOMS + FIRST_FLOOR_ROOMS

# Bathroom priority
BATHROOMS = [
    "climate.lazienka_parter",
    "climate.lazienka_pietro"
]

# Temperature thresholds
ENABLE_THRESHOLD = 17.0
DISABLE_THRESHOLD = 19.0
TARGET_TEMP = 19.0

# Runtime limits (in hours)
SYSTEM_MAX_RUNTIME = 18
ROOM_MAX_RUNTIME = 3
MIN_CYCLE_TIME = 3

# Entities
HEATING_SWITCH = "switch.sonoff_10017fadeb"
SHUTDOWN_BUTTON = "input_button.wylacznik_pompy"


def get_room_temperature(hass, entity_id):
    """Get current temperature for a room."""
    state = hass.states.get(entity_id)
    if state is None:
        return None
    
    try:
        return float(state.attributes.get('current_temperature', 0))
    except (ValueError, TypeError):
        return None


def get_room_target_temperature(hass, entity_id):
    """Get target temperature for a room."""
    state = hass.states.get(entity_id)
    if state is None:
        return None
    
    try:
        return float(state.attributes.get('temperature', 0))
    except (ValueError, TypeError):
        return None


def set_room_target_temperature(hass, entity_id, temperature):
    """Set target temperature for a room."""
    hass.services.call('climate', 'set_temperature', {
        'entity_id': entity_id,
        'temperature': temperature
    })


def calculate_temperature_delta(hass, entity_id):
    """Calculate temperature delta from target (19°C)."""
    current_temp = get_room_temperature(hass, entity_id)
    if current_temp is None:
        return None
    return TARGET_TEMP - current_temp


def should_enable_heating(hass):
    """Check if heating should be enabled (any room < 17°C)."""
    for room in ALL_ROOMS:
        temp = get_room_temperature(hass, room)
        if temp is not None and temp < ENABLE_THRESHOLD:
            return True
    return False


def should_disable_heating(hass):
    """Check if heating should be disabled (all rooms > 19°C)."""
    for room in ALL_ROOMS:
        temp = get_room_temperature(hass, room)
        if temp is None or temp <= DISABLE_THRESHOLD:
            return False
    return True


def get_floor_rooms(floor):
    """Get list of rooms for a floor (0=ground, 1=first)."""
    if floor == 0:
        return GROUND_FLOOR_ROOMS
    elif floor == 1:
        return FIRST_FLOOR_ROOMS
    return []


def select_priority_room(hass, available_rooms):
    """
    Select room with highest heating priority.
    Priority: largest temperature delta, bathrooms preferred.
    """
    best_room = None
    best_delta = 0
    
    for room in available_rooms:
        delta = calculate_temperature_delta(hass, room)
        if delta is None or delta <= 0:
            continue
        
        # Apply bathroom bonus
        if room in BATHROOMS:
            delta += 0.5
        
        if delta > best_delta:
            best_delta = delta
            best_room = room
    
    return best_room


def get_runtime_data(hass):
    """Get runtime tracking data from input_text helper."""
    state = hass.states.get('input_text.heating_runtime_data')
    if state is None or not state.state:
        return {
            'system_start': None,
            'system_runtime': 0,
            'room_runtimes': {},
            'last_cycle_start': None,
            'current_floor': None,
            'cycle_count': 0
        }
    
    try:
        return json.loads(state.state)
    except json.JSONDecodeError:
        return {
            'system_start': None,
            'system_runtime': 0,
            'room_runtimes': {},
            'last_cycle_start': None,
            'current_floor': None,
            'cycle_count': 0
        }


def save_runtime_data(hass, data):
    """Save runtime tracking data to input_text helper."""
    hass.services.call('input_text', 'set_value', {
        'entity_id': 'input_text.heating_runtime_data',
        'value': json.dumps(data)
    })


def get_elapsed_hours(start_time_str):
    """Calculate elapsed hours from ISO timestamp string."""
    if not start_time_str:
        return 0
    
    try:
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now() - start_time
        return elapsed.total_seconds() / 3600
    except (ValueError, TypeError):
        return 0


def manage_heating_system(hass, action):
    """
    Main heating management function.
    
    Args:
        action: 'check' - evaluate and update heating status
                'enable' - force enable heating
                'disable' - force disable heating
    """
    logger = hass.states.get('logger')
    runtime_data = get_runtime_data(hass)
    now = datetime.now().isoformat()
    
    # Check system runtime limit
    if runtime_data.get('system_start'):
        system_runtime = get_elapsed_hours(runtime_data['system_start'])
        if system_runtime >= SYSTEM_MAX_RUNTIME:
            logger.warning(f"System runtime limit reached: {system_runtime:.1f} hours")
            # Force graceful shutdown
            hass.services.call('input_button', 'press', {
                'entity_id': SHUTDOWN_BUTTON
            })
            runtime_data['system_start'] = None
            runtime_data['system_runtime'] = 0
            save_runtime_data(hass, runtime_data)
            return
    
    # Handle enable action
    if action == 'enable':
        switch_state = hass.states.get(HEATING_SWITCH)
        if switch_state and switch_state.state == 'off':
            hass.services.call('switch', 'turn_on', {
                'entity_id': HEATING_SWITCH
            })
            runtime_data['system_start'] = now
            runtime_data['last_cycle_start'] = now
            save_runtime_data(hass, runtime_data)
        return
    
    # Handle disable action
    if action == 'disable':
        switch_state = hass.states.get(HEATING_SWITCH)
        if switch_state and switch_state.state == 'on':
            # Check minimum cycle time
            if runtime_data.get('last_cycle_start'):
                cycle_time = get_elapsed_hours(runtime_data['last_cycle_start'])
                if cycle_time < MIN_CYCLE_TIME:
                    logger.info(f"Minimum cycle time not reached: {cycle_time:.1f} hours")
                    return
            
            # Graceful shutdown
            hass.services.call('input_button', 'press', {
                'entity_id': SHUTDOWN_BUTTON
            })
            runtime_data['system_start'] = None
            runtime_data['last_cycle_start'] = None
            runtime_data['current_floor'] = None
            save_runtime_data(hass, runtime_data)
        return
    
    # Handle check action - evaluate and adjust
    if action == 'check':
        # Check if we should enable heating
        if should_enable_heating(hass):
            switch_state = hass.states.get(HEATING_SWITCH)
            if switch_state and switch_state.state == 'off':
                # Check minimum off time
                if runtime_data.get('last_cycle_start'):
                    off_time = get_elapsed_hours(runtime_data['last_cycle_start'])
                    if off_time < MIN_CYCLE_TIME:
                        logger.info(f"Minimum off time not reached: {off_time:.1f} hours")
                        return
                
                manage_heating_system(hass, 'enable')
                return
        
        # Check if we should disable heating
        if should_disable_heating(hass):
            switch_state = hass.states.get(HEATING_SWITCH)
            if switch_state and switch_state.state == 'on':
                manage_heating_system(hass, 'disable')
                return
        
        # Manage room priorities if heating is on
        switch_state = hass.states.get(HEATING_SWITCH)
        if switch_state and switch_state.state == 'on':
            # Determine which floor to heat
            current_floor = runtime_data.get('current_floor')
            
            # Check room runtimes and filter available rooms
            available_rooms_ground = []
            available_rooms_first = []
            
            for room in GROUND_FLOOR_ROOMS:
                room_runtime = runtime_data['room_runtimes'].get(room, {})
                if not room_runtime.get('start') or \
                   get_elapsed_hours(room_runtime.get('start', '')) >= ROOM_MAX_RUNTIME:
                    delta = calculate_temperature_delta(hass, room)
                    if delta and delta > 0:
                        available_rooms_ground.append(room)
            
            for room in FIRST_FLOOR_ROOMS:
                room_runtime = runtime_data['room_runtimes'].get(room, {})
                if not room_runtime.get('start') or \
                   get_elapsed_hours(room_runtime.get('start', '')) >= ROOM_MAX_RUNTIME:
                    delta = calculate_temperature_delta(hass, room)
                    if delta and delta > 0:
                        available_rooms_first.append(room)
            
            # Select floor and room
            selected_room = None
            selected_floor = None
            
            if current_floor == 0 and available_rooms_ground:
                selected_room = select_priority_room(hass, available_rooms_ground)
                selected_floor = 0
            elif current_floor == 1 and available_rooms_first:
                selected_room = select_priority_room(hass, available_rooms_first)
                selected_floor = 1
            else:
                # Alternate floors or choose best available
                if available_rooms_ground:
                    selected_room = select_priority_room(hass, available_rooms_ground)
                    selected_floor = 0
                elif available_rooms_first:
                    selected_room = select_priority_room(hass, available_rooms_first)
                    selected_floor = 1
            
            # Set room target temperatures
            if selected_room:
                runtime_data['current_floor'] = selected_floor
                
                # Set target for selected room
                set_room_target_temperature(hass, selected_room, TARGET_TEMP)
                
                # Track room runtime
                if selected_room not in runtime_data['room_runtimes']:
                    runtime_data['room_runtimes'][selected_room] = {'start': now}
                
                # Lower temperature for other rooms on same floor
                floor_rooms = get_floor_rooms(selected_floor)
                for room in floor_rooms:
                    if room != selected_room:
                        set_room_target_temperature(hass, room, 16.0)
                
                # Lower temperature for all rooms on other floor
                other_floor = 1 if selected_floor == 0 else 0
                other_rooms = get_floor_rooms(other_floor)
                for room in other_rooms:
                    set_room_target_temperature(hass, room, 16.0)
                
                save_runtime_data(hass, runtime_data)


# Entry point for Home Assistant python_script
if 'action' in data:
    manage_heating_system(hass, data['action'])
else:
    manage_heating_system(hass, 'check')

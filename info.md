# Home Assistant Ksenia Lares integration
Ksenia Lares 48IP integration for home assistant. Compatible with BTicino alarm systems.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | For each zone, defaults to movement sensor.
`sensor` | For each partition, showing the ARM status. 
`alarm_control_panel` | ARM and disarm based on partitions and scenarios
`switch` | Bypass zones/partitions

## Requirements
This integration relies on the web interface to be activated, this is not always the case. Please contact your alarm intaller for more information on activation.

## Configuration
Follow configuration can optionally be done, after integration setup.

### Mapping Alarm
The KSENIA Lares alarm uses more complex scenarios then the default states of the home assistant alarm (away, night, home). A mapping is needed between the Home Assistant states and the KSENIA Lares scenarios (for activation) and zones/partitions (for state).

### Bypass zones
To be able to bypass zones, you will need to configure a PIN to be used. 
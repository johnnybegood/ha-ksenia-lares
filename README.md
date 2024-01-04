# Home Assistant Ksenia Lares integration
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

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

## Installation
### Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=johnnybegood&repository=ha-ksenia-lares)

1. Open HACS
2. Goto the menu in to top right corner
3. Goto custom respositories
4. Add this repositry `https://github.com/johnnybegood/ha-ksenia-lares`
5. Click _explore & download respositories_
6. Search for and add "Ksenia Lares"
7. Restart Home Assistant
8. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Ksenia Lares" or click the button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ksenia_lares)

### Installation directly

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `ksenia_lares`.
4. Download _all_ the files from the `custom_components/ksenia_lares/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Ksenia Lares" or click the button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ksenia_lares)

## Configuration
### Mapping Alarm
The KSENIA Lares alarm uses more complex scenarios then the default states of the home assistant alarm (away, night, home). A mapping is needed between the Home Assistant states and the KSENIA Lares scenarios (for activation) and zones/partitions (for state).

Go to [integration](https://my.home-assistant.io/redirect/integration/?domain=ksenia_lares) to setup the mapping. 

### Bypass zones
To be able to bypass zones, you will need to configure a PIN to be used. 

1. Go to [integration](https://my.home-assistant.io/redirect/integration/?domain=ksenia_lares)
2. Click 'Configure'
3. Enter the PIN code to use (it will need to be entered again each time the configuration screen is used).

# Home Assistant Ksenia Lares integration

[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

Ksenia Lares 48IP integration for home assistant. This is integration is in early stages, use at own risk.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | For each zone, defaults to movement sensor.
`sensor` | For each partition, showing the ARM status. 
`alarm_panel` | ARM and disarm based on partitions and scenarios

## Installation
### Installation via HACS
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

## Quickstart
1. Check your Ksenia Lares has the web interface running
2. Enter the following information from Ksenia Lares 48IP web interface:
   1. Hostname or IP adress (port 4202 will be used)
   2. Username
   3. Password
3. To be able to use the alarm panel, click the 'configure' button on the Ksenia Lares [integration](https://my.home-assistant.io/redirect/integrations/)
4.  Select the partitions and scenarios that match different ARM states.
    1.  When the selected partitions are armed, the alarm panel will show the corresponding state.
    2.  The selected scenario will be activated when changing arm state of the alarm panel

## WIP
- [x] Detect zones from Lares alarm system and show as binary sensor 
- [ ] Integrate with alarm panel in Home Assistant
- [ ] Add logo
- [ ] Improve configuration
- [ ] Move SDK/API to seperate repo
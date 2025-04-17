[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]](hacs)
[![hacs][hacs-shield]](https://my.home-assistant.io/redirect/hacs_repository/?owner=EnlightningMan&repository=ha-bsh_tides&category=integration)


# BSH Tides for Germany Integration for Home Assistant

Custom integration to fetch tidal forecast data from the German Federal Maritime and Hydrographic Agency / the Bundesamt für Seeschifffahrt und Hydrographie (BSH).

DISCLAIMER: This project is a private open source project and doesn't have any connection with BSH. The integration utilizes a public but uncommented API of the BSH. It might break or vanish in the future.

🌊 **Features**

Creates Home Assistant devices and sensors for multiple data points:
- time, water level, expected deviation from mean water level for the next upcoming tide
- time, water level, expected deviation from mean water level for the upcoming high and low tides
- mean low/high tide water levels for the selected station
- timestamp of when the forecast was made
- geograpical area of the station
- You can add multiple stations to HA.

![BSH Sensors](images/bsh_sensors.png)
![BSH Diagnostic Sensors](images/bsh_diagnostic_sensors.png)

📡 **Data Source**

The [BSH Tide Data](https://wasserstand-nordsee.bsh.de/) provides tide data for the German North Sea costal region including measuring points for tide affected rivers: 
- Ems, 
- Weser,
- Elbe,
- Jade und Ostfriesland,
- Nordfriesland bis Elbmündung (inkl. Helgoland)

Check [link](https://wasserstand-nordsee.bsh.de/) for supported gauging stations.

Data © Bundesamt für Seeschifffahrt und Hydrographie (BSH)

## 🔧 Installation

### 📦 Installation via HACS

You can add this custom integration to your Home Assistant setup using [HACS](https://hacs.xyz/):

1. Click [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=EnlightningMan&repository=ha-bsh_tides&category=integration) 
   1. Or:
   1. Go to HACS → Integrations → ⋮ → *Custom repositories*
   1. Paste the URL of this repo and select category "Integration"
   1. Search for **BSH Tides for Germany** 
1. Click install
1. Restart Home Assistant

Then
1. In the HA UI go to Go to `Settings → Devices & Services → + Add Integration` and select **"BSH Tides for Germany"** or use the button: [![Open your Home Assistant instance and start setting up this integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=bsh_tides) _You can repeat this for as many stations as you like._ 
1. Follow the setup instructions.

### 💾 Manual Installation
1. Copy `custom_components/bsh_tides` into your Home Assistant `config/custom_components/` directory.
1. Restart Home Assistant.
1. Go to `Settings → Devices & Services → + Add Integration` and select **"BSH Tides for Germany"**.
1. Follow the setup instructions.

## 📍 Supported Stations

The full list of supported stations can be seen in the map overview at https://wasserstand-nordsee.bsh.de/



## 🖼️ Visualization & Template Examples
![BSH Dashboard Visualization](images/bsh_mushroom_sensors.png)

Find the code for the above cards as examples in these files:

- [Dashboard badge](docs/dashboard_examples/bsh_tides_badge.yaml)
- [Next tide at station](docs/dashboard_examples/bsh_tides_next_tide_at_station.yaml) (Mushroom Template)
- [Next high and low tide](docs/dashboard_examples/bsh_tides_next_high_and_low_tide.yaml) (Mushroom Template)
- [Next high and low tide sorted by time](docs/dashboard_examples/bsh_tides_next_tides_by_time.yaml) (Mushroom Template)
- [Next tide events](docs/dashboard_examples/bsh_tides_next_tide_events.yaml) (Mushroom Template)

You can copy these into your dashboard using the YAML editor.

## 📄 License & Attribution

- Data: © BSH – Bundesamt für Seeschifffahrt und Hydrographie  
- Integration: MIT License

## 🔐 Note on SSL Certificate Verification

> This integration **disables strict SSL certificate validation** when connecting to the BSH tide API.

While the connection is still **secure and encrypted using HTTPS**, the integration does **not validate the certificate authority (CA)**.  
This is necessary because the BSH server sometimes presents a certificate chain that fails verification on some systems, including Home Assistant installations and Docker containers.

⚠️ **If you are concerned about this behavior**, you can review the certificate chain manually via [https://wasserstand-nordsee.bsh.de/](https://wasserstand-nordsee.bsh.de/).

[hacs]: https://github.com/custom-components/hacs
[hacs-shield]: https://img.shields.io/badge/HACS-Install%20via%20HACS-orange?style=for-the-badge&logo=home-assistant
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/EnlightningMan/ha-bsh_tides.svg?style=for-the-badge
[releases]: https://github.com/EnlightningMan/ha-bsh_tides/releases
[downloads-shield]: https://img.shields.io/github/downloads/EnlightningMan/ha-bsh_tides/latest/total.svg?style=for-the-badge
[downloads-all-shield]: https://img.shields.io/github/downloads/EnlightningMan/ha-bsh_tides/total.svg?style=for-the-badge
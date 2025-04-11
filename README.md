# BSH Tides for Germany Integration for Home Assistant

**Disclaimer: Work in progress**

Custom integration to fetch tidal forecast data from the German Federal Maritime and Hydrographic Agency / the Bundesamt für Seeschifffahrt und Hydrographie (BSH).

🌊 **Features**

Creates Home Assistant devices and sensors for multiple data points:
- for the next upcoming tide
- for the upcoming high and low tides
- Provides live forecasted water level and expected deviation from mean
- Supports multiple measurement points via BSH station IDs

📡 **Data Source**

The [BSH Tide Data](https://wasserstand-nordsee.bsh.de/) provides tide data for the German North Sea costal region including measuring points for tide affected rivers (Ems, Weser, Elbe, Hunte, etc). Check link for supported gauging stations.

Data © Bundesamt für Seeschifffahrt und Hydrographie (BSH)

## 🔧 Installation

1. Copy `custom_components/bsh_tides` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to `Settings → Devices & Services → + Add Integration` and select **"BSH Tides for Germany"**.
4. Enter your desired station code (e.g. `DE__508P` for "St. Pauli, Elbe").

## 📍 Supported Stations

You can find station codes (`bshnr`) here: **TODO add documentation**

## 📄 License & Attribution

- Data: © BSH – Bundesamt für Seeschifffahrt und Hydrographie  
- Integration: MIT License

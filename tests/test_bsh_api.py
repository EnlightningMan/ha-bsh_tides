"""Tests for the gdi.bsh.de OGC API translation layer (feature_to_legacy)."""

import pytest

from custom_components.bsh_tides.bsh_api import feature_to_legacy
from custom_components.bsh_tides.exceptions import BshInvalidStation


def _peak_feature():
    """A Feature that carries explicit high/low water predictions."""
    return {
        "type": "Feature",
        "id": "alte_weser_leuchtturm",
        "properties": {
            "gauge_label": "Alte Weser, Leuchtturm",
            "area": "Jade und Ostfriesland",
            "forecast_timestamp": "2026-06-02 07:27:55+02:00",
            "automated_curveforecast_timestamp": "2026-06-02 11:56:22+02:00",
            "mean_high_water": 641.0,
            "mean_low_water": 358.0,
            "copyright": {"de": "@BSH (de)", "en": "@BSH (en)"},
            "high_water_low_water": [
                {
                    "event_timestamp": "2026-06-02 08:24:00+02:00",
                    "event": "NW",
                    "tidal_prediction_value": "339",
                    "forecast_value": 338,
                    "forecast_deviation": "-0,2 m",
                },
                {
                    "event_timestamp": "2026-06-02 14:14:00+02:00",
                    "event": "HW",
                    # no forecast_value -> must fall back to tidal_prediction_value
                    "forecast_value": None,
                    "tidal_prediction_value": "652",
                    "forecast_deviation": "+0,1 m",
                },
            ],
            # present but must be ignored because peak data exists
            "curve": [{"timestamp": "x", "automated_curve_forecast": "1"}],
        },
    }


def _curve_feature():
    """A Feature without peak data, only a model curve (fallback path)."""
    return {
        "type": "Feature",
        "id": "flensburg",
        "properties": {
            "gauge_label": "Flensburg",
            "area": "Kieler Bucht",
            "forecast_timestamp": None,
            "automated_curveforecast_timestamp": "2026-06-02 11:56:22+02:00",
            "mean_high_water": 633.0,
            "mean_low_water": 379.0,
            "copyright": "@plain string copyright",
            "high_water_low_water": [],  # empty -> curve fallback
            "curve": [
                # past point: no forecast field -> curveforecast None
                {"timestamp": "2026-06-02 10:00:00+02:00", "measurement": "500"},
                # future points carry automated_curve_forecast
                {
                    "timestamp": "2026-06-02 11:45:00+02:00",
                    "automated_curve_forecast": "504",
                },
            ],
        },
    }


def test_feature_to_legacy_peak_path():
    data = feature_to_legacy(_peak_feature())

    assert data["station_name"] == "Alte Weser, Leuchtturm"
    assert data["seo_id"] == "alte_weser_leuchtturm"
    assert data["area"] == "Jade und Ostfriesland"
    assert data["creation_forecast"] == "2026-06-02 07:27:55+02:00"
    assert data["MHW"] == 641.0
    assert data["MNW"] == 358.0
    assert data["copyright_note"] == "@BSH (de)"

    # peak path populates hwnw_forecast and NOT curve_forecast
    assert "hwnw_forecast" in data
    assert "curve_forecast" not in data

    events = data["hwnw_forecast"]["data"]
    assert len(events) == 2

    nw = events[0]
    assert nw["timestamp"] == "2026-06-02 08:24:00+02:00"
    assert nw["event"] == "NW"
    assert nw["value"] == 338  # forecast_value
    # raw deviation string kept; the coordinator parses it later
    assert nw["forecast"] == "-0,2 m"

    hw = events[1]
    assert hw["event"] == "HW"
    assert hw["value"] == 652  # fell back to tidal_prediction_value
    assert hw["forecast"] == "+0,1 m"


def test_feature_to_legacy_curve_path():
    data = feature_to_legacy(_curve_feature())

    assert data["seo_id"] == "flensburg"
    assert data["copyright_note"] == "@plain string copyright"
    # no peak data -> falls back to the curve and uses the curve timestamp
    assert "hwnw_forecast" not in data
    assert "curve_forecast" in data
    assert data["creation_forecast"] == "2026-06-02 11:56:22+02:00"

    points = data["curve_forecast"]["data"]
    assert len(points) == 2
    # past point has no forecast value
    assert points[0]["timestamp"] == "2026-06-02 10:00:00+02:00"
    assert points[0]["curveforecast"] is None
    # future point maps automated_curve_forecast -> curveforecast (as number)
    assert points[1]["curveforecast"] == 504


@pytest.mark.parametrize("bad", [None, 42, "string", {}, {"id": "x"}])
def test_feature_to_legacy_invalid_payload(bad):
    with pytest.raises(BshInvalidStation):
        feature_to_legacy(bad)

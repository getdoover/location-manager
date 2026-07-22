"""
Basic tests for the Location Manager application.

Ensures modules import and the config schema exports cleanly.
"""


def test_import_app():
    from location_manager.application import LocationManager
    assert LocationManager
    assert LocationManager.config_cls is not None


def test_config_schema():
    from location_manager.app_config import LocationManagerConfig

    schema = LocationManagerConfig.to_schema()
    assert schema["type"] == "object"
    props = schema["properties"]
    assert "accuracy_threshold" in props
    assert "distance_threshold_m" in props
    assert "update_frequency_seconds" in props


def test_config_export(tmp_path):
    import json
    from location_manager.app_config import LocationManagerConfig

    fp = tmp_path / "doover_config.json"
    LocationManagerConfig.export(fp, "location_manager")
    data = json.loads(fp.read_text())
    assert "config_schema" in data["location_manager"]

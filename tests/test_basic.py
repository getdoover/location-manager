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


def _bare_app():
    from location_manager.application import LocationManager

    return LocationManager.__new__(LocationManager)


LOCATION = {"lat": -27.5758, "long": 152.3632, "alt": 88.4, "accuracy": 4.9}


def test_publish_location_writes_aggregate_and_message():
    import asyncio
    from unittest.mock import AsyncMock

    app = _bare_app()
    app.update_channel_aggregate = AsyncMock(return_value=object())
    app.create_message = AsyncMock()

    assert asyncio.run(app.publish_location(LOCATION)) is True
    app.update_channel_aggregate.assert_awaited_once_with("location", LOCATION)
    app.create_message.assert_awaited_once_with("location", LOCATION)


def test_publish_location_failed_aggregate_skips_message():
    import asyncio
    from unittest.mock import AsyncMock

    app = _bare_app()
    app.update_channel_aggregate = AsyncMock(return_value=None)
    app.create_message = AsyncMock()

    assert asyncio.run(app.publish_location(LOCATION)) is False
    app.create_message.assert_not_awaited()


def test_publish_location_swallows_errors():
    import asyncio
    from unittest.mock import AsyncMock

    app = _bare_app()
    app.update_channel_aggregate = AsyncMock(side_effect=RuntimeError("dda down"))
    app.create_message = AsyncMock()

    assert asyncio.run(app.publish_location(LOCATION)) is False

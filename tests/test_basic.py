"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""
import sys
from pathlib import Path


def test_import_app():
    from location_manager.application import LocationManager
    assert LocationManager

def test_config():
    from location_manager.app_config import LocationManagerConfig

    config = LocationManagerConfig()
    assert isinstance(config.to_dict(), dict)

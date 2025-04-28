"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""
import sys
from pathlib import Path

sys.path.append((Path(__file__).absolute().parent.parent / "application").as_posix())

def test_import_app():
    from application import LocationManager
    assert LocationManager

def test_config():
    from app_config import LocationManagerConfig

    config = LocationManagerConfig()
    assert isinstance(config.to_dict(), dict)

# def test_ui():
#     from app_ui import WarningManagerUI

# def test_state():
#     from app_state import WarningManagerState
#     assert WarningManagerState
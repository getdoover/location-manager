from pydoover.docker import run_app

from .application import LocationManager
from .app_config import LocationManagerConfig


def main():
    """Main entry point for the Location Manager application."""
    run_app(LocationManager(config=LocationManagerConfig()))
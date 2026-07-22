from pydoover.docker import run_app

from .application import LocationManager


def main():
    """Main entry point for the Location Manager application."""
    run_app(LocationManager())

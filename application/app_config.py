from pathlib import Path

from pydoover import config


class LocationManagerConfig(config.Schema):
    def __init__(self):
        self.accuracy_threshold = config.Decimal("Accuracy Threshold (%)", default=10, min_val=0, max_val=100)
        self.distance_threshold = config.Decimal("Distance Threshold (m)", default=15, min_val=0)
        self.update_freq_secs = config.Integer("Update Frequency (seconds)", default=15, min_val=0)

if __name__ == "__main__":
    c = LocationManagerConfig()
    c.export(Path("app_config.json"))

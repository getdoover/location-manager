from pathlib import Path

from pydoover import config


class LocationManagerConfig(config.Schema):
    def __init__(self):
        self.accuracy_threshold = config.Number("Accuracy Threshold (%)", default=10.0, minimum=0, maximum=100)
        self.distance_threshold = config.Number("Distance Threshold (m)", default=15.0, minimum=0)
        self.update_freq_secs = config.Integer("Update Frequency (seconds)", default=15, minimum=0)

if __name__ == "__main__":
    c = LocationManagerConfig()
    c.export(Path("../doover_config.json"), "location_manager")

from pathlib import Path

from pydoover import config


class LocationManagerConfig(config.Schema):
    accuracy_threshold = config.Number(
        "Accuracy Threshold (m)", name="accuracy_threshold", default=8.0, minimum=0, maximum=100
    )
    distance_threshold = config.Number("Distance Threshold (m)", default=10.0, minimum=0)
    update_freq_secs = config.Integer("Update Frequency (seconds)", default=15, minimum=0)


def export():
    LocationManagerConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "doover_location_manager"
    )


if __name__ == "__main__":
    export()

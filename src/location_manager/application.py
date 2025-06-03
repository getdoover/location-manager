import logging
import math
import time

from typing import Optional

from pydoover.docker import Application

from .app_config import LocationManagerConfig

log = logging.getLogger()

class LocationManager(Application):
    config: LocationManagerConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.last_published_location = None
        self.last_location_update_time: Optional[float] = None

    async def fetch_location(self) -> Optional[dict]:
        try:
            location = await self.platform_iface.get_location_async()
            if not location:
                log.warning("Failed to fetch location.")
                return None

            ## Transform the location data to a dictionary
            location = {
                "lat": location.latitude,
                "long": location.longitude,
                "alt": location.altitude_m,
                "accuracy": location.accuracy_m,
            }

            log.debug(f"Fetched location: {location}")
            return location
        except Exception as e:
            log.error(f"Error fetching location: {e}")
            return None

    @staticmethod
    def calculate_distance(loc1: dict, loc2: dict) -> float:
        """
        Calculate the distance between two locations using the haversine formula.

        :param loc1: First location as a dictionary with 'lat' and 'long'.
        :param loc2: Second location as a dictionary with 'lat' and 'long'.
        :return: Distance in meters.
        """
        R = 6_371_000  # Earth radius in meters
        lat1, lon1 = math.radians(loc1['lat']), math.radians(loc1['long'])
        lat2, lon2 = math.radians(loc2['lat']), math.radians(loc2['long'])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    async def handle_location_channel_update(self, channel_name, aggregate):
        log.debug(f"Received update from {channel_name}: {aggregate}")
        if aggregate and channel_name == "location":
            recv_location = aggregate
            if isinstance(aggregate, str):
                recv_location = {}

            self.last_published_location = {
                "lat": recv_location.get("lat", None),
                "long": recv_location.get("long", None),
                "alt": recv_location.get("alt", None),
                "accuracy": recv_location.get("accuracy", None),
            }

    async def publish_location(self, location: dict) -> bool:
        try:
            return await self.publish_to_channel("location", location)
        except Exception as e:
            log.error(f"Error publishing location: {e}")
            return False

    async def setup(self):
        log.info("Setting up LocationManager...")
        self.device_agent.add_subscription("location", self.handle_location_channel_update)

    async def main_loop(self):
        current_time = time.time()

        # Check if the location update frequency interval has passed
        if self.last_location_update_time is not None and \
                (current_time - self.last_location_update_time < self.config.update_freq_secs.value):
            log.debug("Location update frequency interval not reached. Skipping.")
            return

        # Update the last location update time
        self.last_location_update_time = current_time

        # Fetch the current location
        location = await self.fetch_location()
        if not location:
            log.debug("Location is null, skipping update")
            return

        accuracy = location.get("accuracy", float("inf"))
        if accuracy > self.config.accuracy_threshold.value:
            log.info("debug",
                     f"Location accuracy {accuracy} exceeds threshold {self.config.accuracy_threshold.value}. Skipping publish.")
            return

        if self.last_published_location:
            distance = self.calculate_distance(self.last_published_location, location)
            if distance < self.config.distance_threshold.value:
                log.info(
                    "debug",
                     f"Location change ({distance}m) is below threshold "
                     f"{self.config.distance_threshold.value}m. Skipping publish."
                )
                return

        # Publish the new location
        success = await self.publish_location(location)
        if success:
            log.info(f"Published location: {location}")
            self.last_published_location = location
        else:
            log.error("Failed to publish location.")

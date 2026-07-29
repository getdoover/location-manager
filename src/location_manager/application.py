import logging
import math
import time

from typing import Optional

from pydoover.docker import Application

from .app_config import LocationManagerConfig

log = logging.getLogger(__name__)

class LocationManager(Application):
    config_cls = LocationManagerConfig
    config: LocationManagerConfig

    async def fetch_location(self) -> Optional[dict]:
        try:
            location = await self.platform_iface.fetch_location()
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

    @staticmethod
    def _location_from_data(data: Optional[dict]) -> Optional[dict]:
        """Map raw aggregate data to a location dict, or None if it has no coordinates.

        Restores the original guard that skipped assignment for empty/cleared
        aggregates so we never store a truthy dict full of Nones (which would
        crash calculate_distance on the next main_loop).
        """
        if not data or data.get("lat") is None or data.get("long") is None:
            return None
        return {
            "lat": data.get("lat"),
            "long": data.get("long"),
            "alt": data.get("alt"),
            "accuracy": data.get("accuracy"),
        }

    async def on_aggregate_update(self, event):
        if event.channel.name != "location":
            return
        data = event.aggregate.data if event.aggregate else {}
        location = self._location_from_data(data)
        if location is not None:
            self.last_published_location = location

    async def on_channel_sync(self, event):
        # Hydrates last_published_location from the channel's last-published
        # aggregate delivered once on subscribe, so cross-restart distance
        # thresholding persists. ChannelSyncEvent carries only .aggregate
        # (no .channel); the app subscribes only to the "location" channel.
        data = event.aggregate.data if event.aggregate else {}
        location = self._location_from_data(data)
        if location is not None:
            self.last_published_location = location

    async def publish_location(self, location: dict) -> bool:
        # Aggregate updates and messages are independent in Doover 2.0:
        # the aggregate carries the current position, while messages form
        # the location history/track. Publish both.
        try:
            agg = await self.update_channel_aggregate("location", location)
            if agg is None:
                return False
            await self.create_message("location", location)
            return True
        except Exception as e:
            log.error(f"Error publishing location: {e}")
            return False

    async def setup(self):
        log.info("Setting up LocationManager...")
        self.last_published_location = None
        self.last_location_update_time: Optional[float] = None
        await self.subscribe("location")

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

        accuracy = location.get("accuracy")
        if accuracy is None:
            # Unknown accuracy (e.g. GNSS module reports no fix quality) —
            # treat as worst-case so we never publish an unqualified fix.
            accuracy = float("inf")
        if accuracy > self.config.accuracy_threshold.value:
            log.debug(
                f"Location accuracy {accuracy} exceeds threshold "
                f"{self.config.accuracy_threshold.value}. Skipping publish."
            )
            return

        if self.last_published_location:
            distance = self.calculate_distance(self.last_published_location, location)
            if distance < self.config.distance_threshold.value:
                log.debug(
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

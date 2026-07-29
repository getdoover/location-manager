# Location Management

A Doover device app that keeps track of where a device is. It periodically reads
the GNSS fix from the device's 4G card (via the platform interface) and publishes
it to the `location` channel — both the channel aggregate (current position) and
a channel message (location history/track).

## How it works

Every update interval the app:

1. Fetches the current GNSS fix from the platform interface.
2. Discards the fix if its reported accuracy is worse than the accuracy threshold.
3. Skips publishing if the device has moved less than the distance threshold
   since the last published location.
4. Otherwise publishes the location to the `location` channel — updating the
   aggregate and creating a message so the movement history is preserved.

Published locations carry `lat`, `long`, `alt` (m) and `accuracy` (m).

## Configuration

| Setting | Default | Description |
|---|---|---|
| Accuracy Threshold (m) | 8 | Fixes with worse reported accuracy than this are ignored. |
| Distance Threshold (m) | 10 | Minimum movement from the last published location before a new one is logged. |
| Update Frequency (seconds) | 15 | How often to check the current location. |

Tune the distance threshold to suit the asset: it should sit comfortably above
the typical GPS accuracy (otherwise fix-to-fix jitter gets logged as movement),
and below the smallest movement you care about tracking.

## Requirements

- A device with a GNSS-capable 4G card (e.g. a Doovit)
- The `platform_interface` app (declared as a dependency)

"""Shared constants for the frame manager."""
import os
import sys

MAX_FILES_PER_SEQUENCE = 2000
def default_output_root() -> str:
    """Return default output directory (exe folder when frozen)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


# Default output root (repo root or exe folder).
OUT_PARENT = default_output_root()

POSE_FIELDS = [
    "frame_index",
    "image_name",
    "timestamp",
    "gps_latitude",
    "gps_longitude",
    "gps_altitude_m",
    "heading_deg",
    "pitch_deg",
    "roll_deg",
]

POSE_DATA_FIELDS = [
    "timestamp",
    "gps_latitude",
    "gps_longitude",
    "gps_altitude_m",
    "heading_deg",
    "pitch_deg",
    "roll_deg",
]

POSE_CSV_FIELD_ALIASES = {
    "file_name": ("file_name", "filename", "image_name", "imagename"),
    "gps_seconds": ("gps_seconds[s]", "gps_seconds", "gps_time", "gpstime"),
    "unix_seconds": ("gps_sec[s]", "gps_sec", "unix_seconds[s]", "unix_seconds", "unix_time", "unixtime"),
    "latitude": ("latitude[deg]", "latitude", "lat"),
    "longitude": ("longitude[deg]", "longitude", "lon", "lng"),
    "altitude": ("altitude_ellipsoidal[m]", "altitude_ellipsoidal", "altitude", "altitude_m", "alt"),
    "x_coord": ("x[m]", "x", "easting[m]", "easting", "east"),
    "y_coord": ("y[m]", "y", "northing[m]", "northing", "north"),
    "z_coord": ("z[m]", "z", "height[m]", "height"),
    "roll": ("roll[deg]", "roll"),
    "pitch": ("pitch[deg]", "pitch"),
    "heading": ("heading[deg]", "heading", "yaw", "azimuth"),
}

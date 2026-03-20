"""CSV parsing helpers for pose data."""
import os
import re
from typing import Any

from .common import (
    normalize_header_name,
    normalize_image_key,
    parse_float,
    read_csv_headers,
    seconds_to_utc,
    sniff_csv_dialect,
)
from .constants import POSE_CSV_FIELD_ALIASES
from .models import PoseLookup


def build_pose_csv_column_map(fieldnames: list[str]) -> dict[str, str]:
    """Map canonical pose fields to CSV header names."""
    normalized = {normalize_header_name(name): name for name in fieldnames if name}
    mapping: dict[str, str] = {}
    for key, aliases in POSE_CSV_FIELD_ALIASES.items():
        for alias in aliases:
            alias_key = normalize_header_name(alias)
            if alias_key in normalized:
                mapping[key] = normalized[alias_key]
                break
    return mapping


def swiss_grid_to_wgs84(easting: float, northing: float) -> tuple[float, float] | None:
    """Convert Swiss grid (LV95/LV03) coordinates to WGS84 latitude/longitude."""
    if 2400000.0 <= easting <= 2900000.0 and 1000000.0 <= northing <= 1400000.0:
        y_aux = (easting - 2600000.0) / 1_000_000.0
        x_aux = (northing - 1200000.0) / 1_000_000.0
    elif 400000.0 <= easting <= 900000.0 and 0.0 <= northing <= 400000.0:
        y_aux = (easting - 600000.0) / 1_000_000.0
        x_aux = (northing - 200000.0) / 1_000_000.0
    else:
        return None
    latitude = (
        16.9023892
        + 3.238272 * x_aux
        - 0.270978 * (y_aux**2)
        - 0.002528 * (x_aux**2)
        - 0.0447 * (y_aux**2) * x_aux
        - 0.0140 * (x_aux**3)
    )
    longitude = (
        2.6779094
        + 4.728982 * y_aux
        + 0.791484 * y_aux * x_aux
        + 0.1306 * y_aux * (x_aux**2)
        - 0.0436 * (y_aux**3)
    )
    return (latitude * (100.0 / 36.0), longitude * (100.0 / 36.0))


def load_pose_csv(path: str, epoch: str) -> PoseLookup:
    """Load a pose CSV into a mapping keyed by normalized image name."""
    import csv

    if epoch not in ("gps", "unix"):
        raise ValueError("pose-epoch must be 'gps' or 'unix'.")
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(2048)
        handle.seek(0)
        dialect = sniff_csv_dialect(sample)
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("Pose CSV is missing headers.")
        column_map = build_pose_csv_column_map(list(reader.fieldnames))
        if "file_name" not in column_map:
            raise ValueError("Pose CSV is missing a file_name column.")
        poses: PoseLookup = {}
        for row in reader:
            raw_name = (row.get(column_map["file_name"]) or "").strip()
            if not raw_name:
                continue
            gps_seconds = parse_float(row.get(column_map.get("gps_seconds", "")))
            unix_seconds = parse_float(row.get(column_map.get("unix_seconds", "")))
            raw_seconds = gps_seconds if gps_seconds is not None else unix_seconds
            if gps_seconds is not None:
                timestamp = seconds_to_utc(gps_seconds, epoch)
            elif unix_seconds is not None:
                timestamp = seconds_to_utc(unix_seconds, "unix")
            else:
                timestamp = None
            latitude = parse_float(row.get(column_map.get("latitude", "")))
            longitude = parse_float(row.get(column_map.get("longitude", "")))
            altitude = parse_float(row.get(column_map.get("altitude", "")))
            if altitude is None:
                altitude = parse_float(row.get(column_map.get("z_coord", "")))
            if latitude is None or longitude is None:
                x_coord = parse_float(row.get(column_map.get("x_coord", "")))
                y_coord = parse_float(row.get(column_map.get("y_coord", "")))
                if x_coord is not None and y_coord is not None:
                    converted = swiss_grid_to_wgs84(x_coord, y_coord)
                    if converted is not None:
                        converted_lat, converted_lon = converted
                        if latitude is None:
                            latitude = converted_lat
                        if longitude is None:
                            longitude = converted_lon
            poses[normalize_image_key(raw_name)] = {
                "file_name": raw_name,
                "gps_seconds": raw_seconds,
                "timestamp": timestamp,
                "gps_latitude": latitude,
                "gps_longitude": longitude,
                "gps_altitude_m": altitude,
                "heading_deg": parse_float(row.get(column_map.get("heading", ""))),
                "pitch_deg": parse_float(row.get(column_map.get("pitch", ""))),
                "roll_deg": parse_float(row.get(column_map.get("roll", ""))),
            }
        return poses


def csv_has_pose_headers(path: str) -> bool:
    """Return True if a CSV file looks like a pose file."""
    headers = read_csv_headers(path)
    if not headers:
        return False
    column_map = build_pose_csv_column_map(list(headers))
    return "file_name" in column_map


def depth_from_root(root: str, path: str) -> int:
    """Return directory depth of a path relative to a root."""
    rel = os.path.relpath(path, root)
    if rel == os.curdir:
        return 0
    return rel.count(os.sep)


def find_pose_csv_path(folder: str) -> str | None:
    """Locate the closest pose CSV under a folder."""
    candidates: list[str] = []
    for root, _dirs, files in os.walk(folder):
        for file in files:
            if not file.lower().endswith(".csv"):
                continue
            if re.match(r"^s\d{3}_trajectory\.csv$", file.lower()):
                continue
            candidates.append(os.path.join(root, file))
    candidates.sort(key=lambda path: (depth_from_root(folder, path), path.lower()))
    for candidate in candidates:
        if csv_has_pose_headers(candidate):
            return os.path.abspath(candidate)
    return None

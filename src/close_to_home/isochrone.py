"""Drive-time isochrone: real Google Isochrones API when a key is present,
procedural fake polygon otherwise (demo must work with zero keys).

Google Isochrones API (Preview):
  POST https://isochrones.googleapis.com/v1/isochrones:generate
  Response: {"isochrone": {"geoJson": {...RFC 7946 MultiPolygon...}}}
  DRIVE mode caps travelDuration at 3600s.
"""

import logging
import math
import os
import random
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

GOOGLE_URL = "https://isochrones.googleapis.com/v1/isochrones:generate"
KM_PER_MINUTE_DRIVING = 0.5  # rough average urban driving speed (~30 km/h)

_cache: dict[tuple, dict] = {}


def _load_dotenv() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def get_isochrone(lat: float, lng: float, minutes: int) -> dict:
    """Return a GeoJSON MultiPolygon geometry for the N-minute drive area."""
    minutes = max(5, min(60, int(minutes)))  # DRIVE mode caps at 3600s
    key = (round(lat, 5), round(lng, 5), minutes)
    if key not in _cache:
        _cache[key] = _google_isochrone(lat, lng, minutes) or _fake_isochrone(
            lat, lng, minutes
        )
    return _cache[key]


def _google_isochrone(lat: float, lng: float, minutes: int) -> dict | None:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None
    try:
        resp = httpx.post(
            GOOGLE_URL,
            headers={"X-Goog-Api-Key": api_key},
            json={
                "location": {"latitude": lat, "longitude": lng},
                "travelMode": "DRIVE",
                "travelDirection": "TO",
                "travelDuration": f"{minutes * 60}s",
                "routingPreference": "TRAFFIC_AWARE",
                "enableSmoothing": True,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["isochrone"]["geoJson"]
    except Exception as exc:  # any failure -> fall back to fake geometry
        logger.warning("Google Isochrones call failed, using fake polygon: %s", exc)
        return None


def _fake_isochrone(lat: float, lng: float, minutes: int) -> dict:
    """Plausible blobby polygon: noisy radius around the origin, smoothed so it
    looks road-network-organic. Noise is seeded by location only, so polygons
    for different durations at the same spot nest like real isochrones."""
    n_vertices = 28
    rng = random.Random(f"{round(lat, 4)},{round(lng, 4)}")
    raw = [rng.uniform(0.6, 1.3) for _ in range(n_vertices)]
    # Smooth each vertex against its neighbors (two passes).
    for _ in range(2):
        raw = [
            (raw[i - 1] + 2 * raw[i] + raw[(i + 1) % n_vertices]) / 4
            for i in range(n_vertices)
        ]
    stretch_angle = rng.uniform(0, math.pi)  # mild anisotropy (arterial roads)

    base_km = minutes * KM_PER_MINUTE_DRIVING
    deg_lat = base_km / 111.0
    deg_lng = base_km / (111.0 * math.cos(math.radians(lat)))

    ring = []
    for i in range(n_vertices):
        theta = 2 * math.pi * i / n_vertices
        r = raw[i] * (1 + 0.25 * math.cos(2 * (theta - stretch_angle)))
        ring.append(
            [
                round(lng + r * deg_lng * math.cos(theta), 6),
                round(lat + r * deg_lat * math.sin(theta), 6),
            ]
        )
    ring.append(ring[0])
    return {"type": "MultiPolygon", "coordinates": [[ring]]}

"""Coordinate reference system engine.

Implemented from first principles (Snyder, *Map Projections: A Working Manual*,
USGS PP 1395) because ``pyproj`` is blocked by Windows Application Control on
the target machine. Covers exactly what urban cadastral work in India needs:

* WGS84 <-> UTM (India spans zones 42N-47N)
* Everest 1830 (India) <-> WGS84 via a 7-parameter Helmert transform

Everest 1830 matters: legacy Indian cadastral sheets and older Survey of India
products are referenced to it, while drone and GNSS output is WGS84. Ignoring
the datum difference leaves a systematic offset of several hundred metres,
which is the single largest error source when overlaying an old map on new
imagery.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "Ellipsoid", "WGS84", "EVEREST_1830_INDIA",
    "utm_zone_for_lon", "geodetic_to_utm", "utm_to_geodetic",
    "everest_to_wgs84", "wgs84_to_everest", "epsg_for_utm",
]


@dataclass(frozen=True)
class Ellipsoid:
    name: str
    a: float           # semi-major axis (m)
    inv_f: float       # inverse flattening

    @property
    def f(self) -> float:
        return 1.0 / self.inv_f

    @property
    def e2(self) -> float:
        """First eccentricity squared."""
        return self.f * (2.0 - self.f)

    @property
    def ep2(self) -> float:
        """Second eccentricity squared."""
        return self.e2 / (1.0 - self.e2)


WGS84 = Ellipsoid("WGS 84", 6378137.0, 298.257223563)
# Everest 1830 (1937 Adjustment), the definition used for India.
EVEREST_1830_INDIA = Ellipsoid("Everest 1830 (1937 Adj.)", 6377276.345, 300.8017)

K0 = 0.9996          # UTM scale factor on the central meridian
FALSE_EASTING = 500_000.0
FALSE_NORTHING_S = 10_000_000.0


def utm_zone_for_lon(lon_deg: float) -> int:
    """UTM zone number for a longitude. India occupies zones 42-47."""
    return int(math.floor((lon_deg + 180.0) / 6.0) % 60) + 1


def epsg_for_utm(zone: int, northern: bool = True) -> str:
    return f"EPSG:{(32600 if northern else 32700) + zone}"


def _central_meridian(zone: int) -> float:
    return (zone - 1) * 6.0 - 180.0 + 3.0


def _meridional_arc(phi: np.ndarray, ell: Ellipsoid) -> np.ndarray:
    """Distance along the meridian from the equator to latitude ``phi``."""
    e2 = ell.e2
    return ell.a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * np.sin(2 * phi)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * np.sin(4 * phi)
        - (35 * e2**3 / 3072) * np.sin(6 * phi)
    )


def geodetic_to_utm(lon_deg, lat_deg, zone=None, ell: Ellipsoid = WGS84):
    """Geodetic (lon, lat degrees) -> UTM (easting, northing metres).

    Returns ``(easting, northing, zone)``. Accepts scalars or arrays.
    """
    scalar = np.ndim(lon_deg) == 0
    lon = np.atleast_1d(np.asarray(lon_deg, dtype=float))
    lat = np.atleast_1d(np.asarray(lat_deg, dtype=float))
    if zone is None:
        zone = utm_zone_for_lon(float(np.mean(lon)))

    phi = np.radians(lat)
    dlam = np.radians(lon - _central_meridian(zone))
    e2, ep2 = ell.e2, ell.ep2

    sin_p, cos_p, tan_p = np.sin(phi), np.cos(phi), np.tan(phi)
    N = ell.a / np.sqrt(1 - e2 * sin_p**2)
    T = tan_p**2
    C = ep2 * cos_p**2
    A = dlam * cos_p
    M = _meridional_arc(phi, ell)

    easting = K0 * N * (
        A + (1 - T + C) * A**3 / 6
        + (5 - 18 * T + T**2 + 72 * C - 58 * ep2) * A**5 / 120
    ) + FALSE_EASTING

    northing = K0 * (
        M + N * tan_p * (
            A**2 / 2
            + (5 - T + 9 * C + 4 * C**2) * A**4 / 24
            + (61 - 58 * T + T**2 + 600 * C - 330 * ep2) * A**6 / 720
        )
    )
    northing = np.where(lat < 0, northing + FALSE_NORTHING_S, northing)

    if scalar:
        return float(easting[0]), float(northing[0]), zone
    return easting, northing, zone


def utm_to_geodetic(easting, northing, zone: int, northern: bool = True,
                    ell: Ellipsoid = WGS84):
    """UTM (easting, northing) -> geodetic (lon, lat) in degrees."""
    scalar = np.ndim(easting) == 0
    x = np.atleast_1d(np.asarray(easting, dtype=float)) - FALSE_EASTING
    y = np.atleast_1d(np.asarray(northing, dtype=float))
    if not northern:
        y = y - FALSE_NORTHING_S

    e2, ep2, a = ell.e2, ell.ep2, ell.a
    M = y / K0
    mu = M / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))

    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * np.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * np.sin(4 * mu)
        + (151 * e1**3 / 96) * np.sin(6 * mu)
        + (1097 * e1**4 / 512) * np.sin(8 * mu)
    )

    sin1, cos1, tan1 = np.sin(phi1), np.cos(phi1), np.tan(phi1)
    C1 = ep2 * cos1**2
    T1 = tan1**2
    N1 = a / np.sqrt(1 - e2 * sin1**2)
    R1 = a * (1 - e2) / (1 - e2 * sin1**2) ** 1.5
    D = x / (N1 * K0)

    phi = phi1 - (N1 * tan1 / R1) * (
        D**2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1**2 - 9 * ep2) * D**4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1**2 - 252 * ep2 - 3 * C1**2) * D**6 / 720
    )
    lam = (
        D - (1 + 2 * T1 + C1) * D**3 / 6
        + (5 - 2 * C1 + 28 * T1 - 3 * C1**2 + 8 * ep2 + 24 * T1**2) * D**5 / 120
    ) / cos1

    lon = np.degrees(lam) + _central_meridian(zone)
    lat = np.degrees(phi)
    if scalar:
        return float(lon[0]), float(lat[0])
    return lon, lat


# --- Datum transformation -------------------------------------------------
# 7-parameter Helmert (position vector convention), Everest 1830 (India) ->
# WGS84. Published parameter sets for India vary by region; this is a
# representative national set and should be replaced with region-specific
# values when a state grid is known.
_HELMERT_EVEREST_TO_WGS84 = dict(
    dx=295.0, dy=736.0, dz=257.0,      # translation, metres
    rx=0.0, ry=0.0, rz=0.0,            # rotation, arc-seconds
    s=0.0,                             # scale, ppm
)


def _geodetic_to_ecef(lon_deg, lat_deg, h, ell: Ellipsoid):
    lon, lat = np.radians(lon_deg), np.radians(lat_deg)
    N = ell.a / np.sqrt(1 - ell.e2 * np.sin(lat) ** 2)
    x = (N + h) * np.cos(lat) * np.cos(lon)
    y = (N + h) * np.cos(lat) * np.sin(lon)
    z = (N * (1 - ell.e2) + h) * np.sin(lat)
    return x, y, z


def _ecef_to_geodetic(x, y, z, ell: Ellipsoid):
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)
    lat = np.arctan2(z, p * (1 - ell.e2))
    h = 0.0
    for _ in range(8):  # converges in ~4 iterations at terrestrial scales
        N = ell.a / np.sqrt(1 - ell.e2 * np.sin(lat) ** 2)
        h = p / np.cos(lat) - N
        lat = np.arctan2(z, p * (1 - ell.e2 * N / (N + h)))
    N = ell.a / np.sqrt(1 - ell.e2 * np.sin(lat) ** 2)
    h = p / np.cos(lat) - N
    return np.degrees(lon), np.degrees(lat), h


def _helmert(x, y, z, p, inverse=False):
    arcsec = math.pi / 180.0 / 3600.0
    rx, ry, rz = p["rx"] * arcsec, p["ry"] * arcsec, p["rz"] * arcsec
    s = 1.0 + p["s"] * 1e-6
    dx, dy, dz = p["dx"], p["dy"], p["dz"]
    if inverse:
        rx, ry, rz, dx, dy, dz = -rx, -ry, -rz, -dx, -dy, -dz
        s = 1.0 / s
    xo = dx + s * (x - rz * y + ry * z)
    yo = dy + s * (rz * x + y - rx * z)
    zo = dz + s * (-ry * x + rx * y + z)
    return xo, yo, zo


def everest_to_wgs84(lon, lat, h=0.0):
    """Everest 1830 (India) geodetic -> WGS84 geodetic."""
    x, y, z = _geodetic_to_ecef(lon, lat, h, EVEREST_1830_INDIA)
    x, y, z = _helmert(x, y, z, _HELMERT_EVEREST_TO_WGS84)
    return _ecef_to_geodetic(x, y, z, WGS84)


def wgs84_to_everest(lon, lat, h=0.0):
    """WGS84 geodetic -> Everest 1830 (India) geodetic."""
    x, y, z = _geodetic_to_ecef(lon, lat, h, WGS84)
    x, y, z = _helmert(x, y, z, _HELMERT_EVEREST_TO_WGS84, inverse=True)
    return _ecef_to_geodetic(x, y, z, EVEREST_1830_INDIA)

"""Lightweight vector data model.

A deliberately thin stand-in for GeoDataFrame. ``geopandas`` cannot be used on
the target machine (it requires ``pyproj``, which Application Control blocks),
and at demo scale -- a few thousand parcels -- a list of dataclasses is both
fast enough and far easier to reason about.

Every layer carries provenance: which source it came from, its nominal
positional accuracy, and its vintage. The conflict-resolution stage consumes
these directly, so provenance is a first-class field rather than an afterthought.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Iterator

from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry

__all__ = ["Feature", "Layer", "Provenance"]


@dataclass(frozen=True)
class Provenance:
    """Where a layer came from and how much it should be trusted.

    Attributes
    ----------
    source_id:
        Short machine name, e.g. ``"revenue_records"``.
    label:
        Human-readable name for display and reports.
    accuracy_m:
        Nominal 1-sigma positional accuracy in metres. GNSS/CORS ground truth
        is centimetre-level; a scanned 1960s cadastral sheet may be 5-20 m.
    vintage:
        Year the data was captured. Recency breaks ties between sources of
        otherwise equal accuracy.
    authority:
        Whether this source is legally authoritative for ownership. Revenue
        records are authoritative for *who owns*; drone imagery is
        authoritative for *what is on the ground*. The distinction drives
        conflict resolution.
    """
    source_id: str
    label: str
    accuracy_m: float
    vintage: int
    authority: bool = False

    @property
    def weight(self) -> float:
        """Reliability weight used by provenance-weighted voting.

        Inverse-variance weighting on positional accuracy, which is the
        statistically correct way to combine independent measurements of the
        same quantity.
        """
        return 1.0 / max(self.accuracy_m, 0.01) ** 2


@dataclass
class Feature:
    """One spatial object plus its attributes."""
    fid: str
    geometry: BaseGeometry
    attrs: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default=None):
        return self.attrs.get(key, default)

    def with_geometry(self, geom: BaseGeometry) -> "Feature":
        return replace(self, geometry=geom)

    def to_geojson(self) -> dict:
        return {
            "type": "Feature",
            "id": self.fid,
            "geometry": mapping(self.geometry),
            "properties": dict(self.attrs),
        }


@dataclass
class Layer:
    """A named collection of features sharing one CRS and one provenance."""
    name: str
    features: list[Feature] = field(default_factory=list)
    crs: str = "EPSG:32644"
    provenance: Provenance | None = None

    def __len__(self) -> int:
        return len(self.features)

    def __iter__(self) -> Iterator[Feature]:
        return iter(self.features)

    def __getitem__(self, i):
        return self.features[i]

    def add(self, feat: Feature) -> None:
        self.features.append(feat)

    def by_id(self) -> dict[str, Feature]:
        return {f.fid: f for f in self.features}

    def geometries(self) -> list[BaseGeometry]:
        return [f.geometry for f in self.features]

    def map_geometry(self, fn) -> "Layer":
        """Return a copy with ``fn`` applied to every geometry."""
        return Layer(
            name=self.name,
            features=[f.with_geometry(fn(f.geometry)) for f in self.features],
            crs=self.crs,
            provenance=self.provenance,
        )

    def filter(self, pred) -> "Layer":
        return Layer(self.name, [f for f in self.features if pred(f)],
                     self.crs, self.provenance)

    def total_area(self) -> float:
        return sum(f.geometry.area for f in self.features)

    # --- I/O --------------------------------------------------------------
    def to_geojson(self) -> dict:
        return {
            "type": "FeatureCollection",
            "name": self.name,
            "crs": {"type": "name", "properties": {"name": self.crs}},
            "features": [f.to_geojson() for f in self.features],
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_geojson(), fh, indent=1)

    @classmethod
    def load(cls, path: str, name: str | None = None) -> "Layer":
        with open(path, encoding="utf-8") as fh:
            gj = json.load(fh)
        crs = gj.get("crs", {}).get("properties", {}).get("name", "EPSG:32644")
        feats = [
            Feature(str(f.get("id", i)), shape(f["geometry"]),
                    dict(f.get("properties", {})))
            for i, f in enumerate(gj["features"])
        ]
        return cls(name or gj.get("name", "layer"), feats, crs)

    @classmethod
    def from_iter(cls, name: str, items: Iterable[Feature], **kw) -> "Layer":
        return cls(name, list(items), **kw)

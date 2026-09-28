"""Change detection between survey epochs, and encroachment onto public land.

Two related jobs:

**Epoch change** — what happened on the ground between two captures. New
construction, demolition, and extension of an existing structure. Extension is
the one that needs care: a footprint that grew by 8 m2 is an extension, not a
new building and not a digitising difference, and calling it "new" would put a
spurious entry on a surveyor's list.

**Encroachment** — built structure standing on land the state owns. This is the
single most actionable output for an urban local body, and it costs almost
nothing once parcels and public land are both in a common frame.

Two design decisions worth defending:

*Vertical change needs DSM.* A building that gains two storeys has an identical
2-D footprint. Plan-view differencing cannot see it at all, so where a height
surface exists the detector uses the height delta, and where it does not it
says so rather than silently reporting no change.

*Output is a dossier, never a mutation record.* Mutation is a statutory act
requiring notice and a hearing, its format varies by state, and in urban
Karnataka "khata" means a property-tax account rather than a revenue holding.
The system assembles evidence and puts the file on the revenue officer's desk;
the officer signs it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from shapely.strtree import STRtree

from kshetra.geometry import safe_polygon
from kshetra.layers import Feature, Layer

__all__ = [
    "ChangeEvent", "Encroachment", "ChangeReport",
    "detect_change", "detect_encroachment", "build_dossier",
]

#: Below this, a footprint difference is digitising noise rather than a change.
MIN_CHANGE_AREA = 8.0          # m2
#: An overlapping pair this similar is the same structure, not new + demolished.
SAME_STRUCTURE_IOU = 0.55
#: Encroachment smaller than this is boundary uncertainty, not a land grab.
MIN_ENCROACH_AREA = 5.0        # m2
#: Height gain implying an added storey.
STOREY_M = 2.6


@dataclass
class ChangeEvent:
    kind: str                       # new | demolished | extended | reduced | heightened
    fid: str
    area_sqm: float
    delta_sqm: float
    confidence: float
    at: tuple[float, float]
    height_delta_m: float | None = None
    storeys_delta: int | None = None
    matched_fid: str | None = None
    note: str = ""


@dataclass
class Encroachment:
    building_fid: str
    govt_fid: str
    govt_category: str
    encroached_sqm: float
    fraction_of_building: float
    confidence: float
    at: tuple[float, float]
    severity: str                   # minor | significant | severe


@dataclass
class ChangeReport:
    events: list[ChangeEvent] = field(default_factory=list)
    encroachments: list[Encroachment] = field(default_factory=list)
    epoch_from: str = ""
    epoch_to: str = ""
    dsm_available: bool = False

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in self.events:
            out[e.kind] = out.get(e.kind, 0) + 1
        out["encroachment"] = len(self.encroachments)
        return out

    def encroached_area(self) -> float:
        return sum(e.encroached_sqm for e in self.encroachments)

    def summary(self) -> str:
        c = self.counts()
        parts = [f"{self.epoch_from} -> {self.epoch_to}"]
        for k in ("new", "demolished", "extended", "reduced", "heightened"):
            if c.get(k):
                parts.append(f"{c[k]} {k}")
        if self.encroachments:
            parts.append(f"{len(self.encroachments)} encroachments "
                         f"({self.encroached_area():.0f} m2)")
        if not self.dsm_available:
            parts.append("no DSM: vertical change not assessed")
        return " | ".join(parts)


def _centroid(g) -> tuple[float, float]:
    c = g.centroid
    return (float(c.x), float(c.y))


# --------------------------------------------------------------------------
def detect_change(before: Layer, after: Layer,
                  heights_before: dict[str, float] | None = None,
                  heights_after: dict[str, float] | None = None,
                  epoch_from: str = "t0", epoch_to: str = "t1") -> ChangeReport:
    """Compare two building layers and classify what changed.

    Matching is by spatial overlap rather than by id, because the two epochs
    come from different extractions and share no identifier — which is the
    whole premise of this project.
    """
    rep = ChangeReport(epoch_from=epoch_from, epoch_to=epoch_to,
                       dsm_available=bool(heights_before and heights_after))

    bgeom = [safe_polygon(f.geometry) for f in before]
    ageom = [safe_polygon(f.geometry) for f in after]
    if not bgeom or not ageom:
        return rep

    tree = STRtree(bgeom)
    claimed_before: set[int] = set()

    for j, ag in enumerate(ageom):
        af = after[j]
        best, best_iou = None, 0.0
        for i in tree.query(ag):
            i = int(i)
            bg = bgeom[i]
            if not ag.intersects(bg):
                continue
            inter = ag.intersection(bg).area
            union = ag.area + bg.area - inter
            iou = inter / union if union > 0 else 0.0
            if iou > best_iou:
                best, best_iou = i, iou

        if best is None or best_iou < SAME_STRUCTURE_IOU:
            if ag.area >= MIN_CHANGE_AREA:
                rep.events.append(ChangeEvent(
                    kind="new", fid=af.fid, area_sqm=round(ag.area, 1),
                    delta_sqm=round(ag.area, 1),
                    confidence=float(np.clip(1.0 - best_iou / SAME_STRUCTURE_IOU, 0.5, 0.99)),
                    at=_centroid(ag),
                    note="no structure of comparable extent in the earlier epoch"))
            continue

        claimed_before.add(best)
        bg = bgeom[best]
        bf = before[best]
        delta = ag.area - bg.area

        # vertical change, where a height surface exists
        hd = None
        sd = None
        if rep.dsm_available:
            hb = (heights_before or {}).get(bf.fid)
            ha = (heights_after or {}).get(af.fid)
            if hb is not None and ha is not None:
                hd = float(ha - hb)
                sd = int(round(hd / STOREY_M))

        if abs(delta) >= MIN_CHANGE_AREA:
            rep.events.append(ChangeEvent(
                kind="extended" if delta > 0 else "reduced",
                fid=af.fid, area_sqm=round(ag.area, 1), delta_sqm=round(delta, 1),
                confidence=float(np.clip(best_iou, 0.5, 0.99)),
                at=_centroid(ag), height_delta_m=hd, storeys_delta=sd,
                matched_fid=bf.fid,
                note=f"footprint {'grew' if delta > 0 else 'shrank'} "
                     f"by {abs(delta):.1f} m2 at IoU {best_iou:.2f}"))
        elif hd is not None and abs(hd) >= STOREY_M:
            # Same footprint, more building. Invisible in plan view.
            rep.events.append(ChangeEvent(
                kind="heightened", fid=af.fid, area_sqm=round(ag.area, 1),
                delta_sqm=0.0, confidence=float(np.clip(best_iou, 0.5, 0.99)),
                at=_centroid(ag), height_delta_m=round(hd, 2), storeys_delta=sd,
                matched_fid=bf.fid,
                note=f"footprint unchanged, height +{hd:.1f} m "
                     f"(~{sd} storeys) — only the DSM sees this"))

    for i, bg in enumerate(bgeom):
        if i in claimed_before or bg.area < MIN_CHANGE_AREA:
            continue
        rep.events.append(ChangeEvent(
            kind="demolished", fid=before[i].fid, area_sqm=round(bg.area, 1),
            delta_sqm=round(-bg.area, 1), confidence=0.85, at=_centroid(bg),
            note="present in the earlier epoch, absent from the later one"))

    rep.events.sort(key=lambda e: -abs(e.delta_sqm))
    return rep


# --------------------------------------------------------------------------
def detect_encroachment(buildings: Layer, govt_land: Layer,
                        min_area: float = MIN_ENCROACH_AREA
                        ) -> list[Encroachment]:
    """Find built structure standing on government land."""
    if not len(buildings) or not len(govt_land):
        return []
    ggeom = [safe_polygon(f.geometry) for f in govt_land]
    tree = STRtree(ggeom)
    out: list[Encroachment] = []

    for bf in buildings:
        bg = safe_polygon(bf.geometry)
        if bg.is_empty or bg.area <= 0:
            continue
        for i in tree.query(bg):
            i = int(i)
            gg = ggeom[i]
            if not bg.intersects(gg):
                continue
            inter = bg.intersection(gg).area
            if inter < min_area:
                continue
            frac = inter / bg.area
            # A sliver along the boundary is positional uncertainty; a building
            # substantially inside public land is not.
            severity = ("severe" if frac > 0.6 else
                        "significant" if frac > 0.2 else "minor")
            out.append(Encroachment(
                building_fid=bf.fid, govt_fid=govt_land[i].fid,
                govt_category=str(govt_land[i].attrs.get("category", "public")),
                encroached_sqm=round(inter, 1),
                fraction_of_building=round(frac, 3),
                confidence=float(np.clip(frac * 1.4, 0.4, 0.98)),
                at=_centroid(bg.intersection(gg)), severity=severity))
    out.sort(key=lambda e: -e.encroached_sqm)
    return out


# --------------------------------------------------------------------------
def build_dossier(event: ChangeEvent | Encroachment,
                  parcel: Feature | None = None) -> dict:
    """Assemble an evidence pack for the revenue officer.

    Deliberately *not* a mutation record. It states what was observed, on what
    evidence, and what decision is required — and leaves the decision to the
    officer who is empowered to make it.
    """
    if isinstance(event, Encroachment):
        return {
            "type": "encroachment_dossier",
            "status": "flagged_for_officer",
            "building_fid": event.building_fid,
            "government_parcel": event.govt_fid,
            "category": event.govt_category,
            "encroached_sqm": event.encroached_sqm,
            "fraction_of_building": event.fraction_of_building,
            "severity": event.severity,
            "confidence": event.confidence,
            "location": event.at,
            "khasra": (parcel.attrs.get("khasra_no") if parcel else None),
            "recorded_holder": (parcel.attrs.get("owner_name") if parcel else None),
            "evidence": [
                "harmonized parcel geometry",
                "government land layer",
                "computed intersection area",
            ],
            "decision_required": "verify on site; issue notice if confirmed",
            "note": ("Advisory only. This is not a mutation record and carries "
                     "no statutory effect."),
        }
    return {
        "type": "change_dossier",
        "status": "flagged_for_officer",
        "change": event.kind,
        "feature_fid": event.fid,
        "matched_fid": event.matched_fid,
        "area_sqm": event.area_sqm,
        "delta_sqm": event.delta_sqm,
        "height_delta_m": event.height_delta_m,
        "storeys_delta": event.storeys_delta,
        "confidence": event.confidence,
        "location": event.at,
        "khasra": (parcel.attrs.get("khasra_no") if parcel else None),
        "recorded_holder": (parcel.attrs.get("owner_name") if parcel else None),
        "evidence": ["epoch t0 footprints", "epoch t1 footprints"] +
                    (["DSM height delta"] if event.height_delta_m is not None else []),
        "decision_required": "confirm and record if the change is authorised",
        "note": ("Advisory only. This is not a mutation record and carries no "
                 "statutory effect."),
    }

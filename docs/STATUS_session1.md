# BhoomiSetu — status

**SIH 2026 · Automated Integration and Intelligent Harmonization of
Multi-source Geospatial Data for Urban Land Record Management**

Built overnight, 23 September 2026. Model-only (UI deferred by your call).

---

## Headline results

Trained on one synthetic city, evaluated on a **different city** with a
different layout *and* a different corruption profile. Nothing below is a
training number.

| Metric | Value |
|---|---|
| Pairwise precision / recall / **F1** | 0.959 / 0.962 / **0.961** |
| ROC AUC | 0.986 |
| Average precision | 0.967 |
| Brier score | 0.0041 |
| **Expected Calibration Error** | **0.0034** |
| **Blocking recall** (true pairs retained) | **1.0000** |
| **Exact set match** (correct reference set per parcel) | **93.33%** |
| Primary reference correct | 93.53% |
| **Spurious parcels correctly rejected** | **57/57 = 100%** |
| Subdivision detection | **P = 1.000**, R = 0.227 |
| Training time | **1.1 s** |
| Assignment time (2,949 parcels) | 1.1 s |

Scale: 2,949 legacy parcels vs 2,830 reference parcels, 50,693 scored pairs.

---

## The two findings worth putting on a slide

### 1. You cannot match parcels before you georeference them

My first trained model scored F1 0.9955 — and was **worthless**. Feature
importance showed it had learned to join on khasra number and owner name
(96% of the decision); `iou` contributed 0.24%. If identifiers matched reliably
you would write a SQL join and this entire problem statement would not exist.

Two fixes:

- **Made the data honest.** Real resurveys *renumber* whole blocks, so 45% of
  blocks now get a fresh khasra series and 12% of owners genuinely changed hands.
  The identifier stops being a usable join key, exactly as in reality.
- **Fixed the sequencing.** Urban plots are ~11 m across while legacy
  misregistration is 5-15 m, so an unaligned legacy parcel physically overlaps
  its *neighbour* more than its own counterpart. Blocking recall was **0.58** —
  42% of true matches never reached the model.

After coarse alignment first: **blocking recall 1.00**, and the model now runs on
geometry — `centroid_dist` 45.6% + `src_frac_in_tgt` 42.0% = **88% geometric**,
attributes ~6%. Exact match went 55.6% -> 93.33%.

This is a genuine architecture result, and it is the kind of thing judges
remember because it sounds like engineering rather than marketing.

### 2. Calibration is the product, not the accuracy

ECE 0.0034 means the confidence score is *honest*. That is what makes triage
possible: the officer auto-accepts above a threshold and reviews the rest. A
95%-accurate model that claims 99% everywhere is useless here, because there is
no safe cut-off.

---

## Topology correction results

Run: `PYTHONPATH=. .venv/Scripts/python.exe scripts/check_topology.py`

3,047 legacy parcels, repaired in **3.6 s (851 parcels/s)**:

| | before | after |
|---|---|---|
| Invalid geometries (self-intersections) | 31 | **0** |
| Overlapping parcel pairs | 5,038 | **1** |
| Doubly-claimed area | 17,998 m2 | **72.7 m2** |
| Gaps / slivers | 1,130 | 237 |
| **Total topology errors** | **6,199** | **238** |

**96.2% of topology errors eliminated.** Duplicate vertices removed: 105.
Vertices snapped: 19,277.

### The part worth explaining on stage

Of the 237 residual gaps, the cleaner classifies **168 as hairline slivers** and
**69 as parcel-sized holes that it deliberately refuses to fill.** The harness
had deleted exactly **73 parcels** — so the system correctly identified almost
all the genuinely missing records and declined to hand that land to a
neighbour. Filling them would have been silent data fabrication.

### Area conservation (verify before a judge asks)

`scripts/check_area.py` answers the obvious hostile question, "did you lose
2.9% of the city's land?":

| | before | after |
|---|---|---|
| Sum of parcel areas | 422,219 m2 | 410,028 m2 (**-2.89%**) |
| **Union footprint** (ground counted once) | 404,586 m2 | 409,955 m2 (**+1.33%**) |
| Doubly-claimed land | 17,632 m2 | **72.7 m2** |

The cleaner removed **17,560 m2 of double-counted land** and recovered
**5,369 m2 of sliver gaps**. Net -12,191 m2. **No land was lost** — the summed
area fell *because* two people had been recorded owning the same ground, and
the actual footprint went *up*.


---

## What exists

```
bhoomisetu/
  crs.py                  UTM + Everest 1830 <-> WGS84, from first principles
  geometry.py             shape descriptors (IoU, Hausdorff, turning signature…)
  layers.py               Feature/Layer/Provenance data model + GeoJSON I/O
  synth/generator.py      synthetic Indian urban cadastre (ground truth)
  synth/corruption.py     11-stage damage harness + exact recovery key
  georef/transform.py     Similarity / Affine / Polynomial / Thin-Plate-Spline
  georef/coarse.py        Hough translation vote + robust similarity refinement
  matching/features.py    blocking + 29 pairwise features
  matching/model.py       XGBoost + isotonic calibration + SHAP explanations
  matching/assign.py      containment split/merge detection + Hungarian
  attributes/text.py      Jaro-Winkler / token-set, Indian transliteration folding
  evaluation/metrics.py   ROC/AP/Brier/ECE/reliability, hand-implemented
scripts/
  check_crs.py            CRS verification
  check_gen.py            city generation sanity check
  check_corrupt.py        corruption + baseline error
  train_matcher.py        full train + evaluate  <-- the main one
  tune_assignment.py      cached threshold sweep
docs/RESEARCH_DOSSIER.md  1,071 lines, every claim tagged verified/unverified
```

Run it:

```bash
PYTHONPATH=. .venv/Scripts/python.exe scripts/train_matcher.py
```

---

## What does NOT exist yet

Being explicit so nothing is a surprise:

| PS requirement | Status |
|---|---|
| AI/ML spatial matching | **done** |
| Confidence scoring | **done** (calibrated) |
| Geo-referencing & coordinate transformation | **done** (coarse + 4 transform models) |
| Intelligent attribute mapping | **not built** — `FieldMap` is hand-supplied |
| Automated topology correction | **done** |
| Change detection | **not built** |
| Spatial conflict resolution | **not built** — `Provenance.weight` exists, no engine |
| Raster / DSM / DTM handling | **not built** (rasterio is SAC-blocked; needs a plan) |
| Web-GIS UI | deferred by you |

Split recall (0.227) is the weakest real number. Precision is perfect, so it is
a safe weakness — misses go to human review — but it is the obvious next
improvement.

---

## Suggested order when you wake

1. **Attribute schema matching** — produces `FieldMap` automatically; currently
   the one hand-supplied piece in an otherwise automatic pipeline. Judges will
   ask about it.
2. **Change detection + encroachment** — the generator already emits
   `govt_land`, so encroachment scoring is close to free and is the single most
   compelling demo moment for an urban land audience.
3. **Conflict resolution** — `Provenance.weight` (inverse-variance) is there;
   needs the voting engine on top.

---

## Research highlights (full dossier in `docs/`)

- **Survey of India circular T-260/1147, 10 Feb 2025** — the authoritative
  NAKSHA spec. ORI at 5 cm GSD, **RMSEx,y ≤ 10 cm**; DSM/DTM **RMSEz ≤ 15 cm**;
  CORS control better than 5 cm. **CRS settled: UTM on WGS84.**
- **DoLR booklet** — 152 ULBs, 26 states + 3 UTs, **₹194 crore**, 4,142.63 sq km,
  scaling to all **4,912 ULBs**. Survey of India is the named Technology Partner;
  the ministry is **Rural Development / DoLR**, not MoHUA.
- **The killer citation:** the 2026 *Frontiers in Sustainable Cities* paper on
  NAKSHA is first-authored by **Kunal Satyarthi, Joint Secretary, DoLR**. It
  names *"parallel, non-interoperable records"* as a top friction point and
  explicitly recommends **"automated GeoAI-driven updating mechanisms."** The
  programme owner is asking for this system in print.
- **DILRMP: only 49.10% of villages have geo-referenced cadastral maps.**
- **Best unexpected pain evidence:** NIC's Bhu-Naksha manual documents a
  *manually entered per-state magic scale factor* on shapefile import — UP ×4000,
  Himachal ×22 (karam digitised in centimetres). India's incumbent national
  cadastral tool ships with hardcoded unit chaos.

### Three corrections — do not put these on a slide wrong

- **There is no "Indian Geodetic Datum 2023."** It was fabricated by a
  summariser. NGP 2022 commits only to *redefining* the national geodetic
  framework. The **Indian Vertical Datum** is real.
- **ULB count conflicts three ways** (152 / 157 / 150). Use **152**.
- **NUIS is two different things** — National Urban Information *System*
  (MoUD 2006) vs National Urban Innovation *Stack* (MoHUA). Note that NAKSHA
  MAP-1 publishes at **1:500**, finer than any NUIS tier: a real standards gap.

### Honestly unverified

- **No published figure exists for man-hours or cost of manual GIS
  *integration*.** Do not invent one. Substitutes found: **₹56,725/sq km**
  (Tamil Nadu resurvey rate) and ₹10-30 crore per city per MAP milestone.
- The NAKSHA SDMS schema SOP is a 105-page scan with no text layer. **Worth
  OCR'ing** — highest-value remaining unknown.
- ULPIN's exact 14-character encoding is not published. Do not fabricate a
  format string.

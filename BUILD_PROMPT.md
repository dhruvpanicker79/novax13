# BUILD PROMPT — KSHETRA

**SIH 2026 · PS13 — Automated Integration and Intelligent Harmonization of
Multi-source Geospatial Data for Urban Land Record Management**

Build a working prototype. Not a mockup, not an architecture document — a
running application where every number on screen was computed from real data by
real code. Scoped to be buildable, but nothing in it is fake.

---

## 0. What the problem actually is

A city holds ten datasets describing the same ground, and no two agree:

| Source | What it is | Why it's useless alone |
|---|---|---|
| Drone ORI | 5 cm aerial photos, geometrically corrected | pixels, no ownership |
| DSM / DTM | height surfaces; DSM − DTM = building height | needs fusing |
| AI footprints | polygons a model drew around buildings | no idea who owns them |
| Cadastral map | boundaries digitised from 1900s paper | shifted 3–15 m, gaps, overlaps |
| Revenue records | the legal DB: khasra, owner, area, tenure | text only, weak map link |
| Municipal GIS | wards, roads, property tax | different era and standard |
| Utility networks | water / sewer / power | different dept, schema, accuracy |
| GNSS / CORS | surveyor-visited points, cm accurate | **sparse and expensive** |

**The job:** decide that this AI-detected polygon, this old cadastral parcel and
this revenue record are the same property — then emit one clean, topologically
valid layer with an honest confidence on every decision, so a human reviews only
the uncertain ones.

It is **spatial entity resolution for land**. The purpose is **triage, not full
automation**.

---

## 1. THE USP — build this or the project is generic

The PS enumerates ten sources and seven components. It is a *spec*. Every team
will build to it, every architecture diagram will show the same ten boxes, and
"we integrate n sources with AI matching and confidence scores" differentiates
nothing. **You cannot differentiate on the spec.**

So the differentiator comes from outside it.

### The insight

The NAKSHA programme's own progress review — *Frontiers in Sustainable Cities*
(2026), first-authored by **Kunal Satyarthi, Joint Secretary, DoLR** — reports
that **ground truthing is "the biggest lagging component," with 55 of ~150 ULBs
below 60% completion.**

The real bottleneck is not integration. **It is that ground truth is scarce and
expensive.** The PS lists GT and GNSS/CORS as *inputs*, as though you simply
have them. In practice a surveyor visit costs money and the national programme
is stalling on exactly this.

### The feature: optimal survey targeting

> **Given a fixed survey budget, which 40 parcels do you send a surveyor to, to
> maximally reduce uncertainty across the entire city?**

Mechanism:

1. After harmonization every parcel carries a **calibrated** positional
   uncertainty σᵢ.
2. A new GNSS point does not fix one parcel — it becomes a **thin-plate-spline
   control point**, reducing uncertainty across a whole neighbourhood. Benefits
   are spatial and overlapping.
3. Model the residual displacement field as a **Gaussian process** with an RBF
   kernel. Conditioning on a candidate observation reduces posterior variance
   everywhere, in closed form.
4. Selecting the best K observation sites is **submodular maximisation** —
   greedy gives a provable **(1 − 1/e)** bound. Method: Krause, Singh & Guestrin,
   *Near-Optimal Sensor Placements in Gaussian Processes*, JMLR 2008.
5. Output: a ranked list of coordinates plus a predicted error reduction.

```
SURVEY PLAN — 40 points, budget ₹2.3 lakh
Predicted city-wide RMSE   0.81 m  →  0.29 m   (−64%)
Marginal value of point 41: 0.004 m  → stop here
Cost of full resurvey instead: ₹1.9 crore  (₹56,725/sq km × 33.4 sq km)
```

### The diagnostic half

Systematic source disagreement **localises where the original survey is
defective**. If five sources disagree in one ward and agree everywhere else,
that ward's survey is structurally bad. Emit a **survey quality map** — a
per-ward reliability grade the department does not currently have.

### One sentence

> **We don't just harmonize your data — we tell you where it's broken and
> exactly where to send your surveyors next.**

### Why this survives scrutiny

- **Not claimable without building it.** It outputs specific coordinates and a
  predicted error reduction. You either have it or you don't.
- **Verifiable in 60 seconds** — 40 points on a map, and the harness (§6) proves
  the predicted RMSE drop is real.
- **Three layers deep to copy**: needs the GT-bottleneck insight, needs
  *calibrated* uncertainty, needs submodular optimisation.
- **In scope.** Confidence scoring is an explicit required component. A
  confidence score that doesn't change what you do next is decoration. Use that
  bridge sentence verbatim if challenged.

Everything else in this build is **supporting infrastructure for this feature** —
calibration exists because targeting needs honest uncertainty; the validation
harness exists because you must prove the RMSE reduction is real. That framing
keeps the story coherent instead of a list of claims.

---

## 2. DATASETS — real data, no toy GeoJSON

The PS ships no dataset. **Do not generate 20 synthetic parcels.** Two real,
free, independent building datasets already disagree about every Indian city.

### 2.1 The core conflict pair

| Layer | Source | Why |
|---|---|---|
| **AI-extracted footprints** | **Microsoft GlobalMLBuildingFootprints** — `github.com/microsoft/GlobalMLBuildingFootprints` (quadkey-tiled GeoJSONL on Azure blob, no auth) | These *are* AI feature-extraction outputs — exactly what the PS says to integrate |
| **Municipal buildings** | **OpenStreetMap** via Geofabrik India extract — `download.geofabrik.de/asia/india.html` | Independent, human-surveyed, different vintage |

These genuinely disagree — different capture dates, different definitions of
"building", different geometry. **Real conflicts, zero staging.** Lead with it.

Optional third opinion: **Google Open Buildings v3**
(`sites.research.google/open-buildings/`) ships per-polygon confidence, useful
for provenance weighting.

### 2.2 Supporting layers

- **Terrain**: Copernicus GLO-30 DEM via **OpenTopography API**
  (`portal.opentopography.org/apidocs/`, free key by email). DTM; derive
  pseudo-DSM by adding footprint heights.
- **Imagery**: Esri World Imagery tiles (free, no key). Optionally
  **OpenAerialMap** (`openaerialmap.org`) for genuine drone orthos, and
  **Bhuvan** (ISRO) WMS for an Indian-sourced layer.
- **Roads / blocks / landuse / wards**: OSM.

### 2.3 Cadastral parcels — be honest

No free real Indian urban cadastre exists for bulk download. Bhu-Naksha
(`bhunaksha.nic.in/<state>`) has viewers, not data.

**Approach, stated openly in the UI and on the slide:**
1. Derive a **plausible cadastre** from OSM road blocks by recursive
   subdivision — real block geometry, synthesised interior plots, khasra
   numbering `parent/child`, Indian owner names, tenure, and recorded areas that
   drift from surveyed areas the way real records do.
2. Run the damage harness (§6) to produce the "legacy sheet".
3. Label it `SYNTHETIC — derived from OSM blocks` in **every panel and every
   export**.

Never present synthetic data as real. Stating the limit plainly earns more
credit than hiding it, and the harness is what makes measurement possible at all.

### 2.4 Ground control
Simulate GNSS/CORS by sampling true parcel corners at **±3 cm** (Survey of India
CORS spec). Sparse — 30–80 points, as in reality. **These are the points the
targeting module decides where to put.**

### 2.5 Area of interest
Primary: **Chandausi, Sambhal district, UP** (78.7749 E, 28.4515 N) — the actual
NAKSHA pilot launch site. **Verify MS + OSM density there first**; if sparse,
fall back to Bhopal / Indore / Pune and keep Chandausi as a second preset.

Ship 2–3 pre-baked extracts in `data/` so the demo never depends on a live
download. Provide `scripts/fetch_data.py` for reproducibility.

### 2.6 Calibrate damage to published reality
- **Sengupta et al., *Survey Review* (2016)**: modal **3–4 m** RMSE across 310
  real West Bengal cadastral sheets.
- **Survey of India circular T-260/1147 (10 Feb 2025)**: NAKSHA ORI 5 cm GSD,
  **RMSE(x,y) ≤ 10 cm**; DSM/DTM **RMSE(z) ≤ 15 cm**; CORS control < 5 cm.

That **30–40× mismatch is the problem.** Keep synthetic error in that band so
every number is citable.

---

## 3. STACK

```
Frontend   React 18 + Vite + TypeScript
           MapLibre GL JS v4   (NOT Leaflet — vector tiles, 3D, GPU)
           deck.gl v9          (GPU overlay + picking, 10k+ polygons)
           Tailwind + Radix primitives (headless — not a component-kit look)
           Zustand, TanStack Query
           Observable Plot or visx for charts (NOT Chart.js)
Backend    Python 3.11 + FastAPI + Pydantic v2
Geo        Shapely 2.x, NumPy, SciPy, rasterio
ML         XGBoost + isotonic calibration (scipy.optimize.isotonic_regression)
Tiles      PMTiles (protomaps) — single file, no tile server
Storage    SQLite + GeoJSON on disk (PostGIS only if time allows)
Export     GeoJSON, Shapefile, OGC API – Features, PDF audit report
```

**Environment blockers — handle before writing code:**
- **Node.js is NOT installed** on the target machine. Install it first.
- Windows **Smart App Control** blocks `pyproj`, `scikit-learn` and `lightgbm`
  at **every version tested**. Verified working: `numpy 2.4.6`, `scipy 1.17.1`,
  `shapely 2.1.2`, `pandas 2.3.3`, `xgboost 3.2.0`. Pin these. Do not
  `pip install -U`.

**Do not rewrite the engine.** A working, measured implementation exists at
`C:\Users\nairb\OneDrive\Desktop\sih13\kshetra\` — CRS (UTM + Everest 1830
from Snyder), geometry descriptors, synthetic city generator, damage harness,
coarse georeferencing, four transform models, matching features, XGBoost matcher
with isotonic calibration, assignment with split/merge detection, topology
cleaner, and hand-rolled metrics. **Port it.** Measured results:

| Metric | Value |
|---|---|
| Pairwise F1 / ROC AUC | 0.961 / 0.986 |
| Expected Calibration Error | 0.0034 |
| Blocking recall | 1.000 |
| Exact set match | 93.33% |
| Spurious parcels rejected | 57/57 |
| Subdivision detection precision | 1.000 |
| Topology errors | 6,199 → 238 (96.2%) |
| Overlapping pairs | 5,038 → 1 |
| Training time | 1.1 s |

---

## 4. PIPELINE — the order is not negotiable

```
0  INGEST        multi-format readers, CRS sniffing, schema profiling
1  SCHEMA MATCH  auto-map department columns → canonical fields
2  VALIDATE      repair invalid geometry before anything measures area
3  COARSE GEOREF Hough translation vote → robust trimmed similarity fit
4  BLOCKING      R-tree candidates  (MEASURE BLOCKING RECALL)
5  FEATURES      ~29 pairwise features: geometric, attribute, context
6  MATCH         XGBoost → isotonic calibration → honest probability
7  ASSIGN        containment split/merge detection → Hungarian for the rest
8  FINE GEOREF   matched parcels become GCPs → TPS rubber-sheet
9  TOPOLOGY      snap → resolve overlaps → classify & fill gaps
10 CONFLICTS     provenance-weighted resolution + review queue
11 CHANGE        epoch diff + DSM delta → new / demolished / encroachment
12 UNCERTAINTY   GP posterior variance field  ← feeds the USP
13 TARGETING     greedy submodular survey-point selection  ← THE USP
14 OUTPUT        ULPIN, confidence, audit log, OGC API, PDF
```

### Why step 3 must precede step 4 — put this on a slide
Urban plots are **~11 m across**; legacy misregistration is **5–15 m**. An
unaligned legacy parcel **overlaps its neighbour more than its own counterpart**.
Matching first gives **blocking recall 0.58** — 42% of true matches never reach
the model, and the model silently compensates by joining on khasra number
instead of geometry. Align first → **1.00**.

**Instrument blocking recall and display it.** If it isn't ≈1.0, nothing
downstream can recover.

### The leakage trap — avoid deliberately
A matcher trained on clean identifiers scores F1 0.99 and is **worthless** — it
learned a SQL join. If khasra numbers matched reliably this PS would not exist.
The harness **must** renumber ~45% of blocks and genuinely change ~12% of owners.
Then verify via feature importance that geometry dominates.

**Show the feature-importance chart in the UI.** It proves the model does
spatial reasoning and is the answer to "is this actually AI?"

### Matching features (~29)
- **Geometric**: IoU, normalised symmetric difference, centroid distance (raw +
  size-normalised), area ratio, normalised Hausdorff, rotation-invariant turning
  signature distance, src-in-tgt and tgt-in-src containment
- **Shape**: Δcompactness (Polsby-Popper), Δrectangularity, Δelongation, vertex ratio
- **Attribute**: Jaro-Winkler / Levenshtein / token-set on owner names *after
  Indian transliteration folding* (Mohd./Mohammed/MOHAMMAD → one form);
  structured khasra comparison (exact / parent / child); recorded-vs-geometric
  area ratio; land-use and ward agreement
- **Context (critical)**: candidate count, IoU rank, IoU margin to runner-up,
  is-best-IoU, reverse rank. Raw IoU cannot distinguish "confident" from "best
  of several bad options" — these are what make the confidence honest.

### Conflict resolution
Provenance-weighted voting, **inverse-variance weights** (`1/σ²` on stated
accuracy), modulated by recency and legal authority. Hard rules override:
**GNSS/CORS wins on geometry; revenue records win on ownership.** Authority is
per-attribute, not per-source. Every resolution writes an audit entry naming the
rule that fired.

### Conflict taxonomy — explicit thresholds, no hand-waving

Every candidate pair lands in exactly one class. `p` is the **calibrated**
match probability, not a weighted score.

| Class | Condition | Routing |
|---|---|---|
| `confirmed` | `p ≥ 0.95` and centroid residual `≤ 0.50 m` and IoU `≥ 0.80` | auto-accept |
| `positional_conflict` | `p ≥ 0.95` but residual `> 0.50 m` | auto-correct, log, flag if `> 2.0 m` |
| `attribute_conflict` | geometry agrees, attributes disagree on an authoritative field | resolve by per-attribute authority; **owner mismatch always → human** |
| `subdivision` | ≥ 2 sources each `≥ 0.70` contained in one reference, joint coverage `≥ 0.55` | auto, precision-tuned |
| `amalgamation` | mirror of the above | auto, precision-tuned |
| `missing_reference` | source parcel, no candidate `p ≥ 0.10` | flag as new or spurious |
| `missing_source` | reference parcel unmatched | **flag for field survey — never fabricate** |
| `unresolved` | any M:N that is not a clean subdivision/amalgamation | **straight to human** |

**Default to 1:1. Any many-to-many candidate that does not pass the
containment + coverage test goes to a human rather than being auto-resolved.**
Guessing at a tangled boundary is how a system loses an administrator's trust
permanently.

Thresholds live in one config object, are surfaced in the UI, and are
**tuned on the held-out city, never on the demo city.**

### Worked confidence example

Not a weighted sum. The matcher outputs a margin; isotonic calibration maps it
to a frequency; provenance adjusts for source quality.

```
Parcel L02291  ->  reference P01847

  matcher raw margin                    3.81
  sigmoid                               0.9782
  isotonic calibration (held-out fit)   0.9613   <- P(correct match)

  provenance adjustment
    legacy sheet   sigma 6.0 m, 1987, authoritative for ownership
    MS footprint   sigma 1.2 m, 2024, no ownership authority
    inverse-variance weight  ->  reference geometry dominates 25:1

  positional residual after TPS         0.28 m
  post-correction uncertainty (GP)      0.31 m

  FINAL       p = 0.961   sigma = 0.31 m   class = confirmed
  DISPOSITION auto-accept (threshold 0.95); no human review
```

What makes `0.961` meaningful: of all pairs the model scored near 0.96,
**96.1% were actually correct on held-out data** — and the reliability curve in
the Validate tab shows it. That sentence is the whole difference between this
and a weighted score.

---

## 5. THE TARGETING MODULE — implement this properly

`backend/targeting.py`. This is the USP; do not stub it.

```python
# 1. Residual field from georeferencing: at each matched parcel centroid xᵢ
#    we observed displacement rᵢ with known noise.
# 2. Model r(x) as a GP:  k(x,x') = σ_f² · exp(−‖x−x'‖² / 2ℓ²) + σ_n²·I
#    Fit ℓ and σ_f by marginal likelihood on the observed residuals.
# 3. Posterior variance at any x, given observation set S:
#       σ²(x|S) = k(x,x) − k(x,S) · [K(S,S)+σ_n²I]⁻¹ · k(S,x)
# 4. Objective: minimise total posterior variance over all parcels
#       F(S) = Σᵢ [ σ²(xᵢ|∅) − σ²(xᵢ|S) ]
#    F is monotone submodular → greedy is (1 − 1/e)-optimal.
# 5. Greedy: repeatedly add the candidate with the largest marginal gain.
#    Use lazy evaluation (priority queue) — it is ~100× faster and exact.
# 6. Candidate set: parcel corners + a coarse grid over the AOI.
# 7. Stop when marginal gain < threshold, or budget exhausted.
```

Report honestly:
- predicted RMSE before / after, with the GP's own credible interval
- the marginal-gain curve (shows diminishing returns and justifies "stop at 40")
- cost at ₹56,725/sq km vs full resurvey

**Validate it against the harness**: because the damage is known, you can
actually place the recommended points, re-run, and show the real RMSE drop
versus the predicted one. *Predicted 0.29 m, achieved 0.31 m* is far more
convincing than a prediction alone.

---

## 6. VALIDATION HARNESS — how anything gets measured

No ground truth ships with the PS, so manufacture it: take a clean cadastre,
**damage a copy in precisely known ways**, run the pipeline, measure recovery.
This runs **live in the app** as a Validate tab.

| Damage stage | Real cause |
|---|---|
| Similarity misregistration | sheet georeferenced from too few GCPs |
| Smooth non-linear warp (RBF) | paper shrinkage, scanner distortion |
| Vertex jitter / decimation | manual digitisation from paper |
| Sliver & overlap injection | adjacent parcels digitised independently |
| Self-intersection (bow-tie) | careless digitising |
| Schema drift | every department names columns differently |
| Owner-name corruption | transliteration variance |
| Area unit drift | records kept in bigha / biswa, not m² |
| Block renumbering (~45%) | resurvey renumbers whole khasra series |
| Owner genuinely changed (~12%) | property sold since the survey |
| Split / merge / missing / spurious | subdivision and amalgamation |

### Area conservation ledger — render this in the UI
A revenue officer's first question is *"did you change how much land I own?"*

```
summed parcel area   422,219 m²  →  410,028 m²   (−2.89%)
union footprint      404,586 m²  →  409,955 m²   (+1.33%)
doubly-claimed land   17,632 m²  →      72.7 m²
──────────────────────────────────────────────────────
removed double-counting   −17,560 m²
recovered sliver gaps      +5,369 m²
net                       −12,191 m²    NO LAND LOST
```

The summed area falls *because* two people were recorded owning the same ground;
the actual footprint goes *up*. Land is never silently created or destroyed.

### Principled restraint — counter it in the dashboard
When a hole is parcel-sized rather than a hairline sliver, the system **must not
fill it** — it flags it for ground survey. In testing it correctly preserved 69
of 73 deliberately deleted parcels. Filling them would be silent data
fabrication. Show a **"refused to guess"** counter.

---

## 7. UI — make it not look AI-generated

### Banned — these are the tells
Purple/indigo gradients · glassmorphism · `rounded-3xl` everywhere · emoji as
icons · centred marketing hero · "✨ Powered by AI" · pastel cards floating on
gradient · animated blobs · shadcn defaults straight out of the box.

### Target
**Professional geospatial software.** Reference: QGIS, ArcGIS Pro, Felt, Mapbox
Studio, Linear, Observable. Dense, calm, information-first. It should look like
something a tehsildar's office would actually run.

```
Type    IBM Plex Sans      UI  (has Devanagari — bilingual labels)
        IBM Plex Mono      every number, coordinate, ID, area
        base 13px / 1.45 · tabular-nums on all figures

Colour  chrome    #0F1419 → #1C2430  (near-black slate, NOT navy-purple)
        surface   #FFFFFF / #F7F8FA
        accent    ONE only — survey orange #E8590C or ISRO blue #1B5FA8
        semantic  #2F9E44 accept · #F08C00 review · #C92A2A conflict
        confidence ramp: sequential single-hue (Viridis / YlGnBu).
                  NEVER rainbow — it implies false category boundaries.

Layout  8px grid · 1px hairline borders #E3E6EA · radius ≤ 4px
        NO drop shadows on panels — borders only. Shadows read as template.

Chrome  persistent status bar: live lat/lon · CRS (EPSG:32644) · scale bar ·
        zoom · selected count · pipeline stage
        resizable docked panels (react-resizable-panels), not floating modals
```

### Layout — three-pane IDE, not a dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ toolbar: project · AOI · pipeline stage · Run · Export       │
├──────────┬───────────────────────────────────┬──────────────┤
│ LAYER    │                                   │ INSPECTOR    │
│ TREE     │             MAP                   │ parcel /     │
│ opacity  │          (dominant)               │ conflict /   │
│ blend    │                                   │ evidence /   │
│ legend   │                                   │ audit        │
├──────────┴───────────────────────────────────┴──────────────┤
│ DOCK tabs: Conflicts · Matches · Survey Plan · Validate ·    │
│            Audit · Metrics                                   │
│ virtualised grid, sortable, filterable, CSV export           │
└─────────────────────────────────────────────────────────────┘
```

Three-pane, because this is a **workbench, not a dashboard**. A dashboard is
read; a workbench is operated. The map never gets covered — panels dock and
resize, nothing floats over the data. **No modal ever appears over the map.**

### Interaction — where "good" actually separates from "AI-generated"

Visual tokens get you to competent. These get you to convincing.

**Keyboard-first.** A GIS operator's hands stay on the keyboard.
```
1–9      toggle layer n            ⌘K / Ctrl-K   command palette
Space    run / pause pipeline      /             search parcels by khasra
[ ]      prev / next conflict      Enter         accept highlighted suggestion
E        escalate to review        ⌘Z            undo (everything is undoable)
F        zoom to selection         \             toggle swipe compare
?        shortcut overlay          Esc           clear selection
```
The **command palette is the single highest-leverage element** — it makes the
app feel like a tool rather than a demo, and it costs an afternoon.

**Selection is a first-class state.** Clicking a parcel changes the inspector,
highlights its match on the other layer, draws the linkage arc, filters the
conflict grid, and updates the status bar count — all at once, all under 16 ms.
Selection survives layer toggles, pipeline re-runs and panel resizes.

**Optimistic UI.** Accepting a conflict updates the map **immediately** and
reconciles with the server after. Never make a reviewer wait on a round trip to
see their own decision. Roll back visibly if the server disagrees.

**Undo everything, with a visible stack.** A reviewer who fears a misclick
reviews slowly. ⌘Z unwinds accept/reject/geometry edits. The audit log is the
undo stack, rendered.

**Progressive disclosure in the evidence panel.** Default view: the decision and
its confidence. One click: the top-5 SHAP contributions. Another: all 29
features with their values. A judge asking "why did it match these?" should get
a deeper answer at every click, not a wall of numbers up front.

**Hover reveals information, never just colour.** Hovering a parcel shows khasra
+ area + confidence in a cursor-following readout. Hovering a survey point shows
its marginal gain and predicted RMSE delta. Hovering a conflict row highlights
it on the map without changing selection.

**Numbers never jump.** `font-variant-numeric: tabular-nums` everywhere, and
animate counters with `requestAnimationFrame` easing during the pipeline run so
figures settle instead of flickering.

### Motion — one orchestrated moment, not five effects

| Element | Duration | Easing | Why |
|---|---|---|---|
| **Alignment animation** | 1600 ms | `cubic-bezier(.22,1,.36,1)` | the signature moment; slow enough to *read* |
| Panel resize | 0 ms | — | must feel physical, never animated |
| Selection highlight | 120 ms | `ease-out` | acknowledgement, not decoration |
| Conflict pulse | 2400 ms loop | `ease-in-out` | ambient, very low amplitude |
| Stage transition | 240 ms | `ease-out` | progress feels continuous |
| Counter settle | 600 ms | `ease-out` | numbers arrive, don't flicker |

Everything else is instant. **Honour `prefers-reduced-motion`** — the alignment
animation becomes a cross-fade; nothing else moves.

### The states everyone forgets

These are where prototypes look unfinished, and judges notice:

- **Empty** — no AOI loaded: show the two presets with coverage stats, not a
  blank map with "Select a project."
- **Loading** — skeleton rows matching the real grid layout, never a spinner
  over the map. The map stays interactive during pipeline runs.
- **Long-running** — the pipeline takes minutes. Per-stage progress with elapsed
  time, a partial result on the map as each stage lands, and a working cancel.
- **Error** — "Overpass returned 504 — retrying mirror 2 of 4" is a real message.
  "Something went wrong" is not.
- **Zero results** — filtering conflicts to none shows *which* filter emptied it
  and a one-click clear.
- **Degraded** — MS `confidence` is absent for Pune. The UI must say
  "source-level prior (no per-feature confidence in this tile)" rather than
  silently showing a number that isn't real.

### Density and restraint

Base 13px, 28px rows, 8px grid. Target **information density close to QGIS's
attribute table** — an operator should see 25+ parcels without scrolling.

**One accent colour only.** Semantic colours (accept/review/conflict) are not
accents and must never be used decoratively. If everything is coloured, the red
parcel stops meaning anything.

**Borders, not shadows.** A 1px hairline separates; a drop shadow says
"template." The only permitted elevation is the command palette.

**Right-align every number. Left-align every label.** Non-negotiable in tables —
it is the fastest single tell of software written by someone who reads data.

### Accessibility — cheap, and it shows care

Focus rings on every interactive element (never `outline: none`). Full keyboard
traversal of the conflict queue. ARIA live region announcing pipeline stage
changes. **Confidence encoded by more than hue** — the choropleth pairs colour
with a hatch pattern at low confidence, so it survives both projector washout
and colour-blind viewers. That last one is a genuine risk in a demo room.

---

## 8. THE MAP — this must be genuinely beautiful

The map is the product. Budget real effort.

**Base**: a **custom MapLibre style JSON** — do not ship a stock CARTO/OSM style.
Muted monochrome "survey drafting" cartography so data colour pops: greys and
warm off-whites, roads as hairlines, buildings as faint fills. Serve from
**PMTiles** (single file, no tile server).

**Required:**

1. **The alignment animation** — the signature moment. Animate the legacy layer
   from misregistered to aligned over ~1.6 s, interpolating the transform matrix,
   with residual vectors fading out. Rehearse it.
2. **Survey plan layer** — the 40 recommended points, sized by marginal
   information gain, over a **posterior-variance heatmap**. This is the USP made
   visible; make it the best-looking layer in the app.
3. **Residual vector field** — per-parcel displacement arrows before
   georeferencing. Instantly communicates the problem; no other team will have it.
4. **3D building extrusion** from DSM heights, with `sky` and `light` configured
   and a low sun angle for real shadow relief.
5. **Terrain hillshade** from the Copernicus DEM via MapLibre `terrain`.
6. **Swipe / curtain compare** — before/after harmonization, both sides live.
7. **Confidence choropleth** with a continuous legend and a histogram brush that
   filters the map as you drag.
8. **deck.gl `GeoJsonLayer`** with GPU picking; `PolygonLayer` for extrusion;
   `ArcLayer` for match linkages between layers.
9. **Cartographic labels** — collision-detected, halo'd khasra numbers appearing
   by zoom. Bilingual Devanagari + Latin via IBM Plex.
10. Minimap, AOI bounds, scale bar, north arrow, coordinate readout.

One tasteful animation, not five. Target **60 fps at 10,000 parcels** — PMTiles
+ deck.gl, never per-feature DOM layers.

---

## 9. SCREENS

1. **Project / AOI** — pick Chandausi or a preset; per-source coverage, vintage,
   stated accuracy, CRS; "Fetch" or "Use bundled extract".
2. **Ingest & Profile** — geometry validity, CRS detected, column profile,
   **auto schema mapping with per-field confidence and manual override**. Judges
   *will* ask how columns get mapped.
3. **Harmonize** — live stage tracker; map updates per stage; metrics stream in;
   the alignment animation fires at stage 3.
4. **Review queue** — conflicts sorted by (confidence × land area at stake).
   Each opens an **evidence panel**: side-by-side geometry, **per-feature SHAP
   contributions from the matcher**, source comparison table, suggested
   resolution and the rule that produced it. Accept / Reject / Escalate /
   Field-survey. Every action writes to the audit log.
5. **Survey Plan (the USP)** — budget slider, the ranked point list, the
   marginal-gain curve, predicted vs achieved RMSE, cost comparison, export as
   GeoJSON/CSV for a field team.
6. **Validate** — run the harness live: inject known damage, recover, show the
   metrics table, reliability curve, feature importance and the area ledger.
7. **Export** — GeoJSON / Shapefile / GeoPackage, live **OGC API – Features**
   endpoint, and a **PDF audit report** listing every change with its reason,
   confidence and source.

---

## 10. DATA MODEL

```python
Provenance:  source_id, label, accuracy_m, vintage, authority: dict[str, bool]
             weight = 1 / max(accuracy_m, 0.01)**2      # inverse variance
             # authority is PER-ATTRIBUTE: GNSS authoritative for geometry,
             # revenue records authoritative for ownership.

Parcel:      fid, geometry, khasra_no, parent_khasra, owner_name,
             area_sqm, recorded_area_sqm, land_use, tenure, ward_no,
             ulpin, confidence, sigma_m, status, provenance[], audit[]

Match:       src_fid, tgt_fids[], relation, confidence, evidence{}
             relation ∈ {one_to_one, split, merge,
                         unmatched_source, unmatched_reference}

Conflict:    id, type, parcels[], sources[], magnitude, unit, confidence,
             suggested_resolution, rule_fired, status

SurveyPoint: rank, lon, lat, marginal_gain, cumulative_rmse_reduction, reason

AuditEntry:  ts, actor(system|user), action, target, before, after, reason
```

**ULPIN**: assign a 14-character position-derived identifier. The official
encoding is **not published** — implement a faithful *shape* and say so in code
comments and in the UI. Do not fabricate a spec.

---

## 11. ACCEPTANCE CRITERIA

No mocks, no hardcoded results:

- [ ] Real MS Building Footprints + OSM load for a real Indian AOI
- [ ] Schema auto-mapping produces a field map with confidences and overrides
- [ ] Coarse georeferencing measurably reduces RMSE; **blocking recall shown**
- [ ] Matcher trains, calibrates; **feature importance shows geometry ≥ 70%**
- [ ] Reliability curve + ECE from real held-out predictions
- [ ] Splits and merges detected, listed as change dossiers
- [ ] Topology repair reduces errors ≥ 90% with the **area ledger balancing**
- [ ] Parcel-sized holes flagged, **not** filled; counter visible
- [ ] Conflicts resolved by provenance weight with the rule displayed
- [ ] Review actions mutate the harmonized layer and write audit entries
- [ ] Encroachment on government land detected and mapped
- [ ] **Survey targeting returns ranked points with predicted RMSE reduction**
- [ ] **Harness validates targeting: predicted vs achieved RMSE both shown**
- [ ] Export: GeoJSON + Shapefile + OGC API Features + PDF audit report
- [ ] 60 fps at 10,000 parcels; alignment animation smooth
- [ ] Every synthetic layer labelled `SYNTHETIC` in UI and export
- [ ] README with exact setup commands, Node install included

---

## 12. THE 7-MINUTE DEMO — rehearse this exact order

1. Load Chandausi. Real MS footprints + real OSM buildings.
   **"These two real datasets already disagree about 340 buildings. Nobody
   staged this."**
2. Drop in the legacy cadastral sheet — visibly misregistered. Show the
   **residual vector field**.
3. Run harmonization. **The alignment animation.** RMSE 8.04 m → 0.31 m on screen.
4. Blocking recall 1.00; feature importance 88% geometric.
   **"It is doing spatial reasoning, not a database join."**
5. Confidence heatmap. **"1,198 auto-finalised at a 99% precision floor, 42 for
   review — and here is the reliability curve proving that 99% is real."**
6. Open a red parcel → evidence panel → SHAP → officer approves → audit entry.
7. Change detection: 18 new constructions, 3 demolitions, **6 encroachments on
   government land**. Then the **area ledger**: *"we removed 17,560 m² of land
   two people both owned, recovered 5,369 m² of slivers, and lost nothing."*
8. **The close — Survey Plan.** *"NAKSHA's own progress review says ground
   truthing is its biggest lagging component. So: send your surveyor to these 40
   points. Predicted city-wide RMSE 0.81 m → 0.29 m for ₹2.3 lakh, against
   ₹1.9 crore for a full resurvey. And because we can generate ground truth, we
   already verified it — predicted 0.29, achieved 0.31."*

---

## 13. WHAT NOT TO DO

- Don't build synthetic-only demo data — use real MS + OSM
- Don't use a weighted-sum "confidence" (`0.3·geom + 0.3·overlap + …`). It is
  not a probability, cannot be calibrated, and cannot be defended
- Don't match before georeferencing
- Don't train a segmentation model — footprint extraction is **upstream** of
  this PS. Use MS/Google footprints; keep the interface pluggable
- Don't use Leaflet, Chart.js, or stock component-kit styling
- Don't present synthetic data as real
- Don't fabricate the ULPIN encoding or any statistic
- Don't claim NAKSHA uses Everest 1830 — **it uses UTM on WGS84**
- Don't reference "Indian Geodetic Datum 2023" — **it does not exist**
- Don't generate a legal *mutation record* — emit a **change dossier** flagged
  for the revenue officer. Mutation is a statutory act requiring notice and a
  hearing; claiming to automate it invites a question you cannot answer, and
  the format varies by state
- Don't fill parcel-sized holes
- Don't build ten mediocre modules — build seven excellent ones and put the rest
  on a Future Scope slide

---

## 14. WHERE THIS WILL NOT WORK — say it before a judge finds it

Naming your own failure modes is the strongest credibility move available, and
every one of these will occur to a cadastral officer within the first minute.
Each needs a fallback, not a denial.

| Failure mode | Why | Fallback |
|---|---|---|
| **Dense informal settlements** | Roofs touch; no visible plot boundary exists on the ground. AI footprints merge whole blocks into one polygon. | Detect via footprint density + compactness collapse; mark the area `not_automatable` and exclude from auto-accept entirely. Do not report a confidence — report *unsurveyable by imagery*. |
| **Degraded scanned cadastral sheets** | Torn, faded, hand-annotated. Vectorisation is unreliable before georeferencing even starts. | Human vectorisation stays upstream. We consume vectors, not scans. State this scope boundary explicitly. |
| **Multi-storey / vertical tenure** | Flats stack ownership in 3D. A 2-D cadastre cannot represent four owners of one footprint. | Detect via DSM height + parcel-to-footprint cardinality; flag `vertical_tenure` and exclude. Future scope: 3D cadastre (LADM / ISO 19152). |
| **Tree-occluded parcels** | Canopy hides boundaries and roofs; DSM reads canopy, not building. | Mask from DSM–DTM anomaly; downweight rather than drop, and surface the reason. |
| **Sparse ground control** | With few GNSS points the TPS extrapolates wildly outside their hull. | Refuse to rubber-sheet beyond the control hull — fall back to affine there. **This is exactly what the targeting module exists to fix.** |
| **Genuinely ambiguous boundaries** | Some disputes are legal, not geometric. No amount of imagery resolves who owns a contested strip. | Route to human with both claims preserved. **Never auto-resolve a boundary under active dispute.** |
| **Khasra renumbering with no crosswalk** | After a resurvey the identifier carries no information. | Geometry-only matching — which is why the model is 88% geometric by design. |

**The honest framing:** the system is built to be *correct on what it attempts
and explicit about what it declines*. Coverage is a tunable; trustworthiness is
not. Put the `not_automatable` count on the dashboard next to the auto-accept
count — a system that admits its own limits reads as engineering, and one that
claims 100% coverage reads as a sales pitch.

---

## 15. VERIFIED FACTS FOR THE PITCH

- **Survey of India circular T-260/1147 (10 Feb 2025)** — NAKSHA spec: ORI 5 cm
  GSD, RMSE(x,y) ≤ 10 cm; DSM/DTM RMSE(z) ≤ 15 cm; CORS < 5 cm. **CRS: UTM on
  WGS84.**
- **NAKSHA**: 152 ULBs, 26 states + 3 UTs, **₹194 crore**, 4,142.63 sq km,
  scaling to all **4,912 ULBs**. Ministry = **Rural Development / DoLR** (not
  MoHUA). Survey of India = named Technology Partner.
- **DILRMP: only 49.10% of villages have geo-referenced cadastral maps.**
- **Sengupta et al., *Survey Review* (2016)**: modal **3–4 m** RMSE over 310 real
  West Bengal sheets → **30–40× mismatch** against NAKSHA's 10 cm.
- **The anchor citation**: *Frontiers in Sustainable Cities* (2026) on NAKSHA,
  first-authored by **Kunal Satyarthi, Joint Secretary, DoLR**. Names *"parallel,
  non-interoperable records"* as a top friction point, reports **ground truthing
  as the biggest lagging component (55 of ~150 ULBs below 60%)**, and explicitly
  recommends **"automated GeoAI-driven updating mechanisms."** *The programme
  owner is asking for this system in print.*
- **₹56,725/sq km** — Tamil Nadu's official resurvey rate quoted to DoLR. Use
  this for survey-cost economics.
- **Best unexpected evidence**: NIC's Bhu-Naksha manual documents a **manually
  entered per-state magic scale factor** on shapefile import — UP ×4000, Himachal
  ×22 (*karam* digitised in centimetres). India's incumbent national cadastral
  tool ships with hardcoded unit chaos.
- **Closest prior art**: Suwardhi et al., ISPRS 2025 (Indonesia) — SAM + block
  ICP + hierarchical least squares, 6,198 parcels. **Single-source, no schema /
  CRS / tenure handling, and no survey-planning component.**
- **Targeting method**: Krause, Singh & Guestrin, *Near-Optimal Sensor Placements
  in Gaussian Processes*, JMLR 2008 — submodularity and the (1 − 1/e) bound.

**Do not state as fact** (unverified): man-hours or cost of manual GIS
*integration* (no published figure exists); ULPIN's exact encoding; the NAKSHA
SDMS schema contents.

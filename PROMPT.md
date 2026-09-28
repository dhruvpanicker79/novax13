# BUILD PROMPT — KSHETRA

> Paste this whole file as your brief. It is the single source of truth.
> `BUILD_PROMPT.md` is the longer reference it was distilled from;
> `PLAN.md` has the phase ordering; `HANDOFF.md` has the current state.

---

## ROLE

You are a senior GeoAI systems engineer building a **working prototype**, not a
specification. Every number that appears on screen must have been computed from
real data by code you wrote. No mockups, no placeholder metrics, no "this would
show…". If a stage isn't implemented, its panel says so plainly rather than
displaying a fabricated figure.

**Deliverable: a running application.** If you find yourself writing a document
instead of code, you have misread this brief.

---

## MISSION

Smart India Hackathon 2026, PS13 — *Automated Integration and Intelligent
Harmonization of Multi-source Geospatial Data for Urban Land Record Management.*

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
this revenue record are the same property; emit one clean, topologically valid
layer; attach an honest confidence to every decision so a human reviews only the
uncertain ones.

This is **spatial entity resolution for land**. The product is **triage, not
full automation** — say that out loud, it is what makes an administrator believe
you.

---

## NON-NEGOTIABLES

Six rules. Violating any one of them breaks the project.

1. **Georeference before matching.** Not negotiable, established empirically.
2. **Confidence must be a calibrated probability.** Never a weighted sum.
3. **Use real data.** Microsoft + OSM already disagree; don't invent conflicts.
4. **The system must refuse to guess.** Restraint is a feature, not a gap.
5. **Every synthetic layer is labelled `SYNTHETIC`** in UI and in every export.
6. **Never fabricate a statistic or a citation.** §14 lists what is verified.

---

## 0. EXECUTIVE SUMMARY (write this into the README; it is also your PPT abstract)

> Urban land records in India are assembled from a dozen mutually inconsistent
> sources. Legacy cadastral sheets carry a modal positional error of 3–4 m
> (Sengupta et al., *Survey Review*, 2016, across 310 West Bengal sheets), while
> the NAKSHA programme specifies orthoimagery accurate to 10 cm — a 30–40×
> mismatch that makes naive overlay meaningless. KSHETRA harmonises these
> sources automatically: it globally georeferences legacy geometry, resolves
> parcel identity with a learned spatial matcher whose confidence is
> isotonically calibrated against held-out ground truth, repairs topology while
> proving no land was created or destroyed, and resolves inter-source conflicts
> by inverse-variance provenance weighting with per-attribute authority.
> Its distinguishing capability is closing the loop: because every parcel
> carries an honest uncertainty, the system computes **where to send the next
> surveyor** — selecting ground-control locations by submodular optimisation
> over a Gaussian-process error field — and addresses ground truthing, which
> NAKSHA's own 2026 progress review identifies as the programme's
> biggest lagging component.

---

## 1. THE USP — build this or the project is generic

The PS enumerates ten sources and seven components. It is a **spec**. Every
competing team will build to it and every architecture diagram will show the
same ten boxes. **You cannot differentiate on the spec.**

Two tempting positions are already burnt: *"adjudication-grade harmonization"*
(an adjective, claimable by anyone) and *"n-source fusion"* (everyone's diagram
has ten boxes). Do not use either as a headline.

### The insight

NAKSHA's own progress review — *Frontiers in Sustainable Cities* (2026),
first-authored by **Kunal Satyarthi, Joint Secretary, DoLR** — reports that
**ground truthing is "the biggest lagging component," 55 of ~150 ULBs below 60%
completion.** The bottleneck is not integration. **It is that ground truth is
scarce and expensive.** The PS lists GT and GNSS as *inputs*, as though you
simply have them.

### The feature: optimal survey targeting

> **Given a fixed survey budget, which 40 parcels do you send a surveyor to, so
> that uncertainty across the entire city falls as far as possible?**

Implement in `backend/kshetra/targeting/`:

```python
# 1. Residual field: at each confidently matched parcel centroid xᵢ we observed
#    displacement rᵢ. Model r(x) as a Gaussian process:
#       k(x,x') = σ_f² · exp(−‖x−x'‖² / 2ℓ²) + σ_n²·I
#    Fit ℓ, σ_f, σ_n by maximising log marginal likelihood on observed residuals.
#
# 2. Posterior variance given observation set S:
#       σ²(x|S) = k(x,x) − k(x,S)·[K(S,S)+σ_n²I]⁻¹·k(S,x)
#    NOTE: depends only on WHERE you observe, not what you measure — which is
#    exactly why the plan can be computed before anyone leaves the office.
#
# 3. Objective:  F(S) = Σᵢ [σ²(xᵢ|∅) − σ²(xᵢ|S)]
#    F is monotone submodular → greedy is (1 − 1/e)-optimal.
#    Krause, Singh & Guestrin, JMLR 9 (2008).
#
# 4. Closed-form marginal gain — evaluate ALL candidates in one vectorised pass:
#       gain(c) = Σᵢ cov(xᵢ, c | S)² / (σ²(c|S) + σ_n²)
#    Never loop over candidates in Python.
#
# 5. Candidates = parcel CORNERS, not grid nodes. A surveyor needs a physical,
#    identifiable monument to occupy.
#
# 6. Stop when marginal gain < 0.2% of the first point's, or budget exhausted.
```

Output shaped like a work order:

```
SURVEY PLAN — 40 points, ₹2.30 lakh
  expected city-wide RMSE   0.81 m → 0.29 m   (−64%)
  marginal value of point 41: 0.004 m → stop here
  full resurvey instead: ₹18.9 lakh  (₹56,725/sq km × 33.4 sq km)
```

### Validate it, don't just claim it

Because the damage harness (§6) knows ground truth, **actually place the
recommended control, re-run TPS georeferencing, and measure the real result**
— against 40 *random* points as the control:

```
before any new control            0.812 m
PREDICTED after 40 points         0.290 m
ACHIEVED after 40 points          0.310 m
ACHIEVED with 40 RANDOM points    0.604 m
```

**If optimised placement does not beat random, the USP is theatre.** Test this
on day one. Fallback: promote the measurement apparatus (calibration + area
ledger + restraint) to primary — weaker, more copyable, but honest.

### The diagnostic half

Systematic source disagreement **localises where the original survey is
defective**. Five sources disagreeing in one ward but agreeing elsewhere means
that ward's survey is structurally bad. Emit a **survey quality map** — a
per-ward reliability grade the department does not currently have.

**One sentence:** *We don't just harmonize your data — we tell you where it's
broken and exactly where to send your surveyors next.*

---

## 2. DATA — real, already on disk

No dataset ships with the PS. **Do not generate 20 synthetic parcels.** Two
free, independent, real building datasets already disagree about every Indian
city.

| Layer | Source | Role |
|---|---|---|
| AI footprints | **Microsoft GlobalMLBuildingFootprints** (`github.com/microsoft/GlobalMLBuildingFootprints`, quadkey GeoJSONL on Azure, no auth) | these *are* AI feature-extraction outputs — exactly what the PS says to integrate |
| Municipal buildings | **OpenStreetMap** via Overpass / Geofabrik | independent, human-surveyed, different vintage |
| Terrain | **Copernicus GLO-30** via OpenTopography API (free key) | DTM; pseudo-DSM by adding footprint heights |
| Imagery | Esri World Imagery (no key); OpenAerialMap for real drone orthos; Bhuvan WMS | basemap |

### Already fetched and validated (`data/raw/`)

| AOI | MS footprints | OSM buildings | OSM roads |
|---|---|---|---|
| **Chandausi** 78.7749 E, 28.4515 N | **5,488** | **6** | 1,713 |
| **Pune** 73.8553 E, 18.5308 N | **8,527** | **8,171** | 3,133 |

**Chandausi = 915 : 1.** The NAKSHA pilot town has a mapped road network and
essentially no municipal building data, while AI extraction yields thousands of
footprints. **That gap is the problem statement**, not a data limitation. Open
with it.

**Pune = 8,527 vs 8,171, median area 179.6 m² vs 154.2 m²** — a systematic 16%
disagreement over identical ground. Real, uncurated, unstaged conflict. Use this
for the matching and conflict work.

### Cadastral parcels — be honest

No free real Indian urban cadastre exists for bulk download. So:
1. Derive a **plausible cadastre** from OSM road blocks by recursive
   subdivision — real block geometry, synthesised interior plots, khasra
   numbering `parent/child`, Indian owner names, tenure, recorded-area drift.
2. Run the damage harness (§6) to produce the "legacy sheet".
3. Label `SYNTHETIC — derived from OSM blocks` **everywhere**.

Never present synthetic data as real. Stating the limit plainly earns more
credit than hiding it, and the harness is what makes measurement possible.

### Gotchas that will cost you hours

- **MS `confidence` is tile-dependent**: 100% present for Chandausi (median
  0.965), **0% for Pune** (all −1.0). Provenance must fall back to a
  source-level prior, and the UI must *say* it is doing so.
- `height` is −1.0 in both tiles → DSM must come from Copernicus.
- **Overpass `out geom` returns whole ways**, so road layers sprawl far beyond
  the AOI (Chandausi: 0.42° vs the 0.036° AOI). Harmless for display,
  **fatal for block derivation. Clip to AOI first.**
- Overpass main instance throws 504/429 constantly. Rotate mirrors;
  `overpass.kumi.systems` is most reliable.

### Calibrate synthetic damage to measured reality

- **Sengupta et al., *Survey Review* (2016):** modal **3–4 m** RMSE, 310 real
  West Bengal cadastral sheets.
- **Survey of India circular T-260/1147 (10 Feb 2025):** NAKSHA ORI 5 cm GSD,
  **RMSE(x,y) ≤ 10 cm**; DSM/DTM RMSE(z) ≤ 15 cm; CORS < 5 cm. **CRS: UTM on WGS84.**

Keep injected error in that band so every number is citable.

---

## 3. STACK — decided, with the reason in one line

| Layer | Choice | Why |
|---|---|---|
| Frontend | **React 18 + Vite + TypeScript** | fast HMR; TS is mandatory at this data complexity |
| Map | **MapLibre GL JS v4** | vector tiles, 3D, GPU — Leaflet cannot do the alignment animation or 10k parcels |
| Overlay | **deck.gl v9** | GPU picking; DOM layers collapse past ~2k polygons |
| Styling | **Tailwind + Radix primitives** | headless, so it doesn't inherit a component-kit look |
| State | **Zustand + TanStack Query** | selection state is global and cross-panel; server state is cached |
| Charts | **Observable Plot** | grammar-of-graphics; Chart.js looks like a template |
| Backend | **FastAPI + Pydantic v2** | async job orchestration, typed contracts, free OpenAPI |
| Geometry | **Shapely 2.x + NumPy + SciPy** | STRtree returns indices; scipy has isotonic + Hungarian |
| Model | **XGBoost (native Booster API)** | ~29 heterogeneous tabular features with heavy interaction; trains in ~1 s; decision path is printable for audit |
| Calibration | **`scipy.optimize.isotonic_regression`** | monotone, non-parametric, no distributional assumption |
| Tiles | **PMTiles** | single file, no tile server |
| Storage | **SQLite + GeoJSON on disk** | demo scale; PostGIS only if time allows |

**Do not train a segmentation model.** Feature extraction is *upstream* of this
PS — you consume footprints, you don't produce them. Keep the interface
pluggable and say so.

### Environment
- **Node.js and the numeric stack must both work before you start.** On the
  target Windows machine, Smart App Control (enforced) blocks numpy, scipy,
  shapely, pandas and xgboost at every version. WSL2 is the fix — it also
  restores pyproj/rasterio/sklearn and installs Node. See `HANDOFF.md §2`.
- Where `pyproj`/`sklearn` are unavailable, the repo already contains
  hand-written replacements (Snyder UTM, ROC/AP/Brier/ECE, Jaro-Winkler).
  **Keep them and cross-validate against the real libraries** — "we implemented
  the CRS engine and calibration from first principles, and here is the
  sub-millimetre agreement with pyproj" is a better line than an import.

---

## 4. PIPELINE — this order is fixed

```
0  INGEST        multi-format readers, CRS sniffing, schema profiling
1  SCHEMA MATCH  auto-map department columns → canonical fields
2  VALIDATE      repair invalid geometry BEFORE anything measures area
3  COARSE GEOREF Hough translation vote → robust trimmed similarity fit
4  BLOCKING      R-tree candidates          ← MEASURE BLOCKING RECALL
5  FEATURES      ~29 pairwise features
6  MATCH         XGBoost → isotonic calibration → honest probability
7  ASSIGN        containment split/merge detection → Hungarian for the rest
8  FINE GEOREF   matched parcels become GCPs → TPS rubber-sheet
9  TOPOLOGY      snap → resolve overlaps → classify & fill gaps
10 CONFLICTS     provenance-weighted resolution + review queue
11 CHANGE        epoch diff + DSM delta → new / demolished / encroachment
12 UNCERTAINTY   GP posterior variance field
13 TARGETING     greedy submodular survey selection      ← THE USP
14 OUTPUT        ULPIN, confidence, audit log, OGC API, PDF
```

### Why 3 must precede 4 — put this on a slide

Urban plots are **~11 m across**; legacy misregistration is **5–15 m**. An
unaligned legacy parcel therefore **overlaps its neighbour more than its own
counterpart**. Matching first gives **blocking recall 0.58** — 42% of true
matches never reach the model, and the model silently compensates by joining on
khasra number instead of geometry. Align first → **1.00**.

**Instrument blocking recall and display it.** If it isn't ≈1.0, nothing
downstream can recover.

### The leakage trap — avoid deliberately

A matcher trained on clean identifiers scores **F1 0.9955 and is worthless** —
it learned a SQL join. (This happened; `iou` contributed 0.24% of the decision.)
If khasra numbers matched reliably, this PS would not exist.

So the harness **must** renumber ~45% of blocks (real resurveys do this) and
genuinely change ~12% of owners. Then assert in CI:

```python
assert geometry_feature_share >= 0.70   # currently 0.88
```

**Render the feature-importance chart in the UI.** It is the answer to "is this
actually AI, or a database join?"

### Features (~29)

- **Geometric** — IoU, normalised symmetric difference, centroid distance (raw
  + size-normalised), area ratio, normalised Hausdorff, rotation-invariant
  turning-signature distance, src-in-tgt and tgt-in-src containment
- **Shape** — Δcompactness (Polsby-Popper), Δrectangularity, Δelongation, vertex ratio
- **Attribute** — Jaro-Winkler / Levenshtein / token-set on owner names *after
  Indian transliteration folding* (Mohd./Mohammed/MOHAMMAD → one form);
  structured khasra comparison (exact / parent / child); recorded-vs-geometric
  area ratio; land-use and ward agreement
- **Context** — candidate count, IoU rank, IoU margin to runner-up, is-best-IoU,
  reverse rank. **Critical:** raw IoU cannot distinguish "confident" from "best
  of several bad options". These features are what make the confidence honest.

---

## 5. CONFLICT TAXONOMY — explicit thresholds

`p` is the calibrated probability, not a score.

| Class | Condition | Routing |
|---|---|---|
| `confirmed` | `p ≥ 0.95`, residual `≤ 0.50 m`, IoU `≥ 0.80` | auto-accept |
| `positional_conflict` | `p ≥ 0.95`, residual `> 0.50 m` | auto-correct; flag if `> 2.0 m` |
| `attribute_conflict` | geometry agrees, authoritative field disagrees | per-attribute authority; **owner mismatch always → human** |
| `subdivision` | ≥2 sources each `≥0.70` contained in one reference, coverage `≥0.55` | auto, precision-tuned |
| `amalgamation` | mirror of above | auto, precision-tuned |
| `missing_reference` | source parcel, no candidate `p ≥ 0.10` | flag new or spurious |
| `missing_source` | reference unmatched | **field survey — never fabricate** |
| `unresolved` | any M:N failing the containment test | **straight to human** |

**Default to 1:1. Any many-to-many that doesn't pass containment + coverage goes
to a human.** Guessing at a tangled boundary loses an administrator's trust
permanently.

**Split detection is tuned for precision, not F1.** Best F1 was 0.398; we chose
the setting giving **precision 1.000, recall 0.227** instead. Falsely claiming a
subdivision is a legal problem; missing one routes to review, which is where
uncertain cases belong. Say this out loud — it demonstrates domain
understanding.

### Conflict resolution
Inverse-variance provenance weighting (`1/σ²` on stated accuracy), modulated by
recency and **per-attribute** legal authority: **GNSS/CORS wins geometry;
revenue records win ownership.** Detect transitive inconsistency (A≈B, B≈C,
A≠C). Every resolution writes an audit entry naming the rule that fired.

---

## 6. VALIDATION HARNESS + THE THREE PROOFS

No ground truth ships with the PS, so manufacture it: damage a clean cadastre in
precisely known ways, run the pipeline, measure recovery. **Runs live in the app
as a Validate tab.**

Damage stages, each a documented real failure: similarity misregistration ·
smooth RBF warp (paper shrinkage) · vertex jitter · decimation · sliver &
overlap injection · self-intersection · schema drift · owner-name corruption ·
area-unit drift (bigha/biswa) · block renumbering · split/merge/missing/spurious.

### Proof 1 — calibration is honest
Reliability curve + **ECE** from real held-out predictions. Target ECE ≤ 0.02.
This is what converts accuracy into a decision: *"auto-finalise 73% at a 99%
precision floor."*

### Proof 2 — the area ledger balances
```
summed parcel area   422,219 m² → 410,028 m²   (−2.89%)
union footprint      404,586 m² → 409,955 m²   (+1.33%)
doubly-claimed land   17,632 m² →     72.7 m²
──────────────────────────────────────────────────────
removed double-counting −17,560 m² · recovered slivers +5,369 m² · NO LAND LOST
```
Summed area falls *because* two people were recorded owning the same ground;
the real footprint goes **up**. Render this in the UI — it answers the revenue
officer's first question, *"did you change how much land I own?"*

### Proof 3 — the system refuses to guess
Parcel-sized holes are **flagged for survey, not filled**. In testing the
cleaner preserved **69 of 73** deliberately deleted parcels. Filling them would
be silent data fabrication. Put a **"refused to guess" counter** on the
dashboard next to auto-accept.

---

## 7. UI — the part that decides the room

### Banned — these are the tells
Purple/indigo gradients · glassmorphism · `rounded-3xl` everywhere · emoji as
icons · centred marketing hero · "✨ Powered by AI" · pastel cards on gradient ·
animated blobs · shadcn defaults straight out of the box.

### Target
**Professional geospatial software.** Reference QGIS, ArcGIS Pro, Felt, Mapbox
Studio, Linear, Observable. Dense, calm, information-first. It should look like
something a tehsildar's office would actually run.

```
Type    IBM Plex Sans   UI (has Devanagari — bilingual labels)
        IBM Plex Mono   every number, coordinate, ID, area
        13px / 1.45 · tabular-nums on all figures

Colour  chrome   #0F1419 → #1C2430   near-black slate, NOT navy-purple
        surface  #FFFFFF / #F7F8FA
        accent   ONE only — survey orange #E8590C
        semantic #2F9E44 accept · #F08C00 review · #C92A2A conflict
        confidence ramp: sequential single-hue (Viridis / YlGnBu)
                  NEVER rainbow — it implies false category boundaries

Layout  8px grid · 1px hairlines #E3E6EA · radius ≤ 4px
        NO drop shadows on panels — borders only
```

### Three-pane workbench, not a dashboard
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
│ DOCK: Conflicts · Matches · Survey Plan · Validate · Audit   │
│ virtualised grid, sortable, filterable, CSV export           │
└─────────────────────────────────────────────────────────────┘
```
A dashboard is read; a workbench is operated. **No modal ever covers the map.**

### Interaction — where "good" separates from "AI-generated"

**Keyboard-first.**
```
1–9   toggle layer n          ⌘K    command palette
Space run / pause pipeline    /     search by khasra
[ ]   prev / next conflict    Enter accept highlighted suggestion
E     escalate to review      ⌘Z    undo (everything is undoable)
F     zoom to selection       \     toggle swipe compare
?     shortcut overlay        Esc   clear selection
```
The **command palette is the single highest-leverage element** — it makes the
app feel like a tool rather than a demo, and costs an afternoon.

- **Selection is global state.** One click updates inspector, highlights the
  matched counterpart, draws the linkage arc, filters the conflict grid and
  updates the status bar — all under 16 ms. It survives layer toggles and
  pipeline re-runs.
- **Optimistic UI.** Accepting a conflict updates the map *immediately*;
  reconcile after. Never make a reviewer wait to see their own decision.
- **Undo everything, visibly.** The audit log *is* the undo stack, rendered.
- **Progressive disclosure.** Evidence panel: decision + confidence → one click
  for top-5 SHAP contributions → another for all 29 features. A judge asking
  "why?" gets a deeper answer at every click.
- **Hover reveals information, never just colour.**
- **Numbers never jump.** `tabular-nums` everywhere; ease counters during the
  run so figures settle instead of flickering.

### Motion — one orchestrated moment, not five effects

| Element | Duration | Easing |
|---|---|---|
| **Alignment animation** | 1600 ms | `cubic-bezier(.22,1,.36,1)` |
| Panel resize | 0 ms | must feel physical |
| Selection highlight | 120 ms | `ease-out` |
| Conflict pulse | 2400 ms loop | very low amplitude |
| Stage transition | 240 ms | `ease-out` |
| Counter settle | 600 ms | `ease-out` |

Everything else instant. Honour `prefers-reduced-motion` — the alignment
animation becomes a cross-fade.

### The states everyone forgets
**Empty** — show the two AOI presets with coverage stats, not "Select a
project." · **Loading** — skeleton rows matching the real grid; never a spinner
over the map · **Long-running** — per-stage progress, elapsed time, partial
results as each stage lands, working cancel · **Error** — *"Overpass returned
504 — retrying mirror 2 of 4"*, never "Something went wrong" · **Zero results**
— name the filter that emptied it · **Degraded** — say *"source-level prior (no
per-feature confidence in this tile)"* rather than showing a number that isn't real.

### Density, restraint, access
Base 13px, 28px rows. Target **QGIS attribute-table density** — 25+ parcels
visible without scrolling. **One accent colour**; semantic colours are never
decorative. **Borders, not shadows.** **Right-align numbers, left-align labels**
— the fastest tell of software written by someone who reads data. Focus rings on
everything; full keyboard traversal of the queue; ARIA live region for stage
changes. **Encode confidence by hue *and* hatch pattern** — survives projector
washout and colour-blind viewers, both real risks in a demo room.

---

## 8. THE MAP — budget real effort here

Custom **MapLibre style JSON** — never a stock CARTO style. Muted monochrome
"survey drafting" cartography so data colour pops. Serve from **PMTiles**.

1. **The alignment animation** — signature moment. Legacy layer interpolates
   from misregistered to aligned over 1600 ms, residual vectors fading out.
2. **Survey plan layer** — the 40 points sized by marginal gain over a
   posterior-variance heatmap. **Make this the best-looking layer in the app**;
   it is the USP made visible.
3. **Residual vector field** — per-parcel displacement arrows before
   georeferencing. Communicates the problem instantly; nobody else will have it.
4. **3D extrusion** from DSM, with `sky` + `light` and a low sun angle.
5. **Terrain hillshade** from Copernicus.
6. **Swipe compare** — before/after, both sides live.
7. **Confidence choropleth** with a histogram brush that filters as you drag.
8. **deck.gl** `GeoJsonLayer` (GPU picking), `PolygonLayer` (extrusion),
   `ArcLayer` (match linkages).
9. Collision-detected halo'd khasra labels, bilingual Devanagari + Latin.
10. Minimap, AOI bounds, scale bar, north arrow, coordinate readout.

**60 fps at 10,000 parcels.**

---

## 9. SCREENS

1. **Project / AOI** — presets with per-source coverage, vintage, accuracy, CRS
2. **Ingest & Profile** — validity, CRS detected, column profile, **auto schema
   mapping with per-field confidence and manual override** (judges *will* ask)
3. **Harmonize** — live stage tracker; alignment animation fires at stage 3
4. **Review queue** — sorted by (confidence × land area at stake); evidence
   panel with SHAP; Accept / Reject / Escalate / Field-survey; every action audited
5. **Survey Plan** — budget slider, ranked points, marginal-gain curve,
   predicted vs achieved, cost comparison, export for a field team
6. **Validate** — harness live: metrics table, reliability curve, area ledger,
   feature importance
7. **Export** — GeoJSON / Shapefile / GeoPackage, **OGC API – Features**,
   **PDF audit report** listing every change with reason, confidence and source

---

## 10. SECURITY (land records are personal data)

- **Hash-chained audit log** — `hash(prev + entry)`. Any retro-edit breaks the
  chain. ~50 lines, and it upgrades "we have an audit trail" to "our audit trail
  is provably unaltered." **Do this one regardless of time.**
- **RBAC + field-level redaction** — `public / surveyor / clerk / tehsildar`.
  Owner names are PII: the public role sees geometry, khasra, land use — never
  owner. **Enforced server-side at serialisation**, not hidden in the UI.
- **DPDP Act 2023** — purpose limitation, minimisation in exports, retention
  policy on job artifacts. Our demo owners are synthetic; say so plainly.
- **Input hardening** — GeoJSON bombs (millions of vertices), zip bombs in
  shapefiles, coordinate overflow, self-intersecting rings that hang predicates,
  `..` traversal in uploads. Size caps, vertex caps, timeouts.
- No secrets in repo, CORS allowlist, rate limiting, signed export manifests.

---

## 11. ACCEPTANCE CRITERIA — no mocks, no hardcoded results

- [ ] Real MS + OSM load for a real Indian AOI
- [ ] Schema auto-mapping emits a field map with confidences and overrides
- [ ] Coarse georeferencing measurably reduces RMSE; **blocking recall displayed**
- [ ] Matcher trains and calibrates; **feature importance ≥ 70% geometric**
- [ ] Reliability curve + ECE from real held-out predictions
- [ ] Splits/merges detected and listed as change dossiers
- [ ] Topology errors reduced ≥ 90% with the **area ledger balancing**
- [ ] Parcel-sized holes flagged, **not** filled; counter visible
- [ ] Conflicts resolved by provenance weight with the rule shown
- [ ] Encroachment on government land detected and mapped
- [ ] **Survey targeting returns ranked points with predicted RMSE reduction**
- [ ] **Harness shows predicted vs achieved vs random**
- [ ] Export: GeoJSON + Shapefile + OGC API + PDF audit report
- [ ] Hash-chained audit log; tamper detectable
- [ ] 60 fps at 10k parcels; alignment animation smooth
- [ ] Every synthetic layer labelled `SYNTHETIC` in UI and export
- [ ] README with exact setup commands

---

## 12. WHERE THIS WILL NOT WORK — say it before a judge finds it

| Failure mode | Fallback |
|---|---|
| **Dense informal settlements** — roofs touch, no ground boundary exists | detect via density + compactness collapse; mark `not_automatable`, exclude from auto-accept. Report *unsurveyable by imagery*, not a confidence. |
| **Degraded scanned sheets** | human vectorisation stays upstream; we consume vectors, not scans |
| **Vertical tenure** — four owners, one footprint | detect via DSM height + cardinality; flag, exclude. Future: 3D cadastre (LADM / ISO 19152) |
| **Tree occlusion** | mask from DSM–DTM anomaly; downweight and surface the reason |
| **Sparse ground control** | refuse to rubber-sheet beyond the control hull; fall back to affine. **This is what the targeting module exists to fix.** |
| **Legally disputed boundaries** | preserve both claims, route to human. **Never auto-resolve a boundary under dispute.** |
| **Khasra renumbering, no crosswalk** | geometry-only matching — why the model is 88% geometric by design |

**Put the `not_automatable` count on the dashboard next to auto-accept.** A
system that admits its limits reads as engineering; one claiming 100% coverage
reads as a sales pitch.

---

## 13. NEVER DO

- Build synthetic-only demo data — real MS + OSM are on disk
- Use a weighted-sum confidence (`0.3·geom + 0.3·overlap + …`). It is not a
  probability, cannot be calibrated, cannot be defended
- Match before georeferencing
- Train a segmentation model
- Use Leaflet, Chart.js, or stock component-kit styling
- Present synthetic data as real
- Generate a legal **mutation record** — emit a **change dossier flagged for the
  revenue officer**. Mutation is a statutory act requiring notice and hearing,
  the format varies by state, and in urban Karnataka "khata" means a
  property-tax account, not a revenue holding. Answer to "who signs this?" is
  *"the officer does; we built the file."*
- Fill parcel-sized holes
- Build ten mediocre modules — build seven excellent ones, rest to Future Scope

---

## 14. FACTS — verified, and the ones to never claim

### Verified, cite freely
- **SoI circular T-260/1147 (10 Feb 2025)** — NAKSHA: ORI 5 cm GSD,
  RMSE(x,y) ≤ 10 cm; DSM/DTM RMSE(z) ≤ 15 cm; CORS < 5 cm. **UTM on WGS84.**
- **NAKSHA** — 152 ULBs, 26 states + 3 UTs, **₹194 crore**, 4,142.63 sq km,
  scaling to all **4,912 ULBs**. Ministry = **Rural Development / DoLR**, not
  MoHUA. Survey of India = Technology Partner.
- **DILRMP** — only **49.10%** of villages have geo-referenced cadastral maps.
- **Sengupta et al., *Survey Review* (2016)** — modal **3–4 m** RMSE, 310 real
  West Bengal sheets.
- **₹56,725/sq km** — Tamil Nadu's official resurvey rate quoted to DoLR.
- **Bhu-Naksha manual** documents a **manually entered per-state magic scale
  factor** on shapefile import — UP ×4000, Himachal ×22 (*karam* in cm). India's
  incumbent national cadastral tool ships with hardcoded unit chaos.
- **Closest prior art** — Suwardhi et al., ISPRS 2025 (Indonesia): SAM + block
  ICP + hierarchical least squares, 6,198 parcels. **Single-source, no
  schema/CRS/tenure handling, no survey planning.**
- **Targeting method** — Krause, Singh & Guestrin, JMLR 2008.

### Never claim
- ❌ **"Indian Geodetic Datum 2023"** — does not exist. NGP 2022 only commits to
  *redefining* the framework. Indian Vertical Datum is real.
- ❌ NAKSHA uses Everest 1830 — **it uses UTM on WGS84.**
- ❌ **"NAKSHA pilots show deviations of up to 5%"** — unverifiable, and a
  percentage is dimensionally wrong for spatial deviation. Use Sengupta's 3–4 m
  against the 10 cm spec.
- ❌ Any man-hour or cost figure for manual GIS *integration* — no published
  figure exists.
- ❌ A ULPIN encoding spec — not published. Implement a faithful *shape*, say so.
- ⚠ ULB count conflicts three ways (152/157/150). **Use 152.**

---

## 15. BUILD ORDER

1. **Environment** — Node + numeric stack both importing. Nothing else matters first.
2. **Verify the ported engine** — `scripts/verify_all.py`, 25 assertions.
   **Stage 8 is the USP go/no-go.**
3. **Backend completion** — ingest (fix road clipping), block cadastre, schema
   matching, conflict engine, change detection, export.
4. **API** — FastAPI + background jobs + WebSocket progress. Note:
   `setup_wsl.sh` already references `api.main:app`, which does not exist yet.
5. **Frontend foundation** — design system *first*, then the shell. Retrofitting
   a design system never works.
6. **The map** — most of the visual budget.
7. **Screens**, then **security**, then **demo hardening**.

Build an end-to-end path on fake data early, then make each stage real. At every
moment there should be something that runs on screen.

---

## 16. THE DEMO — rehearse this exact order

1. Load Chandausi. **"These two real datasets disagree about 5,482 buildings.
   Nobody staged this."**
2. Legacy cadastral sheet drops in, visibly misregistered. Show the **residual
   vector field**.
3. Run harmonization. **The alignment animation.** RMSE 8.04 m → 0.31 m on screen.
4. Blocking recall 1.00; feature importance 88% geometric. **"Spatial reasoning,
   not a database join."**
5. Confidence heatmap. **"1,198 auto-finalised at a 99% precision floor, 42 for
   review — and here is the reliability curve proving that 99% is real."**
6. Red parcel → evidence panel → SHAP → officer approves → audit entry appears.
7. Change detection: 18 new constructions, 3 demolitions, **6 encroachments on
   government land**. Then the **area ledger**: *"we removed 17,560 m² of land
   two people both owned, recovered 5,369 m² of slivers, and lost nothing."*
8. **Close on the Survey Plan.** *"NAKSHA's own progress review says ground
   truthing is its biggest lagging component. So: send your surveyor to these 40
   points. Predicted city-wide RMSE 0.81 m → 0.29 m for ₹2.3 lakh, against
   ₹18.9 lakh for a full resurvey. And because we can generate ground truth, we
   already verified it — predicted 0.29, achieved 0.31."*

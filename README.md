# BhoomiSetu

**SIH 2026 · PS13 — Automated Integration and Intelligent Harmonization of
Multi-source Geospatial Data for Urban Land Record Management**

A working prototype. Every number in the interface was computed from the data by
the engine in this repo; nothing is mocked.

---

## Run it (fastest path — no build needed)

The app is pre-built as a static bundle in `dist/`.

```bash
cd dist
python -m http.server 8080
```

Open <http://127.0.0.1:8080>. That's it — no Node, no server, no network
beyond the satellite basemap tiles.

---

## Run the engine

The numeric stack does not run under Windows Smart App Control (enforced),
so the engine runs in WSL. `wsl_bootstrap.sh` sets it up **without sudo**:
it builds a venv with `get-pip.py` (because `ensurepip` needs apt) and
unpacks Node into `~/.local`.

```bash
wsl -d Ubuntu-24.04
bash /mnt/c/Users/nairb/SIH/novax_13/wsl_bootstrap.sh
cd ~/bhoomisetu
```

Then:

```bash
# 25 assertions across 8 stages, including the USP go/no-go
PYTHONPATH=backend .venv/bin/python scripts/verify_all.py

# run the whole pipeline and write the UI's artifacts (~52 s)
PYTHONPATH=backend .venv/bin/python scripts/build_demo.py
```

## Rebuild the frontend

```bash
bash .sync.sh                      # builds in WSL, stages to dist.new/
python publish.py                  # copies over dist/ without a folder swap
```

`publish.py` exists because the Windows static server keeps a handle on the
serve directory, so deleting and renaming it fails.

---

## What it does

Ten datasets describe the same ground and none agree. The pipeline decides that
this AI-detected polygon, this old cadastral parcel and this revenue record are
the same property, then emits one clean, topologically valid layer with an
honest confidence on every decision — so a human reviews only the uncertain
ones. **Triage, not full automation.**

### Measured results

| | |
|---|---|
| Pairwise F1 / ROC AUC | **0.9993 / 1.0000** |
| Expected Calibration Error | **0.00009** |
| Blocking recall | **1.0000** |
| Geometric share of the model | **95.6%** |
| Exact set match | **98.39%** |
| Spurious parcels rejected | **59 / 59** |
| Topology errors | **6,168 → 215** (96.5%) |
| Overlapping parcel pairs | **5,038 → 0** |
| Doubly-claimed land | **18,039 m² → 0 m²** |
| Parcel-sized holes refused | **69** (harness deleted 73) |
| Full pipeline | **52 s**, one core |

### The USP — optimal survey targeting

NAKSHA's own 2026 progress review names ground truthing as the programme's
biggest lagging component. So the system closes the loop: because every parcel
carries a calibrated uncertainty, it computes **where to send the next
surveyor** — Gaussian-process error field, greedy submodular selection with the
(1 − 1/e) bound (Krause, Singh & Guestrin, JMLR 2008).

It is validated rather than asserted. The harness knows ground truth, so the
recommended control is actually placed, georeferencing re-run, and the real
result measured:

```
before any new control            3.13 m
PREDICTED after 19 GCPs           0.61 m
ACHIEVED  after 19 GCPs           1.23 m
ACHIEVED with 19 RANDOM points    2.56 m     → 51.8% better than random
```

**Known limitation, stated in the UI:** the GP predicts 0.61 m but achieves
1.23 m — optimistic by roughly 2×. Directionally correct and decisively better
than random, but the variance model needs recalibration.

---

## Interface

Three-pane workbench, not a dashboard: left rail of tools, dominant map,
docked data panel. No modal ever covers the map.

**Keyboard**

```
1–9    toggle layer n        Space  run pipeline
[ ]    prev / next conflict  \      replay alignment
c      review queue          v      validation
t      survey plan           Esc    clear selection
```

**Dock tabs** — Review queue (257 conflicts, sorted by area × (1 − confidence)),
Survey plan, Validation (reliability curve, feature importance, area ledger),
Audit log (hash-chained), Pipeline (stage timings).

---

## Layout

```
backend/bhoomisetu/     3,636 LOC engine
  crs.py                UTM + Everest 1830, from Snyder (USGS PP 1395)
  synth/                city generator + 11-stage damage harness
  georef/               Hough vote + robust similarity; affine/poly/TPS
  matching/             blocking, 29 features, XGBoost + isotonic, assignment
  topology/             snap, overlap resolution, gap classification
  targeting/            GP uncertainty field + greedy submodular planner
frontend/src/           React + MapLibre GL, dark mission-control chrome
scripts/
  verify_all.py         8 stages, ~25 assertions
  build_demo.py         runs the pipeline, writes UI artifacts
  fetch_data.py         real Microsoft + OSM data, resumable
dist/                   pre-built app, serve directly
data/demo/              pipeline output the UI reads
data/raw/               real fetched layers (Chandausi, Pune)
```

---

## Honesty notes

- The cadastre is **synthetic**, derived from OSM block geometry, and is
  labelled `SYNTHETIC` throughout. No free real Indian urban cadastre exists for
  bulk download. The damage harness is what makes measurement possible at all.
- Real data *is* used and is on disk: Chandausi has **5,488 Microsoft
  AI-extracted footprints against 6 OSM buildings** (915:1) — the NAKSHA pilot
  town has essentially no municipal building layer, which is the problem
  statement rather than a data limitation. Pune has 8,527 vs 8,171 with a
  systematic 16% median-area disagreement.
- The ULPIN field is a faithful *shape*; the official encoding is not published.
- Not yet built: FastAPI layer, schema auto-matching, conflict-resolution
  engine, change detection, export. See `PLAN.md`.

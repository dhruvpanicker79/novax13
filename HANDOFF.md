# KSHETRA — device handoff

**SIH 2026 · PS13 — Automated Integration and Intelligent Harmonization of
Multi-source Geospatial Data for Urban Land Record Management**

Written 27 Sep 2026. Everything needed to resume on another machine.

---

## TL;DR

| | |
|---|---|
| Engine written | **3,636 LOC** |
| Engine verified **on the old machine** (23 Sep) | ✅ full pass |
| Engine verified **since** | ❌ **nothing has run since ~26 Sep** |
| Targeting module (the USP) | written, **never executed anywhere** |
| API | **does not exist** |
| Frontend | **does not exist** |
| Real data | ✅ 11 MB validated GeoJSON committed (+98 MB cache, gitignored) |
| Blocker | Windows **Smart App Control enforced** — kills the whole numeric stack |

**The single most important thing to do on the new device: find out whether
Smart App Control is enforced there.** If it isn't, everything just works and
the WSL detour is unnecessary.

---

## 1. Moving the project

Everything is committed to a local git repo (46 files, 2.7 MB).

### Option A — GitHub (recommended)

On **this** machine:
```bash
cd C:\Users\nairb\SIH\novax_13
gh repo create kshetra --private --source=. --push
# or, if you made the repo in the browser:
#   git remote add origin https://github.com/<you>/kshetra.git
#   git branch -M main && git push -u origin main
```

On the **new** machine:
```bash
git clone https://github.com/<you>/kshetra.git
cd kshetra
```

### Option B — copy the folder
Copy `C:\Users\nairb\SIH\novax_13` wholesale, but **delete `.venv/` first**
(Windows-specific, useless elsewhere, and large).

### What is NOT in the repo
`data/raw/_cache/` — 98 MB of raw Microsoft tiles. Deliberately excluded; they
re-download and **resume** automatically:
```bash
python scripts/fetch_data.py chandausi pune
```
The clipped GeoJSON derived from them **is** committed, so you can work without
ever re-downloading.

---

## 2. FIRST STEP on the new device

```powershell
Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' |
  Select-Object VerifiedAndReputablePolicyState
```

| Value | Meaning | What to do |
|---|---|---|
| **0** | SAC off | 🎉 Native Windows works. Skip WSL entirely. |
| **2** | Evaluation | Mostly works. Some packages blocked. Watch for auto-promotion to 1. |
| **1** | **Enforced** | Numeric stack is dead. Use WSL2. |

### If 0 or 2 — native setup
```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
set PYTHONPATH=backend
.venv\Scripts\python.exe scripts\verify_all.py
```

### If 1 — WSL2 setup
Admin PowerShell:
```bash
wsl --install -d Ubuntu-24.04
```
Reboot if prompted. Ubuntu asks for a UNIX username and password
(**the password is invisible while typing — that is normal**). Then:
```bash
cp -r /mnt/c/<path>/kshetra ~/kshetra && rm -rf ~/kshetra/.venv
cd ~/kshetra && bash setup_wsl.sh
```
Keep it on the Linux filesystem (`~`), not `/mnt/c` — cross-filesystem I/O in
WSL is ~10× slower and we parse 80 MB tiles.

`setup_wsl.sh` installs GDAL/GEOS/PROJ, Node 20, a Linux venv, all Python deps,
verifies every import, then runs the test suite. Verification failing at the end
does **not** abort it — that outcome is information, not a setup error.

---

## 3. The environment problem, in full

Windows Smart App Control is reputation-based code integrity. It was in
**evaluation** mode on 23 Sep (things ran) and **auto-promoted to enforced** by
26 Sep. SAC does that by itself once Microsoft's model considers the machine
clean. Once enforced, **turning it off is irreversible without reinstalling
Windows.**

Blocking is **per-binary and effectively arbitrary** — not "newer is safer":

| Package | Result (23 Sep) | Result (26 Sep) |
|---|---|---|
| numpy 2.4.6 | ✅ | ❌ |
| numpy 2.0.2 | ❌ | ❌ |
| scipy 1.17.1 | ✅ | ❌ |
| shapely 2.1.2 | ✅ | ❌ |
| pandas 2.3.3 | ✅ | ❌ |
| pandas 3.0.6 / 2.2.3 | ❌ | ❌ |
| xgboost 3.2.0 | ✅ | ❌ |
| **pyproj** (5 versions tried) | ❌ | ❌ |
| **scikit-learn** (4 versions) | ❌ | ❌ |
| **lightgbm** | ❌ | ❌ |
| requests | ✅ | ✅ |

**WSL is better than disabling SAC**, because SAC never allowed `pyproj`,
`rasterio`, `geopandas` or `scikit-learn` even in evaluation mode. WSL restores
all of them, installs Node, and leaves the Windows side protected.

**Node.js was never installed on the old machine.** The frontend cannot start
until it is. `setup_wsl.sh` handles it.

### This shaped the architecture, and it's a pitch asset
Because `pyproj`/`sklearn`/`lightgbm` were unavailable, these are hand-written:

- `crs.py` — UTM + Everest 1830↔WGS84 Helmert, from Snyder (USGS PP 1395)
- `evaluation/metrics.py` — ROC AUC, average precision, Brier, ECE, reliability
- `attributes/text.py` — Jaro-Winkler, token-set, Indian transliteration folding
- isotonic calibration → `scipy.optimize.isotonic_regression`
- assignment → `scipy.optimize.linear_sum_assignment`

*"We implemented the CRS engine and probability calibration from first
principles"* beats *"we imported pyproj."* And `verify_all.py` now
cross-validates our UTM against `pyproj` (available in WSL) — if they agree to
sub-millimetre, it stops being a workaround and becomes a **verified**
implementation.

---

## 4. What the project is

Ten datasets describe the same ground and none agree. The job: decide that this
AI-detected polygon, this old cadastral parcel and this revenue record are the
same property, then emit one clean, topologically valid layer with an honest
confidence on every decision so humans review only the uncertain ones.

**Spatial entity resolution for land. Triage, not full automation.**

### The USP — optimal survey targeting

The PS enumerates ten sources and seven components. It is a spec; everyone
builds to it. **You cannot differentiate on the spec.**

NAKSHA's own progress review (*Frontiers in Sustainable Cities* 2026,
first-authored by **Kunal Satyarthi, Joint Secretary DoLR**) reports **ground
truthing is "the biggest lagging component," 55 of ~150 ULBs below 60%.** The
real bottleneck is that ground truth is scarce and expensive.

> **Given a fixed survey budget, which 40 parcels do you send a surveyor to, to
> maximally reduce uncertainty across the whole city?**

Mechanism: model the residual displacement field as a **Gaussian process**;
a GNSS point becomes a thin-plate-spline control point reducing uncertainty
across a neighbourhood; selecting the best K is **submodular maximisation**,
greedy gives **(1 − 1/e)** (Krause, Singh & Guestrin, JMLR 2008).

Not claimable without building it. Verifiable in 60 seconds. Three layers deep
to copy.

**Two earlier USP candidates were rejected as too easy to claim:**
"adjudication-grade harmonization" (an adjective) and "n-source fusion"
(everyone's diagram has ten boxes). Don't revive them as headlines.

---

## 5. File inventory

```
backend/kshetra/
  crs.py                231  UTM + Everest 1830, from Snyder      verified 23 Sep
  geometry.py           170  shape descriptors                    verified 23 Sep
  layers.py             154  Feature/Layer/Provenance + GeoJSON    verified 23 Sep
  synth/generator.py    306  synthetic Indian urban cadastre       verified 23 Sep
  synth/corruption.py   464  11-stage damage harness + key         verified 23 Sep
  georef/transform.py   254  Similarity/Affine/Poly/TPS            verified 23 Sep
  georef/coarse.py      186  Hough vote + robust similarity        verified 23 Sep
  matching/features.py  230  blocking + 29 pairwise features       verified 23 Sep
  matching/model.py     200  XGBoost + isotonic + SHAP             verified 23 Sep
  matching/assign.py    250  split/merge detection + Hungarian     verified 23 Sep
  topology/cleaner.py   384  snap/overlap/gap repair               verified 23 Sep
  attributes/text.py    191  Jaro-Winkler, transliteration folding verified 23 Sep
  evaluation/metrics.py 148  ROC/AP/Brier/ECE/reliability          verified 23 Sep
  targeting/uncertainty.py 188  GP residual field  *** NEVER RUN ***
  targeting/planner.py     275  greedy submodular  *** NEVER RUN ***
  change/__init__.py      0  EMPTY STUB — no change detection
  conflict/__init__.py    0  EMPTY STUB — no conflict resolution

scripts/
  verify_all.py         8 stages, ~25 assertions   *** NEVER RUN ***
  fetch_data.py         MS + OSM fetch, resumable  ✅ works
  probe_aoi.py          OSM density probe          ✅ works
  probe_msbuildings.py  MS coverage check          ✅ works
  inspect_data.py       stdlib-only validator      ✅ works

docs/
  RESEARCH_DOSSIER.md   1,071 lines, every claim tagged verified/unverified
  DECISIONS_session1.md / STATUS_session1.md   prior-session records

BUILD_PROMPT.md   full build brief (datasets, USP, pipeline, UI, map, demo)
PLAN.md           8-phase plan with gates, cut list, risks
setup_wsl.sh      one-command environment bring-up
requirements.txt  two profiles, documented
```

### Not built
API (no `api/` at all — **`setup_wsl.sh` references `api.main:app`, which does
not exist; that's a known bug, fixed by Phase 3.1**), schema auto-matching,
conflict resolution, change detection/encroachment, real-data ingest,
block-derived cadastre, export (GeoJSON/Shapefile/OGC/PDF), ULPIN, frontend.

**Backend as a deliverable: ~40%. Verified on current hardware: 0%.**

---

## 6. Measured numbers (old machine, 23 Sep — re-verify)

| Metric | Value |
|---|---|
| Pairwise F1 / ROC AUC | 0.961 / 0.986 |
| Expected Calibration Error | 0.0034 |
| Blocking recall | 1.000 |
| Exact set match | 93.33% |
| Spurious parcels rejected | 57/57 |
| Subdivision detection precision | 1.000 (recall 0.227) |
| Topology errors | 6,199 → 238 (96.2%) |
| Overlapping pairs | 5,038 → 1 |
| Invalid geometries | 31 → 0 |
| Training time | 1.1 s |

### Area conservation ledger
```
summed parcel area   422,219 m² → 410,028 m²   (−2.89%)
union footprint      404,586 m² → 409,955 m²   (+1.33%)
doubly-claimed land   17,632 m² →     72.7 m²
removed double-counting −17,560 m² · recovered slivers +5,369 m² · NO LAND LOST
```
The summed area falls *because* two people were recorded owning the same ground;
actual footprint goes **up**. This answers the revenue officer's first question.

### Principled restraint
Cleaner preserved **69 of 73** deliberately deleted parcels — refused to fill
parcel-sized holes and flagged them for survey instead. Filling them would be
silent data fabrication.

---

## 7. Findings that must not be lost

### 7.1 You cannot match parcels before georeferencing them
Urban plots are ~11 m across; legacy misregistration is 5–15 m — so an unaligned
parcel **overlaps its neighbour more than its own counterpart**. Blocking recall
was **0.58**: 42% of true matches never reached the model. Coarse alignment
first → **1.00**. **Never reorder the pipeline.**

### 7.2 The leakage trap
The first trained model scored **F1 0.9955 and was worthless** — feature
importance showed it had learned to join on khasra number and owner name (96%),
with `iou` at 0.24%. If identifiers matched reliably, this PS wouldn't exist.

Fixed by making the damage honest: **45% of blocks get renumbered** (resurveys
do this) and **12% of owners genuinely change** (property sold). Model is now
**88% geometric**. `verify_all.py` asserts `geometry_share >= 0.70` so this can
never silently regress.

### 7.3 Split detection: precision over F1
Best F1 was 0.398 (containment 0.40). **Chose containment 0.50** → precision
**1.000**, recall 0.227, best overall exact match. Falsely claiming a
subdivision is a legal problem; missing one routes to human review, which is
where uncertain cases belong. Say this out loud — it shows domain understanding.

### 7.4 Mutation records were deliberately dropped
Generating a legal mutation record invites three questions you can't answer:
which state's format, are you bypassing the statutory notice/hearing, and is it
revenue or municipal (in urban Karnataka "khata" is a property-tax account, not
a revenue holding). **Emit a "change dossier" flagged for the revenue officer
instead.** Answer to "who signs this?" → "the officer does; we built the file."

---

## 8. Real data on disk

| AOI | MS AI footprints | OSM buildings | OSM roads |
|---|---|---|---|
| **Chandausi** (78.7749 E, 28.4515 N) | **5,488** | **6** | 1,713 |
| **Pune** (73.8553 E, 18.5308 N) | **8,527** | **8,171** | 3,133 |

**Chandausi: 915 : 1.** The NAKSHA pilot town has a mapped road network and
essentially no municipal building data, while AI extraction yields thousands of
footprints. That gap **is** the problem statement — not a data limitation.

**Pune: 8,527 vs 8,171, but median area 179.6 m² vs 154.2 m²** — a systematic
**16% disagreement** over identical ground. Real, uncurated, unstaged conflict.

Two AOIs, two jobs: Chandausi = thematic NAKSHA story; Pune = technical conflict.

### Data gotchas
- **MS `confidence` is tile-dependent**: present for **100%** of Chandausi
  (min 0.556, median 0.965), **0%** of Pune (all −1.0). Provenance must fall back
  to a source-level prior.
- `height` is −1.0 in both tiles → DSM must come from Copernicus GLO-30.
- **BUG, unfixed:** Overpass `out geom` returns *whole* ways, so
  `chandausi_osm_roads.geojson` spans 0.42° instead of the 0.036° AOI (322.6 km
  of road trailing toward Moradabad). Harmless for display, **fatal for
  block-derived cadastre.** Clip to AOI first. (PLAN.md Phase 2.1)
- Overpass main instance throws 504/429 constantly; `fetch_data.py` rotates
  four mirrors. `overpass.kumi.systems` is the most reliable.
- Real MS median footprint **143.0 m²** vs our synthetic generator's **133.8 m²**
  — independent agreement within 7%, which defends the synthetic plot sizes.

---

## 9. Next steps

**Phase 0** (you): resolve the environment — check SAC, then native or WSL.

**Phase 1** (gate): run `verify_all.py`. Stage 8 is the go/no-go:
```
before any new control          X.XXX
PREDICTED after 40 points       X.XXX
ACHIEVED after 40 points        X.XXX
ACHIEVED with 40 RANDOM points  X.XXX
```
**If optimised placement does not beat random, the USP is theatre.** Plan B:
fall back to the measurement apparatus (calibration + area ledger + restraint)
as primary — weaker and more copyable, but honest.

Then Phases 2–8 per `PLAN.md`: backend completion → API → frontend → map →
screens → security → demo. **18–24 sessions full, 12–15 compressed.**

---

## 10. Research: use these, avoid those

### Verified
- **Survey of India circular T-260/1147 (10 Feb 2025)** — NAKSHA spec: ORI 5 cm
  GSD, RMSE(x,y) ≤ 10 cm; DSM/DTM RMSE(z) ≤ 15 cm; CORS < 5 cm.
  **CRS: UTM on WGS84.**
- **NAKSHA**: 152 ULBs, 26 states + 3 UTs, **₹194 crore**, 4,142.63 sq km,
  scaling to all 4,912 ULBs. Ministry = **Rural Development / DoLR**, not MoHUA.
  Survey of India = Technology Partner.
- **DILRMP: only 49.10%** of villages have geo-referenced cadastral maps.
- **Sengupta et al., *Survey Review* (2016)**: modal **3–4 m** RMSE across 310
  real West Bengal sheets → **30–40× mismatch** vs NAKSHA's 10 cm.
- **₹56,725/sq km** — Tamil Nadu's official resurvey rate to DoLR.
- **Bhu-Naksha manual** documents a **manually entered per-state magic scale
  factor** on shapefile import — UP ×4000, Himachal ×22 (*karam* in cm). India's
  incumbent national cadastral tool ships with hardcoded unit chaos.
- **Closest prior art**: Suwardhi et al., ISPRS 2025 (Indonesia) — SAM + block
  ICP + hierarchical least squares, 6,198 parcels. Single-source, no
  schema/CRS/tenure handling, **no survey planning**.

### Do NOT say
- ❌ **"Indian Geodetic Datum 2023"** — it does not exist; a summariser invented
  it. NGP 2022 only commits to *redefining* the framework. **Indian Vertical
  Datum** is real.
- ❌ NAKSHA uses Everest 1830 — **it uses UTM on WGS84**. (We implement Everest
  only for legacy sheets predating the switch.)
- ❌ Any man-hour or cost figure for manual GIS *integration* — **no published
  figure exists.**
- ❌ A ULPIN encoding spec — **not published.** Implement a faithful *shape* and
  say so.
- ⚠ ULB count conflicts three ways (152 / 157 / 150). **Use 152.**
- ⚠ NUIS is two different things: National Urban Information *System* (MoUD
  2006) vs National Urban Innovation *Stack* (MoHUA). NAKSHA MAP-1 publishes at
  **1:500**, finer than any NUIS tier — a real standards gap.

### Worth chasing
The **NAKSHA SDMS schema SOP** is a 105-page scan with no text layer (105 pages
yielded 105 characters). OCR'ing it is the highest-value remaining unknown —
conforming output to the actual government schema would be a real differentiator.

---

## 11. Resuming with Claude on the new device

Open Claude Code in the project root and say:

> Read HANDOFF.md, PLAN.md and BUILD_PROMPT.md. We're on a new machine.
> Check Smart App Control state, get the environment working, then run
> `scripts/verify_all.py` and report stage 8.

That is enough context to pick up exactly here.

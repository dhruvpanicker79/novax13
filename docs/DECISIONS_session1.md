# Decisions made while you were asleep

Every choice I made without being able to ask. Each one says *why*, and how to
overrule it. Nothing here is load-bearing in a way you cannot reverse.

---

## 1. Environment: native Windows Python, no WSL / Docker / conda

**Why:** none of them are installed. WSL needs `wsl --install` plus a reboot;
Docker needs an installer; both need you. I worked with what was on the machine.

**To overrule:** installing WSL2 later is still worth it, and everything here
runs unchanged inside it.

---

## 2. Smart App Control: worked around, not disabled

Your `novax167` notes said SAC blocked `rasterio` and `polars`. It is worse than
that. I swept versions and found the block is **per-binary and effectively
arbitrary** — not "newer is safer" or "older is safer":

| Package | Result |
|---|---|
| numpy **2.4.6** | works |
| numpy 2.0.2 | **blocked** |
| scipy 1.17.1 | works |
| shapely 2.1.2 | works |
| pandas **2.3.3** | works |
| pandas 3.0.6, 2.2.3 | **blocked** |
| xgboost 3.2.0 | works |
| **pyproj** 3.7.2 / 3.7.1 / 3.7.0 / 3.6.1 / 3.6.0 | **all blocked** |
| **scikit-learn** 1.9.1 / 1.7.2 / 1.6.1 / 1.5.2 | **all blocked** |
| **lightgbm** | **blocked** |

**Decision:** the engine depends only on `numpy`, `scipy`, `shapely`, `pandas`,
`xgboost`. Everything blocked was replaced with hand-written code:

- `pyproj` -> `kshetra/crs.py`, UTM + Everest 1830 implemented from Snyder's
  USGS manual. Verified: sub-millimetre round-trip, exact false-easting on the
  central meridian.
- `scikit-learn` metrics -> `kshetra/evaluation/metrics.py` (ROC AUC,
  average precision, Brier, ECE, reliability curve).
- `sklearn.isotonic` -> `scipy.optimize.isotonic_regression`.
- `lightgbm` -> `xgboost` native Booster API (no sklearn wrapper).
- `rapidfuzz` -> `kshetra/attributes/text.py` (Jaro-Winkler, token-set).

**This turned out to be an advantage, not a workaround.** "We implemented the
CRS engine and the calibration from first principles" is a much better answer to
a judge than "we imported pyproj." Keep the framing.

**Do NOT** run `pip install -U` on this venv. Versions in `requirements.txt` are
pinned because they are the ones that *run*, not because they are the latest.

**To overrule:** turning SAC off is irreversible without reinstalling Windows.
Your call, not mine — I did not touch it.

---

## 3. No UI (you confirmed this mid-session)

Node.js is not installed, so React was impossible anyway. All effort went into
the model. When we do build it: plain HTML + MapLibre GL from CDN served by
FastAPI, no build step.

---

## 4. Demo data is synthetic, and deliberately so

No dataset ships with the PS. Rather than depend on downloads at 3am, I wrote a
generator (`kshetra/synth/`) that builds a realistic Indian urban cadastre
offline from a seed: irregular road grid, blocks recursively subdivided into
plots, khasra numbering as `parent/child`, buildings with setbacks, government
land, and recorded areas that drift from surveyed areas.

**This is the strategic centrepiece, not a shortcut.** Because we generate the
ground truth, we can damage a copy in precisely known ways and measure exactly
how much the pipeline recovers. That is where every number in the results table
comes from, and almost no SIH team produces real quantitative evaluation.

Anchored at **Chandausi, Sambhal district, UP** — the actual NAKSHA pilot launch
site (confirmed in the research dossier).

**To overrule:** real data layers on top later; the pipeline is CRS-correct and
takes GeoJSON.

---

## 5. Damage model tuned to *published measured* values

Corruption parameters are not invented. Sengupta et al., *Survey Review* (2016)
measured RMSE across 310 real West Bengal cadastral sheets and found a modal
**3-4 m** error. NAKSHA's ORI spec is **10 cm** (Survey of India circular
T-260/1147). That 30-40x mismatch is the real problem, and our synthetic damage
sits in that band, so the demo is citable rather than hand-waved.

---

## 6. Everest 1830 is implemented but is NOT the NAKSHA datum

I built the Everest 1830 <-> WGS84 Helmert transform before the research came
back. The research then settled it: **NAKSHA uses UTM projection on WGS84**, with
vertical from SoI CORS / Indian Vertical Datum.

Everest still earns its place — legacy sheets predating the switch are on it, and
handling that is exactly the "legacy integration" the PS asks for. But **do not
claim NAKSHA uses Everest.** It does not.

---

## 7. Split detection tuned for precision, not F1

The threshold sweep (`scripts/tune_assignment.py`) gave a clean tradeoff. Best
F1 was 0.398 at containment=0.40. **I chose containment=0.50 instead**:
precision **1.000**, recall 0.227, and the best overall exact-match (93.33%).

**Why:** asymmetric costs. Falsely claiming a plot was subdivided is a legal
problem in a land record. Missing one just sends it to the human review queue,
which is where the system is designed to send uncertain cases anyway. Say this
out loud to judges — it shows you understand the domain, not just the metric.

**To overrule:** one-line change in `kshetra/matching/assign.py` defaults.

---

## 8. Things I deliberately did NOT do

- Did not touch `novax167` (your old ISRO project).
- Did not install anything system-wide; everything is in `.venv/`.
- Did not disable any security setting.
- Did not commit to git yet — first commit is yours to review.
- Did not fabricate any statistic. Where the research agent could not verify a
  number, the dossier says so explicitly.

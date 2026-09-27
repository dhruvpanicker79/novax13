# BhoomiSetu — build plan, start to finish

Written 26 Sep 2026. Tracks against the spec in `BUILD_PROMPT.md`.

**Legend** — `[YOU]` needs you · `[ME]` I do it · `[GATE]` stop and decide before continuing

Effort is in **working sessions**. One session ≈ one sustained block of my work
plus your review. I stop at the end of each turn, so nothing progresses while
you're away — sessions are not wall-clock hours.

---

## Where we actually are

| | |
|---|---|
| Engine written | 3,636 LOC |
| Engine **verified on this machine** | **0%** |
| API | does not exist |
| Frontend | does not exist |
| Real data | 108 MB on disk, validated ✅ |
| Blocker | Smart App Control enforced — nothing numeric runs |

---

# PHASE 0 — Unblock  `[YOU]`  ~20 min

Everything is gated on this. Nothing below can start.

```bash
wsl --install          # admin PowerShell, then reboot
```

Then in Ubuntu:
```bash
cd ~ && cp -r /mnt/c/Users/nairb/SIH/novax_13 bhoomisetu && cd bhoomisetu
bash setup_wsl.sh
```

Keep the project on the Linux filesystem (`~/bhoomisetu`), not `/mnt/c` — WSL
cross-filesystem I/O is ~10× slower and we parse 80 MB tiles.

**Why WSL over disabling SAC:** it restores `pyproj`, `rasterio`, `geopandas`
and `scikit-learn`, which SAC blocks *even when it was in evaluation mode*. It
installs Node. And it leaves SAC protecting Windows, so the decision is
reversible. Turning SAC off is permanent and gives you less.

---

# PHASE 1 — Verify the foundation  `[ME]` 1–2 sessions  `[GATE]`

```bash
PYTHONPATH=backend python scripts/verify_all.py
```

25 assertions over 8 stages. Fix whatever breaks.

### The gate that matters

Stage 8 places the 40 recommended survey points, re-runs georeferencing, and
compares:

```
predicted RMSE   vs   achieved RMSE   vs   achieved with 40 RANDOM points
```

**If optimised placement does not beat random, the USP is theatre.** Better to
learn that on day one.

- **Plan A holds** → targeting is the USP, proceed as written.
- **Plan B** → fall back to the measurement apparatus as primary (calibration +
  area-conservation ledger + principled restraint). Weaker and more copyable,
  but honest and still ahead of a generic build. We'd rewrite `BUILD_PROMPT.md §1`.

Also validates the hand-rolled CRS against `pyproj`. If they agree to
sub-millimetre, the from-scratch Snyder implementation becomes *verified*
rather than merely *necessary* — a better line for the pitch.

**Deliverable:** green verification run, real numbers for the slides.

---

# PHASE 2 — Finish the backend  `[ME]` 4–6 sessions

The missing ~60%. Ordered by dependency.

### 2.1 Real-data ingest — 1 session
- GeoJSON → `Layer` with correct `Provenance` per source
- **Fix the road-clipping bug**: Overpass `out geom` returns whole ways, so
  Chandausi roads currently sprawl to a 0.42° bbox instead of 0.036°. Clip to
  AOI before block derivation or the cadastre is garbage.
- Reproject WGS84 → UTM 43N/44N on load
- Provenance must tolerate a **missing** MS `confidence` field — present for all
  5,488 Chandausi footprints, absent for all 8,527 in Pune. Fall back to a
  source-level prior.

### 2.2 Block-derived cadastre — 1 session
- Polygonise the clipped OSM road network into city blocks
- Recursive subdivision into plots (port from `synth/generator.py`)
- Khasra numbering, owners, tenure, recorded-area drift
- Label `SYNTHETIC` on every feature — enforced at the model layer, not the UI

### 2.3 Schema auto-matching — 1 session → `attributes/schema_match.py`
Currently the single hand-supplied link in a supposedly automatic pipeline, and
judges **will** ask.
- Column-name similarity against an Indian revenue lexicon (khasra / khatauni /
  khatedar / patta / survey no / RoR)
- Value profiling: dtype, regex, range, cardinality
- Unit inference — **bigha/biswa vs m²** detection from magnitude
- Emits `FieldMap` + per-field confidence + manual override

### 2.4 Conflict resolution — 1 session → `conflict/`
- Conflict graph across n sources (not pairwise)
- Inverse-variance provenance weighting
- **Per-attribute authority**: GNSS wins geometry, revenue wins ownership
- Transitive inconsistency detection (A≈B, B≈C, A≠C)
- Every resolution records the rule that fired

### 2.5 Change detection + encroachment — 1 session → `change/`
- Epoch diff: new / demolished / extended
- DSM delta for vertical change
- **Encroachment**: harmonized parcels ∩ `govt_land`
- Change dossiers (**not** legal mutation records — see `BUILD_PROMPT §13`)

### 2.6 Export + ULPIN — 1 session
- GeoJSON, Shapefile, GeoPackage
- **OGC API – Features** endpoints
- **PDF audit report** — every change with reason, confidence, source
- ULPIN assignment (faithful *shape*; the real encoding is unpublished — say so)

---

# PHASE 3 — API  `[ME]` 2 sessions

### 3.1 FastAPI skeleton
`setup_wsl.sh` already references `api.main:app` — **that module doesn't exist
yet; my script is currently wrong.** Fix by building it.

- Pydantic v2 schemas mirroring `layers.py`
- `/aoi`, `/ingest`, `/profile`, `/harmonize`, `/conflicts`, `/review`,
  `/survey-plan`, `/validate`, `/export`

### 3.2 Job orchestration
The pipeline takes minutes — it cannot be a blocking request.
- Background jobs + `/jobs/{id}` polling
- **WebSocket** for live stage progress (drives the pipeline tracker UI)
- Result caching keyed on (AOI, config hash) so demos are instant
- Cancellation

**Deliverable:** frontend can start against a real contract.

---

# PHASE 4 — Frontend foundation  `[ME]` 2 sessions

- Vite + React 18 + TS, Zustand, TanStack Query
- **Design system first** — tokens from `BUILD_PROMPT §7`: IBM Plex Sans/Mono,
  13px, hairline borders, no shadows, one accent
- Three-pane resizable IDE shell, status bar, keyboard shortcuts
- Layer tree, virtualised data grid

Getting the design system right *before* any screen is what stops it looking
AI-generated. Retrofitting never works.

---

# PHASE 5 — The map  `[ME]` 3–4 sessions

This is the product. Most of the visual budget goes here.

- **5.1** Custom MapLibre style JSON + PMTiles basemap (monochrome survey
  drafting aesthetic — *not* a stock CARTO style)
- **5.2** deck.gl layers, GPU picking, 60 fps at 10k parcels
- **5.3** **The alignment animation** — the signature moment, ~1.6 s transform
  interpolation with residual vectors fading
- **5.4** **Survey plan layer** — 40 points sized by marginal gain over a
  posterior-variance heatmap. Should be the best-looking layer in the app.
- **5.5** Residual vector field, confidence choropleth + histogram brush,
  swipe compare, 3D extrusion, terrain hillshade
- **5.6** Cartographic labels, bilingual Devanagari + Latin

---

# PHASE 6 — Screens  `[ME]` 3–4 sessions

1. Project / AOI picker
2. Ingest & profile (schema mapping UI with overrides)
3. Harmonize (live stage tracker)
4. **Review queue** — evidence panel with SHAP contributions per decision
5. **Survey Plan** — budget slider, ranked list, marginal-gain curve, predicted
   vs achieved, cost comparison
6. Validate — harness live: metrics table, reliability curve, area ledger
7. Export

---

# PHASE 7 — Security & data protection  `[ME]` 1–2 sessions

You asked for this specifically. Land records are personal data, so it is not
decorative — and done right it *reinforces* the adjudication story.

### 7.1 Tamper-evident audit log — do this one regardless
Hash-chain every audit entry (`hash(prev + entry)`). Any retro-edit breaks the
chain and is detectable. ~50 lines, and it converts "we have an audit trail"
into "our audit trail is provably unaltered." That is the difference between a
log and evidence.

### 7.2 RBAC + field-level redaction
Roles: `public` · `surveyor` · `clerk` · `tehsildar`.
**Owner names are PII.** The public role sees geometry, khasra and land use —
never owner, never tenure. Redaction enforced server-side at serialisation, not
hidden in the UI.

### 7.3 DPDP Act 2023 posture
India's Digital Personal Data Protection Act is the governing law for owner data.
- Purpose limitation, data minimisation in every export
- Our demo owners are **synthetic** — state that plainly; it is a genuine
  compliance answer, not a dodge
- Retention policy on job artifacts

### 7.4 Input hardening
Geospatial input is hostile by nature: GeoJSON bombs (millions of vertices),
zip bombs in shapefiles, coordinate values that overflow, self-intersecting
rings that hang predicates, `..` path traversal in uploads. Size caps, vertex
caps, timeouts, schema validation.

### 7.5 Basics
No secrets in repo (OpenTopography key → env), CORS allowlist, rate limiting,
signed export manifests so a PDF audit report can be verified as ours.

---

# PHASE 8 — Demo & pitch  `[ME]` + `[YOU]` 1–2 sessions

- Pre-seeded demo state so nothing loads live on stage
- Kill every crash path; offline fallbacks for all tiles
- Rehearse the 8-beat script in `BUILD_PROMPT §12`
- PPT built on **real measured numbers**, sourced per `BUILD_PROMPT §14`
- **`[YOU]` rehearse it five times.** The alignment animation and the survey-plan
  close are the two moments that decide the room.

---

## Totals

| Path | Sessions | What you get |
|---|---|---|
| **Full** | 18–24 | Everything above |
| **Compressed** | 12–15 | Cuts below |

### Cut list, in the order I'd cut
1. Shapefile + GeoPackage export (GeoJSON only)
2. 3D extrusion + terrain hillshade
3. Bilingual labels
4. OGC API – Features (mention as Future Scope)
5. PMTiles → plain GeoJSON at demo scale
6. Pune AOI (Chandausi only) — **loses the real MS-vs-OSM conflict story, so
   this one costs the most; cut it last**

### Never cut
Phase 1 verification · the survey targeting module · calibration + reliability
curve · the area ledger · the alignment animation · the hash-chained audit log.

Those are the USP and its proof. Everything else is replaceable.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Targeting doesn't beat random | kills the USP | Phase 1 gate; Plan B ready |
| WSL not installed | **blocks everything** | Phase 0 |
| Judge rejects targeting as scope creep | weakens pitch | bridge sentence in `BUILD_PROMPT §1` |
| Map perf collapses at 10k parcels | demo stutters | deck.gl + PMTiles from the start |
| Overpass rate limits mid-demo | hard failure | all data pre-fetched and cached ✅ |
| Time runs out | half-built everything | cut list above; six excellent modules beat ten mediocre |

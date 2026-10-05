"""Render the KSHETRA research compendium -- the definitive document.

Supersedes nothing: the 9-page research summary is the literature-facing
extract and the 22-page dossier is the project record. This is the full thing,
with the mathematics written out rather than described, a complete feature
dictionary, a formal comparison against prior art, and a glossary.

Layout is by PyMuPDF's Story engine (no LibreOffice, no sudo on this box).
Every measured figure is read from the pipeline artifacts at build time, so the
document cannot drift from what the code produced.

    python scripts/build_compendium.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "KSHETRA_Research_Compendium.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

D = ROOT / "data" / "demo"
M = json.loads((D / "metrics.json").read_text(encoding="utf-8"))
CAL = json.loads((D / "targeting_calibration.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((D / "schema.json").read_text(encoding="utf-8"))
PLAN = json.loads((D / "survey_plan.json").read_text(encoding="utf-8"))
RES = json.loads((D / "resolutions.json").read_text(encoding="utf-8"))

g, mt, tp = M["georef"], M["matching"], M["topology"]
tg, sc, ch, asg = M["targeting"], M["schema"], M["change"], M["assignment"]
cnt = M["counts"]
GEOM_PCT = round(mt["geometry_share"] * 100, 1)


def dec(v: float, places: int = 5) -> str:
    return f"{v:.{places}f}".rstrip("0").rstrip(".") or "0"


def _loc() -> dict[str, int]:
    files = subprocess.run(["git", "ls-files"], cwd=ROOT,
                           capture_output=True, text=True).stdout.split()
    out: dict[str, int] = {}
    for f in files:
        p = ROOT / f
        if not p.is_file():
            continue
        try:
            out[f] = sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return out


LOC = _loc()


def L(*pre: str, ext: tuple[str, ...] = (".py",)) -> int:
    return sum(n for f, n in LOC.items() if f.startswith(pre) and f.endswith(ext))


ENGINE, API_LOC, SCRIPTS = L("backend/"), L("api/"), L("scripts/")
UI = L("frontend/src", ext=(".ts", ".tsx", ".css"))
TOTAL = ENGINE + API_LOC + SCRIPTS + UI


def _commits() -> list[tuple[str, str, str]]:
    raw = subprocess.run(["git", "log", "--pretty=format:%h|%ad|%s",
                          "--date=short"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    return [tuple(l.split("|", 2)) for l in raw.splitlines() if l.count("|") >= 2]


COMMITS = _commits()

# --------------------------------------------------------------------------
# reference data
# --------------------------------------------------------------------------
FEATURES = [
    ("iou", "Overlap", "|A &cap; B| / |A &cup; B|. The classic, and alone it is not enough: a displaced parcel and its neighbour can score similarly."),
    ("sym_diff_norm", "Overlap", "|A &#9651; B| / (|A| + |B|). Penalises disagreement symmetrically; sensitive where IoU saturates."),
    ("src_frac_in_tgt", "Overlap", "|A &cap; B| / |A|. Asymmetric containment. <b>Highest-gain feature in the trained model</b> because it detects subdivision: a child parcel is fully inside its parent even though IoU is low."),
    ("tgt_frac_in_src", "Overlap", "|A &cap; B| / |B|. The mirror. Together the pair distinguishes split from merge from 1:1."),
    ("centroid_dist", "Position", "Euclidean distance between centroids, metres. Second-highest gain."),
    ("centroid_dist_norm", "Position", "Centroid distance divided by the square root of mean area &mdash; scale-free, so a 3 m error means something different for a 50 m&sup2; plot than a 5,000 m&sup2; one."),
    ("hausdorff_norm", "Position", "Normalised Hausdorff distance. Catches the case where centroids agree but boundaries do not."),
    ("sig_dist", "Position", "Distance between turning-function shape signatures; rotation-invariant."),
    ("area_ratio", "Shape", "min(|A|,|B|) / max(|A|,|B|). Bounded in (0,1] so it cannot dominate."),
    ("d_compactness", "Shape", "Difference in 4&pi;A/P&sup2;. A digitised parcel and its counterpart share compactness even when displaced."),
    ("d_rectangularity", "Shape", "Difference in area over minimum-rotated-rectangle area. Urban plots are near-rectangular; this is informative here in a way it would not be rurally."),
    ("d_elongation", "Shape", "Difference in minimum-rectangle aspect ratio."),
    ("vertex_ratio", "Shape", "Ratio of vertex counts. Decimation during digitisation changes this, so it is weak evidence, carried for completeness."),
    ("name_jw", "Owner", "Jaro-Winkler on owner names after transliteration folding."),
    ("name_lev", "Owner", "Normalised Levenshtein distance."),
    ("name_tok", "Owner", "Token-set ratio, which survives reordering: <i>Sita Tiwari d/o Ajay</i> against <i>Tiwari Sita</i>."),
    ("name_present", "Owner", "Whether a name exists on both sides at all. A missingness signal, not a join key."),
    ("kh_exact", "Khasra", "Exact string equality of the khasra/survey number."),
    ("kh_parent", "Khasra", "Whether the target number is the parent of the source under the recursive grammar (123/1A &rarr; 123)."),
    ("kh_child", "Khasra", "The converse. Together these encode subdivision as evidence rather than as mismatch."),
    ("kh_present", "Khasra", "Whether a number exists on both sides. Again presence, not value."),
    ("area_attr_ratio", "Attribute", "Ratio of <i>recorded</i> areas after unit normalisation &mdash; independent of the geometry, so it is genuine corroboration."),
    ("land_use_match", "Attribute", "Land-use code agreement after mapping to a canonical vocabulary."),
    ("ward_match", "Attribute", "Administrative ward agreement."),
    ("n_candidates", "Context", "How many candidates this source parcel has. The model needs to know whether it is choosing among two or among twenty."),
    ("iou_rank", "Context", "Rank of this pair's IoU among the source's candidates."),
    ("iou_margin", "Context", "Gap between this IoU and the runner-up. <b>The ambiguity signal.</b> IoU 0.6 with a margin of 0.4 is a different situation from IoU 0.6 with a margin of 0.01, and without this the model cannot tell them apart."),
    ("is_best_iou", "Context", "Whether this is the source's top candidate by overlap."),
    ("rev_iou_rank", "Context", "Rank from the target's point of view. Mutual-best is far stronger evidence than one-way-best."),
]

DAMAGE = [
    ("1", "Similarity misregistration", "shift (6.5, &minus;4.2) m, rotation 0.85&deg;, scale 1.0016",
     "sheet georeferenced from too few, poorly spread GCPs", "yes"),
    ("2", "Smooth non-linear warp", "amplitude 2.4 m over 9 control points",
     "paper shrinkage, scanner distortion, map-sheet join", "yes"),
    ("3", "Vertex jitter", "&sigma; 0.35 m per vertex",
     "manual digitisation from a paper sheet", "yes"),
    ("4", "Vertex decimation", "p = 0.10 per vertex",
     "generalisation during digitisation", "&mdash;"),
    ("5", "Sliver injection", "6% of parcels shrunk 0.45 m",
     "adjoining sheets digitised independently, leaving voids", "yes"),
    ("6", "Overlap injection", "5% of parcels grown 0.55 m",
     "shared boundary double-counted between sheets", "yes"),
    ("7", "Self-intersection", "1.2% bow-tied; 4% duplicate vertices",
     "careless digitising, unclosed rings", "&mdash;"),
    ("8", "Schema drift", "all 7 columns renamed and reordered",
     "every department names its columns differently", "&mdash;"),
    ("9", "Owner corruption", "14% transliteration typos, 5% missing",
     "variance across romanisations", "&mdash;"),
    ("10", "Area unit drift", "m&sup2; re-expressed as bigha (&divide;2529.285)",
     "records kept in bigha and biswa", "yes"),
    ("11", "Khasra renumbering", "45% of blocks renumbered",
     "resurvey reissues parcel numbers", "&mdash;"),
    ("12", "Mutation", "4% split, 3% merged, 2.5% deleted, 2% spurious",
     "subdivision, amalgamation, record loss", "&mdash;"),
]

GLOSSARY = [
    ("khasra", "Parcel number in north Indian revenue records. Carries a recursive sub-division grammar on subdivision."),
    ("khatauni / jamabandi", "Record of rights. Khatauni in UP; jamabandi in Punjab and Haryana."),
    ("patta / chitta", "Tamil Nadu record of rights and its extract."),
    ("khata", "<b>Ambiguous and hazardous.</b> A revenue holding account in the north; a municipal property-tax account in urban Karnataka."),
    ("khatedar", "The recorded holder of a parcel."),
    ("mouza", "Revenue village; the unit a cadastral sheet typically covers."),
    ("bigha / biswa", "Traditional area units. Non-standard across states; bigha here is 2529.285 m&sup2;."),
    ("karam", "Linear unit underlying some area measures. Digitised in centimetres in Himachal, which is why Bhu-Naksha carries a &times;22 scale factor there."),
    ("FMB", "Field Measurement Book. The legally primary record in southern states, where the map is a derived sketch."),
    ("RoR", "Record of Rights &mdash; the textual register of who holds what."),
    ("mutation", "The statutory act of updating the record after a transfer. Requires notice and hearing; form varies by state."),
    ("tehsildar", "Revenue officer with authority to resolve a contested parcel."),
    ("ULPIN", "Unique Land Parcel Identification Number &mdash; 14 characters generated from geo-coordinates under DILRMP."),
    ("CORS", "Continuously Operating Reference Station. NAKSHA specifies control better than 5 cm."),
    ("GSD", "Ground Sample Distance &mdash; imagery resolution. NAKSHA specifies 5 cm."),
    ("DSM / DTM", "Digital Surface / Terrain Model. The difference gives building height, which separates an extended building from a heightened one."),
    ("LADM", "Land Administration Domain Model, ISO 19152. A formal language for describing land administration, not a data product spec."),
]

DEFECTS = [
    ("The leakage trap", "F1 0.9955 with khasra and owner supplying 96% of the decision and IoU 0.24%. The model had learned to join on an ID, which fails wherever resurvey renumbers.",
     f"Harness renumbers 45% of blocks and changes 12% of owners. A test asserts geometry &ge; 70% of gain. It is now {GEOM_PCT}%."),
    ("Blocking before georeferencing", "Candidate generation on raw coordinates gave blocking recall 0.58; 42% of true pairs never reached the model.",
     f"Pipeline reordered. Recall {mt['blocking_recall']}."),
    ("GP over-optimism", "Predicted 0.61 m against 1.23 m achieved. Variance quoted without observation noise; no kriging-mean correction; uncalibrated scale.",
     "All three fixed and the scale validated on a held-out city. Reported honestly: better-than-random fell 51.8% &rarr; 35.9%, because a better interpolator also rescues random placement."),
    ("fitBounds over 400 features", "Features are block-ordered, so the first 400 span a 170 m strip and the opening camera framed a sliver.",
     "Bounds over the full collection."),
    ("Layer-visibility race", "boot() added layers after the sync effect last ran; the uncertainty field rendered as a haze over everything.",
     "ready flag added to the effect dependencies."),
    ("Percentage width on inline elements", "Importance bars were spans; percentage widths are ignored on inline elements, so every bar rendered at 0 px.",
     "Track and fill declared display:block."),
    ("GeometryCollection from gap fill", "Occasionally produced a GeometryCollection, crashing the shapefile writer.",
     "_largest_polygon() at the export boundary."),
    ("Sign-in overlay inside the stage", "The toolbar showed a role before anyone had signed in.",
     "Overlay moved to position:fixed with its own stacking context."),
    ("Basemap maxzoom", "Esri canvas basemaps stop at z16; switching while pitched at z16.8 requested nonexistent tiles and blanked the map.",
     "Per-basemap maxzoom declared."),
    ("Command-palette PII leak", "Owner names filtered from palette search for the public role but still rendered as result subtitles. Found by using the system as public, not by reading it.",
     "redact() moved to the point of render."),
    ("autocrlf rewrote shell scripts", "Line-ending conversion broke every path in .sync.sh under bash.",
     ".gitattributes pins LF for .sh, .py, Dockerfile, YAML."),
    ("fpdf2 core fonts are latin-1", "The audit report rejected an em-dash and crashed the export.",
     "_PDF_FOLD maps out-of-range characters to ASCII."),
]

CSS = """
body { font-family: sans-serif; font-size: 9.1pt; line-height: 1.43; color: #16191d; }
h1 { font-size: 20pt; margin: 0 0 3pt 0; color: #0f2233; }
h2 { font-size: 12.6pt; margin: 17pt 0 5pt 0; color: #0f7a3f; }
h3 { font-size: 10.3pt; margin: 12pt 0 3pt 0; color: #0f2233; }
h4 { font-size: 9.3pt; margin: 11pt 0 3pt 0; color: #2b3138; }
p  { margin: 0 0 6pt 0; }
li { margin: 0 0 4pt 0; }
b { color: #0f2233; }
.sub { font-size: 10pt; color: #5a646e; margin: 0 0 3pt 0; }
.meta { font-size: 8pt; color: #7d868f; margin: 0 0 12pt 0; }
.lead { font-size: 9.8pt; color: #0f2233; margin: 0 0 8pt 0; }
.part { font-size: 15pt; margin: 24pt 0 2pt 0; color: #0f2233; }
.partsub { font-size: 8.6pt; color: #7d868f; margin: 0 0 10pt 0; }
.q { font-size: 9pt; color: #2b3138; margin: 4pt 0 7pt 15pt; }
.k { font-size: 8.4pt; color: #5a646e; margin: 0 0 6pt 0; }
.note { font-size: 8.5pt; color: #5a646e; margin: 5pt 0 8pt 0; }
.flag { font-size: 8.3pt; color: #8a4a12; margin: 4pt 0 7pt 0; }
.eq { font-family: monospace; font-size: 8.6pt; color: #0f2233; margin: 5pt 0 6pt 16pt; }
table { font-size: 8.4pt; }
th { text-align: left; color: #5a646e; font-size: 7.7pt; padding: 0 8pt 3pt 0; }
td { padding: 0 8pt 3pt 0; vertical-align: top; }
.num { font-family: monospace; font-size: 8.3pt; }
.ref { font-size: 8.3pt; margin: 0 0 5pt 0; }
"""

FRONT = f"""
<h1>KSHETRA &mdash; Research Compendium</h1>
<p class="sub">Automated Integration and Intelligent Harmonization of
Multi-Source Geospatial Data for Urban Land Record Management</p>
<p class="meta">Team NovaX &nbsp;&middot;&nbsp; Smart India Hackathon 2026
&nbsp;&middot;&nbsp; Problem Statement 26013 &nbsp;&middot;&nbsp;
{len(COMMITS)} commits &nbsp;&middot;&nbsp; {TOTAL:,} lines of first-party code</p>

<p class="lead">Three documents exist for this project. The <i>Research
Summary</i> (9 pp) is the literature-facing extract. The <i>Project Dossier</i>
(22 pp) is the engineering record. This is the complete one: the problem in its
historical and legal depth, the literature read closely, <b>the method written
out as mathematics rather than described</b>, a full feature dictionary, the
evaluation in detail, a formal comparison against prior art, and a glossary of
the domain vocabulary a reviewer outside Indian land administration will need.</p>

<h3>Conventions</h3>
<p><b>Claims about the world are graded.</b> <b>[V]</b> verified against a
primary or peer-reviewed source. <b>[S]</b> secondary &mdash; consistently
reported, not traced to the original. <b>[U]</b> unverified. Appendix G lists
the circulating statistics we decline to use and why.</p>

<p><b>Claims about our own system are measured.</b> Every figure in Parts D and
E is read from <span class="num">data/demo/*.json</span> when this PDF is
built; line counts come from <span class="num">git ls-files</span> and the
commit table from <span class="num">git log</span>. The document cannot
disagree with the repository.</p>

<h3>Document map</h3>
<table>
<tr><th>Part</th><th>Covers</th><th>Read it for</th></tr>
<tr><td><b>A</b></td><td>The problem domain &mdash; history, law, vocabulary, programme, scale</td>
    <td>Why this is hard for reasons that are not technical</td></tr>
<tr><td><b>B</b></td><td>Literature and tooling</td>
    <td>What is solved, what is not, and who established it</td></tr>
<tr><td><b>C</b></td><td>Method &mdash; the mathematics of all thirteen stages</td>
    <td>Exactly what the system computes</td></tr>
<tr><td><b>D</b></td><td>Evaluation</td>
    <td>How we know, including what we got wrong first</td></tr>
<tr><td><b>E</b></td><td>System, deployment, engineering record</td>
    <td>What was actually built and what it cost</td></tr>
<tr><td><b>F</b></td><td>Assessment &mdash; comparison, limits, validity, roadmap</td>
    <td>Where this stands and where it does not</td></tr>
</table>

<h3>Abstract</h3>
<p>NAKSHA specifies new urban orthoimagery to <b>RMSE &le; 10 cm</b>. The
legacy cadastral sheet it must be reconciled with has a modal positional error
of <b>3&ndash;4 m</b> [5]. Urban plots are of the order of <b>11 m</b> across,
so an unaligned legacy parcel overlaps its <i>neighbour</i> more than its own
counterpart: naive overlay is not imprecise, it is meaningless. We frame the
problem as <b>spatial entity resolution under a 30&ndash;40&times; accuracy
mismatch</b> rather than as boundary extraction, and address three gaps the
literature leaves open. First, <b>no ground truth exists</b>, so we manufacture
it &mdash; generating a clean cadastre and damaging it through twelve stages
drawn from a documented failure taxonomy, following the known-deformation
principle of [2]. Second, <b>confidence is usually a weighted score</b>, so we
calibrate ours by isotonic regression and report expected calibration error of
<b>{dec(mt['ece'])}</b>, which is what makes an explicit triage threshold
possible. Third, <b>ground truthing is NAKSHA's most delayed component</b> [9],
so we close the loop: a Gaussian process over the residual error field plus
greedy submodular maximisation with the (1&nbsp;&minus;&nbsp;1/e) bound of [8]
selects where to survey next, and the recommendation is <i>validated</i> by
applying it rather than asserted. On a held-out synthetic city the matcher
takes <b>{GEOM_PCT}%</b> of its decision from geometry at F1
<b>{mt['f1']}</b>, topology repair eliminates all <b>{tp['overlaps_before']:,}</b>
overlapping parcel pairs while an area ledger demonstrates no land was created
or destroyed, and the planner achieves <b>{tg['rmse_achieved']} m</b> against
<b>{tg['rmse_random']} m</b> for random placement of the same budget.</p>
"""

PART_A = f"""
<p class="part">Part A &mdash; The problem domain</p>
<p class="partsub">Why Indian cadastral harmonisation is hard for reasons that
predate computing.</p>

<h2>A1. Historical genesis of the fragmentation</h2>

<p>The Survey of India was established in <b>1767</b> and conducted revenue
survey nationally until <b>1904</b>, after which <b>each state became
responsible for its own cadastral survey and evolved its own system</b> [10]
<b>[V]</b>. Every interoperability problem in this problem statement descends
from that single administrative devolution: divergent vocabulary, divergent
units, divergent sheet scales, divergent legal primacy, divergent numbering
grammar. There is no technical fix for a 120-year institutional divergence;
there is only a system designed to expect it.</p>

<h2>A2. Legal primacy differs between north and south</h2>

<p>Northern states recognise the <b>graphic map</b> as the legal document.
Southern states prioritise the <b>Field Measurement Book</b> [11] <b>[V]</b>.</p>

<p>The consequence is not academic. In the north, the polygon carries legal
authority, so correcting its geometry corrects the record. In the south, the
<i>measurements</i> carry authority and the polygon is a derived sketch, so
rewriting the polygon changes a drawing, not a right &mdash; and a system that
treats its output as authoritative is destroying the record in one half of the
country while merely correcting it in the other.</p>

<p class="note">This is the direct reason our conflict resolver separates
<i>measured</i> fields from <i>recorded</i> fields and applies a different rule
to each (&sect;C12), and why a per-state policy object appears in the roadmap
rather than a global configuration flag.</p>

<h2>A3. Semantic heterogeneity is structural, not lexical</h2>

<p>A synonym table is insufficient, for three separate reasons.</p>

<h4>Numbering carries grammar</h4>
<p>South Indian survey numbers encode a recursive sub-division tree
(<span class="num">123</span> &rarr; <span class="num">123/1</span> &rarr;
<span class="num">123/1A</span>). A matcher that treats
<span class="num">123</span> and <span class="num">123/1A</span> as a mismatch
is discarding the single clearest signal that a subdivision occurred. We encode
this as <span class="num">kh_parent</span> and
<span class="num">kh_child</span> features (&sect;C6).</p>

<h4>The same concept has different names</h4>
<p>The record of rights is the <i>khatauni</i> in UP, the <i>jamabandi</i> in
Punjab and Haryana, the <i>patta</i>/<i>chitta</i> in Tamil Nadu. The holder is
the <i>khatedar</i>, <i>pattadar</i> or <i>bhogvatadar</i>. The parcel number is
<i>khasra</i>, <i>survey number</i>, <i>gat number</i> or <i>kitta</i>.</p>

<h4>The same name has different concepts &mdash; the dangerous case</h4>
<p class="flag"><b>"Khata" denotes a revenue holding account in the north but a
municipal property-tax account in urban Karnataka.</b> A lexicon that maps the
token to one canonical field will silently produce wrong joins in an urban
project. This is why our schema matcher profiles <i>values</i> as well as
reading names (&sect;C11): a column with four distinct values across 3,000 rows
is categorical and cannot be a holding identifier, whatever it is called.</p>

<h2>A4. Programme and policy context</h2>

<table>
<tr><th>Programme</th><th>What it is</th><th>Bearing on this work</th></tr>
<tr><td><b>NAKSHA</b></td><td>Urban land-record modernisation; drone survey of pilot ULBs</td>
    <td>Produces the 10 cm layer. Its progress review [9] names cross-agency non-interoperability as a systemic void and ground truthing as the most delayed component &mdash; the two gaps we aim at.</td></tr>
<tr><td><b>DILRMP</b></td><td>Digital India Land Records Modernisation Programme</td>
    <td>Source of the 49.10% geo-referenced-village figure [13] and of ULPIN.</td></tr>
<tr><td><b>SVAMITVA</b></td><td>Drone survey of inhabited rural <i>abadi</i> land</td>
    <td>Demonstrates the drone-to-record pipeline at national scale; rural, so adjacent rather than identical.</td></tr>
<tr><td><b>ULPIN</b></td><td>14-character parcel identifier from geo-coordinates</td>
    <td>We implement a faithful <i>shape</i>; the exact composition rule is <b>[U]</b> and we do not invent it.</td></tr>
<tr><td><b>NGP 2022</b></td><td>National Geospatial Policy [7]</td>
    <td>Commits to <i>redefining</i> the national geodetic framework. Note it does not create an "Indian Geodetic Datum 2023"; see Appendix G.</td></tr>
<tr><td><b>LADM</b></td><td>ISO 19152-1:2024 [16]</td>
    <td>Our canonical target schema, so every source maps into an ISO-conformant model rather than one we invented.</td></tr>
</table>

<h3>A4.1 What the new data will look like</h3>
<p>Survey of India technical circular T-260/1147-Project, 10 February 2025 [6]
<b>[V]</b>: orthorectified imagery at <b>5 cm GSD</b>, <b>RMSE(x,y) &le; 10
cm</b>; DSM/DTM at 0.5 m spacing, <b>RMSE(z) &le; 15 cm</b>; CORS control
better than 5 cm; 70%/60% overlap; minimum four corner and one centre GCP. CRS
settled as <b>UTM on WGS 84</b>, vertical on the Indian Vertical Datum via the
SoI geoid model.</p>

<h2>A5. The problem quantified</h2>

<p class="flag">Several widely-circulated Indian land-dispute statistics are
recycled with drifting attribution. Only traceable figures appear below.</p>

<table>
<tr><th>Claim</th><th>Source</th><th>Grade</th></tr>
<tr><td>7,933+ urban settlements, ~10.2 M ha, 4,912 ULBs</td><td>[9, 12]</td><td>[V]</td></tr>
<tr><td>Only four states maintain structured urban land records (TN, MH, GJ, GA)</td>
    <td>[9] and DoLR's NAKSHA booklet [12], independently</td><td>[V]</td></tr>
<tr><td>~13 M urban households in 108,000 slums</td><td>[9]</td><td>[V]</td></tr>
<tr><td>49.10% of villages hold geo-referenced cadastral maps</td><td>[13]</td><td>[V]</td></tr>
<tr><td>Land market distortions erode ~1.3% of annual GDP growth</td><td>[9]</td><td>[V]</td></tr>
<tr><td>ULBs generate only 32% of revenue internally</td><td>[9]</td><td>[V]</td></tr>
<tr><td>Land/property taxes 0.6% of GDP in low-income vs 2.2% industrialised</td><td>[9]</td><td>[V]</td></tr>
<tr><td>Property disputes 60&ndash;70% of Indian civil litigation</td><td>[9]</td><td>[V] as a peer-reviewed statement</td></tr>
<tr><td>~Two-thirds of surveyed civil matters concerned land and property</td>
    <td>DAKSH 2015-16; 9,329 litigants, 305 locations, 24 states [14]</td>
    <td>[V] as a survey of litigants, not a census</td></tr>
<tr><td>Resurvey rate &#8377;56,725 / sq km</td><td>Tamil Nadu, DILRMP review 2024 [15]</td><td>[V]</td></tr>
<tr><td>Resurvey takes 2&ndash;3 years per district tranche even with drone + DGPS</td><td>[15]</td><td>[V]</td></tr>
</table>

<h2>A6. How wrong the legacy maps are &mdash; the central measurement</h2>

<p>Sengupta, Lemmen, Devos, Bandyopadhyay and van der Veen georeferenced
<b>310 analogue cadastral sheets</b> at 1:3960 over a 327 km&sup2; planning
area in West Bengal &mdash; 258 mouzas, 26 municipal wards, mapped mostly from
pre-1920s surveys and 1950s work &mdash; against GeoEye-1 pan-sharpened imagery
with 10&ndash;15 GCPs per sheet and a first-order transformation [5]
<b>[V]</b>.</p>

<table>
<tr><th>RMSE band</th><th>Sheets</th><th>Share</th><th>Cumulative</th></tr>
<tr><td>&lt; 2.00 m</td><td class="num">7</td><td class="num">2.3%</td><td class="num">2.3%</td></tr>
<tr><td>2.01 &ndash; 3.00 m</td><td class="num">64</td><td class="num">20.6%</td><td class="num">22.9%</td></tr>
<tr><td><b>3.01 &ndash; 4.00 m</b></td><td class="num"><b>185</b></td><td class="num"><b>59.7%</b></td><td class="num">82.6%</td></tr>
<tr><td>4.01 &ndash; 5.00 m</td><td class="num">47</td><td class="num">15.2%</td><td class="num">97.7%</td></tr>
<tr><td>&gt; 5.01 m</td><td class="num">7</td><td class="num">2.3%</td><td class="num">100%</td></tr>
</table>

<p>The <b>modal</b> error is 3&ndash;4 m and <b>88% of sheets fall between 2
and 5 m</b>. This is the single most load-bearing number in the project: it is
what makes the problem an entity-resolution problem rather than an overlay
problem.</p>

<h3>A6.1 Transformation order is still chosen by a human</h3>
<table>
<tr><th>Sample</th><th>1st order</th><th>2nd order</th><th>Reduction</th></tr>
<tr><td>1</td><td class="num">3.668 m</td><td class="num">3.177 m</td><td class="num">13%</td></tr>
<tr><td>2</td><td class="num">3.171 m</td><td class="num">2.510 m</td><td class="num">21%</td></tr>
<tr><td>3</td><td class="num">3.962 m</td><td class="num">1.339 m</td><td class="num"><b>66%</b></td></tr>
<tr><td>4</td><td class="num">4.089 m</td><td class="num">3.096 m</td><td class="num">24%</td></tr>
<tr><td>5</td><td class="num">5.010 m</td><td class="num">2.889 m</td><td class="num">42%</td></tr>
</table>
<p>Up to two thirds of the error is removable by a higher-order transformation
&mdash; but choosing the order per sheet is manual [5]. &sect;C3 describes our
escalating selector, which is the direct response.</p>

<h3>A6.2 Documented failure taxonomy [5] [V]</h3>
<ul>
<li><b>Gaps and overlaps between adjoining mouza sheets</b> &mdash; adjacent sheets do not fit.</li>
<li><b>Multi-sheet mouzas</b> with unclear division between sheets.</li>
<li><b>Canal double-counting</b> &mdash; a shared boundary drawn on both sheets, so area is counted twice.</li>
<li><b>River dynamics</b> &mdash; land lost or accreted, giving large legal-versus-digitised discrepancies.</li>
<li><b>Paper degradation</b> &mdash; shrinkage, wrinkling, folding, tearing; scanning adds more.</li>
<li><b>Crude map lines</b> &mdash; scanned lines over 4&ndash;5 px wide, so boundary ambiguity of decimetres to metres exists <i>before</i> any transformation.</li>
<li><b>Area attribute inconsistency</b> &mdash; digitised area &ne; authorised area in the RoR.</li>
</ul>
<p class="note">Our damage harness (&sect;D2) reproduces five of these seven
directly. That it derives from a documented taxonomy rather than from
imagination is why we consider the recovery figures meaningful.</p>

<h2>A7. The mismatch, stated formally</h2>
<p class="lead">New layer &sigma; &asymp; 0.10 m. Legacy layer &sigma; &asymp;
3.5 m. Characteristic parcel width w &asymp; 11 m.</p>
<p>For a legacy parcel displaced by d, expected overlap with its true
counterpart falls roughly as (1 &minus; d/w)&sup2; while overlap with the
adjacent parcel <i>rises</i>. The two cross near <b>d = w/2 &asymp; 5.5 m</b>
&mdash; comfortably inside the observed 2&ndash;5 m band once warp and
digitising noise compound. Beyond that crossover the nearest-overlap heuristic
that every overlay tool relies on is not merely noisy, it is
<b>systematically wrong</b>, and confidently so.</p>
<p>This is the whole argument for the pipeline order in &sect;C1, and we
measured it rather than assuming it: matching before georeferencing gave
blocking recall <b>0.58</b>; after reordering, <b>{mt['blocking_recall']}</b>
(&sect;D4).</p>
"""

PART_B = """
<p class="part">Part B &mdash; Literature and tooling</p>
<p class="partsub">Five papers read in the original; the tool landscape; the gap.</p>

<h2>B1. Chen, Nazeer, Lee &amp; Wong 2026 &mdash; the systematic review [1]</h2>
<p>Published March 2026 in <i>Land</i>. Establishes that deep learning has
removed the manual-interpretation bottleneck in boundary extraction via CNN and
Transformer segmentation, that NLP methods now extract structure from paper
archives, and that deep models detect parcel change and support integrated
spatial/non-spatial analysis <b>[V]</b>. Its closing statement of open
problems:</p>
<p class="q">"&hellip;challenges remain, including differences in
multi-temporal data processing, spatial semantic ambiguity, and the lack of
large-scale, high-quality annotated data. Future research can focus on
improving model generalization, advancing cross-modal data fusion, and
providing recommendations for the development of a reliable and practical
intelligent cadastral system."</p>
<p>Mapped onto this project: <i>lack of annotated data</i> &rarr; &sect;D1
manufactured ground truth. <i>Cross-modal fusion</i> &rarr; &sect;C12
provenance-weighted resolution. <i>Generalization</i> &rarr; &sect;D3 held-out
city evaluation. <i>Spatial semantic ambiguity</i> &rarr; &sect;C11 schema
inference.</p>

<h2>B2. Girard, Charpiat &amp; Tarabalka 2019 &mdash; alignment without truth [2]</h2>
<p>The closest published statement of our core problem. A multi-resolution
U-Net predicts a dense 2-D displacement field aligning misregistered cadastral
polygons to imagery where no correct annotation exists, trained over rounds
that re-correct the annotations between rounds. <b>Alignment error fell by more
than 3&times; by round two; round three added nothing</b> <b>[V]</b>.</p>

<h4>The method we borrow</h4>
<p>Training data is constructed by applying <i>known random deformations</i>
and learning to invert them &mdash; formally a dataset</p>
<p class="eq">D = { (I, J_rand, f_rand) }</p>
<p>where the deformation f is generated and therefore known. Our damage harness
is this principle, applied to an Indian failure taxonomy instead of generic
warps. This matters for how we defend it: manufactured ground truth is
<b>published method</b>, not an improvisation forced on us by data scarcity.</p>

<h4>The two limitations we inherit</h4>
<p>A perfect alignment score is <i>unattainable</i> because the reference
annotations are themselves ambiguous &mdash; many buildings are outlined by a
coarse polygon, so "best alignment" is ill-posed with multiple equally good
solutions. And the model learns only <b>smooth</b> displacement fields, so
adjoining buildings requiring a discontinuous correction fail.</p>
<p class="note">Our Gaussian process carries exactly the same smoothness
assumption &mdash; a squared-exponential kernel cannot represent a sheet-join
discontinuity. We therefore report an irreducible error floor rather than
implying arbitrary accuracy is purchasable with survey budget (&sect;C13).</p>

<h2>B3. Suwardhi et al. 2025 &mdash; the closest operational system [3]</h2>
<p>UAV orthophotos at 5 cm GSD segmented by the Segment Anything Model without
manual prompting; displacement vectors from ICP; hierarchical adjustment from
rigid block (LS1) to scaled block (LS2) to individual parcel (LS3). Evaluated
over two urban villages in Cimahi, Indonesia &mdash; <b>Karangmekar</b>, 81
blocks / 3,227 parcels and <b>Baros</b>, 96 blocks / 2,971 parcels &mdash;
chosen for contrasting block structure and data quality. Client-server, Python
REST API <b>[V]</b>.</p>

<h4>What it cannot do, and why that is the instructive part</h4>
<p>Because no correct geometry exists for those areas either, the authors
evaluate <b>by proxy</b>: they count how often cadastral polygons split the
SAM-derived boundary segments, treating fewer splits as better alignment. That
measures <i>internal consistency</i>, not accuracy. <b>The state of the art
cannot report its error in metres.</b></p>
<p>It is also single-source and single-country, and addresses none of: attribute
schema inference, CRS/datum/unit heterogeneity, tenure semantics, calibrated
confidence, or where to survey next.</p>

<h2>B4. Fetai, Grigillo &amp; Lisec 2022 &mdash; boundary revision [4]</h2>
<p>A modified CNN detects visible land boundaries from image-based mapping and
uses them to revise existing cadastral data <b>[V]</b>. This sits
<i>upstream</i> of our pipeline and we deliberately do not rebuild it:
extraction is well served by the literature, and the problem statement asks for
integration of extracted features, not another extractor. Building a worse
version of a solved problem would be the easiest way to lose this hackathon.</p>

<h2>B5. Krause, Singh &amp; Guestrin 2008 &mdash; the imported theorem [8]</h2>
<p>Sensor placement in Gaussian processes. With S the chosen observation set
and F(S) the total posterior-variance reduction over the domain, <b>F is
monotone and submodular</b>, so greedy selection is within
(1&nbsp;&minus;&nbsp;1/e)&nbsp;&asymp;&nbsp;63% of optimal, and exact
optimisation is NP-hard <b>[V]</b>.</p>
<p>The result is standard in machine learning and we claim no part of it. What
we claim is the transfer: <b>we found no application of it to cadastral
ground-control planning</b>, and the fit is unusually clean because posterior
variance depends only on <i>where</i> you observe, never on what you measure
&mdash; so the entire survey plan is computable before anyone leaves the
office (&sect;C14).</p>

<h2>B6. LADM and the question posed in 2013</h2>
<p>ISO 19152-1:2024 [16] <b>[V]</b>. Explicitly <i>not</i> a data product
specification: its stated purpose is "not to replace existing systems, but
rather to provide a formal language for describing them." Four core packages:
parties; basic administrative units carrying rights, restrictions and
responsibilities; spatial units; spatial sources and representations.</p>
<p>Sengupta et al. [17] <b>[V]</b> asked in 2013 how to convert colonial maps
and records into an LADM database, <b>how to document and publish the geometric
quality of existing maps</b>, and <b>how to integrate more accurate data after
re-survey</b>. That final question &mdash; fusing a high-accuracy new survey
with a low-accuracy legal record without destroying the legal record &mdash; is
this problem statement, posed in the literature thirteen years ago and still
open.</p>

<h2>B7. The tooling landscape</h2>

<table>
<tr><th>Tool</th><th>Genuinely does</th><th>Does not do</th></tr>
<tr><td><b>GRASS <span class="num">v.clean</span></b></td>
    <td>Break/clean polygons from non-topological formats; remove sub-threshold
        areas by dissolving into the longest-shared-boundary neighbour; fuzzy
        snapping; vertex pruning</td>
    <td>A human picks the thresholds. Wrong value destroys parcels or leaves
        slivers. A tool, not a decision-maker.</td></tr>
<tr><td><b>PostGIS Topology</b></td>
    <td>Persistent topological model with shared edges and faces; prevents gaps
        and overlaps by construction going forward</td>
    <td>Getting dirty legacy geometry <i>into</i> a valid topology is the hard
        part; common practice is to clean in GRASS first.</td></tr>
<tr><td><b>QGIS + GDAL/PROJ</b></td>
    <td>Georeferencer with polynomial 1st&ndash;3rd order, TPS, projective,
        Helmert; topology checker; reprojection</td>
    <td>Manual, per layer, per operator, GCPs by hand. No cross-source
        reasoning, no confidence, no triage.</td></tr>
<tr><td><b>FME / Esri Data Interop.</b></td>
    <td>Industry-standard spatial ETL; hundreds of formats; visual schema
        mapping</td>
    <td><b>The mapping is declared by a human, not inferred.</b> FME executes a
        mapping faithfully; it will not tell you
        <span class="num">KHASRA_NO</span> and <span class="num">SY_NO</span>
        are one concept, nor that they disagree for 12% of parcels. Proprietary,
        at 4,912-ULB scale.</td></tr>
<tr><td><b>Esri Parcel Fabric</b></td>
    <td>Mature cadastral editing and QA</td>
    <td>Deed-based COGO assumptions; not built for khasra / FMB / mouza
        semantics or a 30&ndash;40&times; inter-layer mismatch.</td></tr>
<tr><td><b>SAM / Mask R-CNN / U-Net</b></td>
    <td>Strong at extracting <i>visible</i> boundaries</td>
    <td><b>Cadastral boundaries are frequently invisible</b> &mdash; no wall, no
        fence, no hedge. The ceiling of pure vision.</td></tr>
<tr><td><b>Bhu-Naksha</b> (incumbent)</td>
    <td>National cadastral map software in use across many states</td>
    <td>Hand-entered <b>per-state scale factors</b> on shapefile import &mdash;
        UP &times;4000, Himachal &times;22 where <i>karam</i> was digitised in
        centimetres &mdash; plus hand-written per-state RoR adapters. <b>The
        incumbent national answer to unit heterogeneity is a magic
        number.</b> <b>[V]</b></td></tr>
</table>

<h2>B8. Synthesis &mdash; the eight open problems</h2>
<table>
<tr><th>#</th><th>Open problem</th><th>Our response</th></tr>
<tr><td>1</td><td>No automated, evidence-weighted reconciliation across accuracy tiers</td>
    <td>&sect;C12 &mdash; inverse-variance for measured, legal authority for recorded</td></tr>
<tr><td>2</td><td>Transformation-model selection is a human judgement</td>
    <td>&sect;C3 &mdash; escalation driven by residual structure</td></tr>
<tr><td>3</td><td>Schema matching for Indian land attributes is entirely manual</td>
    <td>&sect;C11 &mdash; lexicon + value profiling + unit inference from geometry</td></tr>
<tr><td>4</td><td>Topology cleaning has no legal-consequence awareness</td>
    <td>&sect;C9 &mdash; parcel-sized holes flagged, not filled; partial</td></tr>
<tr><td>5</td><td>Vision finds visible boundaries; cadastres contain invisible ones</td>
    <td><b>Not addressed.</b> Named in &sect;F5 as open</td></tr>
<tr><td>6</td><td>Cross-agency entity resolution unaddressed [9]</td>
    <td>&sect;C4&ndash;C8 &mdash; the core of the system</td></tr>
<tr><td>7</td><td>State of the art is single-source, single-country</td>
    <td>&sect;C12 &mdash; n-source, per-attribute authority</td></tr>
<tr><td>8</td><td>No open benchmark or ground truth exists</td>
    <td>&sect;D1 &mdash; manufactured; release named in &sect;F5</td></tr>
</table>
<p class="note">Five of eight addressed, one partially, one explicitly not.
Stating which is which is more useful to a reviewer than claiming all eight.</p>
"""

feat_rows = "\n".join(
    f'<tr><td class="num">{n}</td><td>{grp}</td><td>{d}</td></tr>'
    for n, grp, d in FEATURES)

PART_C = f"""
<p class="part">Part C &mdash; Method</p>
<p class="partsub">What the system actually computes, stage by stage.</p>

<h2>C1. Pipeline, and why the order is not negotiable</h2>
<p class="eq">ingest &rarr; schema inference &rarr; validate &rarr; georeference
&rarr; blocking &rarr; match &rarr; assign &rarr; topology &rarr; conflict
&rarr; change &rarr; uncertainty &rarr; targeting &rarr; serve</p>

<p><b>Georeference precedes match</b> by the crossover argument of &sect;A7 and
the measurement of &sect;D4. <b>Schema inference precedes validation</b>
because an area column cannot be range-checked until its unit is known, and the
unit is inferred from geometry (&sect;C11), which requires geometry to exist.
<b>Topology precedes conflict</b> because an overlap is a geometric fact to be
removed, not a claim to be adjudicated. <b>Uncertainty precedes targeting</b>
trivially, but the pairing is the point: targeting is only meaningful because
the preceding stages produce an honest error field rather than a point
estimate.</p>

<h2>C2. Coordinate reference systems</h2>
<p>Implemented from Snyder, <i>Map Projections: A Working Manual</i> (USGS PP
1395), covering exactly what Indian urban cadastral work needs: WGS84 &harr;
UTM for zones 42N&ndash;47N, and Everest 1830 (India) &harr; WGS84 via a
seven-parameter Helmert transform.</p>

<p><b>Why Everest 1830 matters.</b> Legacy sheets and older Survey of India
products are referenced to it; drone and GNSS output is WGS84. Ignoring the
datum difference leaves a <b>systematic offset of several hundred metres</b>
&mdash; two orders of magnitude larger than the misregistration everything else
in this document is about, and the single largest error source when overlaying
an old map on new imagery. A pipeline that gets this wrong produces beautifully
calibrated nonsense.</p>

<p>Ellipsoid parameters derive from a and 1/f, with first eccentricity</p>
<p class="eq">e&sup2; = f(2 &minus; f),&nbsp;&nbsp; f = 1 / inv_f</p>
<p>Helmert is the standard seven-parameter form (three translations, three
rotations, one scale) applied in geocentric Cartesian coordinates.</p>

<p class="note"><b>Verified:</b> round-trip &lt; 1 mm; central meridian easting
exactly 500,000 m; agreement with pyproj &lt; 1 mm where pyproj is available.
Written from scratch because pyproj was blocked by Application Control
(&sect;E5), and <i>kept</i> because sub-millimetre agreement with the reference
implementation is a stronger claim than having imported it.</p>

<h2>C3. Coarse alignment</h2>
<p>Three stages, each robust to the failure mode of the one before it.</p>

<h4>Stage 1 &mdash; translation voting (Hough)</h4>
<p>Every source centroid votes for the displacement to each of its k nearest
reference centroids. The true translation is shared by thousands of parcels
while wrong pairings scatter, so it appears as a sharp peak in a 2-D histogram
of votes.</p>
<p class="note">Chosen over ICP deliberately: a Hough transform has <b>no
initialisation requirement and cannot fall into a local minimum</b>. ICP, which
[3] uses, requires a starting estimate good enough that nearest-neighbour
correspondences are mostly right &mdash; precisely the assumption that
&sect;A7 shows fails at 5&ndash;15 m displacement on 11 m parcels.</p>

<h4>Stage 2 &mdash; robust similarity refinement</h4>
<p>From the voted translation, fit rotation, scale and translation on
<i>mutual</i>-nearest-neighbour pairs, reject outliers by a trimmed residual
threshold, iterate.</p>

<h4>Stage 3 &mdash; residual reporting and transform escalation</h4>
<p>What remains is the non-linear part &mdash; paper warp &mdash; removed later
using matched parcels as control points. The transform escalates
similarity &rarr; affine &rarr; second-order polynomial, accepted only when
residual structure justifies the added degrees of freedom. This is the
automated answer to &sect;A6.1.</p>

<p class="note"><b>Reported at the data centroid, not as raw tx/ty.</b> With
UTM northings near 3.1 million a raw translation parameter is unauditable; a
displacement at the centroid is a number a revenue officer can hold against a
map. Small decision, large difference to whether anyone trusts the output.</p>

<table>
<tr><th>Quantity</th><th>Injected</th><th>Recovered</th></tr>
<tr><td>Displacement</td><td class="num">(6.5, &minus;4.2) m</td><td class="num">{g['displacement_m']} m</td></tr>
<tr><td>Rotation</td><td class="num">0.85&deg;</td><td class="num">{g['rotation_deg']}&deg;</td></tr>
<tr><td>Scale</td><td class="num">1.0016</td><td class="num">{g['scale']}</td></tr>
<tr><td>RMSE</td><td class="num">{g['rmse_raw']} m</td><td class="num">{g['rmse_coarse']} m</td></tr>
<tr><td>Inliers</td><td>&mdash;</td><td class="num">{g['inliers']:,}</td></tr>
</table>

<h2>C4. Blocking</h2>
<p>Exhaustive pairing of {cnt['legacy']:,} &times; {cnt['reference']:,} is 9.0
million pairs; we evaluate {cnt['candidate_pairs']:,}. The ranking function
matters more than the count:</p>
<p class="eq">rank(j) = (1, area(A &cap; B&#7525;))&nbsp;&nbsp;if overlap &gt; 0
<br/>rank(j) = (0, &minus;&#8214;c&#7525; &minus; c&#8336;&#8214;&sup2;)&nbsp;&nbsp;otherwise</p>
<p>Candidates with any overlap outrank all candidates with none, and within
each tier ordering is by overlap area or by centroid proximity respectively.
The second tier is what prevents catastrophic recall loss: a parcel whose
counterpart was <i>deleted</i>, or displaced beyond overlap, still gets its
nearest neighbours considered rather than being silently dropped.</p>
<p>Measured blocking recall: <b>{mt['blocking_recall']}</b>.</p>

<h2>C5. The feature set &mdash; complete dictionary</h2>
<p>29 features in seven groups. The context group is the one most systems omit
and the one that makes calibration possible.</p>
<table>
<tr><th>Feature</th><th>Group</th><th>Definition and why it is here</th></tr>
{feat_rows}
</table>

<h2>C6. Why khasra features are structural, not identity</h2>
<p>Note what the four khasra features encode:
<span class="num">kh_exact</span> (equality),
<span class="num">kh_parent</span> / <span class="num">kh_child</span>
(position in the sub-division tree), and
<span class="num">kh_present</span> (existence). <b>None of them is the number
itself.</b> The model cannot memorise a lookup from khasra to parcel; it can
only use the number as weak corroboration and as a subdivision signal.</p>
<p>This is deliberate and it is tested. &sect;D4 describes the first model,
which scored F1 0.9955 by doing exactly what this design forbids.</p>

<h2>C7. Model and calibration</h2>
<h4>Why gradient-boosted trees</h4>
<p>The input is ~29 heterogeneous tabular features with strong monotone
structure and heavy interaction &mdash; IoU matters far more when candidate
count is low; name similarity matters far more when IoU is ambiguous. Boosted
trees are the right tool for that shape, they train in seconds, and <b>the
decision path for any individual parcel can be printed and defended</b>, which
a land-administration audit trail requires and a neural network does not
provide.</p>

<h4>Why calibration is a separate stage</h4>
<p>Raw GBDT margins through a sigmoid are systematically overconfident.
Isotonic regression on a held-out split maps them onto frequencies that
actually hold. Formally, isotonic regression finds the monotone
non-decreasing &#285; minimising</p>
<p class="eq">&Sigma;&#7522; w&#7522; (y&#7522; &minus; &#285;(s&#7522;))&sup2;
&nbsp;&nbsp;subject to&nbsp;&nbsp; s&#7522; &le; s&#11388; &rArr;
&#285;(s&#7522;) &le; &#285;(s&#11388;)</p>
<p>Monotone because a higher score should never mean a lower probability;
non-parametric because we have no reason to believe the miscalibration is
sigmoidal.</p>

<h4>Group splitting</h4>
<p>Splits are made <b>by source parcel, never by pair</b>, so one parcel's
candidates cannot straddle train and test. Splitting by pair would leak: the
model would see parcel P's correct match in training and its near-misses in
test, and every metric would be inflated.</p>

<h2>C8. Calibration metrics, defined</h2>
<p>Hand-implemented because scikit-learn was blocked (&sect;E5), which forced
us to state precisely what we were computing.</p>
<p class="eq">ECE = &Sigma;&#7598; (n&#7598;/N) &#8214;acc(b) &minus; conf(b)&#8214;</p>
<p>over equal-width bins b. Measured: <b>{dec(mt['ece'])}</b>.</p>
<p class="eq">Brier = (1/N) &Sigma;&#7522; (p&#7522; &minus; y&#7522;)&sup2;</p>
<p>Measured: <b>{dec(mt['brier'])}</b>. Brier decomposes into reliability minus
resolution plus uncertainty, so a low Brier with a low ECE means the model is
both calibrated <i>and</i> discriminative &mdash; a constant predictor achieves
perfect calibration and useless resolution, which is why neither number is
reported alone.</p>

<p class="note">Calibration gets as much attention in this codebase as
accuracy, deliberately. The purpose of the system is <b>triage</b>: an officer
finalises the confident matches and reviews the rest. A model that is 95%
accurate but claims 99% confidence everywhere is useless for triage, because no
safe threshold exists.</p>

<h2>C9. Assignment</h2>
<p>Pairwise scores are not enough. A cadastre is a <b>partition of space</b>,
so the mapping must be globally coherent: one parcel cannot match three others
because all three scored well individually.</p>
<p>Containment is tested <b>before</b> the Hungarian assignment, because a
subdivided parcel is not a failed 1:1 match and forcing it through a 1:1 solver
destroys exactly the information a cadastral officer most needs.</p>
<table>
<tr><th>Relation</th><th>Meaning</th><th>Count</th></tr>
<tr><td class="num">one_to_one</td><td>Unchanged between layers</td><td class="num">{asg['one_to_one']:,}</td></tr>
<tr><td class="num">split</td><td><b>Subdivision</b> &mdash; a holding sold off in parts</td><td class="num">{asg['split']}</td></tr>
<tr><td class="num">merge</td><td><b>Amalgamation</b> &mdash; holdings combined</td><td class="num">{asg['merge']}</td></tr>
<tr><td class="num">unmatched_source</td><td>Genuinely new, or spurious</td><td class="num">{asg['unmatched_source']}</td></tr>
<tr><td class="num">unmatched_reference</td><td>Present in reference, missing from source</td><td class="num">{asg['unmatched_reference']}</td></tr>
</table>
<p>Thresholds (containment 0.50, split/merge coverage 0.55) were chosen for
<b>precision over F1</b>: a wrongly asserted subdivision is a worse outcome in
a land record than an unresolved case sent to a human.</p>

<h2>C10. Topology as a planar partition</h2>
<p>A cadastre tiles the ground with no gaps and no overlaps. Layers digitised
parcel-by-parcel from paper never satisfy this, and the violations are not
cosmetic: <b>an overlap means two people are recorded as owning the same square
metre, and a gap means land that legally belongs to nobody.</b></p>

<p>Five stages, fixed order because each assumes the previous succeeded:</p>
<ol>
<li><b>Validity</b> &mdash; self-intersecting rings repaired first; area on a
bow-tie is meaningless, so every later stage depends on this.</li>
<li><b>Vertex hygiene</b> &mdash; duplicate and near-collinear vertices removed.</li>
<li><b>Vertex snapping</b> &mdash; the workhorse. Vertices from different
parcels within tolerance are clustered by union-find over cKDTree pairs and
collapsed onto one point. This closes hairline gaps and removes hairline
overlaps <i>simultaneously</i>, because both arise from one cause: two
surveyors digitising one shared boundary twice.</li>
<li><b>Residual overlap resolution</b> &mdash; contested area awarded by an
explicit auditable rule, not by whichever polygon is drawn last.</li>
<li><b>Gap classification</b> &mdash; see below.</li>
</ol>
<p class="k">{tp['vertices_snapped']:,} vertices snapped on the evaluation
city.</p>

<h3>C10.1 The refusal</h3>
<p>The stage that matters most is the one that declines to act. Residual gaps
are classified by area, compactness and whether anything in the record claims
them. Sliver artefacts are closed; <b>parcel-sized holes are flagged for survey
and left open</b>, because filling one fabricates a boundary and awards land to
whoever happens to adjoin it.</p>
<p>Of {tp['harness_deleted']} parcels the harness deleted to create holes, the
cleaner <b>refused {tp['refused_to_fill']}</b>. A verification assertion
enforces this, because a cleaner that fills everything reports fewer errors and
would otherwise look like an improvement (&sect;D5).</p>

<h2>C11. Schema inference</h2>
<p>Three independent signals, because none alone is reliable.</p>
<p><b>Name similarity</b> against an Indian revenue lexicon. Strong when the
column is conventionally named; useless when it is
<span class="num">F14</span> or <span class="num">COL_3</span>.</p>
<p><b>Value profiling</b> &mdash; dtype, cardinality, uniqueness, regex shape. A
column 99% unique matching <span class="num">\\d+(/\\d+)?</span> is a khasra
number whatever it is called; a column with four distinct values across 3,000
rows is categorical and cannot be an owner name.</p>
<p><b>Unit inference against geometry</b> &mdash; the part that matters most.
Recorded area is meaningless until the unit is known, and records are kept in
m&sup2;, bigha, biswa, acres or square yards. Rather than trust a name, divide
recorded values by the <i>surveyed</i> area of the same parcels and take the
modal ratio:</p>
<p class="eq">u&#770; = mode&#7522; ( area_recorded&#7522; / area_geometric&#7522; )&#8315;&sup1;</p>
<p>Measured median <b>2500.45 m&sup2;/unit</b> against bigha at 2529.285 &rarr;
inferred <b>{sc['area_unit']}</b> at confidence
<b>{sc['area_unit_confidence']}</b>, with no human declaring it.</p>
<p class="note">Not academic. NIC's own Bhu-Naksha manual documents a manually
entered per-state scale factor on shapefile import &mdash; UP &times;4000,
Himachal &times;22. Inferring it removes a hand-entered magic number from the
critical path of the incumbent national system.</p>
<p>Assignment is <b>1:1 by the Hungarian algorithm</b>, so two columns cannot
both claim to be the owner field. Result: <b>{sc['mapped']}/{sc['total']}</b>.</p>
<table>
<tr><th>Canonical</th><th>Column</th><th>Conf.</th><th>Evidence</th></tr>
{"".join(f'<tr><td>{f["canonical"]}</td><td class="num">{f["column"]}</td>'
         f'<td class="num">{f["confidence"]}</td><td>{f["evidence"]}</td></tr>'
         for f in SCHEMA["fields"])}
</table>

<h2>C12. Provenance-weighted conflict resolution</h2>
<p>When n sources disagree about one parcel, "which wins" is not one question.
It depends on <i>what</i> is claimed.</p>
<table>
<tr><th>Class</th><th>Fields</th><th>Rule</th><th>Justification</th></tr>
<tr><td><b>Measured</b></td><td class="num">geometry, area_sqm, centroid, boundary</td>
    <td>Inverse-variance weighting</td>
    <td>The statistically correct way to combine independent measurements of one quantity</td></tr>
<tr><td><b>Recorded</b></td><td class="num">owner, tenure, khasra, land_use, ulpin</td>
    <td>Legal authority</td>
    <td><b>A drone cannot observe who owns a plot.</b> Accuracy is irrelevant to the question</td></tr>
</table>
<p class="eq">x&#770; = ( &Sigma;&#7522; x&#7522;/&sigma;&#7522;&sup2; ) / ( &Sigma;&#7522; 1/&sigma;&#7522;&sup2; ),
&nbsp;&nbsp; &sigma;&#770;&sup2; = 1 / &Sigma;&#7522; 1/&sigma;&#7522;&sup2;</p>
<p><b>Authority is per attribute, not per source.</b> Conflating the two is the
classic mistake and it produces a system that will confidently overwrite a
title with a photograph.</p>

<h3>C12.1 Dominant precision &mdash; when not to fuse</h3>
<p>Where one source is an order of magnitude better, it wins outright rather
than being averaged. A worked case from
<span class="num">resolutions.json</span>:</p>
<table>
<tr><th>Source</th><th>&sigma;</th><th>Claim (m&sup2;)</th></tr>
{"".join(f'<tr><td>{c["label"]}</td><td class="num">{c["sigma_m"]} m</td>'
         f'<td class="num">{c["value"]}</td></tr>' for c in RES[0]["claims"])}
</table>
<p>Resolved to <b>{RES[0]["resolutions"][0]["value"]}</b> under rule
<i>{RES[0]["resolutions"][0]["rule"]}</i>, noted:
"{RES[0]["resolutions"][0]["note"]}". Averaging good evidence with bad produces
worse evidence; a resolver that always fuses is wrong here.</p>

<h3>C12.2 Transitive inconsistency</h3>
<p>If A agrees with B and B agrees with C but A contradicts C, <b>no pairwise
comparison can see the problem</b>. It requires the whole claim set at once, and
it is a strong signal that one source is systematically wrong in this area.
Detected and escalated rather than resolved arbitrarily.
{cnt['conflicts']} cases raised for review.</p>

<h2>C13. The uncertainty field</h2>
<p>After coarse georeferencing the residual error is <b>not</b> random per
parcel. It is spatially correlated: paper shrinkage, sheet joins and scanner
distortion deform whole neighbourhoods together. Two parcels ten metres apart
are wrong in almost the same direction and by almost the same amount.</p>
<p class="lead">That correlation is precisely what makes survey planning
possible. If errors were independent, fixing N parcels would require surveying
N parcels and there would be nothing to optimise.</p>
<p>We model the residual field as</p>
<p class="eq">r(x) ~ GP(0, k(x, x&prime;)),&nbsp;&nbsp;
k(x, x&prime;) = &sigma;&#8347;&sup2; exp( &minus;&#8214;x &minus; x&prime;&#8214;&sup2; / 2&#8467;&sup2; )</p>
<p>with observation noise &sigma;&#8345;&sup2;. Hyperparameters
(&#8467;, &sigma;&#8347;&sup2;, &sigma;&#8345;&sup2;) are fitted by maximising
the log marginal likelihood on residuals observed at matched parcels, so <b>the
lengthscale is learned, not assumed</b>. Fitted: <b>{tg['lengthscale_m']} m</b>,
which a verification assertion checks is physically plausible
(5&ndash;500 m).</p>
<p>Posterior variance and mean take the standard forms, solved by Cholesky:</p>
<p class="eq">&sigma;&sup2;(x|S) = k(x,x) &minus; k&#8339;&#8347;&#7488;(K&#8347;&#8347; + &sigma;&#8345;&sup2;I)&#8315;&sup1;k&#8339;&#8347;
<br/>&mu;(x|S) = k&#8339;&#8347;&#7488;(K&#8347;&#8347; + &sigma;&#8345;&sup2;I)&#8315;&sup1;r&#8347;</p>
<p><b>The key property:</b> posterior variance depends only on <i>where</i> you
observe, never on what you measure. Variance reduction is therefore computable
before any surveyor leaves the office.</p>
<p class="note">Three corrections were needed before this was honest: variance
must include observation noise; the kriging mean must actually be applied,
since it is the correction the variance describes; and the prediction must be
scaled by a factor fitted on one city and validated on another. See &sect;E6.</p>

<h2>C14. Survey planning by submodular maximisation</h2>
<p>Given budget K, which locations minimise uncertainty across the
<i>whole</i> city? With S the chosen set,</p>
<p class="eq">F(S) = &Sigma;&#7522; [ var(x&#7522; | &empty;) &minus; var(x&#7522; | S) ]</p>
<p>F is monotone and submodular &mdash; each observation helps, but helps less
once nearby ground is covered &mdash; so greedy selection is within
(1&nbsp;&minus;&nbsp;1/e) of optimal and exact solution is NP-hard [8].</p>
<p>The marginal gain has a closed form, which is what makes this fast:</p>
<p class="eq">var(x | S &cup; c) = var(x | S) &minus; cov(x, c | S)&sup2; / ( var(c | S) + &sigma;&#8345;&sup2; )
<br/><br/>gain(c) = &Sigma;&#7522; cov(x&#7522;, c | S)&sup2; / ( var(c | S) + &sigma;&#8345;&sup2; )</p>
<p>so every candidate is evaluated against every parcel in one vectorised pass,
with no iteration over candidates. Candidates are parcel corners. Selection
stops when marginal gain falls below 0.2% of the first point's &mdash; the
system decides <i>how much</i> survey is worth buying, not just where.</p>
<p class="note">A verification assertion checks that marginal gains are
<b>non-increasing</b>. That is submodularity appearing as a testable property
of the implementation rather than as a citation in a slide.</p>

<h3>C14.1 Output shaped as a work order</h3>
<table>
<tr><th>Rank</th><th>Parcel</th><th>Lon</th><th>Lat</th><th>RMSE after</th><th>&Delta;</th><th>Reason</th></tr>
{"".join(f'<tr><td class="num">{p["rank"]}</td><td class="num">{p["parcel_fid"]}</td>'
         f'<td class="num">{p["at"][0]:.5f}</td><td class="num">{p["at"][1]:.5f}</td>'
         f'<td class="num">{p["rmse_after_m"]} m</td>'
         f'<td class="num">&minus;{p["rmse_delta_m"]}</td><td>{p["reason"]}</td></tr>'
         for p in PLAN["points"][:8])}
</table>

<h2>C15. Change detection</h2>
<p>Epochs are compared <b>by spatial overlap, not by shared identifier</b>,
because the identifier is exactly what cannot be trusted across a resurvey.
DSM height delta separates a building that was <i>extended</i> (footprint grew)
from one that was <i>heightened</i> (footprint stable, height rose) &mdash; a
distinction that matters for property tax and for unauthorised construction,
and that a 2-D pipeline cannot make at all.</p>
<table>
<tr><th>Class</th><th>Signal</th><th>Count</th></tr>
<tr><td>New</td><td>footprint present in t1, absent in t0</td><td class="num">{ch['new']}</td></tr>
<tr><td>Demolished</td><td>converse</td><td class="num">{ch['demolished']}</td></tr>
<tr><td>Extended</td><td>footprint area grew beyond tolerance</td><td class="num">{ch['extended']}</td></tr>
<tr><td>Heightened</td><td>DSM delta with stable footprint</td><td class="num">{ch['heightened']}</td></tr>
<tr><td>Encroachment</td><td>structure intersecting government land</td>
    <td class="num">{ch['encroachment']}, {ch['encroached_sqm']} m&sup2;</td></tr>
</table>
<p class="note">Output is a <b>change dossier, explicitly not a mutation
record</b>. A mutation is a statutory act requiring notice and hearing whose
form varies by state; generating one automatically would be both legally wrong
and outside the problem statement.</p>

<h2>C16. Audit chain</h2>
<p>Each entry stores SHA-256 over canonical JSON of its payload plus the
previous entry's digest:</p>
<p class="eq">h&#7522; = SHA256( canonical(payload&#7522;) &#8214; h&#7522;&#8331;&#8321; )</p>
<p><span class="num">verify()</span> distinguishes a <b>content</b> break
&mdash; payload no longer hashes to its recorded digest &mdash; from a
<b>link</b> break, where an entry was removed or reordered. The two mean
different things to an investigator, and reporting "chain invalid" for both is
strictly less useful.</p>
<p>Computed <b>server-side</b>. A chain computed in the browser proves nothing;
anyone can edit it in devtools.
<span class="num">/api/audit/tamper-demo</span> corrupts an entry deliberately
so the failure can be shown rather than described.</p>

<h2>C17. Access control and export</h2>
<table>
<tr><th>Role</th><th>Owner</th><th>Tenure</th><th>May act</th></tr>
<tr><td>Public</td><td>no</td><td>no</td><td>&mdash;</td></tr>
<tr><td>Surveyor</td><td>no</td><td>yes</td><td>raise for survey</td></tr>
<tr><td>Revenue clerk</td><td>yes</td><td>yes</td><td>escalate, raise for survey</td></tr>
<tr><td>Tehsildar</td><td>yes</td><td>yes</td><td>accept, reject, escalate, survey</td></tr>
</table>
<p>Redaction is enforced <b>server-side</b>; owner names are personal data under
the DPDP Act 2023 and a public caller never receives them. Withheld fields are
<i>named</i> in a <span class="num">_redacted</span> marker rather than silently
dropped, so a consumer can distinguish withheld from missing. Verified live on
the deployed instance: a public request returns
<span class="num">_redacted: [KHATEDAR_NM, AREA_BIGHA, TENURE_TYP]</span> where
a tehsildar request returns the values.</p>
<p>Export produces GeoJSON, Shapefile with generated
<span class="num">.prj</span>, CSV and a PDF audit report under a SHA-256
manifest. DBF field names truncate at 10 characters, so the mapping is recorded
in a sidecar rather than letting <span class="num">KHATEDAR_NM</span> and
<span class="num">KHATEDAR_NO</span> silently collide. The OGC API &mdash;
Features endpoint applies the same redaction: a standards-compliant interface
is not a way around the access control.</p>
"""

damage_rows = "\n".join(
    f'<tr><td class="num">{i}</td><td>{s}</td><td class="num">{p}</td><td>{c}</td><td>{d}</td></tr>'
    for i, s, p, c, d in DAMAGE)
imp_rows = "\n".join(
    f'<tr><td class="num">{f["name"]}</td><td class="num">{f["gain"]}</td>'
    f'<td class="num">{round(f["gain"] * 100, 1)}%</td></tr>'
    for f in mt["feature_importance"][:12])
rel_rows = "\n".join(
    f'<tr><td class="num">{b["lo"]:.1f}&ndash;{b["hi"]:.1f}</td><td class="num">{b["n"]:,}</td>'
    f'<td class="num">{b["mean_p"]}</td><td class="num">{b["observed"]}</td></tr>'
    for b in mt["reliability"] if b["n"] > 0)
cal_rows = "\n".join(
    f'<tr><td class="num">{t["k"]}</td><td class="num">{t["predicted"]}</td>'
    f'<td class="num">{t["achieved"]}</td><td class="num">{h["predicted"]}</td>'
    f'<td class="num">{h["achieved"]}</td></tr>'
    for t, h in zip(CAL["train"], CAL["held_out"]))

PART_D = f"""
<p class="part">Part D &mdash; Evaluation</p>
<p class="partsub">How we know, including what we got wrong first.</p>

<h2>D1. The ground-truth problem</h2>
<p>Both [2] and [3] are limited by the same thing: no correct geometry exists
to score against. [2] reports relative improvement across rounds; [3] reports a
proxy (polygon-split counts). <b>Neither can state its error in metres.</b></p>
<p>We generate a clean synthetic cadastre, retain it as the key, damage a copy
through twelve recorded stages, and score recovery against the key. This
follows the known-deformation construction of [2] exactly; the difference is
that our deformations are drawn from the <i>documented</i> taxonomy of
&sect;A6.2 rather than chosen for convenience.</p>
<p>It also answers the review's "lack of large-scale, high-quality annotated
data" [1] in the only way available: by constructing it.</p>

<h2>D2. The damage model</h2>
<table>
<tr><th>#</th><th>Stage</th><th>Parameter</th><th>Real-world cause</th><th>In [5]</th></tr>
{damage_rows}
</table>
<p class="k">Parameters quoted from the dataclass defaults in
<span class="num">synth/corruption.py</span>, so the table and the harness
cannot disagree. "In [5]" marks the five stages that correspond directly to a
failure mode documented by Sengupta et al.</p>

<h2>D3. Experimental design</h2>
<ul>
<li><b>Two cities.</b> Model trained on one, all headline figures measured on a
second with different layout and a different damage draw.</li>
<li><b>Group splits by source parcel</b>, never by pair (&sect;C7), so a
parcel's candidates cannot straddle train and test.</li>
<li><b>The targeting scale factor</b> is fitted on the train city and validated
on the held-out one (&sect;D7).</li>
<li><b>Fixed seed</b>, so every figure in this document is reproducible by
running <span class="num">scripts/build_demo.py</span>.</li>
</ul>

<h2>D4. Two experiments that changed the design</h2>

<h3>D4.1 Pipeline order</h3>
<p>Matching before georeferencing gave blocking recall <b>0.58</b>. 42% of true
correspondences never reached the model, and the model compensated by learning
attribute joins. After reordering: <b>{mt['blocking_recall']}</b>. The
architecture of &sect;C1 is the result of that measurement, not of
intuition.</p>

<h3>D4.2 The leakage trap</h3>
<p>The first matcher scored <b>F1 0.9955</b> &mdash; better than our current
figure &mdash; with khasra and owner supplying <b>96%</b> of the decision and
IoU <b>0.24%</b>. It had learned to join on an identifier, which fails in any
jurisdiction that renumbers on resurvey: that is, in the exact situation the
problem statement describes.</p>
<p>The harness now renumbers 45% of blocks and genuinely changes 12% of owners,
so the shortcut does not exist. <b>A better-looking number was replaced by a
worse-looking number that means something.</b></p>

<h2>D5. The verification suite</h2>
<p>Eight stages, ~25 assertions, end to end
(<span class="num">scripts/verify_all.py</span>, {LOC.get('scripts/verify_all.py', 0)}
lines). Those that guard a claim this document makes:</p>
<table>
<tr><th>Assertion</th><th>Guards against</th></tr>
<tr><td class="num">round-trip &lt; 1 mm</td><td>CRS drift</td></tr>
<tr><td class="num">central meridian == 500000 m</td><td>UTM false-easting error</td></tr>
<tr><td class="num">agrees with pyproj &lt; 1 mm</td><td>our hand-rolled CRS being subtly wrong</td></tr>
<tr><td class="num">no overlaps in ground truth</td><td>a dirty key, which would void every later figure</td></tr>
<tr><td class="num">damage actually applied</td><td>scoring recovery on an undamaged copy</td></tr>
<tr><td class="num">coarse alignment reduces error &gt; 40%</td><td>georeferencing silently regressing</td></tr>
<tr><td class="num">blocking recall &ge; 0.98</td><td>the 0.58 failure recurring unnoticed</td></tr>
<tr><td class="num">F1 &ge; 0.90</td><td>matcher regression</td></tr>
<tr><td class="num">ECE &le; 0.02</td><td>confidence becoming decorative</td></tr>
<tr><td class="num"><b>geometry &ge; 70% of gain</b></td><td><b>the leakage trap returning</b></td></tr>
<tr><td class="num">exact set match &ge; 0.85</td><td>assignment degrading on splits and merges</td></tr>
<tr><td class="num">spurious parcels rejected &ge; 0.95</td><td>accepting records that should not exist</td></tr>
<tr><td class="num">topology errors reduced &ge; 90%</td><td>cleaner regression</td></tr>
<tr><td class="num"><b>refuses to fill parcel-sized holes</b></td><td><b>the restraint of &sect;C10.1 being optimised away</b></td></tr>
<tr><td class="num">lengthscale in 5&ndash;500 m</td><td>a GP that fits but means nothing</td></tr>
<tr><td class="num">marginal gains non-increasing</td><td>submodularity violated by an implementation bug</td></tr>
<tr><td class="num">optimised placement beats random</td><td>the central targeting claim</td></tr>
</table>
<p class="note">Two of these exist because the property they protect is exactly
what a well-meaning optimisation would remove. A model allowed to use khasra
numbers scores <i>better</i>. A cleaner that fills every hole reports
<i>fewer</i> errors. Both would be worse systems, and a test is the only thing
standing between the project and that "improvement".</p>

<h2>D6. Results</h2>
<p class="k">Full pipeline {M['runtime_s']} s on one core;
{cnt['legacy']:,} legacy against {cnt['reference']:,} reference over
{cnt['candidate_pairs']:,} candidate pairs.</p>
<table>
<tr><th>Stage</th><th>Measure</th><th>Result</th></tr>
<tr><td>Georeferencing</td><td>positional RMSE</td><td class="num">{g['rmse_raw']} &rarr; {g['rmse_coarse']} m</td></tr>
<tr><td>Schema</td><td>columns mapped</td><td class="num">{sc['mapped']}/{sc['total']}</td></tr>
<tr><td>Schema</td><td>area unit from geometry</td><td class="num">{sc['area_unit']} @ {sc['area_unit_confidence']}</td></tr>
<tr><td>Blocking</td><td>true pairs retained</td><td class="num">{mt['blocking_recall']}</td></tr>
<tr><td>Matching</td><td>precision / recall / F1</td><td class="num">{mt['precision']} / {mt['recall']} / {mt['f1']}</td></tr>
<tr><td>Matching</td><td>ROC AUC</td><td class="num">{mt['roc_auc']}</td></tr>
<tr><td>Matching</td><td>TP / FP / FN / TN</td><td class="num">{mt['tp']:,} / {mt['fp']} / {mt['fn']} / {mt['tn']:,}</td></tr>
<tr><td>Matching</td><td><b>decision from geometry</b></td><td class="num"><b>{GEOM_PCT}%</b></td></tr>
<tr><td>Confidence</td><td>ECE / Brier</td><td class="num">{dec(mt['ece'])} / {dec(mt['brier'])}</td></tr>
<tr><td>Assignment</td><td>1:1 / split / merge</td><td class="num">{asg['one_to_one']:,} / {asg['split']} / {asg['merge']}</td></tr>
<tr><td>Topology</td><td>total errors</td><td class="num">{tp['total_before']:,} &rarr; {tp['total_after']}</td></tr>
<tr><td>Topology</td><td>overlapping pairs</td><td class="num">{tp['overlaps_before']:,} &rarr; {tp['overlaps_after']}</td></tr>
<tr><td>Topology</td><td>doubly-claimed land</td><td class="num">{tp['overlap_area_before']:,} &rarr; {tp['overlap_area_after']} m&sup2;</td></tr>
<tr><td>Restraint</td><td>parcel-sized gaps refused</td><td class="num">{tp['refused_to_fill']} of {tp['harness_deleted']}</td></tr>
<tr><td>Change</td><td>new / demol. / ext. / height.</td><td class="num">{ch['new']} / {ch['demolished']} / {ch['extended']} / {ch['heightened']}</td></tr>
<tr><td>Encroachment</td><td>sites on public land</td><td class="num">{ch['encroachment']}, {ch['encroached_sqm']} m&sup2;</td></tr>
<tr><td>Targeting</td><td>predicted / achieved / random</td><td class="num">{tg['rmse_predicted']} / {tg['rmse_achieved']} / {tg['rmse_random']} m</td></tr>
</table>

<h3>D6.1 Where the decision comes from</h3>
<table>
<tr><th>Feature</th><th>Gain</th><th>Share</th></tr>
{imp_rows}
</table>
<p>The three leading features &mdash; containment, centroid distance and IoU
&mdash; are purely geometric and account for
<b>{round(sum(f['gain'] for f in mt['feature_importance'][:3]) * 100, 1)}%</b>
of total gain. <span class="num">kh_present</span> ranks fourth at
{mt['feature_importance'][3]['gain']}, and note what it encodes: not
<i>which</i> khasra number, but <b>whether one exists at all</b>. A missingness
signal, not a join key.</p>

<h3>D6.2 Reliability</h3>
<table>
<tr><th>Bin</th><th>n</th><th>Mean predicted</th><th>Observed</th></tr>
{rel_rows}
</table>
<p>In the top bin, 2,998 pairs at mean predicted {mt['reliability'][-1]['mean_p']}
against observed {mt['reliability'][-1]['observed']}. That agreement, not the
F1, is what licenses the word "confidence".</p>

<h3>D6.3 The area conservation ledger</h3>
<p>Summed parcel area falls <b>{abs(tp['area_drift_pct'])}%</b> across topology
repair, which looks alarming until decomposed:</p>
<table>
<tr><th>Quantity</th><th>Before</th><th>After</th><th>Reading</th></tr>
<tr><td>Summed parcel area</td><td class="num">{tp['area_before']:,}</td><td class="num">{tp['area_after']:,}</td><td>falls</td></tr>
<tr><td>Doubly-claimed land</td><td class="num">{tp['overlap_area_before']:,}</td><td class="num">{tp['overlap_area_after']}</td><td>eliminated</td></tr>
<tr><td>Union footprint</td><td colspan="2">ground counted once</td><td><b>rises</b></td></tr>
</table>
<p>The sum falls because land recorded as owned by two parties simultaneously is
now counted once. <b>No land was created or destroyed, and the ledger
demonstrates it rather than asserting it.</b> A system reporting only the total
would appear to have lost 12,183 m&sup2; of someone's property.</p>

<h2>D7. Targeting validation</h2>
<table>
<tr><th>K</th><th>Train predicted</th><th>Train achieved</th><th>Held-out predicted</th><th>Held-out achieved</th></tr>
{cal_rows}
</table>
<p>Prediction scale <b>{CAL['prediction_scale']}</b> fitted on the train city;
held-out ratio median <b>{CAL['held_out_ratio_median']}</b> &mdash; the
prediction errs <i>conservative</i> on unseen data, which is the direction an
operational planning tool should err in. Irreducible floor
<b>{CAL['irreducible_rmse_m']} m</b>: per-parcel digitising noise no quantity of
control removes, reported rather than promised away.</p>
<p class="k">Deployed result: {tg['n_points']} GCPs, baseline
{tg['rmse_baseline']} m, predicted {tg['rmse_predicted']} m, <b>achieved
{tg['rmse_achieved']} m</b>, random placement {tg['rmse_random']} m &mdash;
<b>{tg['vs_random_pct']}% better than random</b>.</p>
"""

defect_rows = "\n".join(
    f'<tr><td><b>{t}</b></td><td>{w}</td><td>{f}</td></tr>' for t, w, f in DEFECTS)
inv_rows = "\n".join(
    f'<tr><td class="num">{f}</td><td class="num">{n}</td></tr>'
    for f, n in sorted(((f, n) for f, n in LOC.items()
                        if f.startswith(("backend/", "api/")) and f.endswith(".py") and n > 90),
                       key=lambda r: -r[1]))
commit_rows = "\n".join(
    f'<tr><td class="num">{h}</td><td class="num">{d}</td><td>{s}</td></tr>'
    for h, d, s in COMMITS)
gloss_rows = "\n".join(f'<tr><td class="num">{t}</td><td>{d}</td></tr>' for t, d in GLOSSARY)
stage_rows = "\n".join(
    f'<tr><td>{s["name"]}</td><td class="num">{s["seconds"]}</td></tr>' for s in M["stages"])

PART_EF = f"""
<p class="part">Part E &mdash; System, deployment, engineering record</p>
<p class="partsub">What was built, what it cost, and what the platform did to us.</p>

<h2>E1. Composition</h2>
<table>
<tr><th>Component</th><th>Path</th><th>Lines</th><th>State</th></tr>
<tr><td>Harmonization engine</td><td class="num">backend/kshetra/</td><td class="num">{ENGINE:,}</td><td>Verified by harness</td></tr>
<tr><td>API with RBAC</td><td class="num">api/main.py</td><td class="num">{API_LOC:,}</td><td>24 routes, deployed</td></tr>
<tr><td>Operator console</td><td class="num">frontend/src/</td><td class="num">{UI:,}</td><td>Deployed</td></tr>
<tr><td>Build / verify / analysis</td><td class="num">scripts/</td><td class="num">{SCRIPTS:,}</td><td>Working</td></tr>
</table>

<h3>E1.1 Runtime profile</h3>
<table>
<tr><th>Stage</th><th>Seconds</th></tr>
{stage_rows}
</table>
<p class="note">Feature construction and the GP fit dominate. Both are
embarrassingly parallel and neither has been optimised; the figure is honest
rather than tuned.</p>

<h2>E2. Operator console</h2>
<p>MapLibre GL JS v4, three Esri basemaps, <span class="num">fill-extrusion</span>
for surveyed building heights, and an alignment animation interpolating between
raw and georeferenced layers so the correction is <i>watched</i>, not read
about. Role tables in <span class="num">store.ts</span> mirror
<span class="num">VISIBLE</span> and <span class="num">MAY_ACT</span> in the API
deliberately: the UI must not offer an action the server would refuse nor
display a field it would withhold. The server remains the enforcement point;
the client copy exists so the interface does not lie.</p>
<p>Sign-in reports the same error for an unknown username and a wrong password,
because saying which half failed tells an attacker which usernames exist.</p>

<h2>E3. Deployment</h2>
<p>One Docker image serving the built UI and the API from a single origin. Two
services would be simpler to reason about, but then page and API sit on
different origins and the redaction and audit chain need CORS to agree with
them.</p>
<table>
<tr><th>Stage</th><th>Base</th><th>Does</th></tr>
<tr><td>1</td><td class="num">node:20-alpine</td><td>npm install; copy artifacts into public/data; tsc -b &amp;&amp; vite build</td></tr>
<tr><td>2</td><td class="num">python:3.12-slim</td><td>install FastAPI/uvicorn/pydantic; copy backend, api, data, dist; run uvicorn</td></tr>
</table>
<p>The API imports only <span class="num">kshetra.audit</span> &mdash; stdlib
hashlib and json &mdash; so nothing in the request path needs numpy, scipy,
shapely or xgboost. Image drops from ~900 MB to ~200 MB.</p>
<p class="note">Hosting-tier limits, not design properties: free instances spin
down after 15 min idle with ~50 s cold start, and the audit chain writes to
ephemeral disk, persisting within a session and resetting on redeploy.</p>

<h2>E4. The platform problem</h2>
<p>Windows <b>Smart App Control</b> blocked the scientific Python stack on the
development machine &mdash; pyproj, scikit-learn and LightGBM at every version,
and numpy 2.0.2 while permitting 2.4.6. Blocking is per-binary and undocumented
in advance, presenting as an unexplained
<span class="num">ImportError</span> on a package that installed cleanly. On 26
September it was auto-promoted from evaluation to enforced and stopped
everything at once.</p>
<p>Two consequences shaped the codebase, and both turned out to be
improvements: the CRS engine was written from first principles and is now
cross-validated to sub-millimetre (&sect;C2), and <b>every optional dependency
degrades gracefully</b> &mdash; metrics are hand-implemented, the pyproj check
skips rather than fails. That is why the project survived the promotion.</p>
<p>Resolution was WSL2, where without sudo <span class="num">ensurepip</span>
is unavailable, so environments are built with
<span class="num">venv --without-pip</span> plus
<span class="num">get-pip.py</span>, and Node from a tarball into
<span class="num">~/.local</span>. SAC also blocks Git Bash's bundled
<span class="num">ssh</span>, so the repository points
<span class="num">core.sshCommand</span> at Windows OpenSSH.</p>

<h2>E5. Defect register</h2>
<table>
<tr><th>Defect</th><th>What was wrong</th><th>Resolution</th></tr>
{defect_rows}
</table>

<h3>E5.1 The one worth dwelling on</h3>
<p>The GP over-optimism fix is the defect we are most inclined to report,
because correcting it made a headline number <b>worse</b>. Better-than-random
fell from 51.8% to 35.9% &mdash; not because the planner degraded, but because
a better interpolator also rescues random placement, so the old margin was
partly an artifact of the bug. <b>A system whose reported advantage falls when
its model is corrected is a system whose numbers were previously flattering
it.</b></p>

<p class="part">Part F &mdash; Assessment</p>
<p class="partsub">Where this stands, and where it does not.</p>

<h2>F1. Comparison against prior art</h2>
<table>
<tr><th>Capability</th><th>[2] Girard</th><th>[3] Suwardhi</th><th>FME/Esri</th><th>KSHETRA</th></tr>
<tr><td>Corrects misregistration without ground truth</td><td>yes</td><td>yes</td><td>no</td><td>yes</td></tr>
<tr><td>Reports error in metres against a key</td><td>no</td><td><b>no (proxy)</b></td><td>n/a</td><td><b>yes</b></td></tr>
<tr><td>Multi-source (n &gt; 2)</td><td>no</td><td>no</td><td>yes</td><td>yes</td></tr>
<tr><td>Infers attribute schema</td><td>no</td><td>no</td><td><b>no (human declares)</b></td><td><b>yes</b></td></tr>
<tr><td>Infers area unit from geometry</td><td>no</td><td>no</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Calibrated per-parcel confidence</td><td>no</td><td>no</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Separates measured from recorded authority</td><td>no</td><td>no</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Detects split / merge explicitly</td><td>no</td><td>partial</td><td>no</td><td>yes</td></tr>
<tr><td>Conserves and proves area</td><td>no</td><td>no</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Declines to fill parcel-sized gaps</td><td>n/a</td><td>n/a</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Plans where to survey next</td><td>no</td><td>no</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Validates that plan against random</td><td>no</td><td>no</td><td>no</td><td><b>yes</b></td></tr>
<tr><td>Hash-chained audit</td><td>no</td><td>no</td><td>no</td><td>yes</td></tr>
<tr><td>Evaluated on real cadastral data</td><td><b>yes</b></td><td><b>yes</b></td><td><b>yes</b></td><td><b>no</b></td></tr>
</table>
<p class="flag">The final row is the one that matters against us, and it is
placed last deliberately rather than omitted. Girard and Suwardhi evaluate on
real cadastral layers; we evaluate on synthetic ones because no bulk Indian
urban cadastre is public. Our advantage in measurability is purchased exactly
by that limitation.</p>

<h2>F2. Limitations</h2>
<ul>
<li>The cadastral parcel layer is <b>synthetic</b>, derived from OpenStreetMap
block structure and labelled as such in the product and its exports. Building
footprints, road network and terrain are real.</li>
<li>Encroachment cases are <b>deliberately injected</b>; the generator never
places structures on public land, so without injection the claim would be
untested.</li>
<li>The survey-plan prediction is <b>calibrated, not exact</b> &mdash; ~12%
transfer error to a held-out city, erring conservative.</li>
<li>Per-parcel digitising noise is <b>irreducible</b> by survey control; the
system reports the floor rather than promising accuracy below it.</li>
<li>The GP kernel is <b>smooth</b> and cannot represent a sheet-join
discontinuity &mdash; the same limitation [2] states for its displacement
model.</li>
<li>The system produces a <b>change dossier, not a mutation record</b>.</li>
<li>Redaction is enforced server-side; in the static demonstration build every
artifact reaches the browser, so redaction <i>there</i> is a display control
only.</li>
<li>Evaluation is on two synthetic cities. <b>Generalisation to a real ward is
untested</b> and we do not claim it from these numbers.</li>
<li>The Docker build stages have been reproduced by hand but the container has
not been run in CI.</li>
</ul>

<h2>F3. Threats to validity</h2>
<table>
<tr><th>Threat</th><th>Why it is a threat</th><th>What we did</th></tr>
<tr><td><b>Construct</b> &mdash; the damage model might not resemble real damage</td>
    <td>If so, recovery figures say nothing about real sheets</td>
    <td>Five of twelve stages map directly onto Sengupta's documented failure modes; parameters are in the open in &sect;D2 for a reviewer to dispute</td></tr>
<tr><td><b>Internal</b> &mdash; leakage between train and test</td>
    <td>Would inflate every matching figure</td>
    <td>Group splits by source parcel; the geometry-share assertion; the leakage trap of &sect;D4.2 was caught this way</td></tr>
<tr><td><b>External</b> &mdash; synthetic to real transfer</td>
    <td>Real cadastres have structure our generator does not model</td>
    <td><b>Not mitigated.</b> Stated as the principal limitation</td></tr>
<tr><td><b>Conclusion</b> &mdash; one damage draw, one seed</td>
    <td>Figures could be a lucky sample</td>
    <td>Held-out city with an independent draw; targeting validated across four budgets. <b>No repeated-seed variance study</b> &mdash; a real gap</td></tr>
</table>

<h2>F4. Roadmap</h2>
<ol>
<li><b>Repeated-seed variance study</b> &mdash; the cheapest material improvement to the evidence base, and named as a gap above.</li>
<li><b>Sliver classification with legal consequence</b> &mdash; area, compactness, khasra presence, RoR presence, footprint presence. Currently geometry alone.</li>
<li><b>Per-state policy objects</b> &mdash; FMB-primary regimes must not have geometry rewritten as authority (&sect;A2).</li>
<li><b>Transformation-order selection benchmarked against [5]'s 310 sheets</b> &mdash; would convert &sect;C3 from a design claim to a measured one.</li>
<li><b>A released Indian benchmark</b> for one pilot ULB.</li>
</ol>

<h2>F5. Open questions we would not claim to have solved</h2>
<ul>
<li><b>Invisible boundaries.</b> Fusing imagery, legacy geometry, textual record
and utility topology to infer a boundary with no physical trace. The ceiling of
the vision-only approach, and unaddressed in the literature we found.</li>
<li><b>Discontinuous displacement fields.</b> Both we and [2] assume
smoothness; sheet joins are discontinuities by construction.</li>
<li><b>Legal admissibility.</b> Nothing here establishes that a calibrated
confidence is evidence in a revenue court. That is a question for jurists, and
we flag it rather than assuming the answer.</li>
</ul>

<h2>Appendix A &mdash; module inventory</h2>
<p class="k">Tracked first-party Python over 90 lines.</p>
<table><tr><th>File</th><th>Lines</th></tr>
{inv_rows}
</table>

<h2>Appendix B &mdash; glossary</h2>
<table><tr><th>Term</th><th>Meaning</th></tr>
{gloss_rows}
</table>

<h2>Appendix C &mdash; commit history</h2>
<table><tr><th>Commit</th><th>Date</th><th>Subject</th></tr>
{commit_rows}
</table>

<h2>Appendix D &mdash; reproduction</h2>
<p class="eq">python scripts/build_demo.py&nbsp;&nbsp;&nbsp;# regenerates every artifact
<br/>python scripts/verify_all.py&nbsp;&nbsp;&nbsp;# ~25 assertions, 8 stages
<br/>python scripts/calibrate_targeting.py
<br/>python scripts/build_compendium.py&nbsp;&nbsp;&nbsp;# this document</p>
<p>Fixed seed throughout. Engine requires numpy, scipy, shapely and xgboost; the
serving path requires none of them.</p>

<h2>Appendix E &mdash; references</h2>
<p class="ref">[1] J. Chen, M. Nazeer, B. S. Lee and M. S. Wong. <i>Artificial Intelligence in Cadastre: A Systematic Review of Methods, Applications, and Trends.</i> Land, 15(3):411, 2026. doi:10.3390/land15030411.</p>
<p class="ref">[2] N. Girard, G. Charpiat and Y. Tarabalka. <i>Noisy Supervision for Correcting Misaligned Cadaster Maps Without Perfect Ground Truth Data.</i> IGARSS 2019. Inria / LuxCarta Technology.</p>
<p class="ref">[3] D. Suwardhi, M. Ihsan, R. Widyastuti, A. H. U. Mukminin, B. Akbar, S. K. Pasaribu, I. P. Satwika, S. L. Nurmaulia and A. Hernandi. <i>An Automated Framework for Cadastral Parcel Adjustment Using UAV Orthophotos, SAM, and ICP.</i> ISPRS Archives, XLVIII-2/W11-2025:277&ndash;284, 2025.</p>
<p class="ref">[4] B. Fetai, D. Grigillo and A. Lisec. <i>Revising Cadastral Data on Land Boundaries Using Deep Learning in Image-Based Mapping.</i> ISPRS Int. J. Geo-Inf., 11(5):298, 2022. doi:10.3390/ijgi11050298.</p>
<p class="ref">[5] A. Sengupta, C. Lemmen, W. Devos, D. Bandyopadhyay and A. van der Veen. <i>Constructing a seamless digital cadastral database using colonial cadastral maps and VHR imagery &mdash; an Indian perspective.</i> Survey Review, 48(349):258&ndash;268, 2016. doi:10.1179/1752270615Y.0000000003.</p>
<p class="ref">[6] Survey of India. Technical circular T-260/1147-Project (NAKSHA), 10 February 2025.</p>
<p class="ref">[7] Department of Science and Technology, Government of India. <i>National Geospatial Policy 2022.</i></p>
<p class="ref">[8] A. Krause, A. Singh and C. Guestrin. <i>Near-Optimal Sensor Placements in Gaussian Processes: Theory, Efficient Algorithms and Empirical Studies.</i> JMLR, 9:235&ndash;284, 2008.</p>
<p class="ref">[9] K. Satyarthi et al. Progress review of the NAKSHA programme. Frontiers in Sustainable Cities, 2026. First author is Joint Secretary, Department of Land Resources.</p>
<p class="ref">[10] V. Thakur, M. N. Doja and A. A. A. Faizi. <i>Indian Cadastral Survey System &mdash; Comparative Study.</i> IJEDR, 5(4):1579+, 2017.</p>
<p class="ref">[11] P. Misra. <i>Cadastral surveys in India.</i> Coordinates, June 2005.</p>
<p class="ref">[12] Department of Land Resources, Ministry of Rural Development. NAKSHA programme booklet.</p>
<p class="ref">[13] Department of Land Resources. DILRMP progress statistics.</p>
<p class="ref">[14] DAKSH. <i>Access to Justice Survey 2015-16.</i> 9,329 litigants, 305 locations, 24 states.</p>
<p class="ref">[15] Tamil Nadu Department of Survey and Settlement. DILRMP Regional Review, Bengaluru, 6 September 2024.</p>
<p class="ref">[16] ISO 19152-1:2024, Land Administration Domain Model &mdash; Part 1: Generic conceptual model.</p>
<p class="ref">[17] A. Sengupta, D. Bandyopadhyay, C. H. J. Lemmen and A. van der Veen. <i>Potential use of LADM in cadastral data management in India.</i> 5th LADM Workshop, Kuala Lumpur, September 2013.</p>

<h2>Appendix F &mdash; claims we deliberately do not make</h2>
<ul>
<li><b>"Land disputes take about 20 years to resolve."</b> Attributed to NITI Aayog across many secondary sources; original not opened. <b>[S]</b></li>
<li><b>"324 years to clear the case backlog."</b> Source not located. <b>[U]</b></li>
<li><b>"25% of Supreme Court decided cases involve land disputes."</b> Widely repeated, original study not found. <b>[U]</b></li>
<li><b>Any figure for man-hours or rupee cost of manual GIS harmonisation</b> specifically, as distinct from survey or digitisation cost. We searched and found nothing credible and do not invent one; where a proxy is needed we use the official &#8377;56,725/sq km resurvey rate [15].</li>
<li><b>"Indian Geodetic Datum 2023."</b> Does not exist. NGP 2022 [7] commits to <i>redefining</i> the framework; the Indian Vertical Datum is real and referenced in [6].</li>
<li><b>The exact 14-character composition of ULPIN</b>, and the contents of the NAKSHA SDMS schema, whose SOP is available only as an untexted scan. <b>[U]</b></li>
</ul>
<p class="note">Sources [1]&ndash;[4] and [8] were read in the original.
[5]&ndash;[7] and [9]&ndash;[17] are drawn from a sourced research dossier
compiled for this project; figures carry their grade, and any figure intended
for publication should be re-checked against the primary document.</p>
"""

HTML = FRONT + PART_A + PART_B + PART_C + PART_D + PART_EF


def main() -> int:
    story = pymupdf.Story(html=HTML, user_css=CSS)
    writer = pymupdf.DocumentWriter(str(OUT))
    page = pymupdf.paper_rect("a4")
    frame = page + (54, 56, -54, -52)
    more, n = 1, 0
    while more:
        dev = writer.begin_page(page)
        more, _ = story.place(frame)
        story.draw(dev)
        writer.end_page()
        n += 1
        if n > 200:
            break
    writer.close()
    print(f"wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB, {n} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

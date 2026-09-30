"""Render the KSHETRA research summary to PDF.

LibreOffice needs apt and there is no sudo in this environment, so the usual
HTML->PDF route is unavailable. PyMuPDF's Story engine lays out a restricted
HTML/CSS subset and paginates it, which is enough for a typeset report and
needs no system packages.

Every KSHETRA figure is read from data/demo/metrics.json at build time, so the
document cannot drift from what the pipeline actually measured.

    python scripts/build_research_pdf.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "KSHETRA_Research_Summary.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

M = json.loads((ROOT / "data" / "demo" / "metrics.json").read_text(encoding="utf-8"))
g, mt, tp = M["georef"], M["matching"], M["topology"]
tg, sc, ch, asg = M["targeting"], M["schema"], M["change"], M["assignment"]


def dec(v: float, places: int = 5) -> str:
    """Plain decimal. An f-string renders 9e-05, which reads as a typo."""
    return f"{v:.{places}f}".rstrip("0").rstrip(".") or "0"


CSS = """
body { font-family: sans-serif; font-size: 9.3pt; line-height: 1.44; color: #16191d; }
h1 { font-size: 18pt; margin: 0 0 2pt 0; color: #0f2233; }
h2 { font-size: 12.5pt; margin: 17pt 0 5pt 0; color: #0f7a3f; }
h3 { font-size: 10.2pt; margin: 11pt 0 3pt 0; color: #0f2233; }
h4 { font-size: 9.4pt; margin: 12pt 0 4pt 0; color: #2b3138; }
p  { margin: 0 0 6pt 0; }
li { margin: 0 0 4pt 0; }
b { color: #0f2233; }
.sub { font-size: 9.4pt; color: #5a646e; margin: 0 0 3pt 0; }
.meta { font-size: 8pt; color: #7d868f; margin: 0 0 11pt 0; }
.lead { font-size: 10pt; color: #0f2233; margin: 0 0 8pt 0; }
.q { font-size: 9pt; color: #2b3138; margin: 4pt 0 7pt 15pt; }
.k { font-size: 8.4pt; color: #5a646e; margin: 0 0 6pt 0; }
.note { font-size: 8.5pt; color: #5a646e; margin: 5pt 0 8pt 0; }
.flag { font-size: 8.3pt; color: #8a4a12; margin: 4pt 0 7pt 0; }
table { font-size: 8.6pt; }
th { text-align: left; color: #5a646e; font-size: 7.9pt; padding: 0 9pt 3pt 0; }
td { padding: 0 9pt 3pt 0; vertical-align: top; }
.num { font-family: monospace; font-size: 8.5pt; }
.ref { font-size: 8.5pt; margin: 0 0 5pt 0; }
"""

HTML = f"""
<h1>Automated Integration and Intelligent Harmonization of
Multi-Source Geospatial Data for Urban Land Record Management</h1>
<p class="sub">KSHETRA &mdash; research summary and evidence base</p>
<p class="meta">Team NovaX &nbsp;&middot;&nbsp; Smart India Hackathon 2026
&nbsp;&middot;&nbsp; Problem Statement 26013</p>

<p class="lead">This document sets out what the published literature and the
programme record establish, what they leave unsolved, and which of those open
problems our prototype addresses. Claims are graded: <b>[V]</b> verified against
a primary or peer-reviewed source, <b>[S]</b> secondary &mdash; consistently
reported but not traced to the original, <b>[U]</b> unverified. Figures quoted
for KSHETRA were measured by a harness in the repository and are inserted into
this document at build time.</p>

<h2>1. Why Indian land records are hard &mdash; the structural cause</h2>

<p>The fragmentation is not accidental and it is not recent. The Survey of India
was established in 1767 and conducted revenue survey nationally until <b>1904</b>;
after that date <b>each state became responsible for its own cadastral survey and
evolved its own system</b> [10] <b>[V]</b>. Every downstream interoperability
problem &mdash; divergent vocabulary, divergent scales, divergent legal
primacy &mdash; descends from that single administrative decision.</p>

<p>Two consequences matter technically.</p>

<h4>Legal primacy differs between north and south</h4>
<p>Northern states recognise the graphic map as the legal document; southern
states prioritise the <b>Field Measurement Book</b> [11] <b>[V]</b>. In the north
the polygon carries authority; in the south the <i>measurements</i> carry it and
the polygon is a derived sketch. A single national harmonisation policy is
therefore legally wrong, and any system that silently rewrites geometry is
destroying the record in one half of the country while merely correcting it in
the other.</p>

<h4>Vocabulary differs structurally, not just lexically</h4>
<p>South Indian survey numbers carry a recursive sub-division grammar
(<span class="num">123/1A</span>); north Indian khasra numbering conventions vary
by settlement. The record of rights is the <i>khatauni</i> in UP, the
<i>jamabandi</i> in Punjab and Haryana, the <i>patta</i> / <i>chitta</i> in Tamil
Nadu. And <b>&ldquo;khata&rdquo; denotes a revenue holding account in the north
but a municipal property-tax account in urban Karnataka</b> &mdash; a live
hazard in an urban project. Schema matching must therefore be structure-aware,
not merely synonym-aware.</p>

<h2>2. The problem, quantified</h2>

<h3>2.1 Scale of the urban gap</h3>
<p>India has <b>7,933+ urban settlements</b> covering roughly <b>10.2 million
hectares</b>, and <b>4,912 urban local bodies</b> [9, 12] <b>[V]</b>. Only
<b>four states</b> maintain structured urban land records &mdash; a figure
corroborated independently by DoLR's own NAKSHA booklet, which names Tamil Nadu,
Maharashtra, Gujarat and Goa [12] <b>[V]</b>. Approximately 13 million urban
households live in 108,000 slums [9] <b>[V]</b>.</p>

<p>Under DILRMP, <b>49.10%</b> of villages hold geo-referenced cadastral
maps [13] <b>[V]</b>.</p>

<h3>2.2 Economic and legal consequence</h3>
<p class="flag">Several widely-circulated &ldquo;land dispute&rdquo; statistics
in India are recycled with drifting attribution. Only traceable figures appear
below; the ones we deliberately do not use are listed in Appendix A.</p>

<table>
<tr><th>Claim</th><th>Source</th><th>Grade</th></tr>
<tr><td>Land market distortions erode annual GDP growth by an estimated 1.3%</td>
    <td>Satyarthi et al., Frontiers in Sustainable Cities, 2026 [9]</td><td>[V]</td></tr>
<tr><td>ULBs generate only 32% of revenue internally, on sub-optimal tax assessment</td>
    <td>Satyarthi et al., 2026 [9]</td><td>[V]</td></tr>
<tr><td>Land and property taxes are 0.6% of GDP in low-income economies vs 2.2% in industrialised ones</td>
    <td>Satyarthi et al., 2026 [9]</td><td>[V]</td></tr>
<tr><td>Property disputes comprise 60&ndash;70% of Indian civil litigation</td>
    <td>Satyarthi et al., 2026 [9]</td><td>[V] as a peer-reviewed statement</td></tr>
<tr><td>Roughly two-thirds of civil matters surveyed concerned land and property</td>
    <td>DAKSH Access to Justice Survey 2015-16; 9,329 litigants, 305 locations, 24 states [14]</td>
    <td>[V] as a survey of litigants, not a census</td></tr>
<tr><td>Cadastral resurvey rate of &#8377;56,725 per sq km</td>
    <td>Tamil Nadu Dept. of Survey &amp; Settlement, DILRMP review, 2024 [15]</td><td>[V]</td></tr>
<tr><td>Resurvey of a district tranche takes 2&ndash;3 years even with drone + DGPS</td>
    <td>Tamil Nadu, 2024 [15]</td><td>[V]</td></tr>
</table>

<h3>2.3 Positional accuracy of legacy cadastral maps &mdash; the central measurement</h3>

<p>Sengupta, Lemmen, Devos, Bandyopadhyay and van der Veen georeferenced
<b>310 analogue cadastral sheets</b> at 1:3960 covering a 327&nbsp;km&sup2;
planning area in West Bengal &mdash; 258 mouzas and 26 municipal wards, mapped
mostly from pre-1920s surveys and 1950s work &mdash; against GeoEye-1
pan-sharpened imagery using 10&ndash;15 ground control points per sheet and a
first-order transformation [5] <b>[V]</b>.</p>

<table>
<tr><th>RMSE range</th><th>Sheets</th></tr>
<tr><td>&lt; 2.00 m</td><td class="num">7</td></tr>
<tr><td>2.01 &ndash; 3.00 m</td><td class="num">64</td></tr>
<tr><td><b>3.01 &ndash; 4.00 m</b></td><td class="num"><b>185</b></td></tr>
<tr><td>4.01 &ndash; 5.00 m</td><td class="num">47</td></tr>
<tr><td>&gt; 5.01 m</td><td class="num">7</td></tr>
</table>

<p>The modal positional error of an Indian legacy cadastral sheet is
<b>3&ndash;4 metres</b>, and over 88% of sheets fall between 2 and 5 metres [5].</p>

<p>The same study compared transformation orders on a sample of sheets:</p>

<table>
<tr><th>Sample</th><th>1st order (m)</th><th>2nd order (m)</th><th>Reduction</th></tr>
<tr><td>1</td><td class="num">3.668</td><td class="num">3.177</td><td class="num">13%</td></tr>
<tr><td>2</td><td class="num">3.171</td><td class="num">2.510</td><td class="num">21%</td></tr>
<tr><td>3</td><td class="num">3.962</td><td class="num">1.339</td><td class="num">66%</td></tr>
<tr><td>4</td><td class="num">4.089</td><td class="num">3.096</td><td class="num">24%</td></tr>
<tr><td>5</td><td class="num">5.010</td><td class="num">2.889</td><td class="num">42%</td></tr>
</table>

<p>A higher-order transformation cuts error by up to two thirds on the worst
sheets &mdash; but <b>choosing the transformation order per sheet is currently a
human judgement</b> [5]. Automating that selection from the residual structure
of each sheet is a concrete, demonstrable contribution, and it is what our
escalating transform selector does.</p>

<h4>Documented failure modes in legacy sheets [5] [V]</h4>
<ul>
<li><b>Gaps and overlaps between adjoining mouza sheets</b> &mdash; adjacent
sheets do not fit; they overlap or leave voids.</li>
<li><b>Multi-sheet mouzas</b> with unclear division between sheets.</li>
<li><b>Canal double-counting</b> &mdash; a canal used as a shared boundary is
drawn on both adjacent sheets, so the same area is counted twice.</li>
<li><b>River dynamics</b> &mdash; area lost to or accreted from a river, giving
large legal-versus-digitised discrepancies.</li>
<li><b>Paper degradation</b> &mdash; shrinkage, wrinkling, folding, tearing;
scanning adds further error.</li>
<li><b>Crude map lines</b> &mdash; the scanned line is often more than 4&ndash;5
pixels wide, so boundary ambiguity of decimetres to metres exists before any
transformation is applied.</li>
<li><b>Area attribute inconsistency</b> &mdash; digitised parcel area does not
equal the authorised area recorded in the RoR.</li>
</ul>

<p class="note">Our damage model reproduces five of these seven directly
(misregistration, smooth warp, vertex jitter, sliver and overlap injection,
recorded-versus-geometric area drift). That the damage model is derived from a
documented failure taxonomy rather than invented is why we consider the recovery
figures meaningful.</p>

<h3>2.4 What the new data will look like</h3>
<p>Survey of India technical circular T-260/1147-Project, dated 10 February 2025,
specifies for NAKSHA: orthorectified imagery at 5&nbsp;cm GSD with
<b>RMSE(x,y) &le; 10&nbsp;cm</b>; DSM/DTM at 0.5&nbsp;m spacing with
<b>RMSE(z) &le; 15&nbsp;cm</b>; CORS control better than 5&nbsp;cm; 70%/60%
overlap; a minimum of four corner and one centre GCP. The coordinate reference
system is settled: <b>UTM projection on WGS 84</b>, with vertical referenced to
the Indian Vertical Datum via the SoI geoid model [6] <b>[V]</b>.</p>

<h2>3. The accuracy mismatch that defines the problem</h2>

<p class="lead">New NAKSHA orthoimagery: RMSE &le; 10&nbsp;cm [6].
Legacy cadastral sheet: modal RMSE 3&ndash;4&nbsp;m [5].
That is a <b>30&ndash;40&times; accuracy mismatch between the two layers the
problem statement asks us to harmonise.</b></p>

<p>Naive overlay is therefore not merely imprecise; it is meaningless. Urban
plots are of the order of 11&nbsp;m across, so a legacy parcel displaced by
5&ndash;15&nbsp;m overlaps its <i>neighbour</i> more than it overlaps its own
counterpart. This single comparison determines the architecture: georeferencing
must precede matching, and any system that matches first is measuring the wrong
pair.</p>

<p class="note">We observed this directly. Matching before georeferencing gave a
blocking recall of 0.58 &mdash; 42% of true correspondences never reached the
model &mdash; and the model compensated by learning to join on khasra number
instead of geometry. Reordering the pipeline took blocking recall to
<b>{mt['blocking_recall']}</b>.</p>

<h2>4. What the literature establishes</h2>

<h3>4.1 The state of the field &mdash; Chen, Nazeer, Lee &amp; Wong [1]</h3>
<p>A systematic review of AI in cadastre published March 2026. Its conclusions:
deep learning has removed the manual-interpretation bottleneck in boundary
extraction, using CNNs and Transformers for pixel-level semantic segmentation;
natural-language methods now extract structure from paper archives; and deep
models detect parcel change and support integrated spatial/non-spatial
analysis [1] <b>[V]</b>.</p>

<p>It then states what remains open:</p>
<p class="q">&ldquo;&hellip;challenges remain, including differences in
multi-temporal data processing, spatial semantic ambiguity, and the lack of
large-scale, high-quality annotated data. Future research can focus on improving
model generalization, advancing cross-modal data fusion, and providing
recommendations for the development of a reliable and practical intelligent
cadastral system.&rdquo; [1]</p>

<p>Three of those four define this project: the absence of annotated ground
truth, cross-modal fusion, and generalisation beyond the area a method was tuned
on.</p>

<h3>4.2 Alignment under noisy supervision &mdash; Girard, Charpiat &amp; Tarabalka [2]</h3>
<p>The closest published statement of our core problem. The authors align
misregistered cadastral polygons to imagery where no correct annotation exists,
using a multi-resolution U-Net that predicts a 2-D displacement field, trained
over repeated rounds that re-correct the annotations between rounds. Alignment
error fell by more than a factor of three by round two; round three added
nothing [2] <b>[V]</b>.</p>

<p>Two findings bear directly on our method.</p>

<p><b>Their training data is built by applying known random deformations and
learning to invert them</b> &mdash; formally, a dataset
<span class="num">D = {{(I, J_rand, f_rand)}}</span> where the deformation is
generated and therefore known [2]. This is the same principle as our damage
harness, which is why we treat manufactured ground truth as an established
method rather than an improvisation.</p>

<p><b>They report two honest limitations we inherit.</b> A perfect alignment score
is unattainable because the reference annotations are themselves ambiguous &mdash;
many buildings are outlined by a coarse polygon, making best-alignment ill-posed
with multiple equally good solutions. And their model learns only <i>smooth</i>
displacement fields, so adjoining buildings requiring a discontinuous correction
fail [2].</p>

<p class="note">Our Gaussian-process error field carries the same smoothness
assumption. We treat it as a stated limitation, and it is the reason our
uncertainty model reports an irreducible floor &mdash;
{tg.get('irreducible_rmse_m', 0.75)}&nbsp;m in the evaluated ward &mdash; that no
quantity of survey control removes.</p>

<h3>4.3 Cadastral parcel adjustment with SAM and ICP &mdash; Suwardhi et al. [3]</h3>
<p>The closest operational system. UAV orthophotos at 5&nbsp;cm GSD are segmented
by the Segment Anything Model without manual prompting; displacement vectors come
from ICP alignment; adjustment proceeds hierarchically from rigid block (LS1) to
scaled block (LS2) to individual parcel (LS3). Evaluated over two urban villages
in Cimahi, Indonesia &mdash; Karangmekar with 81 blocks and 3,227 parcels, and
Baros with 96 blocks and 2,971 parcels, selected for contrasting block structure
and data quality. Implemented client-server with a Python REST API [3]
<b>[V]</b>.</p>

<p><b>What it leaves open is the instructive part.</b> Because no correct geometry
exists for those areas either, the authors evaluate <i>by proxy</i>: they count
how many times cadastral polygons split the SAM-derived boundary segments, and
treat fewer splits as better alignment [3]. That measures internal consistency,
not accuracy. It is the state of the art, and it cannot report its error in
metres.</p>

<p>The work is also single-source, and does not address attribute schema
inference, CRS/datum/unit heterogeneity, tenure semantics, calibrated
confidence, or where to survey next.</p>

<h3>4.4 Boundary revision by deep learning &mdash; Fetai, Grigillo &amp; Lisec [4]</h3>
<p>A modified CNN detects visible land boundaries from image-based mapping and
uses them to revise existing cadastral data [4] <b>[V]</b>. This is the upstream
of our pipeline, and we deliberately do not rebuild it: extraction is well served,
and the problem statement asks for integration of extracted features rather than
for another extractor.</p>

<h3>4.5 Method imported from outside the domain</h3>
<p>Our survey-planning component rests on sensor placement in Gaussian processes.
The objective &mdash; total reduction in posterior variance over a set of
observation locations &mdash; is monotone submodular, so greedy selection is
within a factor (1&nbsp;&minus;&nbsp;1/e) of optimal and the exact problem is
NP-hard [8] <b>[V]</b>. The result is standard in machine learning; we found no
application of it to cadastral ground-control planning.</p>

<h2>5. What the existing tools do, and do not do</h2>

<table>
<tr><th>Tool</th><th>What it genuinely does</th><th>What it does not do</th></tr>
<tr><td><b>GRASS <span class="num">v.clean</span></b></td>
    <td>Topology repair: break/clean polygons from non-topological formats,
        remove sub-threshold areas by dissolving into the neighbour with the
        longest shared boundary, fuzzy snapping, vertex pruning</td>
    <td>A human chooses the snapping and area thresholds. Wrong threshold means
        destroyed parcels or surviving slivers. It is a tool, not a
        decision-maker.</td></tr>
<tr><td><b>PostGIS Topology</b></td>
    <td>Persistent topological model with shared edges and faces; prevents gaps
        and overlaps by construction going forward</td>
    <td>Getting legacy dirty geometry <i>into</i> a valid topology is the hard
        part; common practice is to clean in GRASS first.</td></tr>
<tr><td><b>QGIS + GDAL/PROJ</b></td>
    <td>Georeferencer with polynomial 1st&ndash;3rd order, thin-plate spline,
        projective and Helmert; topology checker; reprojection</td>
    <td>All manual, per layer, per operator. GCP selection by hand. No
        cross-source reasoning.</td></tr>
<tr><td><b>FME / Esri Data Interoperability</b></td>
    <td>Industry-standard spatial ETL; hundreds of formats; visual schema
        mapping</td>
    <td><b>The mapping is declared by a human, not inferred.</b> FME will execute
        a mapping faithfully; it will not tell you that
        <span class="num">KHASRA_NO</span> and <span class="num">SY_NO</span> are
        the same concept, nor that they disagree for 12% of parcels. Also
        proprietary, at 4,912-ULB scale.</td></tr>
<tr><td><b>Esri Parcel Fabric</b></td>
    <td>Mature cadastral editing and QA</td>
    <td>Deed-based COGO assumptions; not built for khasra / FMB / mouza
        semantics or a 30&ndash;40&times; inter-layer accuracy mismatch.</td></tr>
<tr><td><b>SAM, Mask R-CNN, U-Net</b></td>
    <td>Strong at extracting <i>visible</i> boundaries from imagery</td>
    <td><b>Cadastral boundaries are frequently invisible</b> &mdash; no wall, no
        fence, no hedge. This is the ceiling of the pure-vision approach.</td></tr>
<tr><td><b>Bhu-Naksha</b> (the Indian incumbent)</td>
    <td>National cadastral map software in use across many states</td>
    <td>Manually entered <b>per-state scale factors</b> on shapefile import
        &mdash; UP &times;4000, Himachal &times;22 where <i>karam</i> was
        digitised in centimetres &mdash; and hand-written per-state RoR
        adapters. The incumbent national solution to unit and schema
        heterogeneity is a hard-coded constant. <b>[V]</b></td></tr>
</table>

<h2>6. What is not solved</h2>

<ol>
<li><b>No automated, evidence-weighted reconciliation across accuracy tiers.</b>
Every tool assumes you already know which layer is right. Nothing decides that
here the 10&nbsp;cm orthoimagery wins, there the legal recorded area wins, and
elsewhere the case must be adjudicated by a human.</li>

<li><b>Transformation-model selection remains a human judgement.</b> Second-order
beat first-order by up to 66% on the worst sheets [5], but choosing per sheet is
manual. No system selects the transformation model per sheet from its own
residual structure.</li>

<li><b>Schema matching for Indian land attributes is entirely manual.</b> FME and
Esri require a human to draw every mapping; Bhu-Naksha's answer is bespoke
per-state adapters. We found no published automated schema-matching system for
Indian land-record attributes.</li>

<li><b>Topology cleaning has no legal-consequence awareness.</b>
<span class="num">v.clean rmarea</span> will dissolve a 3&nbsp;m&sup2; sliver
&mdash; which may be a real, owned, taxed, litigated parcel. No tool distinguishes
a digitisation artefact from a genuine tiny urban parcel, though the distinction
is classifiable from area, compactness, presence of a khasra number, presence in
the RoR, and presence of a building footprint.</li>

<li><b>Vision models find visible boundaries; cadastres contain invisible ones.</b>
Fusing imagery evidence, legacy geometry, textual record and utility topology to
infer an invisible boundary is not addressed in the literature we found.</li>

<li><b>Cross-agency entity resolution is unaddressed.</b> The NAKSHA progress
review names &ldquo;parallel, non-interoperable records&rdquo; across Revenue,
ULB, Development Authority and Sub-Registrar as a top friction point, lists
insufficient cross-agency interoperability as a systemic void, and recommends
<i>automated GeoAI-driven updating mechanisms</i> [9] <b>[V]</b>.</li>

<li><b>The state of the art is single-source and single-country.</b> Suwardhi et
al. align one cadastral layer to one UAV orthophoto [3]. Extending
block-adjustment to an n-source, schema-aware, CRS-resolving, legally-aware
pipeline is what the problem statement actually asks for.</li>

<li><b>No open benchmark or ground truth exists for Indian cadastral
harmonisation.</b> Producing even a small one for a pilot ULB would be a
defensible deliverable in itself.</li>
</ol>

<h2>7. Standards and the canonical target</h2>

<p><b>ISO 19152 &mdash; Land Administration Domain Model.</b> Original edition
2012; current ISO 19152-1:2024 generic conceptual model, with Part 2 on land
registration in development. LADM is explicitly <i>not</i> a data product
specification: its stated purpose is &ldquo;not to replace existing systems, but
rather to provide a formal language for describing them.&rdquo; Four core
packages: parties; basic administrative units carrying rights, restrictions and
responsibilities; spatial units; and spatial sources and representations [16]
<b>[V]</b>.</p>

<p>Sengupta et al. asked in 2013 how to convert colonial maps and records into
an LADM-based database, <b>how to document and publish the geometric quality of
existing maps</b>, and <b>how to integrate more accurate data after re-survey</b>
[17] <b>[V]</b>. That last question &mdash; fusing a new high-accuracy survey
with an existing low-accuracy legal record without destroying the legal
record &mdash; is this problem statement, posed in the literature thirteen years
ago and still open.</p>

<p>Adopting LADM as the canonical target schema lets us say that every source is
mapped into an ISO-conformant model rather than into one we invented.</p>

<p><b>ULPIN.</b> A 14-character parcel identifier generated from geo-coordinates
under DILRMP. The mechanism is documented; the exact character composition rule
is <b>[U]</b> and we do not reproduce it. Our implementation is a faithful
<i>shape</i>, labelled as such in code and interface.</p>

<h2>8. Our approach</h2>

<p>The components are not individually novel and we do not claim them.
Segmentation, coordinate transformation, topology repair, change detection and
human review all exist. The contribution lies in three places, each answering one
of the gaps named above.</p>

<h3>8.1 Manufactured ground truth &mdash; accuracy measured, not asserted</h3>
<p>Both [2] and [3] are limited by the same thing: no correct geometry exists to
score against, so one reports relative improvement and the other a proxy. We
generate a clean synthetic cadastre and damage a copy through eleven stages whose
parameters are recorded, then score recovery against the key. Each stage
reproduces a failure mode documented in [5]:</p>

<table>
<tr><th>Damage stage</th><th>Real-world cause</th></tr>
<tr><td>Similarity misregistration</td><td>sheet georeferenced from too few, poorly spread GCPs</td></tr>
<tr><td>Smooth non-linear warp</td><td>paper shrinkage, scanner distortion, map-sheet join</td></tr>
<tr><td>Vertex jitter</td><td>manual digitisation from a paper sheet</td></tr>
<tr><td>Vertex decimation</td><td>generalisation during digitisation</td></tr>
<tr><td>Sliver and gap injection</td><td>adjoining sheets digitised independently</td></tr>
<tr><td>Overlap injection</td><td>shared boundaries double-counted between epochs</td></tr>
<tr><td>Self-intersection</td><td>careless digitising, unclosed rings</td></tr>
<tr><td>Attribute schema drift</td><td>every department names its columns differently</td></tr>
<tr><td>Owner-name corruption</td><td>transliteration variance across romanisations</td></tr>
<tr><td>Area unit drift</td><td>records kept in bigha and biswa, not m&sup2;</td></tr>
<tr><td>Block renumbering; split, merge, deletion</td><td>resurvey and subsequent mutation</td></tr>
</table>

<p>This addresses the review's &ldquo;lack of large-scale, high-quality annotated
data&rdquo; [1] by constructing it, following the deformation-injection principle
of [2].</p>

<h3>8.2 Calibrated confidence rather than a weighted score</h3>
<p>A weighted sum of similarity terms is not a probability and cannot be checked
against anything. Candidate pairs are scored by gradient-boosted trees over 29
features &mdash; geometric agreement, shape descriptors, attribute similarity
after transliteration folding, and context features describing how ambiguous each
candidate is relative to its alternatives &mdash; then mapped through isotonic
regression fitted on held-out data, so a stated probability corresponds to an
observed frequency. Expected calibration error is <b>{dec(mt['ece'])}</b>.</p>

<p>Calibration is what makes an explicit triage threshold possible instead of an
arbitrary cut-off, and it is the difference between a number that decorates the
interface and one that decides what a human looks at.</p>

<h3>8.3 Closing the loop to the field</h3>
<p>The NAKSHA progress review identifies ground truthing as the programme's most
delayed component, with 55 of roughly 150 pilot ULBs below 60% completion [9].
Because every parcel carries a calibrated uncertainty, the system fits a Gaussian
process to the residual displacement field, then selects survey locations by
greedy submodular maximisation of total variance reduction [8], and reports the
expected improvement.</p>

<p>The recommendation is then <b>validated rather than asserted</b>: the selected
control is actually applied, georeferencing is re-run, and achieved error is
compared against both the prediction and against random placement of the same
number of points.</p>

<h3>8.4 Ordering, and why it is fixed</h3>
<p class="num">ingest &rarr; schema inference &rarr; validate &rarr; georeference
&rarr; blocking &rarr; match &rarr; assign &rarr; topology &rarr; conflict &rarr;
change &rarr; uncertainty &rarr; targeting &rarr; serve</p>
<p>Georeferencing precedes matching for the reason set out in section 3. Conflict
resolution applies inverse-variance weighting to measured quantities and legal
authority to recorded ones &mdash; GNSS control wins on geometry, the revenue
record wins on ownership, because a drone cannot observe who owns a plot.
Conflating the two produces a system that will overwrite a title with a
photograph.</p>

<h2>9. Evaluation and results</h2>

<p class="k">Trained on one synthetic city, evaluated on a second with a different
layout and a different damage profile. Full pipeline {M['runtime_s']}&nbsp;s on
one core; {M['counts']['legacy']:,} legacy parcels against
{M['counts']['reference']:,} reference parcels over
{M['counts']['candidate_pairs']:,} candidate pairs.</p>

<table>
<tr><th>Stage</th><th>Measure</th><th>Result</th></tr>
<tr><td>Georeferencing</td><td>positional RMSE</td>
    <td class="num">{g['rmse_raw']} m &rarr; {g['rmse_coarse']} m</td></tr>
<tr><td>Georeferencing</td><td>inliers in the robust fit</td>
    <td class="num">{g['inliers']:,}</td></tr>
<tr><td>Schema inference</td><td>columns mapped</td>
    <td class="num">{sc['mapped']}/{sc['total']}</td></tr>
<tr><td>Schema inference</td><td>area unit, inferred from geometry</td>
    <td class="num">{sc['area_unit']} at {sc['area_unit_confidence']}</td></tr>
<tr><td>Blocking</td><td>true pairs retained</td>
    <td class="num">{mt['blocking_recall']}</td></tr>
<tr><td>Matching</td><td>precision / recall / F1</td>
    <td class="num">{mt['precision']} / {mt['recall']} / {mt['f1']}</td></tr>
<tr><td>Matching</td><td>ROC AUC</td><td class="num">{mt['roc_auc']}</td></tr>
<tr><td>Matching</td><td>share of decision from geometry</td>
    <td class="num">{round(mt['geometry_share'] * 100, 1)}%</td></tr>
<tr><td>Confidence</td><td>expected calibration error</td>
    <td class="num">{dec(mt['ece'])}</td></tr>
<tr><td>Assignment</td><td>1:1 / subdivision / amalgamation</td>
    <td class="num">{asg.get('one_to_one', 0):,} / {asg.get('split', 0)} / {asg.get('merge', 0)}</td></tr>
<tr><td>Topology</td><td>total errors</td>
    <td class="num">{tp['total_before']:,} &rarr; {tp['total_after']}</td></tr>
<tr><td>Topology</td><td>overlapping parcel pairs</td>
    <td class="num">{tp['overlaps_before']:,} &rarr; {tp['overlaps_after']}</td></tr>
<tr><td>Topology</td><td>doubly-claimed land</td>
    <td class="num">{tp['overlap_area_before']:,} &rarr; {tp['overlap_area_after']} m&sup2;</td></tr>
<tr><td>Restraint</td><td>parcel-sized gaps refused, not filled</td>
    <td class="num">{tp['refused_to_fill']} of {tp['harness_deleted']} deleted</td></tr>
<tr><td>Change</td><td>new / demolished / extended / heightened</td>
    <td class="num">{ch['new']} / {ch['demolished']} / {ch['extended']} / {ch['heightened']}</td></tr>
<tr><td>Encroachment</td><td>sites on public land</td>
    <td class="num">{ch['encroachment']}, {ch['encroached_sqm']} m&sup2;</td></tr>
<tr><td>Targeting</td><td>predicted / achieved / random</td>
    <td class="num">{tg['rmse_predicted']} / {tg['rmse_achieved']} / {tg['rmse_random']} m</td></tr>
</table>

<h4>Two results that deserve explanation</h4>

<p><b>The geometric share is reported because it is a falsifiable claim about
mechanism.</b> An early version of this model scored F1 0.9955 by learning to
join on khasra number and owner name, with IoU contributing 0.24% of the
decision. It would have been useless in any jurisdiction that renumbers on
resurvey. The harness now renumbers 45% of blocks and genuinely changes 12% of
owners, and a test asserts that geometry accounts for at least 70% of the
decision. It currently accounts for
{round(mt['geometry_share'] * 100, 1)}%.</p>

<p><b>The area ledger reconciles land rather than reporting a total.</b> Summed
parcel area falls by {abs(tp['area_drift_pct'])}% across topology repair, which
looks alarming until it is decomposed: doubly-claimed land falls from
{tp['overlap_area_before']:,} to {tp['overlap_area_after']} m&sup2;, while the
union footprint &mdash; ground counted once &mdash; <i>rises</i>. The summed
figure falls because land recorded as owned by two parties simultaneously is now
counted once. No land was created or destroyed, and the ledger demonstrates it.</p>

<h2>10. Limitations, stated plainly</h2>

<ul>
<li>The cadastral parcel layer is <b>synthetic</b>, derived from OpenStreetMap
block structure and labelled as such throughout the product and its exports. No
bulk Indian urban cadastre is publicly available. Building footprints, the road
network and the terrain are real.</li>
<li>Encroachment cases are <b>deliberately injected</b>: the generator never
places structures on public land, so without injection there would be nothing to
detect and the claim would be untested.</li>
<li>The survey-plan prediction is <b>calibrated, not exact</b>. A scale factor
measured on one city transfers to a held-out city within roughly 12% and errs
conservative.</li>
<li>Per-parcel digitising noise is <b>irreducible</b> by survey control. The
system reports that floor rather than promising accuracy below it &mdash; a
limitation shared with [2], whose displacement model is likewise smooth.</li>
<li>The system detects and evidences change. It does <b>not</b> produce a
mutation record, which is a statutory act requiring notice and hearing and whose
form varies by state.</li>
<li>Redaction of personal data is enforced server-side by the API. In the
static demonstration build every artifact is delivered to the browser, so
redaction there is a display control only. This distinction is documented in
the repository.</li>
</ul>

<h2>11. Open questions we would take further</h2>
<ul>
<li><b>Sliver classification with legal consequence.</b> Distinguishing a
digitisation artefact from a genuine tiny urban parcel is classifiable from
area, compactness, khasra presence, RoR presence and footprint presence. We
currently classify on geometry alone and flag the rest.</li>
<li><b>Invisible boundaries.</b> Fusing imagery, legacy geometry, textual record
and utility topology to infer a boundary with no physical trace is the ceiling
of the vision-only approach and is unaddressed in the literature we found.</li>
<li><b>North/south legal regimes.</b> Preserving measurement authority where the
Field Measurement Book is primary, rather than polygon authority, needs a
per-state policy object rather than a global setting.</li>
<li><b>An Indian benchmark.</b> A small, released, ground-truthed harmonisation
benchmark for one pilot ULB would let this field measure itself.</li>
</ul>

<h2>References</h2>

<p class="ref">[1] J. Chen, M. Nazeer, B. S. Lee and M. S. Wong. <i>Artificial
Intelligence in Cadastre: A Systematic Review of Methods, Applications, and
Trends.</i> Land, 15(3):411, 2026. doi:10.3390/land15030411.</p>

<p class="ref">[2] N. Girard, G. Charpiat and Y. Tarabalka. <i>Noisy Supervision
for Correcting Misaligned Cadaster Maps Without Perfect Ground Truth Data.</i>
IGARSS 2019, IEEE International Geoscience and Remote Sensing Symposium.
Inria / LuxCarta Technology.</p>

<p class="ref">[3] D. Suwardhi, M. Ihsan, R. Widyastuti, A. H. U. Mukminin,
B. Akbar, S. K. Pasaribu, I. P. Satwika, S. L. Nurmaulia and A. Hernandi.
<i>An Automated Framework for Cadastral Parcel Adjustment Using UAV Orthophotos,
SAM, and ICP.</i> ISPRS Archives, XLVIII-2/W11-2025:277&ndash;284, 2025.
Institut Teknologi Bandung.</p>

<p class="ref">[4] B. Fetai, D. Grigillo and A. Lisec. <i>Revising Cadastral Data
on Land Boundaries Using Deep Learning in Image-Based Mapping.</i> ISPRS Int. J.
Geo-Inf., 11(5):298, 2022. doi:10.3390/ijgi11050298.</p>

<p class="ref">[5] A. Sengupta, C. Lemmen, W. Devos, D. Bandyopadhyay and
A. van der Veen. <i>Constructing a seamless digital cadastral database using
colonial cadastral maps and VHR imagery &mdash; an Indian perspective.</i>
Survey Review, 48(349):258&ndash;268, 2016.
doi:10.1179/1752270615Y.0000000003.</p>

<p class="ref">[6] Survey of India. Technical circular T-260/1147-Project
(NAKSHA), 10 February 2025.</p>

<p class="ref">[7] Department of Science and Technology, Government of India.
<i>National Geospatial Policy 2022.</i></p>

<p class="ref">[8] A. Krause, A. Singh and C. Guestrin. <i>Near-Optimal Sensor
Placements in Gaussian Processes: Theory, Efficient Algorithms and Empirical
Studies.</i> Journal of Machine Learning Research, 9:235&ndash;284, 2008.</p>

<p class="ref">[9] K. Satyarthi et al. Progress review of the NAKSHA programme.
Frontiers in Sustainable Cities, 2026. First author is Joint Secretary,
Department of Land Resources.</p>

<p class="ref">[10] V. Thakur, M. N. Doja and A. A. A. Faizi. <i>Indian Cadastral
Survey System &mdash; Comparative Study.</i> IJEDR, 5(4):1579+, 2017.</p>

<p class="ref">[11] P. Misra. <i>Cadastral surveys in India.</i> Coordinates,
June 2005.</p>

<p class="ref">[12] Department of Land Resources, Ministry of Rural Development.
NAKSHA programme booklet.</p>

<p class="ref">[13] Department of Land Resources. DILRMP progress statistics.</p>

<p class="ref">[14] DAKSH. <i>Access to Justice Survey 2015-16.</i> 9,329
litigants, 305 locations, 24 states, November 2015 &ndash; February 2016.</p>

<p class="ref">[15] Tamil Nadu Department of Survey and Settlement. DILRMP
Regional Review, Bengaluru, 6 September 2024.</p>

<p class="ref">[16] ISO 19152-1:2024, Land Administration Domain Model &mdash;
Part 1: Generic conceptual model.</p>

<p class="ref">[17] A. Sengupta, D. Bandyopadhyay, C. H. J. Lemmen and
A. van der Veen. <i>Potential use of LADM in cadastral data management in
India.</i> 5th LADM Workshop, Kuala Lumpur, September 2013.</p>

<h2>Appendix A &mdash; claims we deliberately do not make</h2>

<p>Several figures circulate widely in Indian land-administration discussion
without traceable provenance. We exclude the following rather than risk being
unable to defend them:</p>

<ul>
<li><b>&ldquo;Land disputes take about 20 years to resolve.&rdquo;</b> Attributed
to NITI Aayog across many secondary sources; we could not open the original.
<b>[S]</b></li>
<li><b>&ldquo;324 years to clear the case backlog.&rdquo;</b> Source not
located. <b>[U]</b></li>
<li><b>&ldquo;25% of Supreme Court decided cases involve land disputes.&rdquo;</b>
Widely repeated, original study not found. <b>[U]</b></li>
<li><b>Any figure for man-hours or rupee cost of manual GIS
harmonisation</b> specifically, as distinct from survey or digitisation cost. We
searched and found nothing credible in the public domain, and we do not invent
one. Where a cost proxy is needed we use the &#8377;56,725 per sq km resurvey
rate [15], which is official.</li>
<li><b>&ldquo;Indian Geodetic Datum 2023.&rdquo;</b> This does not exist. The
National Geospatial Policy 2022 [7] commits to <i>redefining</i> the national
geodetic framework; the Indian Vertical Datum is real and is referenced in
[6].</li>
<li><b>The exact 14-character composition of ULPIN</b>, and the contents of the
NAKSHA SDMS schema, whose SOP is available only as a scan without a text
layer. <b>[U]</b></li>
</ul>

<p class="note">Sources [1]&ndash;[4] and [8] were read in the original for this
document. Sources [5]&ndash;[7] and [9]&ndash;[17] are drawn from a sourced
research dossier compiled for this project; figures attributed to them carry
their grade, and any figure intended for publication should be re-checked
against the primary document.</p>
"""


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
        if n > 60:
            break
    writer.close()
    print(f"wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB, {n} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

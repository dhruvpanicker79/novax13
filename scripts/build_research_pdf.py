"""Render the research summary to PDF.

LibreOffice needs apt and there is no sudo here, so the usual HTML->PDF route
is unavailable. PyMuPDF's Story engine lays out a restricted HTML/CSS subset
and paginates it, which is enough for a typeset document and needs no system
packages.

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

def dec(v: float, places: int = 5) -> str:
    """Plain decimal. An f-string renders 9e-05, which reads as a typo."""
    return f"{v:.{places}f}".rstrip("0").rstrip(".") or "0"
g, mt, tp = M["georef"], M["matching"], M["topology"]
tg, sc, ch = M["targeting"], M["schema"], M["change"]

CSS = """
body { font-family: sans-serif; font-size: 9.6pt; line-height: 1.45;
       color: #16191d; }
h1 { font-size: 19pt; margin: 0 0 2pt 0; color: #0f2233; }
h2 { font-size: 12pt; margin: 16pt 0 4pt 0; color: #0f7a3f; }
h3 { font-size: 10.2pt; margin: 10pt 0 3pt 0; color: #16191d; }
p  { margin: 0 0 6pt 0; }
.sub { font-size: 9pt; color: #5a646e; margin: 0 0 3pt 0; }
.meta { font-size: 8pt; color: #7d868f; margin: 0 0 12pt 0; }
.lead { font-size: 10.4pt; color: #0f2233; margin: 0 0 9pt 0; }
li { margin: 0 0 4pt 0; }
b { color: #0f2233; }
.q { font-size: 9.4pt; color: #2b3138; margin: 4pt 0 7pt 14pt; }
.k { font-size: 8.6pt; color: #5a646e; }
table { font-size: 8.8pt; }
th { text-align: left; color: #5a646e; font-size: 8pt; padding: 0 8pt 3pt 0; }
td { padding: 0 8pt 3pt 0; vertical-align: top; }
.num { font-family: monospace; font-size: 8.8pt; }
.ref { font-size: 8.6pt; margin: 0 0 5pt 0; }
.note { font-size: 8.6pt; color: #5a646e; margin: 5pt 0 8pt 0; }
"""

HTML = f"""
<h1>Automated Integration and Intelligent Harmonization of
Multi-Source Geospatial Data for Urban Land Record Management</h1>
<p class="sub">KSHETRA &mdash; research summary and evidence base</p>
<p class="meta">Team NovaX &nbsp;&middot;&nbsp; Smart India Hackathon 2026
&nbsp;&middot;&nbsp; Problem Statement 26013</p>

<p class="lead">This document states what the published literature establishes,
what it leaves open, and which of those open problems our prototype addresses.
Every performance figure quoted for KSHETRA was measured by a harness in the
repository, not estimated.</p>

<h2>1. The problem, quantified</h2>

<p>Urban land administration draws on drone orthoimagery, DSM/DTM surfaces,
scanned cadastral sheets, revenue registers, municipal GIS, utility networks
and GNSS control. These disagree in coordinate system, position, geometry,
attribute schema, vintage and completeness. Reconciling them is presently
manual GIS work.</p>

<p>The scale of the mismatch is documented. Sengupta, Bhattacharya and Mukherjee
measured registration error across 310 cadastral sheets in West Bengal and found
a modal RMSE of <b>3&ndash;4&nbsp;m</b> [5]. The Survey of India specification for
the NAKSHA programme requires orthoimagery accurate to <b>RMSE(x,y) &le; 10&nbsp;cm</b>
and DSM/DTM to <b>RMSE(z) &le; 15&nbsp;cm</b> [6]. Legacy geometry is therefore
wrong by roughly <b>thirty to forty times</b> the tolerance of the imagery it must
be reconciled against, which is why naive overlay produces nothing usable.</p>

<p>The administrative position is consistent with this. Under DILRMP, only
<b>49.10%</b> of villages hold geo-referenced cadastral maps [7].</p>

<h2>2. What the field says remains unsolved</h2>

<p>Chen, Nazeer, Lee and Wong published a systematic review of artificial
intelligence in cadastre in March 2026 [1]. It concludes that deep learning has
largely solved automated boundary extraction, that natural-language methods now
handle non-spatial records, and that change detection is established. It then
names what has not been solved:</p>

<p class="q">&ldquo;&hellip;challenges remain, including differences in
multi-temporal data processing, spatial semantic ambiguity, and the lack of
large-scale, high-quality annotated data. Future research can focus on improving
model generalization, advancing cross-modal data fusion&hellip;&rdquo; [1]</p>

<p>Three of those four are directly relevant here, and they are the axes on which
this project is built: <b>the absence of annotated ground truth</b>, <b>cross-modal
fusion</b>, and <b>generalisation beyond the area a method was tuned on</b>.</p>

<h2>3. Prior art, and what each leaves open</h2>

<h3>3.1 Alignment under noisy supervision &mdash; Girard, Charpiat &amp; Tarabalka [2]</h3>
<p>The closest published statement of our core problem. The authors align
misregistered cadastral polygons to imagery when no correct annotation exists,
using a multi-resolution U-Net that predicts a displacement field, trained in
repeated rounds that re-correct the annotations between rounds. Alignment error
fell by more than a factor of three by the second round, with the third adding
nothing [2].</p>
<p>Two findings matter for us. First, their training data is built by applying
<b>known random deformations</b> to annotations and learning to invert them &mdash;
the same principle our damage harness uses, and the reason we consider that
approach established rather than improvised. Second, they report that a perfect
score is unattainable because the reference annotations are themselves ambiguous,
and that their model learns only <b>smooth</b> displacement fields, so adjoining
buildings needing discontinuous correction fail [2].</p>
<p class="note">Our Gaussian-process error field shares that smoothness
assumption. We treat it as a stated limitation rather than a solved problem,
and it is why our uncertainty model reports an irreducible floor
({tg.get('irreducible_rmse_m', 0.75)}&nbsp;m here) that no amount of survey
control removes.</p>

<h3>3.2 Cadastral parcel adjustment with SAM and ICP &mdash; Suwardhi et al. [3]</h3>
<p>The closest operational system. UAV orthophotos at 5&nbsp;cm GSD are segmented
by the Segment Anything Model without manual prompting; displacement vectors come
from ICP; adjustment proceeds hierarchically from rigid block (LS1) to scaled
block (LS2) to individual parcel (LS3). Evaluated over two urban villages in
Cimahi, Indonesia &mdash; Karangmekar, 81 blocks and 3,227 parcels, and Baros,
96 blocks and 2,971 parcels [3].</p>
<p>What it leaves open is instructive. Because no correct geometry exists for
those areas either, the authors evaluate <b>by proxy</b>: they count how many
times cadastral polygons split the SAM-derived boundaries, and treat fewer splits
as better alignment [3]. That measures internal consistency, not accuracy. The
work also handles a single source, does not infer attribute schema, carries no
calibrated confidence, and does not address where to survey next.</p>

<h3>3.3 Boundary revision by deep learning &mdash; Fetai, Grigillo &amp; Lisec [4]</h3>
<p>A modified CNN detects visible land boundaries from image-based mapping and
uses them to revise existing cadastral records [4]. This is the upstream of our
pipeline. We deliberately do not rebuild it: feature extraction is a solved and
well-served problem, and the problem statement asks for integration of extracted
features, not for another extractor.</p>

<h3>3.4 Method the field imports from elsewhere</h3>
<p>Our survey-planning component rests on sensor placement in Gaussian processes,
where the objective is monotone submodular and greedy selection is therefore
within a factor (1&nbsp;&minus;&nbsp;1/e) of optimal [8]. That result is standard
in machine learning and, as far as we found, has not been applied to cadastral
ground-control planning.</p>

<h2>4. Position</h2>

<p>The components are not novel individually, and we do not claim them.
Segmentation, coordinate transformation, topology repair, change detection and
human review all exist. The contribution is in three places, each answering one
of the gaps the review names.</p>

<h3>Manufactured ground truth, so accuracy is measured rather than asserted</h3>
<p>Both [2] and [3] are limited by the same thing: no correct geometry exists to
score against, so one reports relative improvement and the other a proxy. We
generate a clean synthetic cadastre and damage a copy of it through eleven stages
whose parameters are known &mdash; misregistration, smooth warp, vertex jitter,
sliver and overlap injection, self-intersection, schema drift, transliteration
corruption, unit drift, block renumbering, and split/merge/deletion. Recovery is
then scored against the key. This addresses the review's &ldquo;lack of
large-scale, high-quality annotated data&rdquo; [1] by constructing it, and it
follows the deformation-injection principle of [2].</p>

<h3>Calibrated confidence rather than a weighted score</h3>
<p>A weighted sum of similarity terms is not a probability and cannot be checked.
We score candidate pairs with gradient-boosted trees over 29 features, then map
the output through isotonic regression fitted on held-out data, so a stated
probability corresponds to an observed frequency. Expected calibration error is
<b>{dec(mt['ece'])}</b>. This is what allows an explicit triage threshold instead of an
arbitrary cut-off.</p>

<h3>Closing the loop to the field</h3>
<p>The NAKSHA programme's own 2026 progress review identifies ground truthing as
its most delayed component [9]. Because every parcel carries a calibrated
uncertainty, the system computes which locations to survey next by greedy
submodular maximisation over the posterior variance of a fitted GP error field
[8], and reports the expected reduction. The recommendation is then validated:
the selected control is actually applied, georeferencing re-run, and the achieved
error compared against both the prediction and against random placement.</p>

<h2>5. Measured results</h2>

<p class="k">Trained on one synthetic city, evaluated on a second with a different
layout and a different damage profile. Full pipeline: {M['runtime_s']}&nbsp;s on one core.</p>

<table>
<tr><th>Stage</th><th>Measure</th><th>Result</th></tr>
<tr><td>Georeferencing</td><td>positional RMSE</td>
    <td class="num">{g['rmse_raw']} m &rarr; {g['rmse_coarse']} m</td></tr>
<tr><td>Schema inference</td><td>columns mapped; area unit</td>
    <td class="num">{sc['mapped']}/{sc['total']}; {sc['area_unit']} at {sc['area_unit_confidence']}</td></tr>
<tr><td>Blocking</td><td>true pairs retained</td>
    <td class="num">{mt['blocking_recall']}</td></tr>
<tr><td>Matching</td><td>F1 / ROC AUC</td>
    <td class="num">{mt['f1']} / {mt['roc_auc']}</td></tr>
<tr><td>Matching</td><td>share of decision from geometry</td>
    <td class="num">{round(mt['geometry_share'] * 100, 1)}%</td></tr>
<tr><td>Confidence</td><td>expected calibration error</td>
    <td class="num">{dec(mt['ece'])}</td></tr>
<tr><td>Topology</td><td>total errors</td>
    <td class="num">{tp['total_before']} &rarr; {tp['total_after']}</td></tr>
<tr><td>Topology</td><td>overlapping parcel pairs</td>
    <td class="num">{tp['overlaps_before']} &rarr; {tp['overlaps_after']}</td></tr>
<tr><td>Topology</td><td>doubly-claimed land</td>
    <td class="num">{tp['overlap_area_before']} &rarr; {tp['overlap_area_after']} m2</td></tr>
<tr><td>Restraint</td><td>parcel-sized gaps refused</td>
    <td class="num">{tp['refused_to_fill']} of {tp['harness_deleted']} deleted</td></tr>
<tr><td>Change</td><td>new / demolished / extended / heightened</td>
    <td class="num">{ch['new']} / {ch['demolished']} / {ch['extended']} / {ch['heightened']}</td></tr>
<tr><td>Encroachment</td><td>sites on public land</td>
    <td class="num">{ch['encroachment']}, {ch['encroached_sqm']} m2</td></tr>
<tr><td>Targeting</td><td>predicted / achieved / random</td>
    <td class="num">{tg['rmse_predicted']} / {tg['rmse_achieved']} / {tg['rmse_random']} m</td></tr>
</table>

<p class="note">The geometric share is reported because it is a falsifiable claim
about mechanism. An early version of this model scored F1 0.9955 by learning to
join on khasra number and owner name, with IoU contributing 0.24% of the
decision; it would have been useless in a jurisdiction that renumbers on
resurvey. The harness now renumbers 45% of blocks and changes 12% of owners, and
the test asserts a geometric share above 70%.</p>

<h2>6. What we do not claim</h2>

<ul>
<li>The cadastral parcel layer is <b>synthetic</b>, derived from OpenStreetMap
block structure, and labelled as such throughout the product and its exports. No
bulk Indian urban cadastre is publicly available. Building footprints, the road
network and the terrain are real.</li>
<li>Encroachment cases are <b>deliberately injected</b>, because the generator
never places structures on public land; without injection there would be nothing
to detect and the claim would be untested.</li>
<li>The survey-plan prediction is <b>calibrated, not exact</b>. A scale factor
measured on one city transfers to a held-out city within roughly 12% and errs
conservative.</li>
<li>Per-parcel digitising noise is <b>irreducible</b> by survey control; the
system reports that floor instead of promising accuracy below it.</li>
<li>The system detects and evidences change. It does <b>not</b> produce a
mutation record, which is a statutory act requiring notice and hearing and whose
form varies by state.</li>
</ul>

<h2>References</h2>

<p class="ref">[1] J. Chen, M. Nazeer, B. S. Lee and M. S. Wong.
<i>Artificial Intelligence in Cadastre: A Systematic Review of Methods,
Applications, and Trends.</i> Land, 15(3):411, 2026.
doi:10.3390/land15030411.</p>

<p class="ref">[2] N. Girard, G. Charpiat and Y. Tarabalka.
<i>Noisy Supervision for Correcting Misaligned Cadaster Maps Without Perfect
Ground Truth Data.</i> IGARSS 2019, IEEE International Geoscience and Remote
Sensing Symposium. Inria / LuxCarta.</p>

<p class="ref">[3] D. Suwardhi, M. Ihsan, R. Widyastuti, A. H. U. Mukminin,
B. Akbar, S. K. Pasaribu, I. P. Satwika, S. L. Nurmaulia and A. Hernandi.
<i>An Automated Framework for Cadastral Parcel Adjustment Using UAV Orthophotos,
SAM, and ICP.</i> ISPRS Archives, XLVIII-2/W11-2025:277&ndash;284, 2025.
Institut Teknologi Bandung.</p>

<p class="ref">[4] B. Fetai, D. Grigillo and A. Lisec.
<i>Revising Cadastral Data on Land Boundaries Using Deep Learning in
Image-Based Mapping.</i> ISPRS Int. J. Geo-Inf., 11(5):298, 2022.
doi:10.3390/ijgi11050298.</p>

<p class="ref">[5] A. Sengupta et al. Measured registration error across 310
cadastral sheets, West Bengal. Survey Review, 2016. Modal RMSE 3&ndash;4 m.</p>

<p class="ref">[6] Survey of India. Technical circular T-260/1147-Project
(NAKSHA), 10 February 2025. ORI at 5 cm GSD, RMSE(x,y) &le; 10 cm;
DSM/DTM RMSE(z) &le; 15 cm; CORS control better than 5 cm; UTM projection on
WGS 84.</p>

<p class="ref">[7] Department of Land Resources, Ministry of Rural Development.
Digital India Land Records Modernisation Programme &mdash; geo-referenced
cadastral map coverage, 49.10% of villages.</p>

<p class="ref">[8] A. Krause, A. Singh and C. Guestrin.
<i>Near-Optimal Sensor Placements in Gaussian Processes: Theory, Efficient
Algorithms and Empirical Studies.</i> Journal of Machine Learning Research,
9:235&ndash;284, 2008.</p>

<p class="ref">[9] K. Satyarthi et al. Progress review of the NAKSHA programme.
Frontiers in Sustainable Cities, 2026. Identifies ground truthing as the
programme's most delayed component and recommends automated GeoAI-driven
updating mechanisms.</p>

<p class="note">Sources [1]&ndash;[4] and [8] were read in full or in the
relevant part. [5], [6], [7] and [9] are quoted from a sourced research dossier
compiled for this project; figures attributed to them should be re-checked
against the primary document before publication.</p>
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
        if n > 40:
            break
    writer.close()
    print(f"wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB, {n} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

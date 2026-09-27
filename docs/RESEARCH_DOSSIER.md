# Research Dossier — SIH 2026
## "Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management"

**Compiled:** 23 September 2026
**Method:** Web search + direct retrieval of primary government PDFs (DoLR booklet, Survey of India technical circular, National Geospatial Policy PIB backgrounder, DILRMP state review decks) and peer-reviewed literature. Where a PDF had no text layer or a summarizer produced generic text, that is flagged.

### How to read this document
- **[V]** = VERIFIED — traced to a primary/official source or peer-reviewed publication, URL given.
- **[S]** = SECONDARY — reported by a credible secondary source (news, policy institute, coaching portal) but not confirmed against the original.
- **[U]** = UNVERIFIED / UNCERTAIN — could not confirm; do NOT put on a slide without re-checking.
- **⚠ CONFLICT** = sources disagree; both figures given.

> **Rule for the deck:** every number that goes on a slide should carry its source in the speaker notes. Judges for a DoLR/MoRD problem statement will often *be* from DoLR. Getting a NAKSHA figure wrong is worse than omitting it.

---

# 1. NAKSHA Programme

## 1.1 Identity — [V]

| Field | Value |
|---|---|
| Full official name | **NAKSHA — "NAtional geospatial Knowledge-based land Survey of urban HAbitations"** |
| Owning department | **Department of Land Resources (DoLR)** |
| Ministry | **Ministry of Rural Development (MoRD)** — *not* MoHUA, despite being an urban programme |
| Parent scheme | **DILRMP** (Digital India Land Records Modernisation Programme), a Central Sector Scheme |
| Launch date | **18 February 2025** |
| Launch location | **Raisen, Madhya Pradesh** |
| Launched by | Union Minister **Shri Shivraj Singh Chouhan** (Minister of Agriculture & Farmers Welfare / Rural Development) |

Sources:
- DoLR official: https://dolr.gov.in/en/about-naksha/
- DoLR NAKSHA Booklet (Feb/Mar 2025 PDF, text extracted directly): https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2025/03/20250311644815872.pdf
- PIB press release PRID 2104028 (18 Feb 2025): https://pib.gov.in/PressReleseDetailm.aspx?PRID=2104028 *(PIB blocks automated fetch — title and content confirmed via search index and multiple mirrors)*
- DoLR event page: https://dolr.gov.in/en/event/union-minister-shri-shivraj-singh-chouhan-inaugurates-the-national-geospatial-knowledge-based-land-survey-of-urban-habitations-naksha-at-raisen-madhya-pradesh/

**Useful framing for judges:** NAKSHA is the *urban* counterpart to SVAMITVA (rural). Both sit under the land-records modernisation umbrella; NAKSHA under DoLR/MoRD, SVAMITVA under Ministry of Panchayati Raj.

## 1.2 Budgetary origin — [V]

NAKSHA traces to two Union Budget announcements (the DoLR booklet cites page/para explicitly):

- **Union Budget 2024-25** (speech 23 July 2024, p.18, para 100): *"Land records in urban areas will be digitized with GIS mapping. An IT based system for property record administration, updating, and tax administration will be established. These will also facilitate improving the financial position of urban local bodies."*
- **Union Budget 2025-26** (speech 1 Feb 2025, p.14, point 83): launch of the **National Geospatial Mission** — foundational geospatial infrastructure leveraging PM Gati Shakti, to modernise land records and urban planning.
  - National Geospatial Mission allocation: **₹100 crore** in FY2025-26. [V] — PIB backgrounder citing `indiabudget.gov.in/doc/Budget_at_Glance/bag7.pdf` p.06.

Source: NAKSHA booklet p.3 (URL above); PIB National Geospatial Policy backgrounder (27 Feb 2025): https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/feb/doc2025227509401.pdf

## 1.3 Pilot scale — ⚠ CONFLICT (three different official/academic figures)

This is the single most likely place to get caught out. **All three are sourced; pick one and cite it.**

| Figure | Coverage | Area | Source | Date |
|---|---|---|---|---|
| **152 ULBs**, 26 States + 3 UTs | 4,142.63 sq km | DoLR NAKSHA Booklet (primary PDF) + PIB launch release | Feb 2025 (launch) |
| **157 ULBs**, 27 States + 3 UTs | 4,484+ sq km, 1.5 crore+ citizens | DoLR website "About NAKSHA" page | current (2026) |
| **150 ULBs**, 25 States + 3 UTs | — | Frontiers in Sustainable Cities peer-reviewed paper | data to 31 Mar 2026 |

**Recommended slide wording:** "~150+ ULBs across 26–27 States/UTs (pilot)". If you must be exact, use **152 ULBs / 26 States / 3 UTs / ₹194 crore / 4,142.63 sq km** and cite the DoLR booklet — it is the primary launch document and the technology-split numbers (80+48+24) sum exactly to 152, which internally corroborates it.

- Booklet: https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2025/03/20250311644815872.pdf
- DoLR site: https://dolr.gov.in/en/about-naksha/
- Frontiers paper: https://www.frontiersin.org/journals/sustainable-cities/articles/10.3389/frsc.2026.1874630/full

## 1.4 Budget / outlay — [V]

- **₹194 crore** for the one-year pilot, **100% centrally funded** (Central Sector Scheme).
- Scaling plan stated in the booklet: **Phase 1 → 1,000 ULBs**; eventual coverage **all 4,912 ULBs** in the country.

Source: NAKSHA Booklet p.4.

**Note on a *separate, much larger* funding line — [V]:** Under the GoI **Scheme for Special Assistance to States for Capital Investment 2024-25, Part-VIII (Urban Land Records)**, states can claim incentives per city for MAP-1, MAP-2 and MAP-3, **varying from ₹10 crore to ₹30 crore per milestone depending on city population**. This is *distinct from* the ₹194 crore pilot outlay and is a much better number for an "addressable market / scale" slide.
Source: Tamil Nadu DILRMP Regional Review deck (06.09.2024, Bengaluru), pp.22-24: https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2024/10/20241004518377083.pdf

## 1.5 ULB eligibility criteria — [V] (two different criteria sets exist — both real)

**NAKSHA pilot criterion (booklet, p.4):** ULBs with **area less than 35 sq km AND population less than 2 lakh**.

**DoLR urban-land-records city categorisation** (per DoLR letter No. 21014/04/2024-LRD dated 27.06.2024 and guidelines dated 09.08.2024, as reproduced in the Tamil Nadu review deck):

| Category | Population |
|---|---|
| A | 2 lakh and above |
| B | 1 lakh to < 2 lakh |
| C | (implied 50,000 – 1 lakh) — [U] not explicitly seen in extracted text |
| D | Less than 50,000 |

Plus a *city-type* axis: (a) typical old city expanding horizontally, (b) newly developed planned city with peri-urban areas, (c) city growing vertically at a rapid pace.

Source: TN DILRMP deck pp.8-10 (URL above).

**Why this matters for our solution:** the three city *types* are exactly the three harmonisation regimes. (a) old city = legacy cadastral maps + heavy encroachment + no vertical component; (b) planned peri-urban = development-authority layouts vs revenue khasra mismatch; (c) vertical city = 2D parcel ≠ 3D property rights. A slide that names these three DoLR categories and shows a different harmonisation strategy for each will read as insider-grade.

## 1.6 Technology partners / key players — [V]

From NAKSHA Booklet pp.6-7:

| Player | Role |
|---|---|
| **Survey of India (SoI)** | **Technology Partner.** Aerial survey; geospatial services; fixing AOI boundaries; collecting GCPs and fixing flight plans; feature extraction; QA/QC |
| **MPSeDC** (M.P. State Electronics Development Corporation Ltd.) | Enterprise software development; dovetailing to state requirements; training & support on WebGIS |
| **NIC / NICSI** (National Informatics Centre) | Cloud space & storage; database management; data security audit; data recovery |
| **Centres of Excellence (CoEs) / ATIs** | Evaluation study on land governance; documentation of best practices; technical assistance in survey/re-survey; hands-on training to States/UTs; review of acts relating to urban & rural land records and titling |
| **DoLR** | NPMU setup; selection of cities; SOPs and guidance; GIS platforms and storage; national IEC & capacity building, monitoring, documentation |
| **States & UTs** | Supporting SoI in aerial survey clearances; SPMU setup; state IEC & capacity building; procurement of survey equipment (e.g. GNSS Rover); **field survey and ground truthing**; **integration of land records and other details** |

**Yes — Survey of India is definitively involved**, as the named Technology Partner. DoLR site additionally names "five national Centres of Excellence".

⚠ **Critical for our pitch:** notice the last row. *"Integration of Land Records and other details"* is formally assigned to **States/UTs** — the least technically resourced actor in the chain — with no named tooling. That is precisely the gap our platform fills. This is a strong, citable justification for the problem statement existing.

## 1.7 The MAP-1 / MAP-2 / MAP-3 workflow — [V]

NAKSHA runs a **three-map sequential framework** (booklet p.10; milestone definitions in the TN review deck pp.22-24):

**MAP-1 — Aerial Survey & Mapping incl. Feature Extraction**
1. Define Area of Interest → 2. Flight plan → 3. Fly & capture → 4. Process data → 5. True Ortho-Rectified Image (ORI) + feature-extracted data.
Milestone definition adds: fixing of **ground control points and city boundary by CORS network**; high-resolution digital aerial photography using survey-grade equipment; data processing and **3D feature extraction including DEM & DTM**; quality control and production of **ORI with land parcel boundaries**; **MAP-1 publication at 1:500 scale**.

**MAP-2 — Field Survey & Ground Truthing by Rovers & DGPS**
1. Field survey → 2. **Integration of RoR / Property Tax / Registration Deeds, etc.** → 3. 2D/3D model → 4. Publish land ownership details.
Milestone adds: land parcel boundary & area ascertainment by **CORS-based GNSS rovers & controllers**; **integration of property holding details of ULBs & ground validation**; **integration of other documents like authority approvals, land records etc.**; standardized data collection and GIS platform; **MAP-2 publication with GIS-ready land parcel maps**.

**MAP-3 — Claims & Dispute Resolution and Finalisation**
1. Claims and objections → 2. Grievance redressal → 3. Final land ownership.
Milestone adds: IEC, awareness, community engagement; issuance of notices/notifications; claim finalisation and dispute resolution of **ownership, area, boundary and shape**; preparation of updated land and property records; **final MAP-3 publication with land property card & register**.

**The deck-ready insight:** Our problem statement lives almost entirely inside **MAP-2**. MAP-1 is a procurement/photogrammetry problem that SoI and its 17 contractor packages already solve to spec. MAP-3 is a legal/administrative process. **MAP-2 — "integration of RoR / property tax / registration deeds / authority approvals / municipal & utility GIS onto the new ORI-derived parcel geometry" — is the un-automated middle, and it is the documented bottleneck.**

## 1.8 Aerial survey technology split — [V]

| Technology | Sensor | ULBs | Output |
|---|---|---|---|
| **Tech-1** | 2D Nadir camera | **80** | ORI, DEM/DSM, 2D datasets |
| **Tech-2** | Oblique angle camera, 5 cameras (45°–60°, four obliques + one vertical) | **48** | ORI, DEM, 3D reality model, LOD-2 3D vector models |
| **Tech-3** | Oblique angle camera + LiDAR sensor | **24** | As above + bare-earth / point-cloud data for dense urban & vegetated terrain |

(80 + 48 + 24 = 152.) The Frontiers paper reports a slightly different split (80 / 47 / 25 = 152). ⚠ minor conflict; use the booklet's 80/48/24.

Source: NAKSHA Booklet pp.8-9; Frontiers paper.

## 1.9 Survey of India technical specifications — [V] ★ HIGHEST-VALUE TECHNICAL SOURCE

Survey of India circular **No. T-260/1147-Project (NAKSHA PROJECT)/Comp_25490, dated 10 Feb 2025** (file ref `T-1147015/2/2024-TECHNICAL-SGO I/134543/2025`), signed for the Surveyor General of India. Text extracted directly from the PDF.

**URL:** https://surveyofindia.gov.in/documents/circulars/document-86171-ilovepdf_merged.pdf

### Ground control
- Rectangular block: **minimum 4 pre-pointed control points at the 4 corners + 1 at the centre**; additional control points at sharp kinks in the flying-area boundary.
- **CORS network established by Survey of India is to be used** for control/check-point provision.
- Minimum **30 check points by contractor** + minimum **30 independent check points by SoI Geospatial Directorates/Wings**, both via CORS, with RMSE reported.
- Both contractors and SoI wings **MUST use SoI's CORS / Passive GCP libraries** — explicitly "to ensure consistency between various observations."
- **Horizontal accuracy (RMSEx, RMSEy) of control/check points shall be better than 5 cm.**
- If **more than 5%** of QC'd GNSS data fails spec, consequences fall on the contractor.

### Flight
- Minimum **70% forward overlap**, **60% side overlap**, **GSD 5 cm**.
- Tech-1 requires **cross-grid flying**.

### Post-processing accuracy (quote these on the technical slide)
- Ortho-mosaics at **5 cm GSD**, georeferenced to the project coordinate system.
- **ORIs / 3D models / ortho-mosaics at 5 cm GSD: RMSEx ≤ 10 cm, RMSEy ≤ 10 cm**
- **DEM / DSM / DTM at regular spacing of 0.5 m: RMSEz ≤ 15 cm (WGS 84)**
- DTMs (bare-earth DEM) generated after DSM cleaning and editing.
- ORI to be radiometrically and geometrically corrected, seamless edge-matched, no smearing/distortion.

### Coordinate reference system — ★ definitive answer for Section 7
All NAKSHA deliverables must conform to:
- **Projection: Universal Transverse Mercator (UTM)**
- **Horizontal datum: WGS 84**
- **Vertical datum:** (a) WGS 84 ellipsoidal, realised through the **SoI CORS Network**; and (b) DEM/DSM/DTM on the **Indian Vertical Datum**, generated using **SoI's Geoid Model**, supplied by the Geodetic & Research Branch (G&RB), Dehradun. Where no geoid model exists, G&RB develops one with field observations from the Geospatial Directorates.

### Feature extraction
- **2D FE** done on ORI **and in stereo mode separately**, then integrated into a GIS platform as feature layers including a detailed topographical layer **based on property markers**.
- All buildings, utilities, roads and other relevant infrastructure **"must be accurately extracted and attributed as per SDMS / Schema circulated and approved by Competent Authority."**
- **"All topological tests should be done for completeness and consistent vector layers."**
- **3D FE** (Tech-2 & 3): generate **LOD-2 3D vector models**; **horizontal/vertical slicing of buildings based on visible markers**; layout plans may be used for building-plan-based slicing.

### Programme administration
- Work is split into **contractor packages 1 to 17**.
- Weekly physical progress reporting; monthly financial reporting; separate accounting for NAKSHA.
- Copy marked to **Shri Kunal Satyarthi, Joint Secretary, DoLR** — the same person is first author of the 2026 Frontiers paper on NAKSHA (see §1.11). Citing both signals depth.

**★ The two sentences to build the whole technical differentiation on:**
> *"…attributed as per SDMS / Schema circulated and approved by Competent Authority."*
> *"All topological tests should be done for completeness and consistent vector layers."*

A schema (SDMS) **exists** and topology checking is **mandated** — but the circular specifies *that* it must be done, never *how*, and imposes it only on the **freshly extracted aerial features**, not on the legacy cadastral / revenue / utility layers that must be merged onto them in MAP-2. **That asymmetry is our wedge.**

> ⚠ **[U] — I could not retrieve the SDMS / NAKSHA data schema itself.** The full NAKSHA SOP (105 pages, https://surveyofindia.gov.in/UserFiles/files/NAKSHA%20SOP%20_NAKSHA.pdf, listed at https://surveyofindia.gov.in/pages/naksha-sop) **is a scanned image-only PDF with no text layer** — 105 pages yielded 105 characters of extractable text. If you want the actual attribute schema and feature codes, that PDF must be OCR'd or read by eye. **Strongly recommended before the finale.**

## 1.10 Current status (2026) — [V] / ⚠ partly [S]

**Peer-reviewed, as of 31 March 2026** (Frontiers in Sustainable Cities):
- Pilot scope reported as **150 ULBs / 25 States / 3 UTs**.
- **Aerial survey:** 118 ULBs with quality-assured ORI + DSM delivered.
- **Ground truthing:** 44 ULBs at 100%; 16 ULBs above 60%; **55 ULBs below 60%**.
- **"Ground-truthing emerged as the biggest lagging component."** ★ — This is *the* quotable line justifying our problem statement.

**[S]** Secondary reporting of the same data window: ORI and DSM most progressed (116–118 ULBs submitted, QA/QC by SoI); **3D Mesh and 3D Feature Extraction limited to 65 ULBs (Tech-2+3 only), roughly 54–57 completed.**

**Status verdict:** the pilot, nominally one year from Feb 2025, has clearly run past a single year. As of the last verifiable data (Mar 2026) it is **substantially complete on aerial acquisition and substantially incomplete on ground truthing and record integration.** I found **no** official DoLR publication of a *completed* pilot or of a national rollout decision. **[U]** — Treat "NAKSHA is complete" or "nationwide rollout has begun" as unverified.

## 1.11 Academic analysis of NAKSHA — [V] ★ CITE THIS

**Satyarthi, K., Somvanshi, S., & Kumar, D. (2026).** *"Scaling urban land governance in India: the NAKSHA Programme as a platform for governance innovation for sustainable cities."* **Frontiers in Sustainable Cities**, Innovation and Governance section. Published **16 September 2026**.
https://www.frontiersin.org/journals/sustainable-cities/articles/10.3389/frsc.2026.1874630/full

First author Kunal Satyarthi is **Joint Secretary, DoLR** (corroborated by the SoI circular distribution list). This is effectively the programme owner's own published diagnosis — extraordinarily strong to cite in front of DoLR judges.

**Identified friction points (paraphrased from the paper):**
1. **Jurisdictional fragmentation** — Revenue Departments, ULBs, Development Authorities and Sub-Registrars maintain **parallel, non-interoperable records**; institutional ambiguity over responsibility creates administrative delays.
2. **Tenure complexity** — multi-generational ownership, cooperative housing, informal settlements resist straightforward cadastral mapping.
3. **Data obsolescence risk** — high-resolution imagery needs continuous updating or it becomes a static archive rather than a dynamic governance platform.

**Stated systemic voids:**
- No statutory framework granting presumptive title status to Urban Property Ownership Records (**UrPro**) in most jurisdictions.
- Inadequate municipal capacity for continuous cadastral maintenance.
- Legal limbo for informal settlements / unauthorised construction.
- **No 3D property-rights framework despite 3D survey deployment.**
- **Insufficient mechanisms for cross-agency data interoperability.**

**Their own policy recommendations include** inter-agency coordination protocols creating unified governance platforms, and **"automated GeoAI-driven updating mechanisms preventing data obsolescence."** ← Our solution is literally a recommendation from the programme's own Joint Secretary. Put this on the slide.

---

# 2. DILRMP — Digital India Land Records Modernisation Programme

## 2.1 Identity and lineage — [V]

- **Predecessor:** Computerisation of Land Records scheme started **1988-89** (per NIC Bhu-Naksha documentation).
- **NLRMP** — National Land Records Modernization Programme, launched **2008** (Centrally Sponsored Scheme).
- **DILRMP** — renamed and **converted to a Central Sector Scheme with 100% central funding effective 1 April 2016**.
- Implemented by **Department of Land Resources, Ministry of Rural Development**.

⚠ The DoLR web page phrases this as "launched in 2016", which is the *conversion* date, not the original launch (2008 as NLRMP). If a judge says "DILRMP is from 2008" and your slide says 2016, say "2008 as NLRMP, restructured to a 100% centrally funded Central Sector Scheme in 2016" — that is the safe, correct answer.

Sources: https://dolr.gov.in/en/programmes-schemes/dilrmp-2/ ; NIC Bhu-Naksha presentation p.3 (https://bhunaksha.nic.in/bhunaksha/resources/Bhunaksha2.0.pdf)

## 2.2 Outlay and period — [V]
- **₹875.00 crore**, extended from **2021-22 to 2025-26**.
Source: https://dolr.gov.in/en/programmes-schemes/dilrmp-2/

## 2.3 Components — [V]

Core components: computerisation of Records of Rights (RoR); **digitisation of cadastral maps / FMBs / Tippans**; integration of textual and spatial data; survey/re-survey and updation; computerisation of the registration process and SRO–land-records integration; **Modern Record Rooms at tehsil level**; State Level Data Centre; DILRMP Cell / PMU; core GIS and software applications; training, IEC and evaluation studies.

**Two components added later:**
- **Consent-based integration of Aadhaar number with the land record database**
- **Computerization of Revenue Courts and their integration with land records** (RCCMS)

Sources: https://dolr.gov.in/en/programmes-schemes/dilrmp-2/ ; https://www.pib.gov.in/PressReleasePage.aspx?PRID=1989671&reg=48&lang=2

## 2.4 Progress statistics — [V] (as of 31 December 2023 unless noted)

| Indicator | Value |
|---|---|
| RoR computerisation | **95.09%** — 6,25,137 of 6,57,397 villages |
| States/UTs at 99%+ RoR computerisation | 15 |
| Cadastral maps digitised | **68.02%** — ~252.5 million of ~369.9 million maps |
| Registration computerisation | **93%** — 5,060 of 5,329 Sub-Registrar Offices |
| SRO ↔ land records integration | **75%** — 4,669 of 5,329 SROs |
| **Geo-referencing of cadastral maps** | **49.10% — 3,26,776 of 6,57,397 villages** ★ |

Source: https://dolr.gov.in/en/programmes-schemes/dilrmp-2/

★ **The 49.10% geo-referencing figure is the best single national statistic for our problem slide.** It says: half the country's cadastral maps still have **no coordinate system at all**. Digitised ≠ georeferenced ≠ harmonised. That three-stage distinction is a clean, memorable slide.

**Historical contrast — [V]** (PRS Legislative Research, using DILRMP data as of September 2017):

| Component | Sept 2017 |
|---|---|
| Computerisation of land records | 86% |
| Mutation computerised | 47% |
| Digitally signed RoR issuance | 28% |
| Cadastral maps digitised | 46% |
| Spatial data verified | 39% |
| **Cadastral maps linked to RoR** | **26%** |
| **Real-time RoR/map updates** | **15%** |
| **Villages with survey/re-survey completed** | **9%** |
| Area covered under DILRMP | 35% |
| DILRMP funds released (2008–Sep 2017) that were utilised | 64% |

Source: https://prsindia.org/policy/analytical-reports/land-records-and-titles-india

★ **"Only 9% of villages had completed survey/re-survey"** and **"only 26% of cadastral maps were linked to RoR"** are devastating impact numbers — but they are **2017**, so label them as such. Do not present 2017 figures as current.

## 2.5 Relationship to NAKSHA and SVAMITVA — [V]

```
DILRMP  (DoLR, Ministry of Rural Development, Central Sector Scheme, ₹875 cr, 2021-22→2025-26)
│
├── Rural land records  — RoR computerisation, cadastral map digitisation, survey/re-survey
├── ULPIN / Bhu-Aadhaar — 14-digit parcel identity
├── NGDRS               — registration (e-Registration), 28 States/UTs
├── RCCMS / e-Courts    — revenue court case management + integration
├── Transliteration     — records in local languages
├── Bhoomi Samman       — state certification/recognition programme
└── NAKSHA (2025→)      — URBAN land records: aerial survey + field survey + urban property card

SVAMITVA (2020→)  — SEPARATE scheme, Ministry of PANCHAYATI RAJ, not DoLR
                  — RURAL ABADI (inhabited village) areas only
                  — same technical spine: SoI drones + SoI CORS
```

Source: https://dolr.gov.in/en/programmes-schemes/dilrmp-2/ (sub-scheme list); Ministry attributions per §4.

⚠ The DoLR page's own one-line gloss describes NAKSHA as a "capacity building and awareness program" — that is a stale/incorrect description on their site. Use the NAKSHA booklet's definition instead.

**DILRMP vision statement — [V]:** an *"Integrated Land Information Management System"* delivering *"error-free, transparent and tamper-proof land records"* using **AI, Machine Learning and blockchain**, establishing tenancy security and streamlined property transfer. (https://dolr.gov.in/en/programmes-schemes/dilrmp-2/)
★ AI/ML is already in DILRMP's own stated vision — quote it to pre-empt "is AI appropriate here?"

---

# 3. ULPIN / Bhu-Aadhaar

## 3.1 Definition — [V]

**ULPIN = Unique Land Parcel Identification Number**, branded **Bhu-Aadhaar**. Official DoLR definition: *"a 14-digit identification number accorded to a land parcel based on the longitude and latitude coordinates"*.

Source: https://dolr.gov.in/en/ulpin/

## 3.2 How it is generated — [V] on mechanism, [U] on exact bit-layout

DoLR's official page describes two constructs:

- **PNIU — Property Natural Identifier Unit:** an **ECCMA-standard-compliant 14-digit ID computed from the parcel's geo-referenced coordinates**. ECCMA = Electronic Commerce Code Management Association.
- **PNIL — Property Natural Identifier Lot:** the parcel expressed as the **latitude/longitude coordinates of its vertices**.

DoLR states the identifier is *"organically dependent"* on these spatial coordinates and *"points to the parcel's surface"*, adhering to **ECCMA** and **Open Geospatial Consortium (OGC)** standards.

> ⚠ **[U] — The exact digit-by-digit encoding formula is NOT published in any source I could retrieve.** Secondary sources say only "derived from latitude and longitude." **Do not put a fabricated format string (e.g. "SS-DD-TT-VVV-PPPP") on a slide.** Correct, safe phrasing: *"a 14-digit alphanumeric identifier generated from the parcel's geo-referenced vertex coordinates per the ECCMA PNIU standard."*

> ⚠ **[U]** Sources disagree on whether ULPIN is purely numeric or **alphanumeric**. DoLR says "14-digit identification number"; many secondary sources say "14-digit alphanumeric code". Say **"14-character identifier"** if you want to be unimpeachable.

## 3.3 Adoption status — ⚠ CONFLICT

| Claim | Source | Date |
|---|---|---|
| Rolled out in **29 States/UTs**; pilot in **4** (A&N, Manipur, Puducherry, Telangana) | DoLR official ULPIN page: https://dolr.gov.in/en/ulpin/ | current |
| Adopted by **26 States/UTs**; pilot in **7 more** | PIB / DoLR reporting | 2023 |

The DoLR ULPIN page names the 29: Andhra Pradesh, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, J&K, Karnataka, Kerala, Ladakh, Madhya Pradesh, Maharashtra, Mizoram, Nagaland, NCT Delhi, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Tripura, Uttarakhand, Uttar Pradesh, West Bengal, Chandigarh, Dadra & Nagar Haveli / Daman & Diu.
**Integration note:** Madhya Pradesh, Ladakh and J&K incorporate ULPIN into their **SVAMITVA** implementation.

**Underlying constraint — [V]:** ULPIN requires geo-referenced parcels, and only **49.10% of villages** have geo-referenced cadastral maps (§2.4). So "29 states adopted" ≠ "all parcels have a ULPIN". Tamil Nadu's own 2024 review deck says ULPIN generation is *"In progress"*, generated **on a pilot basis for 57 villages of Hosur Taluk, Krishnagiri District** where resurvey is complete. That single line is excellent evidence of the gap between headline adoption and ground reality.
Source: TN DILRMP deck p.5.

## 3.4 Stated benefits — [V]
Standardised unambiguous parcel identification; tracking and transparency in land transactions; land accounting and land banks; real-estate transactions and property taxation; **reduction of boundary disputes**; beneficiary determination for schemes; disaster planning. (https://dolr.gov.in/en/ulpin/)

**Relevance to us:** ULPIN is the natural **join key** for harmonisation. Where it exists, our matching problem becomes an identity problem. Where it doesn't (half the country), we must *do* the spatial entity resolution that would generate it. Framing our output as "we emit ULPIN-ready, PNIL-conformant harmonised parcels" is precisely aligned with DoLR's own roadmap.

---

# 4. SVAMITVA

## 4.1 Identity — [V]

- **SVAMITVA** = *Survey of Villages and Mapping with Improvised Technology in Village Areas*. **[S]** on the exact expansion — widely reported, not confirmed by me against a DoLR/MoPR primary page.
- **Ministry: Ministry of Panchayati Raj** (NOT DoLR/MoRD). Technical support from **Survey of India** and **NICSI**.
- **Launched April 2020** (National Panchayati Raj Day, 24 April 2020). **[S]**
- **Scope: rural ABADI areas** — the inhabited/residential portion of a revenue village, historically *not* surveyed because abadi was excluded from the cultivable-area cadastre.

Sources: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2200803&reg=3&lang=1 *(PIB blocks automated fetch; content confirmed via search index)*; https://en.wikipedia.org/wiki/Svamitva_Yojana

## 4.2 Methodology — [V] on the technical spine

Drone-based aerial survey of abadi areas; **Ground Control Points established using the Survey of India CORS network**; orthorectified imagery; feature extraction of property boundaries; ground truthing; claims-and-objections process; issue of **Property Cards** (called Adhikar Abhilekh / Sampatti Patrak / Title Deed depending on state).

The **SVAMITVA SOP** is published at https://svamitva.nic.in/DownloadPDF/SOPSVAMITVASchemeEnglishVersion_1634724183038.pdf
> ⚠ **[U]** — I could **not** retrieve this PDF (TLS certificate chain failure on `svamitva.nic.in`). **The specific accuracy specification for SVAMITVA drone survey is therefore UNVERIFIED by me.** Do not quote a SVAMITVA cm-accuracy figure without opening this SOP.

**Confirmed via PIB backgrounder — [V]:** *"under the SVAMITVA Scheme, SoI has surveyed and mapped over 2.8 lakh villages across Andhra Pradesh, Haryana, and Karnataka using drone technology"* — note the odd phrasing in the source (2.8 lakh villages is a national figure, the three states named appear to be examples). https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/feb/doc2025227509401.pdf p.9

## 4.3 Results to date — ⚠ multiple vintages, be careful

| Figure | Date | Confidence |
|---|---|---|
| **26.3 million (2.63 crore) property cards issued across 3,29,161 villages** | by March 2026 | **[V]** — Frontiers peer-reviewed paper |
| Drone surveys completed in **3,26,889 villages**; property cards prepared for **1,81,354 villages**; **11.17 crore land parcels digitised** | as of 8 May 2026 | **[S]** — search-index summary of PIB PRID 2200803, PIB fetch blocked |
| **~67,000 sq km** of abadi land surveyed | 2026 | **[S]** |
| PM distributed **65 lakh property cards** across 230 districts, 10 states + 2 UTs | 18 Jan 2025 | **[S]** — newsonair.gov.in |
| **10,900+ bank loans worth ₹1,679 crore** sanctioned against SVAMITVA property cards (IIM Ahmedabad evaluation) | 2026 | **[S]** ⚠ I could not open the IIM-A evaluation. Verify before using — it is a very attractive number and therefore a very attractive thing to be wrong about. |
| States complete on both survey & distribution: Haryana, Uttarakhand, Goa, Tripura, Puducherry, A&N. Lagging: Tamil Nadu, Bihar, Odisha | 2026 | **[S]** |

**Safe slide number:** *"~2.6 crore property cards across ~3.3 lakh villages (March 2026)"* — cite the Frontiers paper, which is peer-reviewed and checkable.

## 4.4 How SVAMITVA differs from NAKSHA — [V]

| | SVAMITVA | NAKSHA |
|---|---|---|
| Ministry | Panchayati Raj | Rural Development (DoLR) |
| Started | 2020 | 2025 |
| Area type | **Rural abadi** (inhabited village area) | **Urban** — ULBs |
| Prior record state | Largely **no prior cadastre at all** for abadi — greenfield | **Multiple conflicting legacy records** — revenue, municipal, development authority, registration |
| Core difficulty | Capture + adjudicate first-ever record | **Reconcile several existing, mutually inconsistent records** |
| Geometry | 2D parcels | 2D + **LOD-2 3D**, vertical/horizontal building slicing |
| Tenure complexity | Simple homestead plots | Apartments, cooperative housing, multi-generational, informal settlements, leasehold |
| Output | Property Card | **Urban Property Card** + UrPro register |

★ **This table is arguably the most important conceptual slide in the deck.** The Frontiers paper makes exactly this argument: NAKSHA *builds on* SVAMITVA's proven rural methodology, but *"transitioning from rural Abadi areas to complex urban habitations demands substantially more sophisticated legal and institutional frameworks."* SVAMITVA is a **capture** problem. NAKSHA is a **reconciliation** problem. Our platform addresses reconciliation. That is the one-sentence pitch.

---

# 5. Bhu-Naksha

## 5.1 What it is — [V]

**Bhu-Naksha** is a **cadastral mapping software developed in-house by NIC** (Land Records Information System Division, LRISD) using **open-source components**, to manage digitised parcel (cadastral) maps and link them to textual RoR data. It is explicitly designed *"to cater to all basic necessities of the Patwari with regard to parcel map management."*

Primary source (text extracted directly from the 104-slide NIC deck): https://bhunaksha.nic.in/bhunaksha/resources/Bhunaksha2.0.pdf
Also: https://www.nic.gov.in/project/bhunaksha/

## 5.2 Technology stack — [V]

| Layer | Technology |
|---|---|
| Geometry engine | **GeoTools** (open-source Java GIS toolkit, GeoAPI contributor, implements OGC specs) |
| Topology/geometry model | **JTS Topology Suite** (via GeoTools) |
| Spatial database | **PostgreSQL + PostGIS** |
| Alternate/attribute DB | **MS SQL Server** (for RoR side in most implementing states) |
| Reporting | **iReport** |
| IDE | NetBeans |
| OS | Windows / Linux |

Stated minimum hardware (dated): 1 GB RAM, Pentium IV, 160 GB HDD.

## 5.3 Data formats and integration — [V]

- **Import from multiple formats: shapefile (.shp), .adf (ArcInfo coverage), and ETS (Electronic Total Station) data.**
- Deployment procedure: install PostgreSQL → install PostGIS → create `bhunaksha` database **with the `postgis` template** → restore blank schema.
- For RoR integration: *"For overcoming diverse structure of ROR database in different states Bhunaksha defines certain interfaces for talking with ROR database. It talks to other external ROR database which are mostly in MS SQL Server in implemented states."*
- Available as **Web, Desktop and Mobile** apps.

## 5.4 Features — [V]
Integration of spatial and textual data; display/print at any scale; distance measurement; automatic area calculation; layer display/print; **plot division (split) with adjustable size and shape**; **merge of two polygons**; map-based queries; display all khasras owned by a person by clicking any one; drawing grid; print khasra map with adjoining khasras and owner details; multilingual display/print of owner information.

**Plot splitting supports two geometric construction methods — [V]:**
1. **Distance–Angle method** — terminal points of the division line must intersect a plot edge; terminal points may be an existing vertex or a point between two vertices specified by distance; intermediate points defined by distance and angle from reference points.
2. **Arc method (adjacent side)** — pick a corner point, define distances toward the second and last points, define arc radii from the first and second points, then choose which of the two arc intersections is intended.

★ This is the *actual sub-division workflow* used in Indian revenue offices. Naming it — "we automate what a patwari today does with the Distance–Angle method in Bhu-Naksha" — is high-credibility detail.

## 5.5 States using it — [V] / [S]

**From the NIC deck's own conclusion [V]:** implemented in tehsils of **Chhattisgarh, Madhya Pradesh, Himachal Pradesh, Assam, Sikkim, Uttar Pradesh.**

**[S]** Wider list of states operating Bhu-Naksha portals: Bihar, Assam, Andhra Pradesh, Himachal Pradesh, Chhattisgarh, Lakshadweep, Jharkhand, Madhya Pradesh, Odisha, Maharashtra, Uttar Pradesh, Rajasthan.

## 5.6 ★ KNOWN LIMITATIONS — the single best "pain" evidence in this dossier

**Verbatim from the NIC Bhu-Naksha manual, on importing plots from a shapefile [V]:**

> *"Type Scale factor if the measurements in shape file is different from that of ground. (In almost all states 1 unit in shape file corresponds to 1 meter(unit) on ground. In case of Uttar Pradesh 1 unit in shape file was equal to 1 unit on printed paper map which is in 1:4000 scale. So UP has to set scale factor 4000. In case of Himachal units on ground is in Karam and digitization is done in centimeters and map is printed by scaling each inch to some karam. HP has to set scale factor 22 because by multiplying each unit in shape file with 22 we will get 1 karam on ground)"*

Source: https://bhunaksha.nic.in/bhunaksha/resources/Bhunaksha2.0.pdf (p.53)

**Why this is gold:** India's national cadastral mapping software ships with a **manually entered, per-state magic scale constant** because state cadastral shapefiles are in **mutually incompatible, non-metric, non-georeferenced units** — UP in paper-map units at 1:4000, Himachal in *karam* digitised in centimetres. This is not a hypothetical interoperability problem; it is documented in the official manual of the incumbent tool. **Put this quote on the problem slide.**

**Other limitations, inferred and evidenced:**
- **[V]** Import path is shapefile / .adf / ETS — i.e. **non-topological** formats. GRASS documentation notes that polygons imported from non-topological formats such as shapefile require explicit cleaning (`v.clean bpol`) — Bhu-Naksha offers no equivalent automated topology repair in its documented feature list; it offers only manual split and merge.
- **[V]** No stated coordinate reference system handling. The manual discusses *scale factors*, not *datums or projections*. There is no documented reprojection, datum transformation, or georeferencing step — consistent with the national reality that only 49.10% of villages are georeferenced at all (§2.4).
- **[V]** RoR integration is via **bespoke per-state interfaces**, not a shared schema — *"for overcoming diverse structure of ROR database in different states."* Schema heterogeneity is handled by hand-written adapters, state by state.
- **[V]** The design target is a **single patwari managing a single village's parcel map**, not multi-source reconciliation across revenue + municipal + utility + imagery.
- **[U]** I found no published accuracy, throughput, or error-rate benchmarks for Bhu-Naksha.

---

# 6. The Pain, Quantified

> **Handle with care.** Several of the most-quoted "land dispute" statistics in India are recycled through coaching portals with drifting attribution. Below, each is traced as far back as I could get, and the provenance problems are flagged. **Use the ones marked ★.**

## 6.1 Litigation volume

| Claim | Original source | Status |
|---|---|---|
| ★ **"Land-related disputes account for two-thirds of all pending court cases"** | **World Bank (2007), *India: Land Policies for Growth and Poverty Reduction*, Report No. 38298-IN, 9 July 2007** — https://documents1.worldbank.org/curated/en/531431468035337578/pdf/382980INoptmzd.pdf ; quoted by PRS: https://prsindia.org/policy/analytical-reports/land-records-and-titles-india | **[V] as a cited claim.** Note the World Bank itself hedges — *"some estimates suggest."* Safest wording: *"A 2007 World Bank study noted estimates that land-related disputes account for two-thirds of all pending court cases."* |
| ★ **Two-thirds (~66%) of civil cases surveyed pertained to land and property** | **DAKSH Access to Justice Survey 2015-16** — 9,329 litigants, 305 locations, 24 states, Nov 2015–Feb 2016. https://www.dakshindia.org/access-to-justice-survey/ ; https://dakshindia.org/wp-content/uploads/2016/05/Daksh-access-to-justice-survey.pdf | **[V] as attributed.** This is a **survey of litigants**, not a census of all cases. Correct phrasing: *"In DAKSH's 2015-16 Access to Justice Survey of 9,329 litigants, roughly two-thirds of civil matters concerned land and property."* |
| "Land disputes are 60–70% of Indian civil litigation" | Frontiers/NAKSHA paper (2026) states *"Property disputes comprise 60–70% of Indian civil litigation"* | **[V]** as a statement in a peer-reviewed paper — safe to cite to that paper |
| "Over 30% of civil cases involve land and property" | another DAKSH analysis | **[S]** ⚠ directly conflicts with the 66% figure — different denominators. **Do not present 66% as uncontested.** |
| "5 crore pending cases, ~60% property-related" | commercial blog | **[U]** — do not use |
| "25% of Supreme Court decided cases involve land disputes, of which 30% are acquisition" | widely circulated, original study not located by me | **[U]** — do not use without the source |
| ~5 million (50 lakh) revenue-related cases pending across state revenue courts | **[S]** | plausible and thematically useful, but unverified |

## 6.2 Duration

- ★ **"Land disputes take on average about 20 years to be resolved."** Attributed to a **NITI Aayog** paper (variously described as a strategy paper / a study on strengthening arbitration). **[S]** — the attribution is consistent across PRS, Drishti, Civilsdaily and others, but I could **not** open the NITI Aayog original and cannot name the exact document. Cite as *"NITI Aayog, as cited by PRS Legislative Research"*: https://prsindia.org/policy/analytical-reports/land-records-and-titles-india
- **[S]** A 2018 NITI Aayog strategy paper reportedly estimated **324+ years** to clear a 29-million-case backlog at then-current disposal rates. **Do not use** — I could not source it and the figure is the kind that invites a challenge.

## 6.3 Economic cost

| Claim | Source | Status |
|---|---|---|
| ★ **₹13.7 lakh crore (~US$190 bn) of committed/earmarked/potential investment embroiled in 335 of 703 land conflicts — equal to 7.2% of India's 2018-19 GDP** | *Land Conflict Watch / Rights and Resources Initiative / Oxfam-supported* report | **[S]** — consistently reported; I did not open the primary report. https://rightsandresources.org/blog/new-research-shows-high-cost-land-disputes-india/ ; https://www.business-standard.com/article/economy-policy/ongoing-land-conflicts-affecting-lives-livelihoods-of-over-6-5-mn-people-120031700149_1.html |
| **Land conflicts affect the lives/livelihoods of 6.5 million+ people; 2.1 million+ hectares locked in conflict; 68% involve common lands** | same body of work | **[S]** |
| ★ **"Land market distortions erode annual GDP growth by an estimated 1.3%"** | **Frontiers/NAKSHA paper (2026)** | **[V]** as a peer-reviewed statement — **this is the cleanest economic number available and it comes from DoLR's own Joint Secretary's paper.** Use this one. |
| ★ **ULBs generate only 32% of revenue internally** due to sub-optimal tax assessment | Frontiers/NAKSHA paper (2026) | **[V]** |
| ★ **Land and property taxes contribute 0.6% of GDP in low-income economies vs 2.2% in industrialised nations** | Frontiers/NAKSHA paper (2026) | **[V]** — excellent for the "municipal finance" benefit slide |
| **DAKSH 2016: ~₹500/day litigant expenditure on land litigation; ~₹850/day business loss** | DAKSH | **[S]** |
| **Capital investment ~3% of GDP stalled due to land acquisition problems** | counterview.net reporting | **[U]** |

## 6.4 Scale of the urban problem — [V] (all from the Frontiers/NAKSHA paper, 2026)

- India has **7,933+ urban settlements** covering approximately **10.2 million hectares**.
- **Only 4 states maintain structured urban land records.** ★ (The NAKSHA booklet independently names them: *"Most urban areas, except in a few states like Tamil Nadu, Maharashtra, Gujarat and Goa, have outdated or unstructured land records"* — **[V]**, NAKSHA Booklet p.5. Two independent sources agreeing on "4 states" is strong.)
- Approximately **13 million urban households live in 108,000 slums.**
- Total ULBs in India: **4,912** (NAKSHA Booklet p.4) — **[V]**

★ **"Only 4 of 28 states maintain structured urban land records"** is, in my judgement, the single strongest one-line problem statement available, and it is double-sourced including DoLR's own booklet.

## 6.5 Positional accuracy of legacy Indian cadastral maps — ★★ [V] BEST HARD DATA

**Sengupta, A., Lemmen, C., Devos, W., Bandyopadhyay, D., & van der Veen, A. (2016).** *"Constructing a seamless digital cadastral database using colonial cadastral maps and VHR imagery – an Indian perspective."* **Survey Review, 48(349), 258–268.** DOI: 10.1179/1752270615Y.0000000003. **Open Access.**
Full text: https://ris.utwente.nl/ws/files/20643154/sengupta_constructing.pdf

**Study:** West Bengal, ~327 km² planning area (258 mouzas + 26 municipal wards), represented by **310 analogue cadastral map sheets** at **1:3960 scale**. Maps mostly from **pre-1920s surveys and 1950s mapping**. Georeferenced against **GeoEye-1 pan-sharpened imagery** using **10–15 GCPs per sheet** and a **first-order (affine/polynomial) transformation**.

### ★ Measured RMSE distribution across the 310 sheets

| RMSE range | No. of sheets |
|---|---|
| < 2.00 m | 7 |
| 2.01 – 3.00 m | 64 |
| **3.01 – 4.00 m** | **185** |
| 4.01 – 5.00 m | 47 |
| > 5.01 m | 7 |

**Read-off: the modal positional error of Indian legacy cadastral sheets is 3–4 metres.** Over 88% of sheets fall between 2 m and 5 m.

**Acceptability benchmark used (Ghosh & Dubey, 2009):** acceptable RMSE for a digital dataset at **1:10,000 scale is 4.38 m**, composed of plotting accuracy (0.25 mm), georeferencing accuracy (0.25 mm) and digitising accuracy (0.3 mm) on the map sheet. **>80% of sheets met this.**

**First- vs second-order transformation comparison (sample, metres):**

| Sample | 1st order | 2nd order |
|---|---|---|
| 1 | 3.668 | 3.177 |
| 2 | 3.171 | 2.510 |
| 3 | 3.962 | **1.339** |
| 4 | 4.089 | 3.096 |
| 5 | 5.010 | 2.889 |

★★ **This table is our technical money shot.** Higher-order / non-rigid transformation cuts error by up to ~66% on the worst sheets — but choosing the right transformation order *per sheet* is currently a manual judgement call. **Automating that choice is a concrete, demonstrable contribution.**

### ★ Documented failure modes (all [V], from the same paper)
1. **Gaps and overlaps between adjoining mouza boundaries** — adjacent sheets do not fit; they overlap or leave voids (mapping/plotting error).
2. **Multi-sheet mouzas** — one mouza split across several sheets with unclear division between sheets.
3. **Canal double-counting** — a canal used as a shared boundary is drawn on *both* adjacent mouza sheets, so the same area is counted twice in area calculations.
4. **River dynamics** — original mouza area lost to a river, or new area accreted; large legal-vs-digitised area discrepancies.
5. **Paper degradation** — maps plotted on low-quality paper or cloth, subject to **shrinkage, wrinkling, folding and tearing**; scanning adds further error.
6. **Crude map lines** — *"the 'map lines' in the analogue cadastre are themselves crude and the scanned version of the line is often more than 4–5 pixels wide."* ← inherent boundary ambiguity of several decimetres-to-metres before any transformation is applied.
7. **Area attribute inconsistency** — digitised parcel area ≠ authorised/legal area recorded in the RoR.

★ **Contrast to put on one slide:**
- **New NAKSHA ORI:** RMSEx, RMSEy **≤ 10 cm** (SoI circular)
- **Legacy cadastral sheet:** modal RMSE **3–4 m** (Sengupta et al. 2016)
- **That is a 30–40× accuracy mismatch between the two layers we are asked to harmonise.** Naive overlay is not merely imprecise — it is meaningless. This single comparison justifies the entire project.

## 6.6 Historical survey practice — [V]

**Prof. P. Misra, "Cadastral surveys in India", Coordinates, June 2005** — https://mycoordinates.org/cadastral-surveys-in-india/
- Revenue surveys initiated by the East India Company towards the end of the 18th century; village boundaries by traverse survey; ground detail by **plane-tabling and chain survey** recorded in **Field Measurement Books (FMB)**.
- Early aerial survey, **Malda district, 1929**, at **16 inches to 1 mile**.
- Standard rural cadastral scale **1:4000**; urban cadastres **1:500 to 1:4000**.
- Achievable accuracies stated: differential GPS **< 5 cm**; orthophoto mapping **~60 cm**; high-resolution satellite imagery **3–4 m planimetric**.
- ★ **North/south legal divergence:** *northern states recognise the graphic map output as the legal document; southern states prioritise the Field Measurement Book.* ← This is a genuine, deep harmonisation problem: in the north the polygon is authoritative; in the south the *measurements* are authoritative and the polygon is a derived sketch. Our system must respect both regimes.

**Thakur, V., Doja, M.N., & Faizi, A.A.A. (2017).** *"Indian Cadastral Survey System – Comparative Study."* IJEDR 5(4), 1579+. https://rjwave.org/ijedr/papers/IJEDR1704252.pdf — **[V]**
- Survey of India established **1767**; carried out revenue survey until **1904**; after 1904 **each state became responsible for its own cadastral survey and evolved its own system**. ★ This one fact explains every downstream interoperability problem in the country.
- Taxonomy: juridical/legal cadastre, fiscal cadastre, multipurpose cadastre. Identifies multipurpose-cadastre integration risks: legal liability for integrated data, data ownership, data protection, **data quality (old survey data less accurate)**, **adoption of standards (agencies reluctant to change tried-and-tested procedures)**, data pricing.

## 6.7 Cost and time of resurvey — [V] (rare, hard, official numbers)

From the **Tamil Nadu Department of Survey and Settlement** DILRMP Regional Review deck (Bengaluru, 06.09.2024):
https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2024/10/20241004518377083.pdf

- ★ **Tamil Nadu requested DoLR revise the admissible resurvey rate to ₹56,725 per sq km.** — a genuine, official, per-unit cost of cadastral resurvey.
- **Resurvey with DGPS + ETS** in 3 districts (Kanniyakumari, Nilgiris, Krishnagiri): *"will be expedited and completed in 2 years time."*
- **Resurvey in 12 districts using Hybrid Technology (Drone + DGPS)**, DoLR-approved, to start 2025, *"completed in 3 years time."*
- ★ **So: cadastral resurvey currently takes 2–3 years per tranche of districts, even with drones and DGPS.**
- Tamil Nadu has digitised **55.20 lakh Field Measurement Sketches (FMS)**.
- Tamil Nadu DILRMP financial position as on 31.08.2024: GoI released ₹6,612.63 lakh + State ₹2,547.21 lakh = ₹9,159.84 lakh total; expenditure ₹8,238.07 lakh.
- Modern Record Rooms: sanctioned for **313 taluks**, created in **232**, pending in **81**.
- Tamil Nadu's claimable incentives under Special Assistance 2024-25 totalled **₹550 crore** across 5 milestones (₹50 cr geo-referencing; ₹200 cr online registry + interlinking; ₹100 cr legacy registries online; ₹50 cr RoR/cadastral computerisation; ₹150 cr revenue court modernisation).
- Milestone-1 (Sub-division / Survey / Re-survey) carries an admissible incentive of **₹1,000 crore** (for 3 sub-components, proportionate for partial achievement).

★ **Cadastral finalisation duration, defensible answer:** *"Resurvey of a district tranche is officially planned at 2–3 years even using drone + DGPS (Tamil Nadu, 2024). NAKSHA's per-ULB pilot was scoped at 1 year and, as of March 2026, ground truthing was still below 60% in 55 of ~150 pilot ULBs."* Both halves are sourced.

## 6.8 ⚠ WHAT I COULD NOT FIND — state this honestly if asked

- **[U] No published figure for man-hours or rupee cost of *manual GIS integration/harmonisation* work specifically** (as distinct from survey or digitisation cost). I searched for man-hours per village, cost per layer, and analyst-days per ULB; nothing credible exists in the public domain. **Do not invent one.** If you need a cost proxy, use the ₹56,725/sq km resurvey rate and the ₹10–30 crore per-milestone urban incentive, both of which are real.
- **[U] No published national statistic on the time to *finalise* an urban cadastre end-to-end.** The 2-3 year and 1-year figures above are plans and pilot scopes, not measured outcomes.
- **[U] No accuracy/throughput benchmark published for Bhu-Naksha or any Indian land-records GIS tool.**
- **[U] The NAKSHA SDMS data schema** — exists (referenced in the SoI circular) but is not retrievable as text; the SOP PDF is scan-only.
- **[U] SVAMITVA's specific drone survey accuracy specification** — SOP PDF unreachable (TLS failure).
- **[U] The exact 14-character composition rule of ULPIN.**
- **[U] NCAER Land Records and Services Index beyond the 2021 edition.** N-LRSI 2020 and 2021 exist (MP ranked 1st both years; 2021 order MP > West Bengal > Odisha > Maharashtra > Tamil Nadu; weighting 60% extent of digitisation / 40% quality of records). https://ncaer.org/publication/ncaer-land-records-and-services-index-n-lrsi-2021/ — **no 2024+ edition found.**

---

# 7. Indian Geospatial Standards & Policy

## 7.1 National Geospatial Policy 2022 — [V] ★ (extracted from the PIB backgrounder, which cites the DST original page-by-page)

**Notified 28 December 2022** by the Government of India; administered by the **Department of Science and Technology (DST)**, Ministry of Science and Technology. Long-term vision to **2035**.
Original: https://dst.gov.in/sites/default/files/National%20Geospatial%20Policy.pdf
PIB backgrounder (27 Feb 2025, "Powering India's Vision for Viksit Bharat"): https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/feb/doc2025227509401.pdf
SoI landing page: https://surveyofindia.gov.in/pages/national-geospatial-policy-2022

**Vision:** position India as a global leader in the geospatial sector, fostering a world-class innovation ecosystem, leveraging geospatial technology for economic growth, ensuring easy access to geospatial data for businesses and citizens.

### Goals **By 2025**
- Enabling policy and legal framework for liberalisation and democratisation of geospatial data.
- Enhance availability and accessibility of high-quality location data across sectors.
- **A unified digital interface for accessing geospatial data collected through public funds.**
- ★ **Redefine the National Geodetic Framework using modern positioning technologies, with online accessibility.**
- ★ **Create a high-accuracy geoid model for the entire country.**
- Strengthen national and sub-national geospatial governance.

### Goals **By 2030**
- ★ **High-resolution topographical surveys: 5–10 cm for urban/rural areas; 50–100 cm for forests/wastelands.**
- ★ **High-accuracy DEM: 25 cm for plains; 1–3 m for hilly/mountainous areas.**
- Establish a **Geospatial Knowledge Infrastructure (GKI)** underpinned by an **Integrated Data and Information Framework**.
- Enhance geospatial skills, capabilities and awareness.

### Goals **By 2035**
- High-resolution bathymetric data for inland waters and deep-sea topography (Blue Economy).
- **Survey and map sub-surface infrastructure in major cities and towns.** ← directly relevant to the *utility networks* component of our problem statement.
- ★ **Develop a National Digital Twin for major urban centres.** ← NAKSHA's LOD-2 3D models are literally the first bricks of this. Say so.

### Key focus areas
Geospatial for transformation & SDGs; Atmanirbhar Bharat/self-reliance; **global best practices & adoption of the UN-GGIM Integrated Geospatial Information Framework (IGIF)**; robust geospatial & ICT infrastructure with a **defined data custodianship model**; fostering innovation & startups; ★ **Standards & Interoperability — "advocating open standards, open data, and compliance frameworks… ensures seamless integration and interoperability of geospatial information"**; capacity development & education; ease of doing business; **democratisation of data — SoI and other publicly funded geospatial data treated as a public good.**

### Associated initiatives — [V]
- **National Geospatial Data Repository** — centralised platform consolidating geospatial datasets from government and private entities for sharing, interoperability and accessibility.
- ★ **Operation Dronagiri** — launched **13 November 2024**, a pilot under NGP 2022, in **five states: Uttar Pradesh, Haryana, Assam, Andhra Pradesh, Maharashtra**. Its centrepiece is an **Integrated Geospatial Data Sharing Interface (GDI)** for cross-sector data access and sharing, envisaged for nationwide rollout under a PPP model. — **Cite this: our platform is a concrete instantiation of the GDI concept for the land-records domain.** https://pib.gov.in/PressReleasePage.aspx?PRID=2073284
- **PM Gati Shakti** National Master Plan — integrates 16 ministries; uses spatial planning tools from **ISRO** and **BiSAG-N**; NGP 2022 is explicitly aligned to it.

## 7.2 Survey of India CORS network

- **[V]** Launched as the "National Survey Network" by Union Minister Dr Jitendra Singh. PIB PRID 1967096 / DST: https://dst.gov.in/union-minister-dr-jitendra-singh-launches-state-art-latest-national-survey-network-nationwide
- **Station count — ⚠ CONFLICT / [S]:** "more than 1,000 CORS stations"; another source says "approximately 1,100 CORS sites". The official SoI CORS page (https://surveyofindia.gov.in/pages/continuously-operating-reference-stations-cors-) does **not** state a count, and the CORS portal (https://cors.surveyofindia.gov.in/) requires login. **Safe wording: "a pan-India network of 1,000+ CORS stations."**
- **Accuracy — [S] / ⚠ CONFLICT:** reported variously as "centimetre-level real-time positioning", "±3 cm", and "2–3 cm within a couple of minutes". **Safe wording: "centimetre-level (few-cm) real-time positioning."**
- ★ **[V] — the authoritative accuracy statement for our purposes is the NAKSHA spec itself:** control/check points established via CORS must achieve **RMSEx, RMSEy better than 5 cm** (SoI circular, §1.9). Quote that instead; it is exact and directly relevant.
- **[V] Services offered** (SoI CORS page): **NRTK** (Network Real-Time Kinematic, incl. continuous topographic survey), **DGNSS**, **VRS** (Virtual Reference Station) data download, and **online post-processing**. SOPs published for registration, data download and Network RTK survey.
- **[V]** CORS is used by **both** SVAMITVA and NAKSHA; in NAKSHA, both contractors and SoI wings are *required* to use **SoI's CORS / Passive GCP libraries** for consistency.
- Other stated uses: upper-atmosphere and space-weather studies, meteorology, plate motion and tectonics, seismology, hydrology.

## 7.3 Coordinate reference systems in use in India

### What NAKSHA mandates — [V] ★ (use this; it is definitive)
- **Projection: Universal Transverse Mercator (UTM)**
- **Horizontal datum: WGS 84**
- **Vertical datum:** WGS 84 ellipsoidal realised via the SoI CORS network, **and** DEM/DSM/DTM additionally on the **Indian Vertical Datum** via **SoI's Geoid Model** (supplied/developed by G&RB Dehradun).
Source: SoI circular T-1147015/2/2024-TECHNICAL-SGO, 10 Feb 2025.

**UTM zones covering India:** mainland India spans **UTM zones 42N–47N** (approximately 66°E–96°E), with Andaman & Nicobar in **zone 46N–47N** and the western extremity of Gujarat in **zone 42N**. — **[U]** as a *cited* fact; this is derived from the standard 6°-wide UTM zone definition (zone = floor((lon+180)/6)+1) rather than from a retrieved Indian government document. It is arithmetically certain but I did not find an official SoI page stating it. **Safe to state as geometry, not as a citation.**

### Legacy systems still in the data — [V]/[S]
- **Everest 1830 spheroid** — defined by Sir George Everest in 1830; **non-geocentric**, its centre offset roughly **1 km** from the Earth's centre of mass. Basis of the historical **Indian Grid** (Lambert Conformal Conic zones 0, I, IIA, IIB, IIIA, IIIB, IVA, IVB) used on all legacy topographic and many cadastral products. **[S]** — https://geospatialworld.net/article/coordinate-transformation-between-everest-and-wgs-84-datums/ ; https://deeppradhan.heliohost.org/gis/indian-grid/
- **WGS 84 series maps** introduced by SoI alongside the Everest series; WGS-84 series made available to civil users. Everest↔WGS84 transformation parameters determined by SoI's **Geodetic & Research Branch** with DST funding. **[S]**
- **ITRF / Indian Terrestrial Reference Frame** — secondary sources mention **ITRF2000** alignment. **[S]**, weakly sourced.
- ⚠ **Prof. Misra (2005) recommended that "all cadastral surveys in India should use the Everest Spheroid for uniformity"** — that recommendation has been superseded in practice by the NAKSHA/WGS-84 mandate, but it explains why so much legacy cadastral data sits on Everest.

### "New Indian Geodetic Datum" — ⚠ IMPORTANT CORRECTION
> **[U] — I found NO evidence of a promulgated "Indian Geodetic Datum (IGD) 2023" or any dated new national geodetic datum.** A WebFetch summariser asserted "Indian Geodetic Datum (IGD) implementation" for NGP 2022, but when I extracted the actual PIB/DST policy text, **no such term appears**. What the policy *actually* commits to (by 2025) is: *"Redefine the National Geodetic Framework using modern positioning technologies, with online accessibility"* and *"Create a high-accuracy geoid model for the entire country."*
>
> **Do not claim a "new Indian Geodetic Datum" on a slide.** Correct, defensible statement: *"NGP 2022 commits to redefining the National Geodetic Framework and delivering a national high-accuracy geoid model by 2025; NAKSHA already mandates a WGS 84 / UTM horizontal frame realised through the SoI CORS network, with vertical heights on the Indian Vertical Datum via SoI's geoid model."* Every clause of that is sourced.
>
> **[V]** The **Indian Vertical Datum (IVD)** *is* real and *is* named in the NAKSHA technical circular. It is the vertical datum. There is no correspondingly named new *horizontal* datum in any source I retrieved.

### ★ The harmonisation implication for our architecture
A single Indian city's incoming layers can plausibly sit in: WGS 84 / UTM (new ORI, DSM/DTM, GNSS rover points); Everest 1830 / Indian Grid (legacy SoI topo sheets); an **unprojected local sheet coordinate system with a per-state scale factor** (Bhu-Naksha shapefiles — UP ×4000, HP ×22 karam); an arbitrary scanned-image pixel frame (un-georeferenced cadastral scans); and WGS 84 geographic (municipal GIS, utility GIS, OSM/commercial building footprints). **A CRS-resolution and datum-transformation engine is not a nice-to-have in this problem — it is step zero.** Say this explicitly; it demonstrates you understand the problem at a level most teams won't.

## 7.4 NUIS — ⚠ NAME COLLISION, be careful

**Two different things share the acronym NUIS. Know both or you will get caught.**

**(a) National Urban Information System (2006)** — **[V]**
- A national mission initiated by the then **Ministry of Urban Development (MoUD)** in **2006**, implemented with **TCPO (Town and Country Planning Organisation)**.
- Purpose: generate an urban geospatial database for **152 towns** using high-resolution satellite data. *(Coincidentally also 152 — do not confuse with NAKSHA's 152 ULBs.)*
- ★ **Three standardised scale tiers:**
  - **1:10,000** — Concept Plan / Master Plan, monitoring urban areas; master & zonal planning parameters
  - **1:2,000** — zonal/site plan and **Municipal GIS**; detailed town planning schemes and urban administration
  - **1:1,000** — **Utility GIS**: power, water supply, sewerage and other utilities, for utility planning and management
- Coverage plan: 1:10,000 and 1:2,000 for **152 towns**; **1:1,000 utility maps for 24 towns**.
- NUIS **Design Standards** document exists and was used as the technical basis by Sengupta et al. (2016): `http://tcp.cg.gov.in/nuis/Design_Standards.pdf`
- Guidelines: https://state.bihar.gov.in/urban/cache/25/Docs/NUIS-Guidelines.pdf ; TCPO: http://tcpo.gov.in/national-urban-information-system

★ **The 1:1,000 / 1:2,000 / 1:10,000 tiering is the pre-existing Indian urban GIS standard, and NAKSHA MAP-1 publishes at 1:500 — finer than any NUIS tier.** That is a concrete, citable standards gap: *there is no national urban GIS content standard at 1:500*. Excellent differentiation material.

**(b) National Urban Innovation Stack (NUIS)** — **[V]** — a MoHUA digital-blueprint document, part of the **National Urban Digital Mission (NUDM)** ecosystem. Completely different thing.
https://mohua.gov.in/dataSmartCities/uploads/resource/resourceDoc/Resource_Doc_1723187578_National_Urban_Innovation_Stack.pdf ; https://www.nudm.mohua.gov.in/nuis/

## 7.5 IUDX — India Urban Data Exchange — [V]

- Initiated and anchored by **MoHUA**; developed in partnership between the **Smart Cities Mission** and the **Indian Institute of Science (IISc), Bengaluru**.
- Fully **open-source, cloud-based** platform for secure sharing of all types of urban data; a seamless interface between data providers (incl. ULBs) and data users.
- Components: **Catalogue, Consent, Resource** — datasets can be searched, requested, permitted and exchanged.
- ★ **IUDX became the first software platform in India to fully adopt the Bureau of Indian Standards (BIS) Architecture and API Specifications for Unified Data Exchange.**
- Live catalogues exist per city, e.g. https://catalogue.cos.iudx.org.in/ , https://agra.catalogue.iudx.org.in/
Sources: https://iudx.org.in/platform/ ; https://www.nudm.mohua.gov.in/mission-artefacts/india-urban-data-exchange/ ; https://iudx.org.in/iudx-becomes-first-software-platform-to-fully-adopt-bis-standards-for-unified-data-exchange/

★ **Strong architectural play:** publish harmonised NAKSHA parcel layers as **IUDX-catalogued, BIS-conformant resources with consent-gated access.** This gives a real, Indian, standards-backed answer to "how does this integrate with the wider urban stack?" rather than inventing an API.

## 7.6 DIGIT — [V]

- **DIGIT** = *Digital Infrastructure for Governance, Inclusion and Transformation*, built by **eGov Foundation**.
- **India's largest microservices-based open-source platform for urban governance**; multi-tenant; deployed across **hundreds of ULBs**.
- Certified by the **Digital Public Goods Alliance (DPGA)**; **MIT License**.
- Modules: **property tax**, trade licences, grievance redressal (PGR), building plan approval, water & sewerage, finance.
- **DIGIT-Property Tax (PT)** is a self-serve citizen facility for real-time assessment and payment, automating municipal property tax operations.
Sources: https://www.digit.org/ ; https://digit.org/digit-urban-property-tax ; https://github.com/egovernments/DIGIT-OSS ; https://github.com/egovernments/Digit-Core

★ **Why this matters concretely:** NAKSHA MAP-2 requires *"integration of property holding details of ULBs."* In a DIGIT-running ULB, those property-holding details live in the DIGIT Property Tax registry with a **property ID**, not a parcel geometry. **Matching a DIGIT property ID to an ORI-derived parcel polygon to a revenue khasra to a ULPIN is exactly the spatial-entity-resolution problem we are solving.** Naming DIGIT, its data model, and its MIT licence turns a vague "integrate municipal records" claim into a specific, implementable one.

## 7.7 NGDRS — [V]
**National Generic Document Registration System** — a configurable centralised registration platform developed by **DoLR with NIC** under DILRMP. **28 States/UTs have adopted it**; e-Registration live or sharing data with the national NGDRS portal via UI/API. Supports online property valuation, deed preparation, appointment scheduling and payment.
https://ngdrs.gov.in/ ; https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1919270

Relevant because NAKSHA MAP-2 explicitly requires integration of **registration deeds** — NGDRS is the source system, and its API is the integration point.

## 7.8 MoHUA urban GIS standards — [U]
I found **no single consolidated "MoHUA urban GIS standard" document.** What exists is the NUIS 1:1,000/1:2,000/1:10,000 design-standards lineage (MoUD/TCPO, 2006), the BIS Unified Data Exchange standards (via IUDX), and NAKSHA's own SDMS schema (SoI/DoLR, not retrievable as text). **If asked, say that — the absence of a unified urban geospatial content standard is itself part of the problem.** ★

## 7.9 ISO 19152 — LADM — [V]
**ISO 19152 Land Administration Domain Model.** Original edition **ISO 19152:2012**; current **ISO 19152-1:2024 (Part 1: Generic conceptual model)**, with **Part 2: Land registration** in development.
- LADM is a **conceptual model, not a data product specification**. *"The purpose of the LADM is not to replace existing systems, but rather to provide a formal language for describing them, so that their similarities and differences can be better understood."*
- Four core packages: **parties**; **basic administrative units** with rights, restrictions and responsibilities (RRR); **spatial units** (parcels); and **spatial sources and representations**.
https://www.iso.org/standard/81263.html ; https://www.iso.org/standard/51206.html

**India-specific LADM work — [V]:** *Sengupta, A., Bandyopadhyay, D., Lemmen, C.H.J., & van der Veen, A. (2013). "Potential use of LADM in cadastral data management in India."* 5th LADM Workshop, Kuala Lumpur, Sept 2013. https://repository.tudelft.nl/record/uuid:a8bd9c8e-dbbd-4505-90cd-9bdf1c77cc3a
The paper asks exactly our questions: how to convert and link existing colonial maps and records into an LADM-based digital database; **how to document and publish the geometric quality of existing maps**; how to keep them up to date; **and how to integrate more accurate data after re-survey.** ★ That last question — how to fuse a new high-accuracy survey with an existing low-accuracy record without destroying the legal record — is literally our problem statement, posed in the academic literature 13 years ago and still open.

★ **Adopting LADM as our canonical target schema is defensible, international, and lets us say "we map every source into an ISO 19152 conformant model" instead of inventing a schema.**

---

# 8. Technical Prior Art & Competing Approaches

## 8.1 The closest prior art — ★★ READ THIS ONE

**Suwardhi, D., Ihsan, M., Widyastuti, R., Mukminin, A.H.U., Akbar, B., Pasaribu, S.K., Satwika, I.P., Nurmaulia, S.L., & Hernandi, A. (2025).** *"An Automated Framework for Cadastral Parcel Adjustment Using UAV Orthophotos, SAM, and ICP."* **ISPRS Archives XLVIII-2/W11-2025, 277–284.** Institut Teknologi Bandung, **Indonesia**.
https://isprs-archives.copernicus.org/articles/XLVIII-2-W11-2025/277/2025/isprs-archives-XLVIII-2-W11-2025-277-2025.pdf

**Problem they state (near-identical to ours):** *"inconsistencies remain in many registered parcels in Indonesia due to legacy georeferencing systems, fragmented survey methods, and non-uniform base maps."*

**Their pipeline:**
1. **VTOL fixed-wing UAV** at 300 m altitude → orthophotos at **~5 cm GSD** (same spec as NAKSHA), mapping scale **1:1,000**, validated by the national geospatial agency (BIG).
2. **Segment Anything Model (SAM)** in **zero-shot automatic mask generation mode** (no prompts, no training) → candidate boundary segments; filtered to retain closed shapes with consistent geometry, adjacency to roads/building outlines, or alignment with vegetation lines.
3. **Random Forest** classification of segments into 5 land-cover types.
4. **Geometric rule preprocessing:** simplification, **orthogonalization**, centerline extraction.
5. **Automatic parcel grouping into blocks** by spatial proximity.
6. **Block-level alignment via Iterative Closest Point (ICP)** (Besl & McKay 1992).
7. **Statistical inlier/outlier detection** on displacement vectors — mean and standard deviation of vector *lengths* **and angular deviations**; beyond ~2σ in length or direction = outlier. Explicitly *"avoiding rigid thresholding that may not generalize."*
8. **Hierarchical least-squares adjustment in 3 stages:** LS1 rigid (translation + rotation, block level) → LS2 similarity (add uniform scale) → LS3 per-parcel full 2D similarity (2 translations, 1 rotation, 1 scale) if residuals remain significant.

**Tested on:** two urban villages (Karangmekar, Baros, Cimahi City) — **177 blocks, 6,198 parcels**. Reported consistent reduction in average displacement and variance, notably at LS2/LS3.

**Related work they cite (our literature map):**
- **Šafář et al. (2021)** — UAV photogrammetry integrated into the official cadastral workflow of the **Czech Republic**.
- **Koeva et al. (2016)** — UAV imagery for parcel delineation in **Rwanda**, where no reliable base maps exist.
- **Crommelinck et al. (2019)** — **Mask R-CNN** for cadastral boundary delineation from high-resolution imagery. *(A related result reports a CNN approach on UAV imagery reducing processing time by **38%** and manual labour by **80%** — **[S]**, verify against the original before quoting.)*
- **Vafaeinejad et al. (2025)** — **SAM** for agricultural parcels: **digitisation time reduced up to 40%, IoU 92%**, with SAM's advantage being that it is a foundation model requiring **no additional training**. **[S]** as reported in the ISPRS paper.
- **Hadir et al. (2025)** — **SAM + LoRA** fine-tuning outperforming other deep models on complex agricultural parcels.
- ★ **Safra & Doytsher (2006)** — **mutually-nearest and normalized-weight matching followed by rubber-sheeting** to adjust cadastral inconsistencies. **This is the canonical parcel-matching + rubber-sheeting citation.**
- ★ **Vantas & Mirkopoulou (2025)** — **clustering to detect and classify typical error patterns in cadastral data**, enabling automated recognition of spatial anomalies. Published as *"Towards Automated Cadastral Map Improvement: A Clustering Approach for Error Pattern Recognition"*, **Geomatics 5(2), 16** — https://doi.org/10.3390/geomatics5020016
- **Besl & McKay (1992)** — ICP.

## 8.2 Other relevant literature

| Work | Relevance |
|---|---|
| **Crommelinck, S., Koeva, M., Yang, M.Y., & Vosselman, G. (2019).** *Application of deep learning for delineation of visible cadastral boundaries from remote sensing imagery.* Univ. of Twente. https://research.utwente.nl/en/publications/application-of-deep-learning-for-delineation-of-visible-cadastral/ | Three-step workflow: image segmentation → boundary classification (boundary likelihood) → **interactive delineation** connecting lines by predicted likelihood. **Note: still interactive — a human closes the loop.** |
| **Crommelinck et al. (2016)** review of automatic feature extraction from high-resolution optical sensors for UAV-based cadastral mapping | The standard survey of the field |
| **"Towards Automated Cadastral Boundary Delineation from UAV Data"** arXiv:1709.01813 | gPb contour detection pipeline |
| **"Automatic Cadastral Boundary Detection of Very High Resolution Images Using Mask R-CNN"** arXiv:2309.16708 | Mask R-CNN for boundary detection |
| **"From pixels to vectorized cadastral boundaries: Deep learning-based automated delineation of property boundaries in the Netherlands"** (ScienceDirect) | End-to-end raster→vector in a mature cadastre |
| ★ **Dhrubo, M.S., Akter, S., Shuaib, A.B., Tahmid, M.T., Hasan, Z., & Islam, A.B.M.A.A. (2024).** *"A Paradigm Shift in Mouza Map Vectorization: A Human-Machine Collaboration Approach."* arXiv:2410.15961 | **South Asian, hand-drawn *mouza* cadastral maps (Bangladesh)** — nearest cultural/technical analogue to Indian mouza/khasra maps. Method: separate plot boundaries from identifiers; CNNs for preprocessing and **plot-number detection**; custom smoothing from observed vector-map patterns; **human verification for final precision.** ⚠ **[U]** — the abstract reports outperforming existing processes but gives **no quantified time/accuracy figures**; don't quote numbers from it. |
| **Ferrod, R., Lecene, M., Sapkota, K., Leifman, G., Silverman, V., Beryozkin, G., & Lobry, S. (2026).** *"GroundSet: A Cadastral-Grounded Dataset for Spatial Understanding with Vector Data."* arXiv:2603.14609 | **3.8M annotated objects, 510k high-resolution aerial images, 135 semantic categories**, grounded in official cadastral vector data; benchmark over 7 spatial reasoning tasks. Finding: **RS-specialised and commercial models (e.g. Gemini) struggle zero-shot**, but standard architectures do well with good labelled data. ⚠ country of cadastral source not stated in the abstract. **Useful to cite as evidence that off-the-shelf VLMs are NOT sufficient for cadastral-grade spatial reasoning.** |
| **"Automated and semi-automated map georeferencing"**, *Cartography and Geographic Information Science* 47(1) | Survey of georeferencing automation |
| **"Automated Image Matching: An Efficient Tool for Georeferencing Historical Cadastral Maps"** (Springer) | Image-matching alternative to manual GCP picking |
| **"An open-source based toolchain for the georeferencing of old cadastral maps"** | QGIS + GDAL + Python toolchain |
| **"Aligning geographic entities from historical maps for building knowledge graphs"** arXiv:2012.03069 | **Textual label alignment to find matching entities → control points for rubber-sheeting**; also automatic extraction of road intersections as control points. ★ Directly applicable: khasra *numbers* printed on scanned maps are exactly such textual labels. |
| **"Illegal Buildings Detection from Satellite Images using GoogLeNet and Cadastral Map"** (ResearchGate) | Encroachment detection by imagery-vs-cadastre comparison |
| **"BCE-Net: Reliable Building Footprints Change Extraction based on Historical Map and Up-to-Date Images using Contrastive Learning"** arXiv:2304.07076 | Footprint change extraction against a historical map — the encroachment-detection formulation |
| **"Temporal Cluster Matching for Change Detection of Structures from Satellite Imagery"** arXiv:2103.09787 | Structure change detection |
| **ISO 19152 / LADM** and **Sengupta et al. (2013)** | See §7.9 |

## 8.3 Tools — what already exists (be honest about this; judges will know)

| Tool | What it genuinely does | What it does NOT do |
|---|---|---|
| **GRASS GIS `v.clean`** (https://grass.osgeo.org/grass-stable/manuals/v.clean.html) | Automatic topology repair. Tools: **`bpol`** (break/topologically clean polygons imported from non-topological formats **like shapefile**), **`rmarea`** (remove areas below a threshold, dissolving into the adjacent area with the longest shared boundary — i.e. sliver removal), **`snap`** (fuzzy tolerance to merge near-parallel lines), **`prune`** (vertex reduction preserving area topology), **`rmline`** (remove zero-length lines), plus break/rmdupl/rmdangle/chdangle. See also https://grasswiki.osgeo.org/wiki/Vector_topology_cleaning | **Requires a human to choose the snapping threshold and area threshold.** Wrong threshold = destroyed parcels or surviving slivers. It is a *tool*, not a *decision-maker*. **There is no per-parcel, evidence-weighted, legally-aware threshold selection.** |
| **PostGIS Topology** (`topology` extension, `TopoGeometry`) | Persistent topological model with shared edges/faces — edits propagate to all sharing features; prevents gaps/overlaps *by construction* going forward | Getting *legacy dirty geometry* into a valid topology is the hard part; the postgis-users list has long threads on the difficulty of deleting slivers/gaps once in a topology. Common practice is to clean in **GRASS `v.clean` first**, then load into PostGIS topology. |
| **QGIS + GDAL/OGR + PROJ** | Georeferencer with polynomial 1st/2nd/3rd order, **Thin Plate Spline (true rubber-sheeting)**, projective, Helmert; Topology Checker plugin; `ogr2ogr` reprojection; PROJ datum/grid transformations | All manual, per-layer, per-operator. No cross-source reasoning. GCP selection is by hand. |
| **FME (Safe Software)** / **Esri ArcGIS Data Interoperability** (which is *built on FME technology*) | Industry-standard spatial ETL: hundreds of formats, visual no-code schema mapping via FME Workbench, reusable "spatial ETL tools" in the geoprocessing framework. https://en.wikipedia.org/wiki/Spatial_ETL ; https://pro.arcgis.com/en/pro-app/latest/help/data/data-interoperability/spatial-etl-tools.htm | ★ **Schema mapping in FME is DECLARED BY A HUMAN, not inferred.** You draw the connectors. FME will faithfully execute a mapping; it will not tell you that `KHASRA_NO` in the revenue table and `SY_NO` in the municipal table are the same concept, nor resolve that they disagree for 12% of parcels. **Also: proprietary and licence-cost-prohibitive at 4,912-ULB scale** — a real argument for an open, DPG-aligned Indian stack. |
| **Esri ArcGIS (Parcel Fabric, Spatial Adjustment/rubber-sheet, Data Reviewer)** | Mature cadastral editing and QA | Proprietary, licence cost, US/Western cadastral assumptions (deed-based COGO), not built for khasra/FMB/mouza semantics or a 30–40× accuracy mismatch between layers |
| **SAM (Segment Anything Model)**, **Mask R-CNN**, **U-Net** | Strong at extracting *visible* boundaries from imagery | ★ **Extract what is VISIBLE. Cadastral/legal boundaries are frequently INVISIBLE** — no wall, no fence, no hedge. Crommelinck's own framing is "**visible** cadastral boundaries." This is the fundamental ceiling of the pure-vision approach. |
| **Bhu-Naksha** | The incumbent Indian tool (§5) | Manual per-state scale factors; no CRS handling; bespoke per-state RoR adapters; single-village patwari workflow |

## 8.4 ★ WHAT IS NOT SOLVED — our differentiation

Stated honestly and defensibly. Each point is grounded in a source above.

1. **No automated, evidence-weighted reconciliation across accuracy tiers.** Every tool assumes you know which layer is right. Nothing decides *"here the 10 cm ORI wins; there the legal RoR area wins; here flag for human adjudication."* The Sengupta 3–4 m vs NAKSHA 10 cm mismatch (§6.5) makes this the central unsolved problem, and Sengupta et al. (2013) posed it explicitly as an open LADM question: *how to integrate more accurate data after re-survey without discarding the legal record.*

2. **Transformation-model selection is still a human judgement.** Sengupta et al. showed 2nd-order beat 1st-order by up to ~66% on the worst sheets — but *choosing* per sheet is manual. **No system auto-selects transformation order / rubber-sheeting model per map sheet from its own residual structure.**

3. **Schema matching for Indian land attributes is entirely manual.** FME/Esri Data Interoperability require a human to draw every mapping. Bhu-Naksha's own solution is *bespoke per-state adapters*. Meanwhile the vocabulary genuinely differs (khasra / survey number / dag / sy.no / plot no; khatauni / jamabandi / patta / chitta / 7-12) and the *legal semantics* differ north vs south (§6.6, §9). **No published automated schema-matching system exists for Indian land-record attributes.**

4. **Topology cleaning has no legal-consequence awareness.** `v.clean rmarea` will happily dissolve a 3 m² sliver — which may be a real, owned, taxed, litigated parcel. **No tool distinguishes "digitisation artefact sliver" from "genuine tiny urban parcel."** This is a classifiable problem (area, shape compactness, presence of a khasra number, presence in the RoR, presence of a building footprint) and nobody has classified it.

5. **Vision models find visible boundaries; cadastres contain invisible ones.** SAM/Mask R-CNN ceiling (§8.3). The fusion of *imagery evidence* + *legacy geometry* + *textual record* + *utility network topology* to infer an invisible boundary is not addressed in the literature I found.

6. **Cross-agency entity resolution is unaddressed.** The Frontiers/NAKSHA paper names *"parallel, non-interoperable records"* across Revenue / ULB / Development Authority / Sub-Registrar as a top friction point and lists *"insufficient mechanisms for cross-agency data interoperability"* as a systemic void — **and then recommends "automated GeoAI-driven updating mechanisms."** The programme's own Joint Secretary is describing the gap and asking for our solution.

7. **The state-of-the-art (Suwardhi et al. 2025) is single-source and single-country.** It aligns *one* cadastral layer to *one* UAV orthophoto in Indonesia. It does **not** handle: multiple heterogeneous legacy sources, attribute/schema harmonisation, CRS/datum/unit heterogeneity (the UP ×4000 / HP ×22 problem), utility networks, or Indian tenure semantics. **Extending block-ICP + hierarchical LS adjustment to an n-source, schema-aware, CRS-resolving, legally-aware pipeline is a genuine, non-trivial, publishable contribution — and it is exactly what the problem statement asks for.**

8. **No open benchmark or ground truth for Indian cadastral harmonisation.** GroundSet (2026) provides cadastral-grounded vector data but not for India, and shows commercial VLMs fail zero-shot. **There is no Indian equivalent.** Producing even a small one for a pilot ULB would be a defensible deliverable.

9. **Bhu-Naksha's own manual documents the unsolved state:** per-state hard-coded scale factors and hand-written per-state RoR adapters are the incumbent national solution to unit and schema heterogeneity (§5.6).

> ★ **One-sentence differentiation:** *"The literature solves boundary **extraction** and single-layer **alignment**. NAKSHA's actual bottleneck — documented by DoLR's own Joint Secretary as ground truthing and cross-agency integration — is multi-source **reconciliation** under a 30–40× accuracy mismatch, heterogeneous CRSs and units, and divergent north/south legal semantics. Nobody has automated that."*

---

# 9. Terminology Glossary

> ⚠ **Read this warning.** Indian land terminology is **not standardised across states** — the IJEDR (2017) paper establishes why: SoI conducted revenue surveys until **1904**, after which **each state evolved its own system**. Sources for these terms are mostly commercial/legal-services glossaries; I could not find a single authoritative DoLR national glossary. Terms marked **[V]** are corroborated by a primary or academic source; the rest are **[S]** from consistent glossary agreement. **When in doubt in front of judges, name the state.** Saying *"in UP the RoR is the khatauni; in Punjab/Haryana it's the jamabandi; in Tamil Nadu the patta/chitta"* is far safer and far more impressive than asserting a single national term.

## 9.1 The parcel and its identity

| Term | Definition | Region | Conf. |
|---|---|---|---|
| **Khasra** | The **survey/plot number** assigned to an individual surveyed land parcel within a revenue village. Also the register of such plots with land and crop details. *The unit of geometry.* | North India (UP, MP, Rajasthan, Bihar, Haryana, Punjab, HP, Uttarakhand) | [S] strong |
| **Survey number** | The equivalent of khasra in South/West India — unique identifier per parcel from the revenue survey. | Tamil Nadu, Karnataka, AP, Telangana, Maharashtra, Gujarat | [S] strong |
| **Sub-division number** | Identifies a **split of a survey number**. On partition, `123` becomes `123/1`, `123/2`, or `123/1A`. Recursive sub-division is a principal driver of record drift. | South India esp. TN | [S] strong |
| **Dag** | West Bengal's term for the individual plot on a mouza map. | West Bengal | **[V]** — Sengupta et al. 2016 |
| **Mouza** | The **revenue village**, the unit of cadastral survey. *"In West Bengal, the unit of survey for cadastral mapping and land records is a mouza (i.e. revenue village)."* | West Bengal, Bihar, Assam, Odisha, Bangladesh | **[V]** — Sengupta et al. 2016 |
| **ULPIN / Bhu-Aadhaar** | 14-character national parcel identifier generated from geo-referenced vertex coordinates (ECCMA PNIU standard). | National | **[V]** — §3 |

## 9.2 The records

| Term | Definition | Region | Conf. |
|---|---|---|---|
| **Record of Rights (RoR)** | The authoritative **textual** record: landholder names, plot sizes/extent, revenue rates, rights and tenancy. Maintained by the **Revenue Department**. **This is the generic national English term**; each state has a vernacular name for it. | National (generic) | **[V]** — PRS |
| **Jamabandi** | **The RoR of a village** in Punjab, Haryana, HP. Contains owner names, area, shares of owners, other rights; also cultivation, rent, revenue and cesses payable. Traditionally revised on a **four-year cycle**. | Punjab, Haryana, HP, J&K, Rajasthan | [S] strong |
| **Khatauni** | The register compiling, **by holder**, all khasra plots held or cultivated by a person or family in a village — i.e. the *account* view, versus khasra's *plot* view. | UP, Uttarakhand, MP, Bihar | [S] strong |
| **Khewat** | A list of the **owner's** holdings (ownership account). In Punjab/Haryana practice, **khewat = ownership account** and **khatauni = cultivation/possession account** — a distinction that matters legally. | Punjab, Haryana, HP | [S] |
| **Khata** | Generic term for an **account/ledger** of holdings attached to a landholder. In **Karnataka (esp. BBMP/Bengaluru urban)**, "**Khata**" (A-Khata / B-Khata) is a *municipal property tax account*, not a revenue RoR — ★ **a classic and dangerous ambiguity in an urban context.** | Widespread; urban Karnataka usage distinct | [S] |
| **Khatedar** | The person in whose name a khata/khatauni stands — the recorded holder. Rajasthan uses **"Khatedari" tenure** as a specific statutory tenancy class. | North India, esp. Rajasthan | [S] |
| **Patta** | **The ownership/title document** issued by the Revenue Department naming the holder of a survey number, with extent, land classification and tax due. In TN, the canonical ownership record. Elsewhere (e.g. Odisha, Rajasthan, Assam) "patta" can mean a *grant/lease* of government land — ★ **not the same thing.** | South India (TN esp.); different sense elsewhere | [S] strong |
| **Chitta** | An extract from the Patta register giving **current ownership and land details** (ownership, extent, classification — *nanjai* wet / *punjai* dry). | Tamil Nadu | [S] strong |
| **Adangal** | "Village Account No. 2" — maintained by the **Village Administrative Officer (VAO)**; documents land ownership, **crop patterns**, trees on government land, and land-revenue payment records for the past three years. AP/Telangana equivalent: **Pahani**. | Tamil Nadu (Adangal), AP/Telangana (Pahani) | [S] strong |
| **A-Register** | TN government register containing survey number, sub-division number, patta number, area, tax details, soil type and quality, land type, water resource, owner name. | Tamil Nadu | [S] |
| **7/12 extract (Satbara)** | Maharashtra's combined RoR — Village Form 7 (rights) + Form 12 (crops). | Maharashtra | [S] |
| **Khasra Girdawari** | **Harvest Inspection Register** — periodic crop inspection record kept by the patwari. | North India | [S] |
| **Misal Haqiyat / Misl-e-Haqiyat** | The RoR prepared at the time of original **settlement**. | North India | [S] |
| **Shajra** | The **village cadastral map** (the graphical sheet showing khasra boundaries). *Shajra Kishtwar* = the field map; *Shajra Nasab* = the pedigree/genealogy table of owners. | North India | [S] |
| **FMB — Field Measurement Book / Field Measurement Sketch (FMS)** | The **measurement record** per survey number — bearings and distances. ★ In **southern states the FMB is the legally prioritised record**, and the graphic map is derived; in **northern states the graphic map itself is recognised as the legal document.** Tamil Nadu has digitised **55.20 lakh FMS**. | South India primarily | **[V]** — Misra 2005; TN DILRMP deck |
| **Tippan** | The field sketch / measurement sketch (Maharashtra, MP, Gujarat usage). Named alongside FMB in DILRMP's "digitisation of cadastral maps/FMBs/Tippans" component. | Maharashtra, MP, Gujarat | **[V]** — DILRMP component list |
| **Bhulekh / Bhu-Abhilekh** | Hindi for **"land records"** — the **textual** record (ownership, extent, use). Most north-Indian state land-record portals are branded *Bhulekh*. | North India | [S] |
| **Bhu-Naksha** | Literally **"land map"** — the **spatial/map** counterpart to Bhulekh, and also the name of NIC's cadastral mapping software (§5). | National (NIC software) | **[V]** — §5 |

★ **The Bhu-Abhilekh vs Bhu-Naksha distinction is THE clean way to frame the problem to a judge:** *"India has largely solved Bhu-Abhilekh — 95% of RoRs are computerised. It has not solved Bhu-Naksha — only 68% of cadastral maps are digitised and only 49% are georeferenced. And it has barely begun on joining the two — only 26% of cadastral maps were linked to RoR as of 2017."* Three numbers, one narrative, all sourced (§2.4).

## 9.3 Processes

| Term | Definition | Conf. |
|---|---|---|
| **Mutation (Intkal / Dakhil-Kharij / Namantaran)** | Recording a **change of ownership** in the RoR following transfer by registered deed, inheritance, survivorship, bequest, partition or lease — sanctioned by a revenue officer. ★ **Mutation is the update mechanism and its failure/lag is the primary cause of record–reality divergence.** DILRMP reported only **47% of mutations computerised as of Sept 2017**. | [S] def., **[V]** stat |
| **Takseem** | Mutation involving **partition** of land among co-sharers. | [S] |
| **Tabadala** | Mutation of **exchange** between landowners. | [S] |
| **Hibba** | Property transfer by **gift**. | [S] |
| **Girdawari** | Periodic **crop inspection** by the patwari. | [S] |
| **Settlement / Re-settlement** | The periodic comprehensive survey and revision of the RoR and maps for a whole area. The base event that produced most of India's cadastral maps — largely colonial-era (§6.5-6.6). | **[V]** |
| **Survey / Re-survey** | Under DILRMP, re-establishing parcel geometry with modern instruments (**DGPS, ETS**, now drone hybrids). **Only 9% of villages completed as of Sept 2017**; TN plans 2–3 years per district tranche. | **[V]** |

## 9.4 Land classification

| Term | Definition | Conf. |
|---|---|---|
| **Abadi / Abadi Deh** | The **inhabited/residential area of a village** — houses, streets, common buildings. ★ **Historically excluded from the cultivable-area cadastre and recorded separately**, which is exactly why it had no property records and why **SVAMITVA exists**. | [S] strong, thematically **[V]** |
| **Gair Mumkin** | **Non-cultivable / barren** land. Compound forms are common and important: *Gair Mumkin Abadi Deh* (non-cultivable inhabited area), *Gair Mumkin Rasta* (road), *Gair Mumkin Nadi* (river), *Gair Mumkin Pahar* (hill). ★ In an urban harmonisation context, *gair mumkin* classes are where roads, drains and public land live in the revenue record — **they are the revenue record's version of the utility/infrastructure layer.** | [S] strong |
| **Banjar** | **Uncultivated** land; commonly *Banjar Jadid* (recently fallow) vs *Banjar Qadim* (long fallow — typically not cultivated for four or more cropping seasons). | [S] |
| **Barani** | **Rain-fed** land. | [S] |
| **Nahri / Chahi** | **Canal-irrigated / well-irrigated** land. | [S] |
| **Nanjai / Punjai** | **Wet (irrigated) / dry** land classification. | [S] — Tamil Nadu |
| **Natham** | Village **house-site** land in Tamil Nadu (the TN analogue of abadi). *Natham puramboke* = government-owned house-site poramboke. | [S] |
| **Poramboke / Puramboke** | **Government land not assigned to any individual** — roads, water bodies, grazing land. The TN/South analogue of gair-mumkin government land. | [S] |

## 9.5 Administration

| Term | Definition | Conf. |
|---|---|---|
| **Tehsil / Taluk (Taluka)** | The sub-district revenue administrative unit. **"Tehsil" is used across the northern states; "taluka/taluk" in Maharashtra, Gujarat, Goa, Karnataka, Kerala and Tamil Nadu.** Headed by a **Tehsildar** (or *Talukdar*). DILRMP's "Modern Record Room" component is explicitly at **tehsil level**. | [S] strong; **[V]** on DILRMP tehsil-level record rooms |
| **Patwari** | The **village-level revenue officer/accountant**, responsible for maintaining the land records (khasra, khatauni, shajra) of his *patwar circle*. ★ **The lowest rung of revenue administration and the single most important actor for land matters.** Known as **Lekhpal** (UP), **Talati** (Gujarat, Maharashtra, Karnataka), **Karnam** (AP), **Village Administrative Officer / VAO** (Tamil Nadu), **Adhikari/Mandal** elsewhere. | [S] strong; **[V]** that Bhu-Naksha is designed around the patwari's workflow |
| **Patwar circle** | The group of villages assigned to one patwari. | [S] |
| **Kanungo** | The **supervisor of patwaris**, typically at the *qanungo circle* level between patwari and tehsildar. | [S] |
| **Tehsildar / Naib Tehsildar** | Revenue officer in charge of a tehsil / deputy. Sanctions mutations and presides over certain revenue court matters. | [S] |
| **Sub-Registrar (SRO)** | Officer of the **Registration Department** who registers sale deeds under the Registration Act. ★ **A different department from Revenue.** 5,329 SROs nationally; 93% computerised, 75% integrated with land records. **The Revenue/Registration split is a root cause of India's record fragmentation.** | **[V]** — §2.4 |
| **Circle rate** (a.k.a. **guidance value**, Karnataka; **ready reckoner rate**, Maharashtra; **collector rate**, Punjab/Haryana; **market value guideline**, TN) | The **government-notified minimum price per unit area** for a location, below which a property may not be registered. Used as the floor for stamp duty and registration fee, and as fair market value for capital-gains purposes in the absence of an actual price. ★ **Highly relevant to us: circle-rate zones are themselves a geospatial layer that must be harmonised with parcels, and NAKSHA's stated benefit of improved ULB revenue runs through exactly this.** | [S] strong |

## 9.6 ★ Three north/south distinctions that will impress judges

1. **Legal primacy of map vs measurement.** *Northern states recognise the graphic map (shajra) as the legal document; southern states prioritise the Field Measurement Book.* — **[V]**, Misra 2005. **Consequence for our system:** in the north we must preserve polygon geometry as the authority; in the south we must preserve *measurements* and treat the polygon as derived. A single harmonisation policy across India is therefore legally wrong.

2. **Vocabulary is not merely translation.** khasra ≠ survey number in structure: south Indian survey numbers carry a formal recursive **sub-division** grammar (`123/1A`), while north Indian khasra numbering conventions vary by settlement. Schema matching must be *structure-aware*, not just *synonym-aware*.

3. **"Khata" means different things in different places** — a revenue holding account in the north, and a **municipal property tax account** (A-Khata/B-Khata) in urban Karnataka. In an *urban* land-records project this ambiguity is a live hazard.

---

# 10. SIH 2026 Submission Format & Evaluation

## 10.1 Idea submission PPT structure — [V] on section names, [S] on the 2026 file

**Maximum 6 slides (including the title slide).** The canonical SIH idea-presentation section headings, consistent across SIH 2024, 2025 and 2026 templates:

| # | Slide heading | Contents (per the official template) |
|---|---|---|
| 1 | **Title slide** | Problem Statement ID; Problem Statement Title; Theme; PS Category (Software/Hardware); **Team ID**; **Team Name** (as registered on the portal) |
| 2 | **Idea Title / Proposed Solution** | Detailed explanation of the proposed solution; how it addresses the problem; **innovation and uniqueness of the solution** |
| 3 | **Technical Approach** | Technologies to be used (programming languages, frameworks, hardware); methodology and process for implementation — **flow charts / images / working prototype** |
| 4 | **Feasibility and Viability** | Analysis of the feasibility of the idea; **potential challenges and risks**; strategies for overcoming these challenges |
| 5 | **Impact and Benefits** | Potential impact on the target audience; benefits — **social, economic, environmental** |
| 6 | **Research and References** | **Details / links of reference and research work** |

**Explicit template instruction — [V]:** *"Keep the maximum slides limit up to six (including the title slide), and try to avoid paragraphs and post your idea in points, diagrams, infographics, or pictures."*

Sources: official SIH template files as circulated — SIH2026 IDEA Presentation Format (https://www.scribd.com/presentation/1077930858/SIH2026-IDEA-Presentation-Format), SIH2025 (https://www.scribd.com/presentation/884917405/SIH2025-IDEA-Presentation-Format), SIH2024 (https://www.scribd.com/presentation/831331764/SIH2024-IDEA-Presentation-Format-Ss). SIH FAQ confirms the template exists and must be used: https://www.sih.gov.in/faqs

> ⚠ **[U] / ACTION REQUIRED:** the SIH portal's own template file for 2026 (`SIH2026-IDEA-Presentation-Format.pptx`) should be downloaded from **sih.gov.in** directly and used verbatim. Third-party "SIH-compliant" templates (SlideEgg, SlideTeam, ScorchingTech, etc.) are **commercial products, not official**, and some restructure the sections (e.g. splitting "Technical Feasibility & Tech Stack" from "Feasibility and Viability"). **Use the portal file.** Reported acceptance: **PPT, PPTX and PDF**, max file size **25 MB** — **[S]**, confirm on the portal.

## 10.2 Official rules — [V] (from sih.gov.in/faqs)

- **Team size: exactly 6 members** including the team leader, and **at least one female member**.
- Multi-disciplinary teams encouraged for hardware; software teams need strong programming capability.
- **Each team can submit only two ideas.**
- Students may submit only **after SPOC registration and nomination by the institute following an internal hackathon**.
- **Stage 1 (idea screening) is online**; the **Grand Finale is offline**.
- Shortlisted teams may select **up to 2 mentors** with **5+ years** relevant experience.
- **Prize money: ₹1,00,000... ⚠ the FAQ as retrieved states "INR 1.5 Lakh" for both Hardware and Software categories.** Treat the exact amount as **[S]** and confirm on the portal.
- Teams may present or demonstrate a **working prototype** where available.

**[S]** SIH 2026 scale: **226+ problem statements from 30 participating organisations**, across Software and Hardware categories and **18 themes**.

## 10.3 Evaluation criteria — ⚠ [S] / [U] — HANDLE CAREFULLY

A commonly circulated weighting is:

| Criterion | Weight |
|---|---|
| Problem understanding & innovation | 20% |
| Technical approach & feasibility | 25% |
| Prototype / implementation plan | 25% |
| Impact & scalability | 20% |
| Presentation clarity | 10% |

Source (institutional portal, not MoE/AICTE): https://nmietsihportal.vercel.app/ppt-template ; also repeated on reskilll.com

> ⚠ **I could NOT find an official MoE / AICTE / SIH published rubric with these percentages.** Do not present this as "the official SIH rubric." **However**, note that the five criteria map almost exactly onto the six official template slides — so the practical guidance is sound even if the percentages are unofficial:
> - Slide 2 → problem understanding & innovation
> - Slide 3 → technical approach
> - Slide 4 → feasibility
> - Slide 5 → impact & scalability
> - Whole deck → clarity
>
> **Actionable read:** technical approach + implementation plan together carry roughly half the weight. **Two of six slides must carry real architecture, not aspiration.**

## 10.4 Template guidance worth heeding — [S] but sensible
- Do not copy-paste the official problem statement text verbatim into slide 2 — restate it.
- Use **original, team-made diagrams**, not stock architecture images.
- **Do not invent statistics.** One widely circulated SIH guide explicitly advises using Low/Medium/High framing for impact rather than fabricated numbers. ★ **In our case this is unnecessary — §6 gives real, sourced numbers. Use them, with citations in the speaker notes. That will differentiate us from every team that writes "saves 80% time."**

---

# 11. Recommended Deck Skeleton (mapped to the official 6 slides)

**Slide 1 — Title.** PS ID, title, theme, category, Team ID, Team Name.

**Slide 2 — Problem.** Three numbers, one diagram:
- Only **4 of 28 states** maintain structured urban land records *(NAKSHA Booklet p.5; Frontiers 2026)*
- Only **49.10%** of villages have geo-referenced cadastral maps *(DoLR/DILRMP)*
- **New ORI: ≤10 cm RMSE. Legacy cadastral sheet: 3–4 m modal RMSE. A 30–40× mismatch.** *(SoI circular 10.02.2025; Sengupta et al., Survey Review 2016)*
- Kill shot quote: **"Ground-truthing emerged as the biggest lagging component"** — *Satyarthi (JS, DoLR) et al., Frontiers in Sustainable Cities, 2026*

**Slide 3 — Solution.** Position precisely inside **NAKSHA MAP-2**. Show the n-source funnel: ORI/DSM/DTM + cadastral shapefile + RoR + property tax (DIGIT) + registration (NGDRS) + utility GIS + GNSS rover points + building footprints → **[CRS & unit resolution] → [spatial entity resolution] → [accuracy-tiered geometric reconciliation] → [legally-aware topology repair] → [schema harmonisation to LADM] → ULPIN-ready Urban Property Card**. Mark which stages are automated, which are human-in-the-loop, and which emit an adjudication flag for MAP-3.

**Slide 4 — Technical Approach.** Named, real techniques: SAM/Mask R-CNN boundary evidence; block-level ICP + **hierarchical least-squares (LS1 rigid → LS2 similarity → LS3 per-parcel)** after Suwardhi et al. 2025; **adaptive 2σ displacement-vector inlier/outlier detection** rather than fixed thresholds; **automatic transformation-order selection** from residual structure (our extension of Sengupta et al.); PROJ/GDAL datum pipeline + per-state unit inference (the Bhu-Naksha ×4000 / ×22 problem); GRASS `v.clean` + PostGIS Topology with a **learned sliver-vs-real-parcel classifier**; schema matching to **ISO 19152 LADM**; publish via **IUDX/BIS** APIs.

**Slide 5 — Feasibility & Viability.** Standards already mandated (UTM/WGS84, SoI CORS, SDMS, IUDX/BIS, LADM); open-source stack (PostGIS, GRASS, GDAL, GeoTools lineage, DIGIT MIT-licensed) so no FME licence at 4,912-ULB scale; risks named honestly — invisible boundaries, informal settlements, no statutory presumptive title for UrPro, ground-truth scarcity — each with a mitigation.

**Slide 6 — Impact & References.** Impact: unlock the **₹10–30 crore per-milestone** urban incentives; ULB own-revenue currently **32%**; land/property taxes **0.6% of GDP** in low-income economies vs **2.2%** industrialised; land market distortions cost **~1.3% of annual GDP growth**. References: Frontiers 2026; SoI circular 10.02.2025; Survey Review 2016; ISPRS 2025; ISO 19152; DoLR NAKSHA Booklet.

---

# 12. Master Source List

**Primary government (retrieved and text-extracted directly)**
- DoLR NAKSHA Booklet (Feb 2025) — https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2025/03/20250311644815872.pdf
- ★ Survey of India circular T-260/1147-Project (NAKSHA)/Comp_25490, 10 Feb 2025 — https://surveyofindia.gov.in/documents/circulars/document-86171-ilovepdf_merged.pdf
- PIB backgrounder, National Geospatial Policy 2022 (27 Feb 2025) — https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/feb/doc2025227509401.pdf
- Tamil Nadu Dept. of Survey & Settlement, DILRMP Regional Review, 06.09.2024 — https://cdnbbsr.s3waas.gov.in/s3d69116f8b0140cdeb1f99a4d5096ffe4/uploads/2024/10/20241004518377083.pdf
- NIC Bhu-Naksha "Cadastral Mapping" manual (LRISD) — https://bhunaksha.nic.in/bhunaksha/resources/Bhunaksha2.0.pdf

**Primary government (web pages)**
- DoLR — About NAKSHA: https://dolr.gov.in/en/about-naksha/
- DoLR — DILRMP: https://dolr.gov.in/en/programmes-schemes/dilrmp-2/
- DoLR — ULPIN/Bhu-Aadhaar: https://dolr.gov.in/en/ulpin/
- Survey of India — NAKSHA SOP index: https://surveyofindia.gov.in/pages/naksha-sop
- Survey of India — CORS: https://surveyofindia.gov.in/pages/continuously-operating-reference-stations-cors-
- Survey of India — NGP 2022: https://surveyofindia.gov.in/pages/national-geospatial-policy-2022
- DST — National Geospatial Policy PDF: https://dst.gov.in/sites/default/files/National%20Geospatial%20Policy.pdf
- NGDRS: https://ngdrs.gov.in/
- NIC BhuNaksha project: https://www.nic.gov.in/project/bhunaksha/
- TCPO NUIS: http://tcpo.gov.in/national-urban-information-system
- NUIS Guidelines: https://state.bihar.gov.in/urban/cache/25/Docs/NUIS-Guidelines.pdf
- MoHUA National Urban Innovation Stack: https://mohua.gov.in/dataSmartCities/uploads/resource/resourceDoc/Resource_Doc_1723187578_National_Urban_Innovation_Stack.pdf
- PIB DILRMP: https://www.pib.gov.in/PressReleasePage.aspx?PRID=1989671&reg=48&lang=2
- PIB NGDRS 28 states: https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1919270
- PIB CORS launch (PRID 1967096) / DST mirror: https://dst.gov.in/union-minister-dr-jitendra-singh-launches-state-art-latest-national-survey-network-nationwide
- PIB Operation Dronagiri (PRID 2073284): https://pib.gov.in/PressReleasePage.aspx?PRID=2073284
- PIB SVAMITVA drone survey (PRID 2200803): https://www.pib.gov.in/PressReleasePage.aspx?PRID=2200803&reg=3&lang=1
- SVAMITVA SOP *(unreachable — TLS)*: https://svamitva.nic.in/DownloadPDF/SOPSVAMITVASchemeEnglishVersion_1634724183038.pdf
- NAKSHA SOP *(scan-only, no text layer)*: https://surveyofindia.gov.in/UserFiles/files/NAKSHA%20SOP%20_NAKSHA.pdf

**Peer-reviewed / academic**
- ★ Satyarthi, Somvanshi & Kumar (2026), *Frontiers in Sustainable Cities* — https://www.frontiersin.org/journals/sustainable-cities/articles/10.3389/frsc.2026.1874630/full
- ★ Sengupta, Lemmen, Devos, Bandyopadhyay & van der Veen (2016), *Survey Review* 48(349):258-268 — https://ris.utwente.nl/ws/files/20643154/sengupta_constructing.pdf
- ★ Suwardhi et al. (2025), *ISPRS Archives* XLVIII-2/W11 — https://isprs-archives.copernicus.org/articles/XLVIII-2-W11-2025/277/2025/isprs-archives-XLVIII-2-W11-2025-277-2025.pdf
- Sengupta, Bandyopadhyay, Lemmen & van der Veen (2013), LADM in India — https://repository.tudelft.nl/record/uuid:a8bd9c8e-dbbd-4505-90cd-9bdf1c77cc3a
- Thakur, Doja & Faizi (2017), IJEDR 5(4) — https://rjwave.org/ijedr/papers/IJEDR1704252.pdf
- Vantas & Mirkopoulou (2025), *Geomatics* 5(2):16 — https://doi.org/10.3390/geomatics5020016
- "Artificial Intelligence in Cadastre: A Systematic Review", *Land* 15(3):411 — https://doi.org/10.3390/land15030411 *(⚠ MDPI blocked automated fetch — cited from search metadata only, [U])*
- Crommelinck et al. (2019) — https://research.utwente.nl/en/publications/application-of-deep-learning-for-delineation-of-visible-cadastral/
- Dhrubo et al. (2024), Mouza map vectorization — https://arxiv.org/abs/2410.15961
- Ferrod et al. (2026), GroundSet — https://arxiv.org/abs/2603.14609
- arXiv:1709.01813; arXiv:2309.16708; arXiv:2304.07076; arXiv:2103.09787; arXiv:2012.03069
- Misra, P. (2005), *Coordinates* — https://mycoordinates.org/cadastral-surveys-in-india/

**Policy / think-tank**
- PRS Legislative Research, *Land Records and Titles in India* — https://prsindia.org/policy/analytical-reports/land-records-and-titles-india
- World Bank (2007) Report 38298-IN — https://documents1.worldbank.org/curated/en/531431468035337578/pdf/382980INoptmzd.pdf
- World Bank (2017) India Land Governance Assessment — https://documents1.worldbank.org/curated/en/632011504866265171/pdf/119622-WP-P095390-PUBLIC-7-9-2017-10-7-28-NationalSynthesisReportIndia.pdf
- DAKSH Access to Justice Survey 2015-16 — https://www.dakshindia.org/access-to-justice-survey/
- NCAER N-LRSI 2021 — https://ncaer.org/publication/ncaer-land-records-and-services-index-n-lrsi-2021/
- NITI Aayog Model Conclusive Land Titling Act — https://www.niti.gov.in/sites/default/files/2022-12/ModelConclusiveLandTitlingAct.pdf
- Rights and Resources Initiative, cost of land disputes — https://rightsandresources.org/blog/new-research-shows-high-cost-land-disputes-india/

**Standards / platforms / tools**
- ISO 19152-1:2024 — https://www.iso.org/standard/81263.html ; ISO 19152:2012 — https://www.iso.org/standard/51206.html
- IUDX — https://iudx.org.in/platform/ ; BIS adoption — https://iudx.org.in/iudx-becomes-first-software-platform-to-fully-adopt-bis-standards-for-unified-data-exchange/
- DIGIT — https://www.digit.org/ ; https://github.com/egovernments/DIGIT-OSS
- GRASS `v.clean` — https://grass.osgeo.org/grass-stable/manuals/v.clean.html ; topology cleaning wiki — https://grasswiki.osgeo.org/wiki/Vector_topology_cleaning
- Spatial ETL / FME — https://en.wikipedia.org/wiki/Spatial_ETL ; Esri Data Interoperability — https://pro.arcgis.com/en/pro-app/latest/help/data/data-interoperability/spatial-etl-tools.htm

**SIH**
- SIH FAQs — https://www.sih.gov.in/faqs
- SIH 2026 idea presentation format — https://www.scribd.com/presentation/1077930858/SIH2026-IDEA-Presentation-Format

---

## Appendix A — Immediate follow-ups before the finale

1. **OCR the NAKSHA SOP** (105 scanned pages, `surveyofindia.gov.in/UserFiles/files/NAKSHA SOP _NAKSHA.pdf`) to recover the **SDMS feature schema and attribute codes**. Highest-value remaining unknown — designing our canonical schema against the actual SDMS would be decisive.
2. **Retrieve the SVAMITVA SOP** (TLS-broken host; try a mirror or browser download) for its accuracy spec and claims/objections workflow.
3. **Download the official SIH 2026 PPT template from sih.gov.in**, not a third-party copy.
4. **Verify the IIM Ahmedabad SVAMITVA evaluation** (₹1,679 crore / 10,900 loans) before using it.
5. **Confirm the SIH prize amount and evaluation rubric** on the portal.
6. **Decide and lock one ULB-count figure** (152 recommended) and use it consistently across the deck and the speech.

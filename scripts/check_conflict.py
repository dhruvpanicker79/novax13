"""Exercise the conflict engine on the cases that actually matter."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from kshetra.conflict.resolve import Claim, SourceProfile, resolve_parcel

GNSS   = SourceProfile("gnss_cors", "GNSS/CORS control", 0.03, 2026)
DRONE  = SourceProfile("drone_ori", "Drone ORI 5cm", 0.10, 2025)
MSAI   = SourceProfile("ms_ai", "MS AI footprints", 1.20, 2024)
MUNI   = SourceProfile("municipal", "Municipal GIS", 2.50, 2019)
LEGACY = SourceProfile("legacy", "Legacy sheet 1987", 6.00, 1987,
                       authority=frozenset({"owner", "tenure", "khasra"}))
REVENUE= SourceProfile("revenue", "Revenue record", 8.00, 2023,
                       authority=frozenset({"owner", "tenure", "khasra", "ulpin"}))

def show(title, pr):
    print(f"\n{'='*72}\n{title}\n{'='*72}")
    for f, r in pr.resolutions.items():
        print(f"  {f:<10} = {str(r.value)[:38]:<38} [{r.rule}]")
        print(f"             src={r.source_id}  conf={r.confidence:.3f}  agree={r.agreement:.2f}")
        if r.note: print(f"             {r.note}")
    for t in pr.transitive_conflicts: print(f"  TRANSITIVE: {t}")
    print(f"  needs_human={pr.needs_human}" + (f"  — {pr.reason}" if pr.reason else ""))

# 1. geometry: precise control must not be averaged with a paper sheet
show("1. Area claim, GNSS vs legacy sheet", resolve_parcel("P001", [
    Claim(GNSS, "area_sqm", 142.8),
    Claim(LEGACY, "area_sqm", 149.5),
    Claim(MSAI, "area_sqm", 144.1),
]))

# 2. ownership: accuracy is irrelevant, authority decides
show("2. Owner, drone vs revenue record", resolve_parcel("P002", [
    Claim(DRONE, "owner", "UNKNOWN"),
    Claim(REVENUE, "owner", "Ramesh Kumar s/o Suresh Kumar"),
    Claim(LEGACY, "owner", "Ramesh Kr. s/o Suresh Kr."),
]))

# 3. genuine ownership dispute -> must go to a human
show("3. Owner genuinely disputed", resolve_parcel("P003", [
    Claim(REVENUE, "owner", "Sunita Devi w/o Mahesh Pal"),
    Claim(LEGACY, "owner", "Imran Ansari s/o Abdul Ansari"),
]))

# 4. transitive inconsistency: invisible to any pairwise check
show("4. Transitive inconsistency", resolve_parcel("P004", [
    Claim(GNSS, "area_sqm", 100.0),
    Claim(DRONE, "area_sqm", 118.0),
    Claim(MUNI, "area_sqm", 139.0),
]))

# 5. sources concur within their error bars
show("5. Sources agree", resolve_parcel("P005", [
    Claim(DRONE, "area_sqm", 210.4),
    Claim(MSAI, "area_sqm", 210.9),
    Claim(MUNI, "area_sqm", 209.8),
]))

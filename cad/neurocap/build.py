"""NeuroCap S0 ellipsoid assembly visualization generator.

Nonfunctional, nonwearable model; no actual anatomy or biopotential hardware.
Standard library only, independent of NeuroShield scientific kernels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIGIN = "SYNTHETIC_NONHUMAN_HEADFORM"
STATUS = "UNVALIDATED_NONWEARABLE_CONCEPT"


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _number(value, label, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{label} outside finite range [{minimum},{maximum}]")
    return float(value)


def _triplet(value, label, minimum, maximum):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must have three coordinates")
    return [_number(v, f"{label}[{i}]", minimum, maximum) for i, v in enumerate(value)]


def validate_manifest(obj):
    """Check reference-only source, axes, geometry, labels, and site domains."""
    if not isinstance(obj, dict):
        raise ValueError("Expected manifest object")
    for key, exact in {
        "schema_version": "0.1.0",
        "origin": ORIGIN,
        "evidence_tier": "S0",
        "status": STATUS,
        "units": "mm",
    }.items():
        if obj.get(key) != exact:
            raise ValueError(f"{key} must be {exact}")
    frame = obj.get("coordinate_frame")
    if frame != {
        "handedness": "right",
        "x": "+right",
        "y": "+anterior",
        "z": "+superior",
        "origin": "ellipsoid center",
    }:
        raise ValueError("Unknown coordinate frame")
    g = obj.get("geometry", {})
    if not isinstance(g, dict):
        raise ValueError("geometry must be object")
    g["radii_mm"] = _triplet(g.get("radii_mm"), "radii_mm", 50, 150)
    for name, lo, hi in [
        ("cap_shell_gap_mm", 2, 30),
        ("cap_shell_thickness_mm", 0.5, 8),
        ("band_z_mm", -30, 60),
        ("band_offset_mm", 1, 30),
        ("rail_radius_mm", 0.5, 8),
        ("rib_half_span_mm", 20, 75),
        ("brim_length_mm", 20, 120),
        ("brim_width_mm", 60, 220),
        ("ear_center_x_mm", 50, 140),
        ("ear_center_y_mm", -80, 80),
        ("ear_center_z_mm", -70, 60),
        ("ear_y_radius_mm", 5, 50),
        ("ear_z_radius_mm", 5, 60),
    ]:
        g[name] = _number(g.get(name), name, lo, hi)
    g["rib_y_mm"] = _triplet(g.get("rib_y_mm"), "rib_y_mm", -70, 70)
    g["pod_center_mm"] = _triplet(g.get("pod_center_mm"), "pod_center_mm", -180, 180)
    g["pod_size_mm"] = _triplet(g.get("pod_size_mm"), "pod_size_mm", 5, 90)
    if g["cap_shell_thickness_mm"] >= g["cap_shell_gap_mm"]:
        raise ValueError("Cap shell thickness must be smaller than gap")
    rx, ry, _ = g["radii_mm"]
    for y in g["rib_y_mm"]:
        if (g["rib_half_span_mm"] / rx) ** 2 + (y / ry) ** 2 >= 0.94:
            raise ValueError("Crown rib falls outside idealized ellipsoid")
    if g["ear_center_x_mm"] <= rx:
        raise ValueError("Ear visual modules must clear reference ellipsoid")
    components = obj.get("components")
    if not isinstance(components, list) or len(components) != 7:
        raise ValueError("Seven declared visual components required")
    component_ids = [part.get("id") for part in components if isinstance(part, dict)]
    if set(component_ids) != {"headform", "cap", "frame", "scalp", "ears", "routing", "pod"}:
        raise ValueError("Component IDs missing, duplicated or unknown")
    if any(part.get("qualification") not in ("S0_ONLY", "NOT_MEASURED") for part in components):
        raise ValueError("Components must not claim validation")
    seen = set()
    scalp_sites = obj.get("scalp_sites")
    if not isinstance(scalp_sites, list) or len(scalp_sites) < 2:
        raise ValueError("Need at least two nominal scalp sites")
    for site in scalp_sites:
        if not isinstance(site, dict):
            raise ValueError("Invalid site")
        site_id = site.get("id")
        if not isinstance(site_id, str) or not site_id.isalnum() or site_id in seen:
            raise ValueError("Duplicate or malformed site ID")
        seen.add(site_id)
        _number(site.get("polar_deg"), "polar_deg", 1, 150)
        _number(site.get("azimuth_deg"), "azimuth_deg", 0, 359.9999)
        if site.get("status") != "NOMINAL":
            raise ValueError("Cannot assert measured electrode position")
    ear_sites = obj.get("ear_sites")
    if not isinstance(ear_sites, list) or len(ear_sites) != 2:
        raise ValueError("Expected two nominal ear sites")
    for site in ear_sites:
        if site.get("id") in seen or site.get("status") != "NOMINAL":
            raise ValueError("Duplicate or measured ear site")
        seen.add(site["id"])
        if type(site.get("side")) is not int or site["side"] not in (-1, 1):
            raise ValueError("Ear side must be -1 or 1")
    if {site["side"] for site in ear_sites} != {-1, 1}:
        raise ValueError("Must include bilateral ear sites")
    e = obj.get("electrical_contract", {})
    if e.get("skin_connection") != "PROHIBITED_IN_THIS_CONCEPT" or e.get("amplifier_reference") != "UNSPECIFIED":
        raise ValueError("No human electrical setup or reference is authorized")
    return obj


def load_manifest(path=ROOT / "manifest.json"):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Manifest must be a regular file, not a symlink")
    if path.stat().st_size > 100_000:
        raise ValueError("Manifest too large")
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    return validate_manifest(data)


def _q(value):
    return f"{float(value):.4f}"


def generate_scad(data):
    """Generate deterministic, inspectable OpenSCAD from versioned geometry."""
    data = validate_manifest(data)
    g = data["geometry"]
    def vec(v):
        return "[" + ", ".join(_q(x) for x in v) + "]"
    sites = []
    for site in data["scalp_sites"]:
        t = math.radians(site["polar_deg"])
        a = math.radians(site["azimuth_deg"])
        rx, ry, rz = g["radii_mm"]
        pos = [rx * math.sin(t) * math.cos(a), ry * math.sin(t) * math.sin(a), rz * math.cos(t)]
        sites.append((site["id"], pos))
    site_lines = "\n".join(
        f'  translate({vec(pos)}) color([0.68,0.30,0.23]) sphere(r=5,$fn=28); // {name} NOMINAL'
        for name, pos in sites
    )
    return f"""// GENERATED FROM cad/neurocap/manifest.json. UNVALIDATED_NONWEARABLE_CONCEPT.
// S0 FICTIONAL HEADFORM ONLY. No measured human anatomy, contacts, compliance,
// acoustic design, certified protective helmet, skin connection, or validation.
// All dimensions millimeters. Right-handed x right, y anterior, z superior.
$fn=32;
r={vec(g['radii_mm'])};
cap_gap={_q(g['cap_shell_gap_mm'])};
cap_thick={_q(g['cap_shell_thickness_mm'])};
band_z={_q(g['band_z_mm'])};
band_gap={_q(g['band_offset_mm'])};
rail_r={_q(g['rail_radius_mm'])};
rib_y={vec(g['rib_y_mm'])};
rib_half={_q(g['rib_half_span_mm'])};
brim_w={_q(g['brim_width_mm'])};
brim_l={_q(g['brim_length_mm'])};
ear_x={_q(g['ear_center_x_mm'])};
ear_y={_q(g['ear_center_y_mm'])};
ear_z={_q(g['ear_center_z_mm'])};
ear_yr={_q(g['ear_y_radius_mm'])};
ear_zr={_q(g['ear_z_radius_mm'])};
pod_at={vec(g['pod_center_mm'])};
pod_size={vec(g['pod_size_mm'])};

// Toggle parts independently in OpenSCAD. These are VISUAL PLACEHOLDERS only.
show_headform=true;
show_cap=true;
show_frame=true;
show_sites=true;
show_ears=true;
show_routing=true;
show_pod=true;

module link(a,b,w=rail_r) {{
  hull() {{ translate(a) sphere(r=w,$fn=12); translate(b) sphere(r=w,$fn=12); }}
}}
function top_z(x,y) = r[2]*sqrt(max(0,1-pow(x/r[0],2)-pow(y/r[1],2)))+band_gap;
module headform() {{
  color([0.77,0.66,0.55,0.18]) scale(r) sphere(r=1,$fn=50);
}}
module crown_and_brim() {{
  color([0.73,0.69,0.60,0.24])
    difference() {{
      intersection() {{
        scale([r[0]+cap_gap,r[1]+cap_gap,r[2]+cap_gap]) sphere(r=1,$fn=56);
        translate([-200,-200,band_z]) cube([400,400,270]);
      }}
      scale([r[0]+cap_gap-cap_thick,r[1]+cap_gap-cap_thick,r[2]+cap_gap-cap_thick])
        sphere(r=1,$fn=56);
    }}
  color([0.64,0.59,0.49,0.45])
    translate([0,r[1]+brim_l*0.52,band_z+0.6])
      linear_extrude(height=2)
        hull() {{
          translate([-brim_w*0.43,-brim_l*0.5]) circle(r=9);
          translate([ brim_w*0.43,-brim_l*0.5]) circle(r=9);
          translate([-brim_w*0.32, brim_l*0.5]) circle(r=6);
          translate([ brim_w*0.32, brim_l*0.5]) circle(r=6);
        }}
}}
module frame_study() {{
  color([0.18,0.38,0.46]) {{
    for(i=[0:71]) {{
      a=i*360/72; b=(i+1)*360/72;
      k=sqrt(1-pow(band_z/r[2],2));
      link([k*r[0]*cos(a)+band_gap*cos(a),k*r[1]*sin(a)+band_gap*sin(a),band_z],
           [k*r[0]*cos(b)+band_gap*cos(b),k*r[1]*sin(b)+band_gap*sin(b),band_z]);
    }}
    for(y=rib_y) for(j=[0:19]) {{
      xa=-rib_half+2*rib_half*j/20;
      xb=-rib_half+2*rib_half*(j+1)/20;
      link([xa,y,top_z(xa,y)],[xb,y,top_z(xb,y)],rail_r*0.82);
    }}
  }}
}}
module scalp_placeholders() {{
{site_lines}
}}
module ear_placeholders() {{
  for(side=[-1,1]) {{
    color([0.44,0.52,0.47]) for(j=[0:35]) {{
      a=j*360/36; b=(j+1)*360/36;
      link([side*ear_x,ear_y+ear_yr*cos(a),ear_z+ear_zr*sin(a)],
           [side*ear_x,ear_y+ear_yr*cos(b),ear_z+ear_zr*sin(b)],2.8);
    }}
    color([0.68,0.30,0.23])
      translate([side*ear_x,ear_y,ear_z]) sphere(r=5,$fn=24);
  }}
}}
module signal_paths() {{
  color([0.76,0.49,0.26]) for(side=[-1,1])
    link([side*ear_x,ear_y-ear_yr,ear_z],
         [side*(r[0]+band_gap),-r[1]*0.8,band_z],1.1);
}}
module pod_placeholder() {{
  color([0.37,0.43,0.48,0.75])
    translate(pod_at) cube(pod_size,center=true);
}}
if(show_headform) headform();
if(show_cap) crown_and_brim();
if(show_frame) frame_study();
if(show_sites) scalp_placeholders();
if(show_ears) ear_placeholders();
if(show_routing) signal_paths();
if(show_pod) pod_placeholder();
"""


def build(manifest, out, receipt):
    path = Path(manifest)
    data = load_manifest(path)
    source = generate_scad(data)
    out = Path(out)
    receipt = Path(receipt)
    if out.resolve() == path.resolve() or receipt.resolve() in (path.resolve(), out.resolve()):
        raise ValueError("Input/output paths must be distinct")
    if out.is_symlink() or receipt.is_symlink():
        raise ValueError("Output symlinks not permitted")
    out.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(source, encoding="utf-8")
    raw = path.read_bytes()
    record = {
        "schema_version": "0.1.0",
        "design_id": data["design_id"],
        "origin": ORIGIN,
        "evidence_tier": "S0",
        "status": STATUS,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "scad_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "site_count": len(data["scalp_sites"]) + len(data["ear_sites"]),
        "units": "mm",
        "human_anatomy_measured": False,
        "electrical_safety_assessed": False,
        "skin_contact_authorized": False,
        "protective_use_authorized": False,
    }
    receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--out", type=Path, default=ROOT / "assembly.scad")
    parser.add_argument("--receipt", type=Path, default=ROOT / "assembly-receipt.json")
    args = parser.parse_args()
    print(json.dumps(build(args.manifest, args.out, args.receipt), indent=2))


if __name__ == "__main__":
    main()

"""Deterministic, NON-WEARABLE visualization of abstract markers on a synthetic ellipsoid.

No electrode construction, headwear fit, scalp registration, electrical interface,
biocompatibility, protective performance or human measurements are supported.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re

SCHEMA = "neuroshield.synthetic-headform-markers.v1"
ORIGIN = "SYNTHETIC_NONHUMAN_HEADFORM_ONLY"
LIMITATION = "UNVALIDATED_NON_INSTALLABLE_CONCEPT"
FRAME = "x_right_y_anterior_z_superior"
DESIGN_ID = re.compile(r"[a-z][a-z0-9-]{4,63}\Z")
SITE_ID = re.compile(r"SITE-[A-Z0-9-]{2,24}\Z")
MAX_BYTES = 32_768


class HeadformConceptError(ValueError):
    """Reject ambiguous or non-synthetic geometry as a safe visual concept."""


def _strict_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise HeadformConceptError("Duplicate manifest property")
        obj[key] = value
    return obj


def _number(value):
    return type(value) in (float, int) and math.isfinite(value)


def _vec(value):
    return (isinstance(value, list) and len(value) == 3
            and all(_number(x) for x in value))


def load_manifest(path):
    path = Path(path)
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= MAX_BYTES):
        raise HeadformConceptError("Missing, symlinked or oversized synthetic manifest")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object,
                         parse_constant=lambda _: (_ for _ in ()).throw(
                             HeadformConceptError("Non-finite values rejected")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HeadformConceptError("Unreadable synthetic manifest") from exc
    validate(obj)
    return obj


def validate(obj):
    """Structural checks for an abstract geometric illustration only."""
    if not isinstance(obj, dict) or set(obj) != {
        "schema", "origin", "design_id", "claim", "units", "frame",
        "headform_radii_mm", "sites",
    }:
        raise HeadformConceptError("Unexpected synthetic marker manifest fields")
    if (obj["schema"] != SCHEMA or obj["origin"] != ORIGIN
            or obj["claim"] != LIMITATION or obj["units"] != "mm"
            or obj["frame"] != FRAME):
        raise HeadformConceptError("Unsupported context of use, units, origin or frame")
    if not isinstance(obj["design_id"], str) or not DESIGN_ID.fullmatch(obj["design_id"]):
        raise HeadformConceptError("Invalid design identifier")
    radii = obj["headform_radii_mm"]
    if not _vec(radii) or not all(40 <= x <= 200 for x in radii):
        raise HeadformConceptError("Headform ellipsoid radii must be finite and explicitly in mm")
    sites = obj["sites"]
    if not isinstance(sites, list) or not 3 <= len(sites) <= 32:
        raise HeadformConceptError("Expected 3..32 symbolic headform sites")
    seen, pts = set(), []
    for site in sites:
        if not isinstance(site, dict) or set(site) != {"id", "direction_unit"}:
            raise HeadformConceptError("Site requires only ID and symbolic unit direction")
        ident, direction = site["id"], site["direction_unit"]
        if not isinstance(ident, str) or not SITE_ID.fullmatch(ident) or ident in seen:
            raise HeadformConceptError("Duplicate or invalid site ID")
        seen.add(ident)
        if not _vec(direction) or abs(math.sqrt(sum(x*x for x in direction)) - 1.0) > 1e-6:
            raise HeadformConceptError("Marker direction must be a finite unit vector")
        pts.append([float(a)*float(b) for a, b in zip(radii, direction)])
    min_spacing = min(math.dist(a, b) for i, a in enumerate(pts) for b in pts[i+1:])
    if min_spacing <= 8.0:
        raise HeadformConceptError("Symbolic markers overlap: render spacing below 8 mm")
    return pts, min_spacing


def render_scad(obj):
    """Render a display-only solid ellipsoid and colored dots, no wearable parts."""
    pts, _ = validate(obj)
    radii = obj["headform_radii_mm"]
    fmt = lambda v: f"{v:.6f}"
    lines = [
        "// NEUROSHIELD S0 SYNTHETIC NONHUMAN HEADFORM VISUALIZATION.",
        "// UNVALIDATED NON-INSTALLABLE CONCEPT. NO WEARABLE, ELECTRODE,",
        "// SCALP FIT, WIRING, SAFETY, PROTECTION OR HUMAN USE.",
        "// Marker labels are arbitrary SITE codes, NOT 10-20 scalp locations.",
        f"// Design: {obj['design_id']} | units: mm | frame: {FRAME}",
        "$fn = 64;",
        f"radii_mm = [{', '.join(fmt(x) for x in radii)}];",
        "color([0.65, 0.76, 0.87, 0.28]) scale(radii_mm) sphere(r=1);",
    ]
    for site, p in zip(obj["sites"], pts):
        lines.append(f"// {site['id']}: [{', '.join(fmt(x) for x in p)}] mm")
        lines.append(f"color([0.92, 0.38, 0.24]) translate([{', '.join(fmt(x) for x in p)}]) sphere(r=3, $fn=24);")
    return "\n".join(lines) + "\n"


def receipt(obj, scad_source):
    pts, minimum = validate(obj)
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "schema": SCHEMA,
        "design_id": obj["design_id"],
        "origin": ORIGIN,
        "evidence_tier": "S0",
        "status": LIMITATION,
        "frame": FRAME,
        "units": "mm",
        "site_count": len(pts),
        "minimum_symbolic_site_spacing_mm": round(minimum, 6),
        "headform_bounds_mm": [round(2.0*x, 6) for x in obj["headform_radii_mm"]],
        "manifest_canonical_sha256": sha256(canonical).hexdigest(),
        "scad_sha256": sha256(scad_source.encode("utf-8")).hexdigest(),
        "electrode_montage_validated": False,
        "physical_fabrication_authorized": False,
        "independent_hardware_validation": False,
        "human_data_processed": False,
        "warning": "Rendering and numeric geometry checks are not electrode localization, fit, electrical safety or protective-equipment evidence.",
    }


def _safe_new_path(path, input_path):
    path = Path(path)
    source = Path(input_path).resolve()
    if path.resolve() == source or path.exists() or path.is_symlink():
        raise HeadformConceptError("Refusing to overwrite existing input or output")
    cursor = path.parent
    if not cursor.is_dir():
        raise HeadformConceptError("Output directory must exist")
    while cursor != cursor.parent:
        if cursor.is_symlink():
            raise HeadformConceptError("Symlinked output directory rejected")
        cursor = cursor.parent
    return path


def write_concept(manifest, output_scad, output_receipt):
    """Fail closed before writing and clean up only files created by this call."""
    obj = load_manifest(manifest)
    output_scad = _safe_new_path(output_scad, manifest)
    output_receipt = _safe_new_path(output_receipt, manifest)
    if output_scad.resolve() == output_receipt.resolve():
        raise HeadformConceptError("Geometry and receipt output paths must differ")
    scad = render_scad(obj)
    report = receipt(obj, scad)
    created = []
    try:
        with output_scad.open("x", encoding="utf-8") as f:
            created.append(output_scad)
            f.write(scad)
        with output_receipt.open("x", encoding="utf-8") as f:
            created.append(output_receipt)
            f.write(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline, nonhuman EEG site illustration (NOT wearable)")
    p.add_argument("manifest")
    p.add_argument("--out", required=True)
    p.add_argument("--receipt", required=True)
    args = p.parse_args(argv)
    try:
        report = write_concept(args.manifest, args.out, args.receipt)
        print(json.dumps(report, indent=2, sort_keys=True))
    except (HeadformConceptError, OSError, ValueError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

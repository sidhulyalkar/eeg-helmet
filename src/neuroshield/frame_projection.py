"""Fixed-frame, nonhuman headform kinematic projection (S0 only).

This is a geometry / numerical validation tool, NOT biomechanical validation.
Source vectors are in a rigid sensor/headform frame. A constant *proper*
rotation converts them to a predeclared target frame. Lever-arm correction
moves acceleration from the sensor to a named point on the same rigid body.
No sensor-to-skull fit, anatomy, calibration or concussion metric is inferred.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from .bench_intake import _iter_samples, _read_profile, validate_intake
from .headform import _metadata
from .provenance import canonical_hash

SCHEMA = "neuroshield.frame-projection/0.1"
FIELDS = {"schema_version", "scope", "source_frame", "target_frame",
          "source_to_target_rotation", "sensor_to_target_m",
          "projection_axis_target", "input_acceleration_semantics", "window_s",
          "registration_reference"}
_MAX_JSON = 16384
_HEX = re.compile(r"[0-9a-f]{64}\Z")


def _number(x):
    if type(x) not in (int, float) or not math.isfinite(x):
        raise ValueError("Expected a finite numeric coordinate (not bool)")
    return float(x)


def _vec(values, name):
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError(f"{name} must be a length-three array")
    return tuple(_number(v) for v in values)


def _dot(a, b):
    return sum(x*y for x, y in zip(a,b))


def _norm(a):
    return math.sqrt(_dot(a,a))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _rotate(rotation, vector):
    return tuple(_dot(row,vector) for row in rotation)


def _validate_rotation(value):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("Rotation must be a 3x3 matrix")
    matrix = tuple(_vec(row,"rotation row") for row in value)
    error = max(abs(_dot(matrix[i],matrix[j]) - (1.0 if i == j else 0.0))
                for i in range(3) for j in range(3))
    det = _dot(matrix[0],_cross(matrix[1],matrix[2]))
    if error > 1e-6 or abs(det-1) > 1e-6:
        raise ValueError("Rotation must be orthonormal and right-handed (determinant +1)")
    return matrix, error, det


def _read_json(path):
    p=Path(path)
    if p.stat().st_size > _MAX_JSON:
        raise ValueError("JSON metadata exceeds 16 KiB")
    try:
        result=json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid UTF-8 JSON") from exc
    return result


def validate_plan(plan):
    if not isinstance(plan,dict) or set(plan) != FIELDS:
        raise ValueError("Projection plan requires exact fields")
    if plan["schema_version"] != SCHEMA or plan["scope"] != "NONHUMAN_HEADFORM_ONLY":
        raise ValueError("Unsupported schema or human/unknown scope")
    if plan["source_frame"] != "right_handed_headform_body" or plan["target_frame"] != "rigid_headform_target":
        raise ValueError("Explicit known nonhuman source and target frames required")
    if plan["input_acceleration_semantics"] != "GRAVITY_REMOVED_LINEAR_ACCELERATION":
        raise ValueError("Acceleration must be independently gravity compensated")
    if not isinstance(plan["registration_reference"],str) or not 1 <= len(plan["registration_reference"]) <= 160 or any(ord(c)<33 or ord(c)>126 for c in plan["registration_reference"]):
        raise ValueError("Registration reference required; self-declaration is not timestamp proof")
    matrix, err, det = _validate_rotation(plan["source_to_target_rotation"])
    offset=_vec(plan["sensor_to_target_m"],"sensor_to_target_m")
    if _norm(offset) > 0.5:
        raise ValueError("Lever arm exceeds supported 0.5 m research range")
    axis=_vec(plan["projection_axis_target"],"projection_axis_target")
    if abs(_norm(axis)-1)>1e-6:
        raise ValueError("Projection axis must be a fixed unit vector")
    window=plan["window_s"]
    if not isinstance(window,list) or len(window)!=2:
        raise ValueError("Window must have two timestamps")
    start,end=(_number(v) for v in window)
    if start < 0 or end <= start or end > 60:
        raise ValueError("Invalid predeclared analysis window")
    return matrix,offset,axis,start,end,{"orthonormality_max_error":err,"rotation_determinant":det}


def project_sample(accel, alpha, omega, matrix, offset, axis):
    """Project acceleration at rigid target using a_P=a_S+alpha×r+omega×(omega×r)."""
    if any(len(a) != 3 for a in (accel,alpha,omega)):
        raise ValueError("Each sample vector must be 3D")
    a, angular, velocity=(tuple(_number(v) for v in x) for x in (accel,alpha,omega))
    tangential=_cross(angular,offset)
    centripetal=_cross(velocity,_cross(velocity,offset))
    corrected=tuple(a[i]+tangential[i]+centripetal[i] for i in range(3))
    return (_dot(axis,_rotate(matrix,corrected)),
            _dot(axis,_rotate(matrix,angular)),
            _dot(axis,_rotate(matrix,velocity)))


def _summarize(times, values):
    if len(times)<3 or times[-1]<=times[0]:
        raise ValueError("At least three samples over a nonzero window required")
    squares=sum(.5*(values[i]**2+values[i+1]**2)*(times[i+1]-times[i])
                for i in range(len(times)-1))
    peak=max(range(len(values)),key=lambda i:abs(values[i]))
    return {"peak_absolute":abs(values[peak]),"signed_at_peak":values[peak],
            "peak_time_s":times[peak],"rms":math.sqrt(squares/(times[-1]-times[0]))}


def evaluate(plan_path, profile_path, manifest_path, csv_path, *, expected_plan_sha256):
    """Aggregate-only. Structural checks do NOT certify the declared calibration."""
    if not isinstance(expected_plan_sha256,str) or not _HEX.fullmatch(expected_plan_sha256):
        raise ValueError("Expected pinned plan SHA-256 required")
    plan=_read_json(plan_path)
    matrix,offset,axis,start,end,qa=validate_plan(plan)
    fingerprint=canonical_hash(plan)
    if fingerprint != expected_plan_sha256:
        raise ValueError("Projection plan changed from the pinned SHA-256")
    # Structural and license-intake gates run BEFORE projection.
    intake=validate_intake(profile_path,manifest_path,csv_path)
    if not intake["quality_structural_pass"]:
        raise ValueError("Missing samples or saturation blocks projection")
    if intake["source_origin"] == "NONHUMAN_INSTRUMENTED_HEADFORM" and intake["intake_status"] != "REVIEW_REQUIRED":
        raise ValueError("Nonhuman measurements require documented local-analysis rights")
    manifest=_metadata(_read_json(manifest_path))
    profile=_read_profile(profile_path)
    if manifest["coordinate_frame"]!=plan["source_frame"]:
        raise ValueError("Plan / headform frame mismatch")
    if profile["acquisition"]["frame_reference"] in ("", "UNKNOWN"):
        raise ValueError("Sensor orientation reference missing")
    sample_hz=profile["acquisition"]["sampling_hz"]
    times=[]; projected=[[],[],[]]; previous=None; count=0
    for record in _iter_samples(csv_path):
        count+=1
        t=record[0]
        if start<=t<=end:
            if previous is not None and abs((t-previous)*sample_hz-1)>0.05:
                raise ValueError("Irregular sampling inside preregistered window")
            previous=t;times.append(t)
            for series,value in zip(projected,project_sample(record[1:4],record[4:7],record[7:10],matrix,offset,axis)):
                series.append(value)
    if count != intake["trace_count"]:
        raise ValueError("Unexpected raw trace length")
    if len(times)<3 or times[0]>start+1.1/sample_hz or times[-1]<end-1.1/sample_hz:
        raise ValueError("Analysis window not fully covered")
    synthetic=intake["source_origin"]=="SYNTHETIC_HEADFORM_FIXTURE"
    return {"schema_version":SCHEMA,"status":"SYNTHETIC_GEOMETRY_ONLY" if synthetic else "EXPLORATORY_LAB_REVIEW_REQUIRED",
        "scientific_evidence_level":"S0","sample_count":len(times),
        "plan_sha256":fingerprint,"acquisition_identity_sha256":intake["reference_identity_sha256"],
        "rotation_qa":qa,"lever_arm_length_m":_norm(offset),
        "window_s":[start,end],
        "signed_axis_kinematics":{
            "linear_acceleration_m_s2":_summarize(times,projected[0]),
            "angular_acceleration_rad_s2":_summarize(times,projected[1]),
            "angular_velocity_rad_s":_summarize(times,projected[2])},
        "blockers":["NO_VERIFIED_SENSOR_TO_HEADFORM_TRANSFORM",
            "NO_INDEPENDENT_CALIBRATION_OR_UNCERTAINTY_PROPAGATION",
            "NO_VALIDATED_1D_MODEL_CORRESPONDENCE",
            "NO_PHYSICAL_OR_CLINICAL_SAFETY_INFERENCE"] + (["SYNTHETIC_ONLY"] if synthetic else []),
        "notes":"Signed, fixed-axis rigid-body geometry only. Source rights and calibration are self-declared, not independently authenticated. Raw samples never returned."}


def main(argv=None):
    parser=argparse.ArgumentParser(description="Offline, S0 nonhuman sensor-to-headform projection")
    parser.add_argument("plan")
    parser.add_argument("profile")
    parser.add_argument("manifest")
    parser.add_argument("csv")
    parser.add_argument("--expected-plan-sha256",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    report=evaluate(args.plan,args.profile,args.manifest,args.csv,expected_plan_sha256=args.expected_plan_sha256)
    Path(args.out).write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(f"S0 frame projection: {report['status']} => {args.out}")


if __name__=="__main__":
    main()

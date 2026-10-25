"""Fail-closed metadata-only nonhuman headform evidence review; never assigns S1."""
import argparse
import json
import re
from hashlib import sha256
from pathlib import Path

SCHEMA = "neuroshield.external-evidence/0.1"
METRICS = {"linear_peak_m_s2", "angular_peak_rad_s2", "angular_velocity_peak_rad_s", "linear_waveform_rmse_m_s2", "angular_waveform_rmse_rad_s2"}
def _exact(obj, fields):
    if not isinstance(obj, dict) or set(obj) != set(fields):
        raise ValueError("Unexpected or missing metadata fields")
    return obj
def review_record(record):
    _exact(record, ("schema_version", "dataset_id", "origin", "source", "rights", "acquisition", "evaluation"))
    if record["schema_version"] != SCHEMA: raise ValueError("Unsupported evidence schema")
    if record["origin"] not in ("NONHUMAN_INSTRUMENTED_HEADFORM", "SYNTHETIC_HEADFORM_FIXTURE"):
        raise ValueError("Human and unknown records prohibited")
    if not isinstance(record["dataset_id"], str) or not 1 <= len(record["dataset_id"]) <= 160: raise ValueError("Invalid dataset ID")
    s = _exact(record["source"], ("url", "sha256", "license_document", "citation"))
    if not isinstance(s["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", s["sha256"]):
        raise ValueError("Invalid source SHA-256")
    if record["origin"] == "NONHUMAN_INSTRUMENTED_HEADFORM" and (not isinstance(s["url"],str) or not s["url"].startswith("https://")):
        raise ValueError("External source must be HTTPS")
    for key in ("license_document","citation"):
        if not isinstance(s[key],str) or not s[key].strip(): raise ValueError("Missing source metadata")
    rights=_exact(record["rights"], ("local_analysis_approved","redistribution_approved","reviewer_reference"))
    acq=_exact(record["acquisition"], ("calibration_reviewed","coordinate_frame_reviewed","uncertainty_reviewed","laboratory_reference"))
    ev=_exact(record["evaluation"], ("preregistration_reference","metrics","replicate_count","independent_lab_reviewed"))
    for obj,keys in ((rights,("local_analysis_approved","redistribution_approved")),(acq,("calibration_reviewed","coordinate_frame_reviewed","uncertainty_reviewed")),(ev,("independent_lab_reviewed",))):
        for k in keys:
            if type(obj[k]) is not bool: raise ValueError("Review flags must be Boolean")
    for obj,keys in ((rights,("reviewer_reference",)),(acq,("laboratory_reference",)),(ev,("preregistration_reference",))):
        for k in keys:
            if not isinstance(obj[k],str) or not obj[k].strip(): raise ValueError("Missing review reference")
    if not isinstance(ev["metrics"],list) or not ev["metrics"] or any(x not in METRICS for x in ev["metrics"]) or len(set(ev["metrics"])) != len(ev["metrics"]):
        raise ValueError("Unsupported or duplicate metrics")
    if type(ev["replicate_count"]) is not int or not 0 <= ev["replicate_count"] <= 100000: raise ValueError("Invalid replicate count")
    blockers=[]
    if record["origin"] != "NONHUMAN_INSTRUMENTED_HEADFORM": blockers.append("SYNTHETIC_ONLY")
    if not rights["local_analysis_approved"]: blockers.append("RIGHTS_LOCAL_ANALYSIS_UNVERIFIED")
    if not acq["calibration_reviewed"]: blockers.append("CALIBRATION_REVIEW_MISSING")
    if not acq["coordinate_frame_reviewed"]: blockers.append("FRAME_REVIEW_MISSING")
    if not acq["uncertainty_reviewed"]: blockers.append("UNCERTAINTY_REVIEW_MISSING")
    if ev["replicate_count"] < 2: blockers.append("REPLICATION_INSUFFICIENT")
    if not ev["independent_lab_reviewed"]: blockers.append("INDEPENDENT_LAB_REVIEW_MISSING")
    digest=sha256(json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    return {"schema_version":SCHEMA,"dataset_id":record["dataset_id"],"record_sha256":digest,
        "status":"BLOCKED" if blockers else "REVIEW_REQUIRED","scientific_evidence_level":"S0",
        "blockers":blockers,"redistribution_allowed_by_declaration":rights["redistribution_approved"],
        "note":"Declarative metadata only; no calibration, legal permission, injury, safety, or certification proof."}
def main(argv=None):
    p=argparse.ArgumentParser(description="Offline metadata-only external headform evidence gate")
    p.add_argument("record",type=Path);p.add_argument("--out",type=Path)
    a=p.parse_args(argv)
    if a.record.stat().st_size > 65536: raise ValueError("Record too large")
    report=review_record(json.loads(a.record.read_text(encoding="utf-8")))
    output=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if a.out: a.out.write_text(output,encoding="utf-8")
    else: print(output,end="")
    return 2 if report["status"] == "BLOCKED" else 0
if __name__ == "__main__": raise SystemExit(main())

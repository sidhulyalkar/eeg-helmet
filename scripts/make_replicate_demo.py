"""Create a deterministic SYNTHETIC study for testing the replicate-study CLI.

No sensor or medical measurements; destination must be a new directory.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from shutil import copyfile

from neuroshield.headform import validate_headform_bundle
from neuroshield.replicate_study import CHANNELS, SCHEMA


def generate(destination: Path, *, example_dir: Path) -> Path:
    if destination.exists():
        raise ValueError("Destination already exists; refusing to overwrite any data")
    destination.mkdir(parents=True)
    pairs = []
    for i in range(3):
        pair = {}
        for arm in ("reference", "candidate"):
            triple = {}
            for kind in ("profile", "manifest", "csv"):
                src = example_dir / (f"bench-{arm}-SYNTHETIC.csv" if kind == "csv" else f"bench-{arm}-SYNTHETIC-{kind}.json")
                dst = destination / f"pair-{i+1}-{arm}-{kind}.{'csv' if kind == 'csv' else 'json'}"
                copyfile(src,dst)
                triple[kind] = dst.name
            csv = destination / triple["csv"]
            lines = csv.read_text(encoding="utf-8").splitlines()
            # Distinct synthetic waveforms and SHA-256 data identities per acquisition.
            multiplier = 1 + i*.009 + (0.002 if arm == "candidate" else 0)
            for row in range(1,len(lines)):
                values = lines[row].split(",")
                values[1] = f"{float(values[1])*multiplier:.9f}"
                lines[row] = ",".join(values)
            csv.write_text("\n".join(lines)+"\n",encoding="utf-8")
            profile_path = destination / triple["profile"]
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["acquisition"]["replicate_id"] = f"synthetic-{i+1}-{arm}"
            profile["acquisition"]["trial_id"] = f"synthetic-{i+1}"
            bundle = validate_headform_bundle(destination/triple["manifest"],csv)
            profile["headform_bundle_sha256"] = bundle["bundle_sha256"]
            profile["source"]["raw_data_sha256"] = bundle["csv_sha256"]
            profile_path.write_text(json.dumps(profile,indent=2)+"\n",encoding="utf-8")
            pair[arm] = triple
        pairs.append(pair)
    study = {
        "schema_version":SCHEMA,"plan_id":"synthetic-paired-replicates-v09",
        "scope":"NONHUMAN_PAIRED_IMPACT_TRIALS","expected_origin":"SYNTHETIC_HEADFORM_FIXTURE",
        "protocol":"NOT_A_REAL_PROTOCOL","impact_location":"facemask","rig_id":"NO_RIG_SIMULATED",
        "target_speed_m_s":5.0,"speed_tolerance_m_s":.05,
        "max_peak_regression_percent":{k:0.0 for k in CHANNELS},"pairs":pairs,
    }
    path = destination / "study-SYNTHETIC.json"
    path.write_text(json.dumps(study,indent=2)+"\n",encoding="utf-8")
    return path

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("destination",type=Path)
    args=cli.parse_args()
    examples = Path(__file__).resolve().parents[1] / "examples"
    print(generate(args.destination,example_dir=examples))

"""Entrypoint for local demonstration, deterministic exports, and validation."""
import argparse
import json
from pathlib import Path
from .models import Parameters, SCENARIOS
from .analysis import comparison
from .cad import write_mount_visualization
from .ingestion import validate_kinematics_csv
from .server import serve


def main():
    parser = argparse.ArgumentParser(prog="neuroshield")
    command = parser.add_subparsers(dest="command", required=True)
    web = command.add_parser("serve", help="Run loopback-only synthetic demo server")
    web.add_argument("--port", type=int, default=8765)
    sim = command.add_parser("export", help="Write synthetic comparison JSON")
    sim.add_argument("--scenario", choices=SCENARIOS, default="oblique")
    sim.add_argument("--out", required=True)
    sweep_parser = command.add_parser("sweep", help="Exploratory Pareto grid over unvalidated model; no safety conclusions")
    sweep_parser.add_argument("--out", required=True)
    sample = command.add_parser("validate-csv", help="Validate schema/units of a local IMU CSV, without uploading")
    sample.add_argument("path")
    qual = command.add_parser("qualify", help="Generate S0 numerical step-size qualification report")
    qual.add_argument("--scenario", choices=SCENARIOS, default="oblique")
    qual.add_argument("--out", required=True)
    session = command.add_parser("validate-session", help="Check local synthetic-only session contract")
    session.add_argument("path")
    fixture = command.add_parser("synthetic-session", help="Write a synthetic-only multimodal fixture")
    fixture.add_argument("--out", required=True)
    cad = command.add_parser("cad-preview", help="Create a NONFUNCTIONAL OpenSCAD geometry visualization")
    cad.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "serve":
        serve(port=args.port)
    elif args.command == "export":
        result = comparison(args.scenario, Parameters.suggested())
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Saved synthetic research output to {args.out}")
    elif args.command == "sweep":
        from .design_space import sweep
        result=sweep()
        Path(args.out).write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(f"Saved {result['candidate_count']} synthetic candidates ({result['pareto_count']} Pareto designs) to {args.out}")
    elif args.command == "qualify":
        from .qualification import qualify
        result = qualify(args.scenario)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Numerical qualification: {result['status']} => {args.out}")
    elif args.command == "validate-session":
        from .session import validate_session_file
        print(json.dumps(validate_session_file(args.path), indent=2))
    elif args.command == "synthetic-session":
        from .session import synthetic_fixture
        Path(args.out).write_text(json.dumps(synthetic_fixture(), indent=2), encoding="utf-8")
        print(f"Saved synthetic fixture to {args.out}")
    elif args.command == "validate-csv":
        print(json.dumps(validate_kinematics_csv(args.path), indent=2))
    else:
        print(write_mount_visualization(args.out, Parameters.suggested()))


if __name__ == "__main__":
    main()

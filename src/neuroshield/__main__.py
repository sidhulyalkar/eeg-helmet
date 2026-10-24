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
    audit_trace = command.add_parser("export-audit-trace", help="Full-precision aligned S0 impact trace, no human data")
    audit_trace.add_argument("--scenario", choices=SCENARIOS, default="oblique")
    audit_trace.add_argument("--out", required=True)
    sweep_parser = command.add_parser("sweep", help="Exploratory Pareto grid over unvalidated model; no safety conclusions")
    sweep_parser.add_argument("--out", required=True)
    sample = command.add_parser("validate-csv", help="Validate schema/units of a local IMU CSV, without uploading")
    sample.add_argument("path")
    qual = command.add_parser("qualify", help="Generate S0 numerical step-size qualification report")
    qual.add_argument("--scenario", choices=SCENARIOS, default="oblique")
    qual.add_argument("--out", required=True)
    iq = command.add_parser("qualify-independent", help="Cross-integrator / energy-budget audit (synthetic model only)")
    iq.add_argument("--scenario", choices=("all", *SCENARIOS), default="all")
    iq.add_argument("--out", required=True)
    bench = command.add_parser("validate-headform", help="Local-only NONHUMAN headform metadata and CSV structure check")
    bench.add_argument("manifest")
    bench.add_argument("csv")
    intake = command.add_parser("inspect-bench-intake", help="Offline NONHUMAN provenance and quality-gate check")
    intake.add_argument("profile")
    intake.add_argument("manifest")
    intake.add_argument("csv")
    paired = command.add_parser("compare-bench-pair", help="Offline nonhuman reference/candidate comparison; no safety rating")
    paired.add_argument("reference_profile")
    paired.add_argument("reference_manifest")
    paired.add_argument("reference_csv")
    paired.add_argument("candidate_profile")
    paired.add_argument("candidate_manifest")
    paired.add_argument("candidate_csv")
    paired.add_argument("--out", required=True)
    session = command.add_parser("validate-session", help="Check local synthetic-only session contract")
    session.add_argument("path")
    fixture = command.add_parser("synthetic-session", help="Write a synthetic-only multimodal fixture")
    fixture.add_argument("--out", required=True)
    cad = command.add_parser("cad-preview", help="Create a NONFUNCTIONAL OpenSCAD geometry visualization")
    cad.add_argument("--out", required=True)
    kn = command.add_parser("knowledge", help="Offline evidence registry and committed-source retrieval workflow")
    kn_sub = kn.add_subparsers(dest="knowledge_action", required=True)
    kn_audit = kn_sub.add_parser("audit", help="Validate local S0 evidence registry structure")
    kn_audit.add_argument("--root", default=".")
    kn_stage = kn_sub.add_parser("stage", help="Stage allowlisted committed HEAD files outside checkout")
    kn_stage.add_argument("--root", default=".")
    kn_stage.add_argument("--out", required=True)
    kn_search = kn_sub.add_parser("search", help="Search staged committed sources with a lexical baseline")
    kn_search.add_argument("--stage", required=True)
    kn_search.add_argument("--top-k", type=int, default=5)
    kn_search.add_argument("query")
    kn_bench = kn_sub.add_parser("bench", help="Run frozen retrieval benchmark against staged corpus")
    kn_bench.add_argument("--root", default=".")
    kn_bench.add_argument("--stage", required=True)
    kn_bench.add_argument("--top-k", type=int, default=5)
    kn_bench.add_argument("--out", required=True)
    cp = command.add_parser("corpora", help="Offline curated research reference catalogs (no source documents downloaded)")
    cp_sub = cp.add_subparsers(dest="corpora_action", required=True)
    for action in ("audit", "list", "gaps", "stage", "search", "bench"):
        sub = cp_sub.add_parser(action)
        sub.add_argument("--root", default=".")
        if action in ("list", "search"):
            sub.add_argument("--domain", choices=("all", "biomechanics", "neural", "evidence"), default="all")
        if action == "search":
            sub.add_argument("query")
            sub.add_argument("--top-k", type=int, default=5)
        if action == "stage":
            sub.add_argument("--out", required=True)
        if action == "bench":
            sub.add_argument("--top-k", type=int, default=5)
            sub.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "corpora":
        from . import corpora
        from .knowledge import KnowledgeError
        try:
            if args.corpora_action == "audit":
                result = corpora.audit(args.root)
            elif args.corpora_action == "list":
                result = corpora.list_sources(args.root, args.domain)
            elif args.corpora_action == "gaps":
                result = corpora.qualification_gaps(args.root)
            elif args.corpora_action == "stage":
                result = corpora.stage_metadata(args.root, args.out)
            elif args.corpora_action == "search":
                result = corpora.search(args.root, args.query, args.domain, args.top_k)
            else:
                result = corpora.benchmark(args.root, args.top_k)
                Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        except (KnowledgeError, OSError) as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2, allow_nan=False))
    elif args.command == "knowledge":
        from .knowledge import KnowledgeError, audit, stage, search, benchmark
        try:
            if args.knowledge_action == "audit":
                result = audit(args.root)
            elif args.knowledge_action == "stage":
                result = stage(args.root, args.out)
            elif args.knowledge_action == "search":
                result = search(args.stage, args.query, args.top_k)
            else:
                result = benchmark(args.root, args.stage, args.top_k)
                Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        except KnowledgeError as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2, allow_nan=False))
    elif args.command == "serve":
        serve(port=args.port)
    elif args.command == "export":
        result = comparison(args.scenario, Parameters.suggested())
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Saved synthetic research output to {args.out}")
    elif args.command == "export-audit-trace":
        from .physics import simulate
        result = simulate(args.scenario, include_audit_traces=True)
        Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
        print(f"Saved full-precision synthetic audit trace to {args.out}")
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
    elif args.command == "qualify-independent":
        from .independent_qualification import qualify_independent
        result = qualify_independent(args.scenario)
        Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
        print(f"Independent S0 numerical check: {result['status']} ({result['passed']}/{result['case_count']}) => {args.out}")
        if result["status"] != "PASS_NUMERICAL_ONLY":
            raise SystemExit(1)
    elif args.command == "validate-headform":
        from .headform import validate_headform_bundle
        print(json.dumps(validate_headform_bundle(args.manifest, args.csv), indent=2))
    elif args.command == "inspect-bench-intake":
        from .bench_intake import validate_intake
        print(json.dumps(validate_intake(args.profile, args.manifest, args.csv), indent=2, allow_nan=False))
    elif args.command == "compare-bench-pair":
        from .bench_intake import compare_paired_trials
        report = compare_paired_trials(
            (args.reference_profile, args.reference_manifest, args.reference_csv),
            (args.candidate_profile, args.candidate_manifest, args.candidate_csv))
        Path(args.out).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Descriptive NONHUMAN benchmark: {report['status']} => {args.out}")
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

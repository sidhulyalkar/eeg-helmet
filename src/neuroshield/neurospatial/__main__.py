"""Run the synthetic NeuroSpatial inverse-research experiment offline."""
import argparse
import json
from pathlib import Path

from .experiment import run_toy_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="S0 NeuroSpatial inverse research; synthetic data only")
    parser.add_argument("--out", required=True, help="Path for an explicitly synthetic JSON report")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--channels", type=int, default=24)
    parser.add_argument("--sources", type=int, default=96)
    args = parser.parse_args()
    result = run_toy_experiment(args.seed, args.channels, args.sources)
    Path(args.out).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"S0 synthetic source inversion: rank {result['leadfield_rank']} / {result['modeled_sources']} => {args.out}")


if __name__ == "__main__":
    main()

"""Third-party RO-Crate validation, not a scientific evidence check.
Requires pip install roc-validator==0.12.2 (optional developer dependency).
"""
from __future__ import annotations
import argparse
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Attached RO-Crate root")
    args = parser.parse_args(argv)
    if not args.directory.is_dir():
        parser.error("Expected a research bundle directory")
    try:
        from rocrate_validator import services
    except ImportError:
        parser.error("Install optional roc-validator==0.12.2")
    result = services.validate({"rocrate_uri": str(args.directory), "profile_identifier": "ro-crate-1.3"})
    print(result.to_json())
    return 0 if result.passed() else 1

if __name__ == "__main__":
    raise SystemExit(main())

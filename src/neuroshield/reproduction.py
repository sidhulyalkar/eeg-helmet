"""Offline re-execution of a synthetic research bundle against the installed source.

A successful replay shows computational reproducibility, not source authenticity,
physical calibration, clinical validity, or signed provenance. Never reads user
provided code or exposes any network/device capability.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .agent_protocol import (
    MAX_REPORT_BYTES, _bounded_json, _source_identity, execute,
    read_request, verify_bundle,
)
from .provenance import canonical_hash

# Reproduction tolerances are fixed policy, not user- or agent-controlled.
REL_TOL = 1e-10
ABS_TOL = 1e-12
MAX_DIFFERENCE_PATHS = 12


def _compare(previous, observed, path, differences):
    """Recursively compare a replay. No tolerance on decisions or integer counts."""
    if type(previous) is not type(observed):
        differences.append(path + ':TYPE_CHANGED')
    elif isinstance(previous, dict):
        if previous.keys() != observed.keys():
            differences.append(path + ':FIELDS_CHANGED')
        else:
            for key in sorted(previous):
                _compare(previous[key], observed[key], path + '.' + key, differences)
    elif isinstance(previous, list):
        if len(previous) != len(observed):
            differences.append(path + ':LENGTH_CHANGED')
        else:
            for i, (a, b) in enumerate(zip(previous, observed)):
                _compare(a, b, f'{path}[{i}]', differences)
    elif type(previous) is float:
        if not (math.isfinite(previous) and math.isfinite(observed)):
            differences.append(path + ':NONFINITE')
        elif previous != observed:
            if not math.isclose(previous, observed, rel_tol=REL_TOL, abs_tol=ABS_TOL):
                differences.append(path + ':NUMERIC_OUTSIDE_TOLERANCE')
    elif previous != observed:
        differences.append(path + ':VALUE_CHANGED')


def replay_bundle(bundle_path: str | Path) -> dict:
    """Replay a verified bundle. Report never contains raw samples or input paths."""
    root = Path(bundle_path)
    receipt = verify_bundle(root)
    task = read_request(root / 'task.json')
    saved = _bounded_json(root / 'result.json', MAX_REPORT_BYTES)
    code_sha = _source_identity(task['operation'])
    observed_identity = canonical_hash(code_sha)
    if saved['source_sha256'] != code_sha:
        return {
            'schema_version': 'neuroshield.replay/0.1',
            'status': 'BLOCKED_SOURCE_REVISION_MISMATCH',
            'scientific_evidence_level': 'S0',
            'task_sha256': receipt['task_sha256'],
            'recorded_result_sha256': receipt['result_sha256'],
            'source_identity_sha256': observed_identity,
            'difference_paths': [],
            'numerical_tolerances': {'relative': REL_TOL, 'absolute': ABS_TOL},
            'note': 'Recorded implementation sources differ from installed sources. No replay was attempted.',
        }
    rerun = execute(task)
    differences = []
    # A change to source or any categorical scientific conclusion is never tolerated.
    before = {k: v for k, v in saved.items() if k != 'result_sha256'}
    after = {k: v for k, v in rerun.items() if k != 'result_sha256'}
    _compare(before, after, 'report', differences)
    if differences:
        verdict = 'FAILED_REPRODUCTION_MISMATCH'
    elif saved['result_sha256'] == rerun['result_sha256']:
        verdict = 'REPRODUCED_EXACT'
    else:
        verdict = 'REPRODUCED_WITHIN_NUMERICAL_TOLERANCE'
    return {
        'schema_version': 'neuroshield.replay/0.1',
        'status': verdict,
        'scientific_evidence_level': 'S0',
        'task_sha256': receipt['task_sha256'],
        'recorded_result_sha256': receipt['result_sha256'],
        'recomputed_result_sha256': rerun['result_sha256'],
        'source_identity_sha256': observed_identity,
        'difference_paths': differences[:MAX_DIFFERENCE_PATHS],
        'difference_count': len(differences),
        'numerical_tolerances': {'relative': REL_TOL, 'absolute': ABS_TOL},
        'note': 'Computational check only: hashes are not signatures; no physical or clinical claims.',
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Recompute an offline synthetic NeuroShield research bundle')
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    try:
        report = replay_bundle(args.bundle)
        encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n'
        if args.out is not None:
            # Never overwrite an existing report or write into the source bundle.
            if args.out.exists() or args.out.is_symlink():
                raise ValueError('Refusing to overwrite replay report')
            if args.bundle.resolve() in args.out.resolve().parents:
                raise ValueError('Replay report must be outside the source bundle')
            args.out.write_text(encoded, encoding='utf-8', newline='\n')
        print(encoded, end='')
        return 0 if report['status'] in ('REPRODUCED_EXACT', 'REPRODUCED_WITHIN_NUMERICAL_TOLERANCE') else 2
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

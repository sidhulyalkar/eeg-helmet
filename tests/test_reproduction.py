"""Independent-replay controls for synthetic research artifacts."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from neuroshield.agent_protocol import SCHEMA, create_bundle, verify_bundle
from neuroshield.provenance import canonical_hash
from neuroshield.reproduction import replay_bundle


def task(op='simulate_synthetic'):
    return {'schema_version': SCHEMA, 'task_id': 'replay-001', 'operation': op,
            'data_class': 'SYNTHETIC_ONLY', 'inputs': ({'scenario': 'oblique', 'parameters': {}}
            if op == 'simulate_synthetic' else {'scenario': 'oblique'})}


def rehash_report(path, edit):
    report_path = path / 'result.json'
    report = json.loads(report_path.read_text())
    edit(report)
    report['result_sha256'] = canonical_hash({k: v for k, v in report.items() if k != 'result_sha256'})
    encoded = (json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    report_path.write_bytes(encoded)
    checks_path = path / 'checksums.json'
    checks = json.loads(checks_path.read_text())
    checks['files']['result.json'] = hashlib.sha256(encoded).hexdigest()
    checks_path.write_text(json.dumps(checks))


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / 'bundle'

    def test_exact_replay_simulation(self):
        create_bundle(task(), self.bundle)
        result = replay_bundle(self.bundle)
        self.assertEqual(result['status'], 'REPRODUCED_EXACT')
        self.assertEqual(result['difference_count'], 0)
        self.assertEqual(result['scientific_evidence_level'], 'S0')
        self.assertNotIn(str(self.root), str(result))

    def test_exact_replay_numerical(self):
        create_bundle(task('audit_synthetic_numerics'), self.bundle)
        self.assertEqual(replay_bundle(self.bundle)['status'], 'REPRODUCED_EXACT')

    def test_independently_rehashed_false_result_is_detected(self):
        create_bundle(task(), self.bundle)
        rehash_report(self.bundle, lambda r: r['result']['metrics_unrounded'].__setitem__(
            'peak_head_accel_g', r['result']['metrics_unrounded']['peak_head_accel_g'] * 1.2))
        self.assertEqual(verify_bundle(self.bundle)['status'], 'LOCAL_INTEGRITY_VERIFIED_NOT_AUTHENTICATED')
        report = replay_bundle(self.bundle)
        self.assertEqual(report['status'], 'FAILED_REPRODUCTION_MISMATCH')
        self.assertTrue(any('peak_head_accel_g' in x for x in report['difference_paths']))

    def test_rehashed_categorical_change_always_fails(self):
        create_bundle(task(), self.bundle)
        rehash_report(self.bundle, lambda r: r.__setitem__('status', 'PHYSICAL_VALIDATION_PASSED'))
        self.assertEqual(replay_bundle(self.bundle)['status'], 'FAILED_REPRODUCTION_MISMATCH')

    def test_nearby_float_change_is_reported_not_claimed_exact(self):
        create_bundle(task(), self.bundle)
        def subtle(r):
            metrics = r['result']['metrics_unrounded']
            metrics['peak_head_accel_g'] *= (1 + 1e-11)
        rehash_report(self.bundle, subtle)
        self.assertEqual(replay_bundle(self.bundle)['status'], 'REPRODUCED_WITHIN_NUMERICAL_TOLERANCE')

    def test_modified_code_identity_blocks_even_if_bundle_self_consistent(self):
        create_bundle(task(), self.bundle)
        with patch('neuroshield.reproduction._source_identity', return_value={'wrong.py': 'a' * 64}):
            result = replay_bundle(self.bundle)
        self.assertEqual(result['status'], 'BLOCKED_SOURCE_REVISION_MISMATCH')
        self.assertNotIn('recomputed_result_sha256', result)

    def test_tampered_bundle_fails_before_execution(self):
        create_bundle(task(), self.bundle)
        (self.bundle / 'result.json').write_text('{}')
        with self.assertRaises(ValueError): replay_bundle(self.bundle)

    def test_symlinked_bundle_rejected(self):
        create_bundle(task(), self.bundle)
        link = self.root / 'symlink'
        try: link.symlink_to(self.bundle, target_is_directory=True)
        except (OSError, NotImplementedError): self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError): replay_bundle(link)

    def test_replay_cli_returns_nonzero_on_replay_failure(self):
        create_bundle(task(), self.bundle)
        rehash_report(self.bundle, lambda r: r['result']['metrics_unrounded'].__setitem__('peak_head_accel_g', 9999.0))
        proc = subprocess.run([sys.executable, '-m', 'neuroshield.reproduction', str(self.bundle)],
                              capture_output=True, text=True, timeout=35)
        self.assertEqual(proc.returncode, 2)
        self.assertIn('FAILED_REPRODUCTION_MISMATCH', proc.stdout)

    def test_replay_cli_writes_new_report_outside_bundle(self):
        create_bundle(task(), self.bundle)
        out = self.root / 'replay.json'
        proc = subprocess.run([sys.executable, '-m', 'neuroshield.reproduction', str(self.bundle), '--out', str(out)],
                              capture_output=True, text=True, timeout=35)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(out.read_text())['status'], 'REPRODUCED_EXACT')
        proc2 = subprocess.run([sys.executable, '-m', 'neuroshield.reproduction', str(self.bundle), '--out', str(out)],
                               capture_output=True, text=True, timeout=35)
        self.assertNotEqual(proc2.returncode, 0)

    def test_reject_output_inside_bundle(self):
        create_bundle(task(), self.bundle)
        proc = subprocess.run([sys.executable, '-m', 'neuroshield.reproduction', str(self.bundle), '--out', str(self.bundle / 'report.json')],
                              capture_output=True, text=True, timeout=35)
        self.assertNotEqual(proc.returncode, 0)

    def test_reject_unknown_source_schema(self):
        create_bundle(task(), self.bundle)
        rehash_report(self.bundle, lambda r: r.__setitem__('source_sha256', {'evil.py':'a'*64}))
        self.assertEqual(replay_bundle(self.bundle)['status'], 'BLOCKED_SOURCE_REVISION_MISMATCH')


if __name__ == '__main__': unittest.main()

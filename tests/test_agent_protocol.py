"""Adversarial contract tests for the strictly S0, offline agent interface."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from neuroshield.agent_protocol import (
    SCHEMA, capabilities, validate_request, execute, create_bundle,
    verify_bundle, read_request, task_schema,
)


def request(op="simulate_synthetic"):
    return {"schema_version": SCHEMA, "task_id": "agent-test-1",
            "operation": op, "data_class": "SYNTHETIC_ONLY",
            "inputs": ({"scenario": "oblique", "parameters": {}}
                       if op == "simulate_synthetic" else {"scenario": "oblique"})}


class AgentContractTests(unittest.TestCase):
    def test_bundled_schema_is_pinned_and_refuses_unsafe_ops(self):
        schema = task_schema()
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(schema["oneOf"]), 2)
        self.assertEqual(schema["$defs"]["numericalTask"]["properties"]["operation"]["const"], "audit_synthetic_numerics")
        try:
            import jsonschema
        except ImportError:
            return  # jsonschema is an optional *developer* verification dependency.
        validator = jsonschema.Draft202012Validator(schema)
        validator.check_schema(schema)
        self.assertTrue(validator.is_valid(request()))
        self.assertTrue(validator.is_valid(request("audit_synthetic_numerics")))
        invalid = request(); invalid["operation"] = "read_private_file"
        self.assertFalse(validator.is_valid(invalid))

    def test_exposes_only_allowlisted_offline_capabilities(self):
        result = capabilities()
        self.assertEqual(set(result["capabilities"]), {"simulate_synthetic", "audit_synthetic_numerics"})
        self.assertTrue(all(not c["network"] and not c["writes"] and c["evidence_ceiling"] == "S0"
                            for c in result["capabilities"].values()))

    def test_rejects_unknown_operations_and_command_injection(self):
        for name in ["shell", "fetch_url", "ingest_human", "__import__('os').system('whoami')"]:
            with self.subTest(name=name):
                req = request(); req["operation"] = name
                with self.assertRaises(ValueError): validate_request(req)

    def test_rejects_human_nonhuman_and_unknown_data_origins(self):
        for kind in ["HUMAN_RECORDING", "NONHUMAN_MEASURED", "UNKNOWN", None]:
            req = request(); req["data_class"] = kind
            with self.assertRaises(ValueError): validate_request(req)

    def test_refuses_extra_task_metadata_and_io_directives(self):
        for key in ["url", "write_path", "command", "evidence_level", "subject_id"]:
            req = request(); req[key] = "fake"
            with self.assertRaises(ValueError): validate_request(req)

    def test_rejects_id_traversal_and_bad_parameters(self):
        for val in ["../foo", "a/b", "a b", "", ".", "~" * 80]:
            req = request(); req["task_id"] = val
            # Single '.' ID is safe but ideally rejected by policy.
            if val == ".":
                self.assertRaises(ValueError, validate_request, req)
            else:
                with self.assertRaises(ValueError): validate_request(req)
        for param in [{"mount_k_n_m": 1}, {"mount_k_n_m": True}, {"subprocess": "ls"}, ["arbitrary"]]:
            req = request(); req["inputs"]["parameters"] = param
            with self.assertRaises(ValueError): validate_request(req)

    def test_normalization_is_deterministic(self):
        req = request()
        task = validate_request(req)
        self.assertEqual(task, validate_request(copy.deepcopy(task)))
        self.assertEqual(len(task["inputs"]["parameters"]), 5)

    def test_synthetic_run_never_claims_physical_evidence(self):
        a = execute(request()); b = execute(request())
        self.assertEqual(a, b)
        self.assertEqual(a["scientific_evidence_level"], "S0")
        self.assertEqual(a["status"], "SYNTHETIC_DEMONSTRATION_ONLY")
        self.assertEqual(len(a["source_sha256"]), 4)
        self.assertEqual(len(a["result"]["trace_sha256"]), 64)
        self.assertNotIn("raw_samples", json.dumps(a))

    def test_numerical_audit_never_promotes(self):
        result = execute(request("audit_synthetic_numerics"))
        self.assertEqual(result["scientific_evidence_level"], "S0")
        self.assertIn(result["status"], {"NUMERICAL_CHECK_ONLY", "NUMERICAL_CHECK_FAILED"})
        self.assertEqual(result["result"]["cases_total"], 4)
        self.assertEqual(result["result"]["cases_passed"], 4)

    def test_bundle_roundtrip_and_rocrate_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "new-bundle"
            create_bundle(request(), out)
            x = verify_bundle(out)
            self.assertEqual(x["status"], "LOCAL_INTEGRITY_VERIFIED_NOT_AUTHENTICATED")
            crate = json.loads((out / "ro-crate-metadata.json").read_text())
            self.assertEqual(crate["@context"], "https://w3id.org/ro/crate/1.3/context")
            self.assertEqual(len(crate["@graph"]), 7)
            self.assertEqual(json.loads((out/"result.json").read_text())["scientific_evidence_level"],"S0")

    def test_disallows_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            create_bundle(request(), out)
            with self.assertRaises(FileExistsError): create_bundle(request(), out)

    def test_tampered_reports_and_tasks_fail(self):
        for name in ["result.json", "task.json"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                out = Path(temp) / "bundle"
                create_bundle(request(), out)
                with (out / name).open("a") as f: f.write("\n")
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    verify_bundle(out)

    def test_rejects_symlinked_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            create_bundle(request(), out)
            (out / "task.json").unlink()
            (out / "task.json").symlink_to(out / "result.json")
            with self.assertRaises(ValueError): verify_bundle(out)

    def test_crate_tampering_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            create_bundle(request(), out)
            crate = json.loads((out / "ro-crate-metadata.json").read_text())
            crate["@graph"][1]["name"] = "Unverified physical experiment"
            (out / "ro-crate-metadata.json").write_text(json.dumps(crate))
            with self.assertRaisesRegex(ValueError, "metadata mismatch"):
                verify_bundle(out)

    def test_rejects_duplicate_json_fields_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "req.json"
            for content in ['{"schema_version": "x", "schema_version": "y"}', '{"thing": NaN}']:
                p.write_text(content)
                with self.assertRaises(ValueError): read_request(p)

    def test_does_not_trust_rehashed_evidence_escalation(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            create_bundle(request(), out)
            # Rewrite both report and hash file, simulating a malicious local editor.
            import hashlib
            report = json.loads((out / "result.json").read_text())
            from neuroshield.provenance import canonical_hash
            report["scientific_evidence_level"] = "S4"
            report["result_sha256"] = canonical_hash({k:v for k,v in report.items() if k != "result_sha256"})
            encoded = (json.dumps(report,sort_keys=True,indent=2)+"\n").encode()
            (out / "result.json").write_bytes(encoded)
            checks = json.loads((out / "checksums.json").read_text())
            checks["files"]["result.json"] = hashlib.sha256(encoded).hexdigest()
            (out / "checksums.json").write_text(json.dumps(checks))
            with self.assertRaisesRegex(ValueError, "escalated"):
                verify_bundle(out)


if __name__ == "__main__":
    unittest.main()

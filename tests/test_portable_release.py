"""Standalone, offline checks that a research crate is portable and versioned."""
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from importlib import metadata, resources

from neuroshield.agent_protocol import create_bundle, task_schema, verify_bundle
from neuroshield.reproduction import replay_bundle


TASK = {"schema_version":"neuroshield.agent-task/0.1", "task_id":"portable-001",
        "operation":"simulate_synthetic", "data_class":"SYNTHETIC_ONLY",
        "inputs":{"scenario":"oblique", "parameters":{}}}


class PortableReleaseTests(unittest.TestCase):
    def test_schema_loads_as_package_resource(self):
        self.assertEqual(task_schema()["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertTrue(resources.files("neuroshield").joinpath("schemas/agent-task.schema.json").is_file())

    def test_publication_date_required_and_integrity_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"crate"
            create_bundle(TASK,dst)
            data=json.loads((dst/"ro-crate-metadata.json").read_text())
            root=next(x for x in data["@graph"] if x["@id"]=="./")
            self.assertEqual(date.fromisoformat(root["datePublished"]).isoformat(),root["datePublished"])
            self.assertIn("No output license", root["license"])
            software=next(x for x in data["@graph"] if x["@id"]=="#neuroshield")
            self.assertEqual(software["version"],"1.3.0")
            self.assertEqual(software["url"],"https://github.com/sidhulyalkar/eeg-helmet")
            checks=json.loads((dst/"checksums.json").read_text())
            self.assertEqual(checks["schema_version"],"neuroshield.artifact-checksums/0.2")
            self.assertIn("ro-crate-metadata.json",checks["files"])
            self.assertEqual(verify_bundle(dst)["status"],"LOCAL_INTEGRITY_VERIFIED_NOT_AUTHENTICATED")
            # A merely changed publication date must be detected even if no
            # scientific result or task value changes.
            root["datePublished"]="2020-01-01"
            (dst/"ro-crate-metadata.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"checksum mismatch"):
                verify_bundle(dst)

    def test_historical_v01_crate_can_still_be_verified(self):
        from neuroshield.agent_protocol import _json_bytes, _crate_metadata
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"crate"
            create_bundle(TASK,dst)
            t=json.loads((dst/"task.json").read_text())
            r=json.loads((dst/"result.json").read_text())
            (dst/"ro-crate-metadata.json").write_bytes(_json_bytes(_crate_metadata(t,r)))
            checksum={"schema_version":"neuroshield.artifact-checksums/0.1","files":{
                x:hashlib.sha256((dst/x).read_bytes()).hexdigest() for x in ("task.json","result.json")}}
            (dst/"checksums.json").write_bytes(_json_bytes(checksum))
            self.assertEqual(verify_bundle(dst)["scientific_evidence_level"],"S0")

    def test_unsupported_malformed_date_is_rejected_even_if_rehashed(self):
        from neuroshield.agent_protocol import _json_bytes
        with tempfile.TemporaryDirectory() as tmp:
            dst=Path(tmp)/"crate"
            create_bundle(TASK,dst)
            data=json.loads((dst/"ro-crate-metadata.json").read_text())
            next(x for x in data["@graph"] if x["@id"]=="./")["datePublished"]="2026-99-99"
            b=_json_bytes(data)
            (dst/"ro-crate-metadata.json").write_bytes(b)
            checks=json.loads((dst/"checksums.json").read_text())
            checks["files"]["ro-crate-metadata.json"]=hashlib.sha256(b).hexdigest()
            (dst/"checksums.json").write_bytes(_json_bytes(checks))
            with self.assertRaisesRegex(ValueError,"datePublished"):
                verify_bundle(dst)

    def test_scientific_identity_is_not_time_dependent(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a",Path(tmp)/"b"
            create_bundle(TASK,a)
            create_bundle(TASK,b)
            first=json.loads((a/"result.json").read_text())
            second=json.loads((b/"result.json").read_text())
            self.assertEqual(first,second)
            self.assertEqual(first["scientific_evidence_level"],"S0")

if __name__=="__main__": unittest.main()

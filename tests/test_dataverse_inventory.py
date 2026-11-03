"""S0-only offline Dataverse metadata intake, adversarial and deterministic tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from neuroshield.dataverse_inventory import inspect_snapshot, verify_local_file, main

DOI = "doi:10.5683/SP3/ZUZMCM"

def provider_fixture(raw):
    """Entirely fabricated Dataverse-shaped JSON; not actual source metadata."""
    def file(fid,folder,name,data,restricted=False,algorithm="MD5"):
        checksum = hashlib.new("md5" if algorithm=="MD5" else "sha256",data).hexdigest()
        return {"label":name,"directoryLabel":folder,"restricted":restricted,
                "dataFile":{"id":fid,"filename":name,"filesize":len(data),
                            "checksum":{"type":algorithm,"value":checksum}}}
    folder="Data_open_Repository/Crash_1/Measurement_data"
    return {"status":"OK","data":{"persistentId":DOI,"latestVersion":{
        "versionState":"RELEASED","versionNumber":1,"versionMinorNumber":0,
        "files":[file(90001,folder,"Crash_1.csv",raw),
                 file(90002,folder,"_Read_me.txt",b"synthetic directions"),
                 file(90003,"Data_open_Repository","_Read_me.txt",b"synthetic repository readme"),
                 file(90004,"Data_open_Repository/Crash_1/Pictures","picture.JPG",b"not imported")]}}}

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.csv=self.root/"Crash_1.csv"
        self.csv.write_bytes(b"time,ax\n0,1\n1,2\n2,3\n")
        self.metadata=self.root/"dataverse-response.json"
        self.doc=provider_fixture(self.csv.read_bytes())
        self.save()

    def save(self):
        self.metadata.write_text(json.dumps(self.doc))

    def inspect(self):
        return inspect_snapshot(self.metadata)

    def test_metadata_only_no_promoted_evidence(self):
        r=self.inspect()
        self.assertEqual(r["status"],"BLOCKED_SOURCE_REVIEW")
        self.assertEqual(r["scientific_evidence_level"],"S0")
        self.assertEqual(r["dataset_version"],"1.0")
        self.assertEqual(set(r["selected_files"]),{"trial_csv","trial_measurement_readme","repository_readme"})
        self.assertEqual(r["selected_files"]["trial_csv"]["provider_checksum"]["type"],"MD5")
        self.assertFalse(r["source_identity_verified"])
        self.assertFalse(r["data_import_authorized"])
        self.assertNotIn("picture.JPG",str(r))

    def test_byte_consistency_not_authentication(self):
        r=verify_local_file(self.metadata,self.csv)
        self.assertTrue(r["provider_checksum_matched"])
        self.assertEqual(r["status"],"CHECKSUM_MATCHES_UNAUTHENTICATED_SNAPSHOT")
        self.assertFalse(r["source_identity_verified"])
        self.assertFalse(r["mapping_approved"])
        self.assertNotIn(str(self.csv),str(r))
        self.assertNotIn("time,ax",str(r))

    def test_mutation_same_size_detected(self):
        self.csv.write_bytes(b"time,ax\n0,2\n1,2\n2,3\n")
        r=verify_local_file(self.metadata,self.csv)
        self.assertEqual(r["status"],"FAILED_CHECKSUM_MISMATCH")
        self.assertFalse(r["provider_checksum_matched"])

    def test_wrong_size_blocked(self):
        self.csv.write_bytes(b"other-size")
        with self.assertRaisesRegex(ValueError,"file size"):
            verify_local_file(self.metadata,self.csv)

    def test_snapshot_hash_pins_metadata_revision(self):
        original=self.inspect()
        self.assertEqual(original,self.inspect())
        self.doc["data"]["latestVersion"]["files"][0]["dataFile"]["checksum"]["value"]="0"*32
        self.save()
        self.assertNotEqual(original["metadata_snapshot_sha256"],self.inspect()["metadata_snapshot_sha256"])

    def test_wrong_doi(self):
        self.doc["data"]["persistentId"]="doi:10.5683/SP3/OTHER"
        self.save()
        with self.assertRaisesRegex(ValueError,"Wrong dataset DOI"):self.inspect()

    def test_draft_prohibited(self):
        self.doc["data"]["latestVersion"]["versionState"]="DRAFT"
        self.save()
        with self.assertRaisesRegex(ValueError,"released"):self.inspect()

    def test_unpinned_version(self):
        self.doc["data"]["latestVersion"].pop("versionMinorNumber")
        self.save()
        with self.assertRaisesRegex(ValueError,"version"):self.inspect()

    def test_restricted_csv_prohibits_byte_comparison(self):
        self.doc["data"]["latestVersion"]["files"][0]["restricted"]=True
        self.save()
        self.assertIn("TRIAL_CSV_RESTRICTED",self.inspect()["blockers"])
        with self.assertRaisesRegex(ValueError,"Public trial CSV"):
            verify_local_file(self.metadata,self.csv)

    def test_missing_readme_stays_visible(self):
        self.doc["data"]["latestVersion"]["files"].pop(1)
        self.save()
        self.assertIn("TRIAL_MEASUREMENT_README_MISSING",self.inspect()["blockers"])

    def test_duplicate_selected_file_rejected(self):
        self.doc["data"]["latestVersion"]["files"].append(
            self.doc["data"]["latestVersion"]["files"][0].copy())
        self.save()
        with self.assertRaisesRegex(ValueError,"Duplicate selected"):self.inspect()

    def test_malformed_checksum_rejected(self):
        self.doc["data"]["latestVersion"]["files"][0]["dataFile"]["checksum"]["value"]="bad"
        self.save()
        with self.assertRaisesRegex(ValueError,"checksum"):self.inspect()

    def test_path_traversal_rejected(self):
        self.doc["data"]["latestVersion"]["files"][0]["directoryLabel"]="Data_open_Repository/../Crash_1/Measurement_data"
        self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe selected"):self.inspect()

    def test_duplicate_json_key_rejected(self):
        self.metadata.write_text('{"status":"OK","status":"FAIL","data":{}}')
        with self.assertRaisesRegex(ValueError,"Duplicate JSON"):self.inspect()

    def test_symlinked_metadata_and_raw_rejected(self):
        for name,target,fun in (("metadata-link",self.metadata,lambda p:inspect_snapshot(p)),
                                ("raw-link",self.csv,lambda p:verify_local_file(self.metadata,p))):
            p=self.root/name
            try:p.symlink_to(target)
            except (OSError,NotImplementedError):self.skipTest("Symlinks not supported")
            with self.assertRaisesRegex(ValueError,"nonsymlink"):fun(p)

    def test_sha256_checksum_supported(self):
        c=self.doc["data"]["latestVersion"]["files"][0]["dataFile"]["checksum"]
        c["type"]="SHA-256";c["value"]=hashlib.sha256(self.csv.read_bytes()).hexdigest()
        self.save()
        self.assertTrue(verify_local_file(self.metadata,self.csv)["provider_checksum_matched"])

    def test_cli_never_overwrites(self):
        destination=self.root/"report.json"
        destination.write_text("KEEP")
        with self.assertRaises(SystemExit) as ctx:
            main(["inspect",str(self.metadata),"--out",str(destination)])
        self.assertEqual(ctx.exception.code,2)
        self.assertEqual(destination.read_text(),"KEEP")

if __name__=="__main__":
    unittest.main()

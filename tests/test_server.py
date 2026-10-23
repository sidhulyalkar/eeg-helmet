import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from neuroshield.server import Handler


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.addr = f"http://127.0.0.1:{cls.http.server_port}"
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=2)

    def call(self, path, data=None):
        request = Request(self.addr + path, data=json.dumps(data).encode() if data is not None else None,
                          headers={"Content-Type":"application/json"})
        with urlopen(request, timeout=10) as res:
            return res.status, res.read(), dict(res.headers)

    def test_health_config_and_asset(self):
        code, body, headers = self.call("/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["mode"], "synthetic_only")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        code, _, _ = self.call("/app.js")
        self.assertEqual(code, 200)
        code, body, _ = self.call("/api/config")
        self.assertIn("oblique", json.loads(body)["scenarios"])

    def test_qualify_endpoint_and_reject_real_data(self):
        code, body, _ = self.call("/api/qualify", {"scenario":"oblique"})
        self.assertEqual(code,200)
        report=json.loads(body)
        self.assertEqual(report["evidence_level"],"S0_UNVALIDATED_MECHANICS")
        self.assertIn(report["status"],("PASS_NUMERICAL_REFINEMENT_ONLY","FAIL_NUMERICAL_REFINEMENT"))
        for request in ({"data_origin":"real"},{"scenario":"oblique","subject_data":"abc"}):
            with self.assertRaises(HTTPError) as e:
                self.call("/api/qualify",request)
            self.assertEqual(e.exception.code,400)

    def test_compare_and_invalid(self):
        code, body, _ = self.call("/api/compare", {"scenario":"oblique"})
        self.assertEqual(code, 200)
        result = json.loads(body)
        self.assertIn("baseline", result)
        self.assertFalse(result["candidate"]["provenance"]["clinically_validated"])
        for path, payload in [("/api/compare",{"parameters":{"mount_travel_mm":50}}),
                              ("/api/compare",{"subject_data":[1,2,3]}),
                              ("/api/ingest", {"subject":"x"})]:
            with self.subTest(path=path, payload=payload), self.assertRaises(HTTPError) as ex:
                self.call(path, payload)
            self.assertIn(ex.exception.code, (400, 404))


if __name__ == "__main__":
    unittest.main()

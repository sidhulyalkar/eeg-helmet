"""Build and install an actual wheel in a clean venv outside this source tree.

This catches missing package data and import assumptions hidden by editable
installs. Intended for CI; pip build dependencies may require network access.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def call(*args, cwd, env=None):
    subprocess.run([str(a) for a in args], cwd=cwd, env=env, check=True)


def main():
    with tempfile.TemporaryDirectory(prefix="neuroshield-dist-") as tmp:
        root = Path(tmp)
        wheelhouse = root / "wheels"
        wheelhouse.mkdir()
        # The wheel is built as a real distributable, not an editable checkout.
        call(sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", wheelhouse, str(ROOT), cwd=root)
        wheels = list(wheelhouse.glob("neuroshield_research-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected exactly one NeuroShield wheel")
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        call(interpreter, "-m", "pip", "install", "--no-index", "--no-deps", wheels[0], cwd=root)
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONPATH", None)
        call(interpreter, "-c",
             "import neuroshield, importlib.metadata as md; "
             "from neuroshield.agent_protocol import task_schema; "
             "assert neuroshield.__version__ == md.version('neuroshield-research'); "
             "assert task_schema()['$schema'].endswith('/2020-12/schema')",
             cwd=root, env=clean_env)
        task = root / "task.json"
        task.write_text(json.dumps({"schema_version": "neuroshield.agent-task/0.1",
            "task_id": "installed-wheel-001", "operation": "simulate_synthetic",
            "data_class": "SYNTHETIC_ONLY", "inputs": {"scenario": "oblique", "parameters": {}}}), encoding="utf-8")
        bundle = root / "bundle"
        call(interpreter, "-m", "neuroshield.agent_protocol", "run", task, "--out", bundle, cwd=root, env=clean_env)
        call(interpreter, "-m", "neuroshield.agent_protocol", "verify", bundle, cwd=root, env=clean_env)
        call(interpreter, "-m", "neuroshield.reproduction", bundle, "--out", root / "replay.json", cwd=root, env=clean_env)
        print("Installed wheel: schema, run, verify and replay passed outside source checkout")


if __name__ == "__main__":
    main()

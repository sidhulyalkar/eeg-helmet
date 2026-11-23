# CAD concept visualization

**New: [NeuroCap S0 cap-and-ear assembly workbench](neurocap/index.html).** Read [the full part-by-part assembly plan](../docs/neurocap-assembly-workbench-v1.md) and [manifest](neurocap/manifest.json). Run `cd cad/neurocap && python -m http.server 8766 --bind 127.0.0.1` for an interactive rotate/zoom/layers/explode viewer. Generate an editable but **nonfunctional** OpenSCAD study from the repo root with `python cad/neurocap/build.py --out ../neurocap-assembly-SYNTHETIC.scad --receipt ../neurocap-assembly-receipt.json`.

All seven visualized groups are synthetic headform-only reference placeholders, never approved human-contact hardware or protective headgear.

For educational, **nonprotective EEG headwear** design workflows, alternatives to OpenSCAD and Zoo/KCL/XERJ evaluation, see [the EEG builder guide](../docs/eeg-headwear-build-guide.md) and [CAD and retrieval toolchain](../docs/cad-and-retrieval-toolchain.md). These guides do not grant permission to modify certified sports helmets or connect unreviewed electronics to people.

Run `python -m neuroshield cad-preview --out cad/concept-mount.scad`, then open the generated file in OpenSCAD. This is a 2-plate **geometry study**, not a facemask attachment design. It includes no fastener pull-out model, faceguard clearance, load testing, safety margin, material characterization, certification, or tolerancing. Never fabricate and attach it to a helmet intended for use.

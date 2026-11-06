# CAD concept visualization

For educational, **nonprotective EEG headwear** design workflows, alternatives to OpenSCAD and Zoo/KCL/XERJ evaluation, see [the EEG builder guide](../docs/eeg-headwear-build-guide.md) and [CAD and retrieval toolchain](../docs/cad-and-retrieval-toolchain.md). These guides do not grant permission to modify certified sports helmets or connect unreviewed electronics to people.

A separate [nonwearable synthetic ellipsoid and site-marker demonstration](../docs/synthetic-headform-layout-v1.md) can be generated offline with `python -m neuroshield.headform_concept`. Its markers are **not** 10-20 electrodes or participant anatomy and the object has no fitted mechanical components.

Run `python -m neuroshield cad-preview --out cad/concept-mount.scad`, then open the generated file in OpenSCAD. This is a 2-plate **geometry study**, not a facemask attachment design. It includes no fastener pull-out model, faceguard clearance, load testing, safety margin, material characterization, certification, or tolerancing. Never fabricate and attach it to a helmet intended for use.

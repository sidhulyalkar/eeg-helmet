# Synthetic headform marker lab: first CAD reproduction exercise

**Scientific status:** S0 software-only / nonhuman / nonwearable / non-installable geometry visualization.

This is the first **fully reproducible, editable, hardware-free CAD example** for researchers who want to explore how named sites might relate to a 3D coordinate frame. It is *not* an EEG headset, a true electrode montage, a fabrication plan, a skin contact, a verified anatomical head shape, protective equipment or permission to test on anyone.

Do not mount this design or generated objects on certified helmets, connect circuitry, use the geometry for clinical/BCI claims or print it as a participant-facing device.

## What it does

The versioned [synthetic fixture](../examples/headform-sites-SYNTHETIC.json) declares:

- Three ellipsoid radii, measured **only in millimeters**, defining a fictional rigid headform.
- A fixed right-handed representation with axes `x right, y anterior, z superior`; the origin is the ellipsoid center. **No** anatomical fiducials are measured or represented.
- Nine **abstract** `SITE-...` labels, each with a three-component *unit direction vector*. They are **not** 10-20 electrodes, individualized cap positions or observed scalp landmarks.
- An explicit S0 origin and non-installable status. No filenames, identifiers, recordings or scan geometry derived from a person.

For each symbolic direction `u` and ellipsoid radii `(r_x,r_y,r_z)`, the display dot is computed as:

```text
p_x = r_x u_x
p_y = r_y u_y
p_z = r_z u_z
u_x² + u_y² + u_z² = 1
```

This is a simple mapping to the *declared mathematical ellipsoid surface*. It is not an anatomical electrode localization algorithm.

A validator rejects duplicate labels and JSON keys, nonfinite/bool dimensions, invalid norms, out-of-bounds radii, ambiguous units/frames, too-close visual markers, non-synthetic origin, unknown fields and symlinked input. The **8 mm minimum marker spacing** merely prevents overlapping colored dots in this demonstration; it is **not** a required scalp distance or a physiological/safety threshold.

## Reproduce with no external Python packages

Run from the repository root:

```bash
python -m pip install -e .
python -m neuroshield.headform_concept \
  examples/headform-sites-SYNTHETIC.json \
  --out ../headform-marker-preview.scad \
  --receipt ../headform-marker-receipt.json
python -m unittest discover -s tests -p test_headform_concept.py -v
```

Open `../headform-marker-preview.scad` in [OpenSCAD](https://openscad.org/) to view a translucent abstract ellipsoid with colored marker dots. OpenSCAD is optional for CLI generation and tests; no Zoo, GPU, network service, amplifier, human data or third-party CAD download is required.

The receipt records the manifest's canonical SHA-256, generated OpenSCAD SHA-256, exact declared frame/units, ellipsoid bounds, marker count, minimum visual marker spacing, and **explicit false flags** for montage validation, human data, safety and physical authorization. Two independent contributors running the same package/fixture should obtain the same bytes and hashes. Hash agreement proves only reproducible local computation, not physical adequacy.

**No overwrite:** the CLI refuses pre-existing output paths and symlinked manifest files. Use a fresh output directory or manually review/delete old generated files; the tool never silently overwrites a report.

## Why this is useful

It gives beginners a concrete and safe first contribution involving **geometry, typed data, tests, physical assumptions and reproducibility**. Contributors can locate and fix a coordinate error, improve the portable manifest, compare two open CAD backends on the same mathematical surface, or translate the tutorial without owning an EEG headset.

It deliberately stops before questions that require qualified physical evidence:

| Concept available today | Not yet established |
| --- | --- |
| Frozen, fictional ellipsoid radii | Any human head shape, fit or tolerance range |
| Computed symbolic marker positions | Actual 10-20/10-10 electrode locations or digitized fiducials |
| Visible OpenSCAD headform and points | Any wearable, contact, electrodes, cabling, attachment or manufacturability |
| Finite coordinates and renderer sanity checks | Contact pressure, skin biocompatibility, electrical isolation or approval |
| Identical generated source SHA | Independent experimental or safety validation |

## Next gated extension

Once this abstraction is independently reproduced, a **separate** versioned electrode-location model could import standard nominal montage definitions from a *reviewed* scientific source, add fiducial registration to an authorized synthetic mesh, distinguish `nominal_template` from `measured_subject` at the type level, and evaluate montage error under deliberately perturbed registration. Even then, anatomical location estimates and registration QC do not verify electrical safety or physiological signal interpretation.

For the broader research context, see [EEG headwear builder guidance](eeg-headwear-build-guide.md), [CAD and XERJ comparison](cad-and-retrieval-toolchain.md), [global EEG ecosystem blueprint](open-eeg-ecosystem-and-community.md), and [scientific evidence contract](research-contract.md).

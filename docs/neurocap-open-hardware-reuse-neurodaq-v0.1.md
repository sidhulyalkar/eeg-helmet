# NeuroCap open-hardware reuse: NeuroDAQ-first decision and bench pilot (2026-11-22)

**Status:** evaluated publicly documented source and proposed an S0 bench-only research path. Not a completed integration, safety approval, fabrication instruction for body-connected use, or verified human EEG recording. Protect real neural data per `AGENTS.md` and `docs/research-contract.md`.

## Decision

**Use NeuroDAQ as the leading reference implementation, not as an unmodified final wearable.** Independently evaluate PiEEG-8, HackEEG, EEGFrontier, and CONVEY for specific design alternatives. We want control of raw data, board design, register-level acquisition and local storage with **no proprietary EEG SDK**. Using public ESP-IDF, Python, KiCad, and other open developer tools is allowed; lack of a *vendor-specific proprietary EEG SDK* does not require reinventing every driver.

Do not confuse open-source **code** with zero-cost **physical hardware**, nor open-source electronics with tested human-use safety.

## Source projects and licensing review

| Source | Public offering | Strength | Critical risk/unknown | Source |
|---|---|---|---|---|
| **NeuroDAQ** | Eight-channel ADS1299, ESP32-S3, Wi-Fi, UDP/TCP protocol, Python host, PCB and 3D files | Complete project split across hardware / firmware / host / driver; useful as working architecture | Firmware issues, no validated isolation or human safety; EasyEDA native export incomplete in GitHub; derived OpenBCI parts GPLv3 | https://github.com/carlos-lorenzo/neurodaq |
| **PiEEG-8** | Open Raspberry Pi ADS1299 shield; documented local drivers | Easy Pi-oriented learning and alternative source of board/driver patterns | Full Pi is unsuitable as a discreet wearable without major re-engineering and safety review | https://docs.pieeg.com/hardware/devices/pieeg-8/ |
| **HackEEG** | Arduino Due ADS1299 8-ch shield, open hardware and software | Good transparent low-level ADC learning/reference and bench experiments | Bulky mechanical architecture, verify current hardware availability; hardware license CERN OHL 1.2 | https://github.com/starcat-io/hackeeg-shield |
| **EEGFrontier V1** | Four-channel KiCad + firmware / host | Particularly useful compact mechanical/electrical reference | Its own README warns not to fabricate V1 before V2 corrections | https://github.com/TheusHen/EEGFrontier |
| **CONVEY** | 8-ch ADS1299, KiCad, formal isolation design checks, ESP32 reference | Safety architecture and reproducible design verification case study | README states **not yet physically fabricated**; design verification is not patient isolation certification | https://github.com/kennito2035/convey |

**Licensing must be reviewed at file level before incorporation.** NeuroDAQ board/author-created parts and code indicate MIT; OpenBCI-derived mechanical STL parts have different GPLv3 requirements. HackEEG's hardware has its own CERN OHL terms, and CONVEY's hardware uses CERN-OHL-S. Do not copy licensed design files into an Apache-2.0 repository based on README license alone. Prefer documentation links and independent implementation.

## Repository architecture to reuse or learn from

NeuroDAQ includes **Git submodules** (host, hardware, firmware) and a separate reusable ADS1299 driver. Pin all component commit SHAs before every experiment; do not simply follow moving `main` branches without a recorded lockfile.

- Main: https://github.com/carlos-lorenzo/neurodaq
- Firmware: https://github.com/carlos-lorenzo/neurodaq-firmware
- Hardware: https://github.com/carlos-lorenzo/neurodaq-hardware
- Host: https://github.com/carlos-lorenzo/neurodaq-host
- ADS1299 driver: https://github.com/carlos-lorenzo/ads1299
- Getting started: https://github.com/carlos-lorenzo/neurodaq/blob/main/docs/GETTING_STARTED.md
- Wire protocol: https://github.com/carlos-lorenzo/neurodaq/blob/main/docs/PROTOCOL.md

### Crucial source-specific findings

**Hardware:** ADS1299 eight differential channels, 4-layer carrier with ±2.5 V analog rails, ESP32-S3 DevKitC-1 N32R8 sockets, 6-axis IMU, passive electrode breakout, Gerber/BOM/STEP-STL artifacts. GitHub hardware README says editable EasyEDA `.epro`/JSON export remains unavailable there; separate OSHWLab source may need registration or review. Fabrication files are not a substitute for fully reviewed and editable schematics. Original mechanical parts have mixed provenance.

**Firmware:** ESP-IDF v6.0.2, ESP32-S3-DevKitC-1-N32R8. Documented issues: CONFIG1 sample-rate mask bug; lead-off writes wrong register; fixed 25-sample frame means **250 SPS only** for now; Wi-Fi station failure prevents running; on-device DSP/ML unimplemented; Catch2 tests are placeholder assertions. Do not rely on any of these features until independently fixed and tested.

**Protocol:** one UDP packet 1209 bytes with magic, sequence, 25 records of 48 bytes, XOR checksum. UDP on 3333, TCP JSON control on 3334. The receiver must check magic, packet length, checksum, packet order, 32-bit sequence rollover, and explicit gaps. Acquisition firmware includes a monotonic microsecond timestamp on each DRDY sample, but does not itself provide verified alignment to external stimulus times, PC clocks or game events. **Never substitute host arrival time for proven EEG acquisition time.**

**Host:** `neurodaq-host/README.md` is more current than `neurodaq/docs/GETTING_STARTED.md`: use `uv run neurodaq` for the modular host; `neurodaq_gui.py` is a retired legacy monolith. The host claims UDP integrity checks, LSL outlet and event marking, but those paths must be tested with held-out recordings and independent timing checks. Known local baseline files include `shorted.npz` and `test_signal.npz`. `open.npz` and `closed.npz` are **not** to be copied into NeuroShield or agents because they may represent real human data with unreviewed permissions.

## First software-only exercise (no electrical connection or hardware needed)

```bash
git clone --recurse-submodules https://github.com/carlos-lorenzo/neurodaq.git
cd neurodaq/neurodaq-host
uv sync
uv run pytest tests/ -q
uv run neurodaq
```

Actual folder/submodule paths and supported Python/OS versions must be rechecked when cloned. Start with included **shorted-input** and **internal test-signal** reference captures; never assume a passing UI or example plots imply a calibrated EEG device. Keep access to any human recordings explicit and separate. Make a local report of installation friction, dependency versions, samples that load, and tests that pass/fail; do not claim the commands have been run by the NeuroShield project until executed and evidenced.

## Bench-only hardware path (after software comparison)

1. Review ADS1299 datasheet and NeuroDAQ schematic, component selection, layout, power, safety and license provenance. Prepare independent review checklist and bill of materials. **Do not directly connect a subject to the prototype**.
2. Obtain a vetted compatible board or commission fully reviewed assembly only after checking vendor fabrication files against intended CAD and bill of materials. Hardware project is not yet a validated body-connected device.
3. Run internal test waveforms, shorted inputs, synthetic input/phantom networks and independently characterized function generator signals in a suitable lab bench setup. Measure amplitude conversion, input-referred noise vs bandwidth, line interference, channel crosstalk, sample rates, CRC, packet loss, firmware recovery and full-session power stability.
4. Test source and binary reproducibility with pinned toolchain versions, signatures/checksums, firmwares, board revisions and firmware register dumps.
5. Before any human EEG acquisition, obtain independent expert electrical protection/isolation, fault/current leakage, skin-contact, thermal, mechanical, radio and protocol review. Follow an approved or otherwise properly reviewed self-study protocol. Battery-only is not a safety certification; vendor evaluation boards must never be assumed suitable for body connection.
6. If or when validated, run repeated same-person controlled sessions with independently established paradigm contrasts, then carefully connect to a private event-aligned gameplay data pipeline. No real data in Git or retrieval index.

## Explicit acceptance tests for an open acquisition adapter

**Synthetic protocol/unit tests (can be built now):** valid magic/length/CRC, sequence wrap, reordering, duplicate detection, lost packets, nonmonotonic source timestamps, invalid gains, sample-rate mismatch, negative signed 24-bit ADC conversion, unexpected reference metadata, format revision mismatch, missing source provenance, and the ability to explicitly label 'not measured'.

**Bench waveform tests (require hardware):** shorted-input noise and PSD, ADS1299 internal calibration tone with amplitude/rate reporting, external phantom injected sinusoids with prespecified peak/RMS and latency criteria; cross-channel leakage and frame-loss under constrained Wi-Fi.

**Multi-device synchronization tests (separate evidence):** compare source ADC DRDY times, host/LSL clock observations and physically or independently timed game stimulus cues. Report an error distribution, drift and uncertainty. Ethernet/Wi-Fi network timestamps alone do not prove ERP timing accuracy.

**Experimental fit tests (much later):** separately qualified headform-only ear/temple/scalp cartridges, repeatable placement and mechanical deformation; evaluate actual neural signal contrasts with approved human acquisition before claiming a usable headphone or cap.

## Proposed implementation PRs

- PR-1: synthetic-only open-wire decoder and independent parser tests in a **separate optional adapter**, no human recording inputs in core NeuroShield.
- PR-2: pin NeuroDAQ and alternative upstream source versions, source licenses, host test receipts and benchmark data **without copying third-party raw human EEG**.
- PR-3: independent bench test specification and electronics review notes; capture measured input noise, channel gain, packet integrity and power-fail results.
- PR-4: custom headform-only, flexible headphone/hat electrode cartridge CAD; preserve an independent acoustic system design.
- PR-5: independently reviewed, controlled human signal feasibility study (not automatic or approved by earlier PRs), followed by game synchronization and held-out-session modeling.

**Success criterion:** an outside contributor can independently replay public synthetic and bench signals, inspect exact circuit versions, reproduce a self-contained data record with honest missing/failed sections, and understand every acquisition limitation. This is a prerequisite for building comfortable personal NeuroCap hardware, not proof that it is safe or useful on human subjects.

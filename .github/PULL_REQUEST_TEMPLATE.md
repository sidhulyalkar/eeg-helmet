# Scientific contribution

**Purpose and owning research workflow**

**What changed?** (Code, docs, manifest, reference metadata, UI)

**Research question and evidence class**
- [ ] S0 synthetic/structural/metadata only
- [ ] Units, coordinates, clock definitions, assumptions and limitations are documented
- [ ] No clinical inference, protection claims, real human data or unsafe hardware directions added

**Reproducibility and negative tests**
- [ ] `python -m unittest discover -s tests -v`
- [ ] `python -m neuroshield.research_map audit --root .`
- [ ] `python -m neuroshield knowledge audit --root .`
- [ ] `python -m neuroshield.ecosystem audit --root .` (when ecosystem files change)
- [ ] Added or updated an intentional failure case, or explained why none applies
- [ ] Reported failed tests and adverse changes rather than hiding them

**External work / provenance**
- [ ] Linked external sources are pinned or explicitly marked as living pages
- [ ] Actual file-level licenses/redistribution terms reviewed before reusing code, CAD, standards or data
- [ ] No identifiable recordings, scans, credentials or private sources in commits, logs, tests or research indexes

**Independent reproduction**
Provide clean-install commands, expected hashes/artifacts, observed limitations, and external review steps.

**Safety and governance review required**
Identify whether electronics, human contact, protective equipment, privacy or licensed data require a qualified independent reviewer. Software tests are not electrical or physical safety approvals.

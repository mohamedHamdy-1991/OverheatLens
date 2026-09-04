---
title: 'OverheatLens: a local-first, validation-first platform for domestic overheating assessment with versioned overheating standards'
tags:
  - Python
  - buildings
  - overheating
  - thermal comfort
  - EnergyPlus
  - TM59
  - validation
authors:
  - name: Mohamed Hamdy Ali
    affiliation: 1
    orcid: 0009-0009-6074-8524
affiliations:
  - name: Leeds Sustainability Institute, School of the Built Environment and Architecture, Leeds Beckett University, United Kingdom
    index: 1
date: 4 September 2026
bibliography: paper.bib
---

# Summary

OverheatLens is an open, local-first research platform for domestic overheating
assessment. It chains the full evidence workflow — weather-file quality control,
building-model readiness checks, EnergyPlus simulation, versioned overheating
standards, thermal-comfort analytics, mitigation experiments and a reproducible
evidence archive — behind a single local service with a laboratory-style web
interface. Its distinguishing design rule is traceability: every number shown in
the interface carries provenance (weather-file hash, model hash, rule-pack
version, EnergyPlus version and a run identifier), and every archived run can be
replayed or exported as a reproducibility bundle.

# Statement of need

Domestic overheating is a growing risk in temperate climates, and the United
Kingdom now has two operational assessment methodologies — CIBSE TM59 [@cibse_tm59_2017;
@cibse_tm59_2026] and the dynamic route of Approved Document O [@ado_2021] —
plus the wider TM52 framework [@cibse_tm52_2013] they derive from. In practice
these assessments are produced with commercial graphical tools whose criteria
implementations are not inspectable, whose standards versions are implicit, and
whose outputs are difficult to audit or reproduce. Researchers comparing
archetypes, weather years or mitigation strategies therefore struggle to answer
a simple question: which definition of the standard produced this number?

OverheatLens addresses that gap. All criteria are transcribed into versioned
rule packs that record the SHA-256 hash of the official PDF they were verified
against, and machine-verification evidence documents that each implemented limit
appears in that document. The simulation engine is the official EnergyPlus
binary [@energyplus_crawley_2001], driven in isolated run directories with an
error interpreter and a harvest step that preserves full zone keys (level:room)
and hourly resolution. Comfort indices are never reimplemented: PMV/PPD,
adaptive comfort and UTCI come from pythermalcomfort [@pythermalcomfort_2020],
which wraps ISO 7730 [@iso_7730] and EN 16798-1 [@en_16798_1], with the UTCI
operational procedure of Bröde et al. [@brode_2012].

The platform is built for researchers who need to trust, reproduce and re-use
their overheating evidence rather than re-type it from a GUI report.

# Key features

- **Weather intelligence.** Parsing of standard and CIBSE-variant EPW files,
  a calibrated QC battery (range, sentinel, dew-point physics, discontinuity,
  stuck-sensor and duplicate checks) with PASS / PASS_WITH_WARNINGS / FAIL
  classification, headline metrics, and standards-compatibility review (e.g.
  TM59:2017 and TM59:2026 weather requirements differ, and the app states which
  files satisfy which).
- **Model readiness.** Object-level IDF inspection before any simulation: zone
  inventory, occupant and glazing census, and standards-specific checks with an
  explicit reason for every finding.
- **Versioned standards.** TM59:2017 (adaptive criterion a with the published
  occupancy bases, 32-hour sleep-window criterion b), TM59:2026 (criteria a–d
  with night-based criterion b and a communal 28 °C criterion), Approved
  Document O dynamic route, and TM52 criteria 1–3 — each evaluated with exact
  published boundaries and explicit NOT_EVALUATED honesty states rather than
  invented numbers.
- **Thermal comfort.** PMV/PPD, EN 16798-1 adaptive acceptability and UTCI,
  computed by the wrapped library on the simulated operative temperature, with
  assumptions recorded in every result.
- **Mitigation experiments.** Real paired EnergyPlus experiments (baseline
  versus stored strategy variants on a chosen weather file) reporting overheating
  verdicts, comfort and annual facility energy; cases that cannot be computed
  are reported as INCOMPLETE, never estimated.
- **Evidence archive.** Every run is persisted with manifest, series, criteria
  tables and provenance; any run can be exported as a reproducibility bundle.

# Validation

A 16-case scientific validation campaign ships with the repository and runs in
about fifteen minutes on a laptop. It covers the rule-pack source chain, real
weather-file QC, verdict-flip exactness at published TM59:2017, TM59:2026, TM52
and Part O boundaries, PMV/PPD against the published ISO 7730 anchors, UTCI
against the Bröde et al. reference conditions, EnergyPlus determinism, facility
meter internal consistency, a zone-by-zone cross-check against DesignBuilder
results for the same measured dwelling, and three-way equality between the
EnergyPlus output file, the on-disk archive and the numbers served to the
interface. The campaign reports PASS, FAIL or INCOMPLETE and its results are
rendered inside the application's validation page.

# Quality of tests and ongoing development

The repository carries 147 core, 34 API and 12 interface tests, all runnable
locally without cloud services (`Run Tests` launchers are provided), plus a
GitHub Actions workflow for continuous integration. Governance documents
(contribution guide, code of conduct, security policy, disclaimer and
governance model) are included; the project explicitly labels research-only
outputs and refuses to present them as compliance certificates. Development is
active, with the validation campaign designed to grow alongside the standards
it tracks.

# References

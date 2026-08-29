# PRODUCT.md — OverheatLens

## What this is

OverheatLens is an open, version-aware research-software platform for building-overheating
assessment: weather-file intelligence, model readiness, EnergyPlus simulation, versioned
overheating standards (TM59:2017, TM59:2026, Approved Document O dynamic route, TM52),
and reproducible evidence. The web interface is the instrument panel for that pipeline.

## Who uses it

1. Building-performance researchers (primary): inspect, question, reproduce, export.
2. Overheating assessors / engineers: run a standard, see exactly where things fail.
3. Planners, students, the public (later phases): plain-language risk stories.

Primary user on this machine: Mohamed Hamdy Ali, PhD researcher (Leeds Beckett),
who runs everything locally via double-click launchers. Zero-install experience is a
hard constraint. Results on screen, always.

## The job of each surface

- **Home (Persuade):** make a researcher trust the tool in ten seconds — real data,
  visible standards status, one honest claim. Hero: "See where overheating begins."
- **Weather Lab (Operate):** choose an EPW from the local library, see its quality
  verdict and its climate at a glance; nothing hidden.
- **Analyze (Operate):** run the pipeline (model + weather → EnergyPlus → standards);
  see readiness, criteria, and provenance; export later.
- **Validation (Read):** the live validation matrix; evidence, never a vague badge.

## Non-negotiables

- Every number on screen traces to the core package (RULE 3) with provenance (RULE 6).
- Status never depends on colour alone (icon + text + colour).
- Research-mode results are labelled; compliance mode states the rule pack edition.
- Real data only — synthetic unit-test data must be labelled as such (RULE 28).
- WCAG 2.2 AA target; keyboard and reduced motion respected.
- The interface is a scientific instrument: quiet, precise, editorial. It is never a
  neon "AI dashboard".

## Environment

Local-first. FastAPI serves the core package and the built web app on one port.
The Start launcher bootstraps everything on first run. Real CIBSE weather files stay
on the machine; nothing copyrighted is committed.

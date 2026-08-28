# OVERHEATLENS — MANUSCRIPT, FIGURE AND PUBLICATION AGENT PROMPT
## Prepare a submission-ready SoftwareX package from the finished research software

**Target software:** OverheatLens  
**Primary journal:** SoftwareX  
**Article type:** Original Software Publication  
**Secondary option:** Journal of Open Source Software (JOSS)  
**Date strategy prepared:** 28 August 2026

---

# ROLE

Act as:
- a senior research-software author;
- a building-performance researcher;
- a SoftwareX manuscript editor;
- a reproducibility auditor;
- an information-visualisation editor;
- a strict peer reviewer.

Do not write a promotional article.

Write a concise, evidence-backed software paper that makes a reviewer immediately understand:
1. the problem;
2. the software gap;
3. what OverheatLens contributes;
4. how it is architected;
5. why its scientific outputs are trustworthy;
6. how it differs from existing tools;
7. how another researcher can obtain and reproduce it.

---

# PRIMARY JOURNAL DECISION

Use **SoftwareX** as the primary submission target.

Why:
- SoftwareX publishes detailed articles describing research software and its application;
- OverheatLens is a substantive open research-software system, not only a website;
- the reusable `overheatlens-core` package, versioned standards engine, EnergyPlus workflow, validation framework and public interface provide a strong software contribution;
- the manuscript can remain focused on the software while a later Building and Environment / Energy and Buildings paper can address a distinct scientific application.

Current planning limits to honour unless the official guide has changed at submission:
- **maximum manuscript text approximately 3,000 words**;
- **maximum 6 figures**;
- required SoftwareX template;
- open-source code;
- public GitHub repository;
- recognised open-source licence;
- repository and version metadata.

Before final submission, re-check the live SoftwareX Guide for Authors and update the compliance checklist.

---

# JOSS BACKUP STRATEGY

JOSS is a credible secondary option only if:
- the core library is reusable outside the browser;
- tests are comprehensive;
- documentation is excellent;
- open-source licence is present;
- the code is feature-complete;
- the web UI is not merely a monolithic site.

JOSS papers are currently expected to be short (roughly 750–1750 words) and focus on:
- summary;
- statement of need;
- comparison to related software;
- research use;
- references.

Do not submit the same manuscript unchanged to JOSS.

---

# INPUTS YOU MUST READ BEFORE WRITING

Read completely:

1. `OverheatLens_Publication_Grade_Detailed_Plan.md`
2. repository `README.md`
3. `CITATION.cff`
4. `CHANGELOG.md`
5. `SOURCE_REGISTER.md`
6. `VALIDATION_MATRIX.md`
7. `docs/validation/VALIDATION_REPORT_v1.0.md`
8. architecture documentation
9. rule-pack definitions
10. API documentation
11. example notebooks
12. GitHub Actions configuration
13. release notes
14. DOI/Zenodo metadata
15. all final screenshots/figure data
16. final software version
17. licence
18. test/coverage report

Do not write numerical claims from memory or from this prompt.

---

# ABSOLUTE EVIDENCE RULE

Every quantitative sentence in the manuscript must be backed by:
- repository test output;
- validation report;
- benchmark output;
- release metadata;
- application output;
- source document.

If evidence is absent:
- do not invent it;
- add `[EVIDENCE REQUIRED]`;
- identify exactly what test/output must be generated.

Never invent:
- runtime;
- speedup;
- number of tests;
- coverage;
- error;
- agreement;
- user count;
- download count;
- star count;
- accuracy.

---

# CENTRAL PAPER CLAIM

The paper should be organised around this defensible contribution:

> **OverheatLens is an open, version-aware research-software platform that makes building-overheating assessment reproducible from weather and model readiness through EnergyPlus simulation, standards evaluation, visual interpretation and evidence export.**

The novelty is not “we made a dashboard”.

The software contribution is the combination of:
1. machine-readable, versioned standards logic;
2. explicit separation of TM59:2026 and the current Part O route;
3. reusable scientific core;
4. EnergyPlus provenance;
5. weather/model readiness;
6. public/practitioner/research views;
7. reproducibility bundles;
8. validation and cross-tool evidence;
9. publication-quality visual export.

---

# COMPETITOR / RELATED SOFTWARE POSITIONING

Discuss fairly.

Benchmark categories:

## DesignBuilder
Strengths:
- professional EnergyPlus-based workflow;
- TM59:2026 implementation/reporting;
- parametric and optimisation features.

OverheatLens difference:
- open source;
- reusable core;
- raw EPW/IDF readiness;
- transparent rule packs;
- reproducibility bundle;
- public/researcher modes.

Do not claim OverheatLens is “more accurate”.

## IESVE
Strengths:
- professional dynamic simulation;
- Part O workflow/certification context.

Difference:
- open research-software transparency;
- open source;
- programmatic core;
- provenance/validation visibility.

## CBE Comfort Tool
Strengths:
- mature interactive thermal-comfort visualisation.

Difference:
- building-overheating standards + EnergyPlus + weather/model pipeline.

## CBE Clima
Strengths:
- excellent web climate analysis.

Difference:
- OverheatLens connects climate files to building simulation and standards evaluation.

## pythermalcomfort
Strengths:
- standards-based tested thermal-comfort library.

Relationship:
- dependency/benchmark where appropriate, not a competitor to disparage.

## Ladybug/Honeybee
Strengths:
- modular environmental-analysis ecosystem and EnergyPlus workflows.

Difference:
- OverheatLens focuses on a hosted, standards-aware overheating assessment and evidence workflow.

## epwvis
Strength:
- lightweight EPW visualisation.

Difference:
- OverheatLens adds validation, standards compatibility, multi-file research comparison and simulation link.

State the gap narrowly and accurately.

---

# MANUSCRIPT TITLE

Preferred:

**OverheatLens: Open-source, version-aware building-overheating assessment and climate-resilience analytics**

Alternative if the journal/editor prefers more specificity:

**OverheatLens: A reproducible web platform for version-aware overheating assessment, weather diagnostics and EnergyPlus workflows**

Avoid putting “AI” in the title.

---

# ABSTRACT — 180 TO 220 WORDS

Structure:

1. Problem: overheating assessment spans weather, model preparation, simulation, standard-specific post-processing and reporting.
2. Gap: these steps are fragmented and version changes create reproducibility risks.
3. Software: OverheatLens.
4. Architecture: open core + web interface + official EnergyPlus.
5. Distinctive methods: rule packs, readiness checks, provenance, multi-EPW/weather analysis.
6. Validation: only actual final evidence.
7. Availability: open repo + DOI.
8. Limitation: research/decision support, not automatic professional certification.

No citations unless SoftwareX template convention requires/permits them.

---

# KEYWORDS

Select 5–7:
- overheating;
- EnergyPlus;
- TM59;
- thermal comfort;
- weather files;
- reproducible research;
- building simulation.

---

# HIGHLIGHTS

If required, draft 3–5 short highlights.

Candidate ideas:
- Versioned rule packs separate current TM59 guidance from statutory Part O workflows.
- Open scientific core links EPW/IDF checks, EnergyPlus runs and traceable overheating metrics.
- Interactive weather, room and mitigation views support public, practitioner and research use.
- Reproducibility bundles preserve software, rule, weather, model and calculation provenance.
- Validation combines boundary tests, reference calculations and cross-software benchmarks.

Do not claim validation results until evidence exists.

---

# SOFTWAREX METADATA TABLE

Populate from the repository, not guesses.

Fields to prepare:
- current code version;
- permanent repository link;
- archive DOI;
- legal code licence;
- version-control system;
- languages;
- dependencies;
- operating environment;
- installation requirements;
- documentation URL;
- support route.

---

# ARTICLE OUTLINE AND WORD BUDGET

Aim for **2,700–2,950 words total** excluding elements excluded by the current guide.

## Abstract
**180–220 words**

## 1. Motivation and significance
**400–500 words**

Cover:
- overheating as a growing building-design/resilience concern;
- method fragmentation;
- version changes;
- reproducibility;
- expert-only tooling/access barrier;
- statement of software need.

Do not turn this into a full literature review.

End with 3–4 explicit software contributions.

## 2. Software description
**850–950 words**

### 2.1 Architecture
**180–220 words**
Explain:
- React web;
- FastAPI;
- OverheatLens Core;
- EnergyPlus worker;
- provenance layer.

### 2.2 Versioned standards engine
**180–220 words**
Explain:
- rule packs;
- edition locking;
- TM59:2017 / TM59:2026 / Part O distinction;
- traceability.

### 2.3 Input readiness and weather intelligence
**160–190 words**
Explain:
- EPW;
- IDF/epJSON;
- compatibility;
- weather lab.

### 2.4 Results and visual analytics
**170–200 words**
Explain:
- criteria;
- room evidence;
- heat events;
- multi-EPW;
- mitigation;
- modes.

### 2.5 Reproducibility and export
**150–180 words**
Explain:
- hashes;
- manifests;
- version;
- JSON/CSV/SVG/PDF;
- bundle.

## 3. Scientific implementation and validation
**550–650 words**

### 3.1 Test strategy
- boundary;
- unit;
- property-based;
- metamorphic;
- regression.

### 3.2 Reference and cross-software comparison
Use actual DesignBuilder/IES/reference evidence.

### 3.3 End-to-end reproducibility
Use actual deterministic/rebuild evidence.

Include one compact validation table.

## 4. Illustrative example
**350–450 words**

Use one real, fully reproducible Leeds archetype.

Purpose:
- demonstrate workflow;
- not claim a new scientific discovery.

Show:
- chosen standard;
- weather;
- readiness;
- simulation;
- result;
- one mitigation comparison;
- export.

Do not overload with many case-study results.

## 5. Impact and reuse
**250–350 words**

Discuss:
- researchers;
- practitioners;
- education;
- local authorities;
- archetype libraries;
- batch CLI/API;
- extensibility.

State how others can contribute rule packs or datasets.

## 6. Limitations and future development
**180–250 words**

Include:
- regulatory updates;
- dependence on input-model quality;
- weather licensing;
- not certified sign-off;
- approximated outdoor metrics if any;
- hosted compute;
- geographic scope of archetype atlas;
- cross-tool limitations.

## 7. Conclusions
**100–150 words**

One concise paragraph.

---

# FIGURE PLAN — MAXIMUM 6

All figures must be made from:
- vector diagrams;
- real application screenshots;
- real validation data;
- real simulation data.

**No generative illustration.**
**No fabricated chart.**
**Prefer SVG.**

## Figure 1 — System architecture and evidence lineage
Format:
clean vector workflow.

Show:
EPW + IDF → readiness → EnergyPlus → core → rule pack → metrics → dashboard → exports

Overlay:
version/hash/provenance chain.

Purpose:
establish software architecture immediately.

## Figure 2 — Version-aware standards workflow
A compact structured visual showing:
- TM59:2017;
- TM59:2026;
- Part O current dynamic route;
- research mode.

Use “selection → compatibility guard → rule pack → output”.

Do not reproduce copyrighted source-document pages.

## Figure 3 — OverheatLens interface composite
Create a publication-grade composite of:
- Weather Lab thermal ribbon;
- criteria matrix;
- room detail;
- provenance panel.

Use one figure with labelled panels a–d.

Avoid tiny unreadable screenshots. Rebuild selected app views at publication layout dimensions if needed.

## Figure 4 — Validation evidence
Preferred panels:
a. production vs independent reference parity;
b. benchmark comparison;
c. edge/boundary test matrix;
d. deterministic-repeat difference.

Only include panels supported by final validation data.

## Figure 5 — Illustrative Leeds archetype
Panels:
a. archetype summary;
b. outdoor + room heat-event timeline;
c. criterion result;
d. one mitigation comparison.

Use it as a software demonstration.

## Figure 6 — Reproducibility / reuse workflow
Show:
run manifest → export bundle → GitHub release → Zenodo DOI → rerun.

If Figure 6 feels weak, omit it rather than filling the figure quota.

---

# TABLE PLAN

## Table 1 — Related software comparison

Columns:
- tool;
- open source;
- hosted/public UI;
- EPW analysis;
- model readiness;
- EnergyPlus workflow;
- UK overheating rule versioning;
- public mode;
- provenance bundle;
- reusable API/core.

Use cautious entries:
Yes / Partial / No / Not assessed.

Do not make claims you have not verified.

## Table 2 — Validation matrix summary

Rows:
- rule boundaries;
- independent reference;
- cross-software;
- parser faults;
- archetype regression;
- deterministic rerun;
- export equality;
- visual/accessibility QA.

Columns:
- cases;
- acceptance threshold;
- result;
- status.

## Table 3 — Optional illustrative example metrics

Only if the case cannot be explained clearly without it.

---

# GRAPHICAL ABSTRACT

If requested by SoftwareX:

Create a horizontal five-stage graphical abstract:

**Check → Simulate → Evaluate → Explain → Reproduce**

Under each:
- EPW/IDF;
- EnergyPlus;
- versioned rules;
- visual analytics;
- manifest/DOI.

Use the OverheatLens visual identity.
No decorative building render.

---

# VALIDATION REQUIREMENTS BEFORE THE AGENT MAY WRITE “VALIDATED”

The manuscript may use “validated” only if `VALIDATION_REPORT_v1.0.md` contains evidence for all critical routes.

Minimum:
1. every rule boundary;
2. independent reference implementation;
3. at least one external software comparison;
4. end-to-end deterministic rerun;
5. corrupted input tests;
6. report/dashboard equality;
7. release test suite passing.

Otherwise write:
- “tested”;
- “benchmarked”;
- “cross-checked”;
with the exact scope.

---

# REQUIRED VALIDATION ANALYSES FOR THE PAPER

Create reproducible scripts/notebooks for:

## A. Rule parity
For each criterion:
- expected;
- OverheatLens;
- difference.

Output:
CSV + figure.

## B. Boundary sweep
Generate values around every key threshold.

Output:
binary transition plot/table.

## C. Cross-software benchmark
For controlled cases:
- same weather;
- equivalent model;
- same evaluation assumptions.

Compare:
- key hourly output where possible;
- criterion inputs;
- criterion result.

Separate:
1. EnergyPlus/simulation differences;
2. post-processing differences.

## D. Determinism
Run identical inputs at least twice.

Compare:
- hashes where stable;
- key timeseries;
- result JSON.

## E. Parser fault detection
Plant known faults.

Report:
- true detections;
- misses;
- false alarms.

Do not use the terms sensitivity/specificity unless a sufficiently defined labelled fault dataset supports them.

## F. Performance
Optional.

Only report runtime if measured on a documented machine/configuration with repeated runs.

---

# FIGURE STYLE

All manuscript figures must match the app.

Palette:
- paper `#F7F5F0`;
- ink `#172126`;
- teal `#1F5F70`;
- heat accents `#F4C95D`, `#E58A3A`, `#D4553D`, `#8F2D3A`;
- neutral lines `#D9D7D1`.

Rules:
- white or paper background;
- no drop shadows;
- no 3D;
- no gradient unless it encodes a continuous variable;
- no chartjunk;
- no tiny legends;
- text remains legible at journal size;
- panel labels a, b, c, d;
- consistent typography;
- units on axes;
- uncertainty visible;
- zero-centered divergent scales where appropriate.

---

# CAPTION STYLE

Every caption must answer:
1. what is shown;
2. what data/software version;
3. what comparison/threshold;
4. what the reader should notice.

Do not interpret beyond the evidence.

---

# REFERENCES THE PAPER SHOULD CONSIDER

Build a Zotero/BibTeX-ready list from authoritative sources.

At minimum consider:
- CIBSE TM59:2026;
- CIBSE TM59:2017;
- CIBSE TM52;
- current Approved Document O;
- CIBSE weather-data documentation;
- EnergyPlus paper/documentation;
- pythermalcomfort SoftwareX paper;
- CBE Thermal Comfort Tool SoftwareX paper;
- CBE Clima publication if applicable;
- Ladybug Tools/Honeybee scholarly reference where appropriate;
- relevant reproducible-research software references;
- one or two recent overheating-methodology references only where they support the motivation.

Do not create a bloated literature review.

---

# SOFTWARE CITATION PACKAGE

Before submission produce:
- `CITATION.cff`;
- `codemeta.json`;
- BibTeX entry;
- Zenodo metadata;
- release DOI;
- preferred software citation.

Ensure version in manuscript equals archived release.

---

# OPEN-SOURCE REPOSITORY AUDIT

Before drafting the final manuscript, score each:

## Documentation
- installation;
- quick start;
- examples;
- methods;
- API;
- troubleshooting.

## Testing
- automated;
- CI;
- coverage;
- regression;
- fixtures.

## Community
- contributing;
- code of conduct;
- issues;
- support;
- licence.

## Reproducibility
- release;
- DOI;
- pinned dependencies;
- rule versions;
- sample data.

## Software quality
- modularity;
- typing;
- linting;
- security;
- changelog.

If any critical item is missing, fix repository first.

---

# MANUSCRIPT WRITING STYLE

Use:
- clear British English;
- direct technical prose;
- short-to-medium sentences;
- explicit nouns;
- restrained claims.

Avoid:
- “revolutionary”;
- “groundbreaking”;
- “state-of-the-art” unless demonstrated;
- “novel” in every paragraph;
- excessive adjectives;
- generic AI prose;
- long lists in running text;
- em dashes if avoidable;
- first-person filler such as “it is worth noting”.

Prefer:
> “OverheatLens stores each assessment method as a versioned rule pack.”

Not:
> “It should be noted that our innovative platform has been carefully designed in order to…”

---

# HUMAN-LIKE SCIENTIFIC NARRATIVE

Each section should follow a real argumentative sequence.

Example:
**problem → consequence → software decision → implementation → evidence**

Do not write every paragraph with identical sentence rhythm.

Use transitions that arise from content:
- “This distinction matters because…”
- “To preserve this provenance…”
- “The same mechanism is used for…”
- “A separate check is needed for…”

Avoid formulaic:
- “Furthermore”
- “Moreover”
- “In addition”
at the start of every paragraph.

---

# LIMITATIONS — MUST BE CANDID

Discuss:
- software is not professional sign-off;
- standards/regulations evolve;
- input quality determines simulation validity;
- cross-software comparisons can differ due to engine/model translation;
- CIBSE weather redistribution/licensing may restrict bundled examples;
- public archetypes are representative, not individual-home diagnoses;
- outdoor comfort indices have defined assumptions/applicability;
- hosted EnergyPlus compute can create operational cost/queue limits.

A strong limitations section improves credibility.

---

# SOFTWAREX SUBMISSION PACKAGE

Create:

```text
/manuscript/softwarex/
    manuscript.docx or manuscript.tex
    manuscript.pdf
    highlights.txt
    graphical_abstract.svg
    cover_letter.docx
    figures/
        fig01_architecture.svg
        fig02_standards.svg
        fig03_ui.svg
        fig04_validation.svg
        fig05_case.svg
        fig06_reproducibility.svg   # only if retained
    tables/
    supplementary/
        validation_report.pdf
        reproducibility_manifest.json
        figure_data/
    submission_checklist.md
```

Use the current official SoftwareX template without altering required formatting.

---

# COVER LETTER CONTENT

The cover letter should state:
- manuscript title;
- software name/version;
- open-source licence;
- repository;
- archive DOI;
- fit with SoftwareX;
- scientific use;
- validation approach;
- originality/submission declaration;
- related manuscripts if any.

Do not oversell.

---

# OPTIONAL JOSS PACKAGE

If the user decides to submit to JOSS instead/also where policy permits:

Create:

```text
/paper.md
/paper.bib
```

Target:
**1,100–1,500 words**

Required narrative:
1. Summary
2. Statement of need
3. Related software
4. Research use
5. Acknowledgements
6. References

Do not include user documentation in the paper.

---

# FINAL PEER-REVIEW SIMULATION

Before calling the manuscript ready, review it from five roles:

## Reviewer 1 — software engineer
Questions:
- modular?
- testable?
- reusable?

## Reviewer 2 — building-performance specialist
Questions:
- standards correctly versioned?
- EnergyPlus provenance?
- claims accurate?

## Reviewer 3 — reproducibility reviewer
Questions:
- can I obtain exact release?
- can I rerun examples?
- are fixtures open/licensed?

## Reviewer 4 — information-visualisation reviewer
Questions:
- figures readable?
- values traceable?
- charts scientifically appropriate?

## Reviewer 5 — journal editor
Questions:
- clearly SoftwareX?
- concise?
- software contribution obvious?
- no duplicated science paper?

Create:
`PRE_SUBMISSION_REVIEW.md`

For every criticism:
- severity;
- location;
- fix;
- status.

Resolve all major issues before final submission files.

---

# FINAL OUTPUT REPORT

When finished, provide:

## Journal
Primary + why.

## Release frozen
Version, tag, DOI.

## Manuscript
Word count and template status.

## Figures
List 1–6, data source, file.

## Tables
List.

## Validation
Summary with exact evidence.

## Repository
Audit status.

## Remaining human checks
Only items that genuinely require author/supervisor/legal/publisher confirmation.

---

# FINAL COMMAND

Create a SoftwareX submission that makes the software itself the evidence.

Do not hide weak validation behind polished prose.

Do not hide an ugly interface behind strong tests.

Do not hide a monolithic website behind the phrase “research software”.

The submission is ready only when the **science, software engineering, visual design and reproducibility tell the same story**.

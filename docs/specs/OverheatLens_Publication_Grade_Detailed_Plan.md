# OverheatLens — Publication-Grade Detailed Build Plan
## Open overheating, weather, thermal-comfort and climate-resilience intelligence for buildings

**Version:** 2.0  
**Date:** 28 August 2026  
**Status:** implementation specification / single source of truth  
**Supersedes:** `TM59_Overheating_Hub_Detailed_Plan.md`

---

# 0. PRODUCT IDENTITY

## 0.1 Name

**OverheatLens**

**Long form:** **OverheatLens — Open Building Overheating & Climate-Resilience Hub**

**Tagline:** **See the heat. Trace the evidence. Test the response.**

The name was selected because it is:
- short;
- understandable outside academia;
- not tied only to Leeds;
- not tied only to TM59;
- suitable for a GitHub repository, research paper, public web tool and future city deployments;
- visually compatible with a “lens + building + thermal contour” identity.

**Naming note:** an exact-name web search on 28 August 2026 did not surface a directly competing building-overheating software product named “OverheatLens”. This is not legal or trademark clearance. Perform a formal trademark/domain check before public launch.

## 0.2 Product positioning

OverheatLens is not merely a “TM59 calculator”. It is an **open research software platform** that links:

**weather-file quality → building-model readiness → EnergyPlus simulation → versioned overheating standards → thermal-comfort analytics → mitigation scenarios → reproducible evidence → public communication**

Primary audiences:
1. building-performance researchers;
2. overheating assessors;
3. architects and engineers;
4. planners and local authorities;
5. postgraduate students;
6. building owners and residents using the public-facing mode;
7. software developers who need a reusable overheating-analysis core library.

## 0.3 Core differentiator

The software must combine five layers that existing products usually separate:

1. **Standards-aware overheating assessment**
2. **EPW / climate intelligence**
3. **EnergyPlus model and simulation provenance**
4. **Visual, decision-ready mitigation analysis**
5. **Open, reproducible research software**

The application must not claim to replace a qualified overheating assessor or provide a statutory certificate.

---

# 1. CRITICAL STANDARDS CORRECTION

The previous plan treated “TM59” as one fixed method. That is no longer scientifically acceptable.

## 1.1 Version-aware standards architecture

As of 28 August 2026:

- **CIBSE TM59:2026** was published in July 2026 and is the current CIBSE design-stage overheating methodology for dwellings.
- **Approved Document O / Part O** has not yet simply become “TM59:2026 compliance”. CIBSE states that the Part O compliance route still requires the older **TM59:2017** route and relevant **2016 weather files** while regulatory incorporation of the new guidance/weather data is being discussed.
- CIBSE also states that TM59:2026 requires the newer 2025 weather-file set and that the v1.1 weather files should replace affected v1.0 files for DesignBuilder/EnergyPlus work.
- TM59:2026 introduces changed criteria, reporting and modelling expectations. It must not be represented by the legacy TM59:2017 formulas.

Therefore the software shall use **versioned rule packs**.

## 1.2 Required assessment modes

The user must explicitly choose one of the following at project creation:

### Mode A — TM59:2026 Design Assessment
Purpose: current CIBSE design-stage overheating methodology.

UI label:
> **TM59:2026 — current design guidance**

The software must show the exact weather-data requirements, criteria, assessment period, occupancy interpretation and reporting logic defined by the current TM59:2026 source.

### Mode B — Approved Document O Dynamic Route
Purpose: current regulatory workflow.

UI label:
> **Part O — statutory dynamic route**

This must be locked to the currently applicable statutory/reference version. Do not silently substitute TM59:2026 logic or 2025 weather files.

### Mode C — TM59:2017 Legacy / Comparison
Purpose: historical research, legacy planning work and direct comparison with earlier studies.

### Mode D — TM52
Purpose: adaptive overheating analysis where TM52 is the appropriate method. Never imply that TM52 is interchangeable with TM59.

### Mode E — Research / Custom
Purpose: explicitly non-compliance research weather files, sensor-morphed EPWs, future weather, UHI experiments and sensitivity studies.

Research mode must carry a persistent banner:
> **Research weather / non-standard compliance assessment**

## 1.3 Machine-readable rule packs

Create:

```text
/packages/overheatlens-core/overheatlens/rules/
    uk_tm59_2017.yaml
    uk_tm59_2026.yaml
    uk_part_o_dynamic.yaml
    uk_part_o_simplified.yaml
    uk_tm52.yaml
    comfort_iso7730_2025.yaml
    comfort_en16798.yaml
```

Each rule pack must contain:
- rule-pack ID;
- title;
- publisher;
- edition/year;
- effective date;
- source-document citation;
- weather-file requirements;
- assessment window;
- space types;
- occupancy assumptions;
- criteria;
- thresholds;
- rounding rules;
- aggregation rules;
- warnings;
- incompatibilities;
- test fixture IDs;
- version number;
- changelog.

**No threshold may be buried only in frontend code.**

---

# 2. BENCHMARK RESEARCH THAT MUST INFORM THE BUILD

The following current products/projects were reviewed before this revision.

## 2.1 GitHub / open-source benchmark

### Center for the Built Environment — CBE Comfort Tool
Useful patterns to adopt:
- web-first scientific calculator;
- interactive adaptive and psychrometric visualisation;
- SI/IP units;
- direct comparison of multiple conditions;
- documentation integrated with the tool;
- automated browser tests.

### Center for the Built Environment — CBE Clima Tool
Useful patterns to adopt:
- rich EPW climate exploration;
- upload-own-EPW workflow;
- derived climate variables;
- architect-friendly climate visualisations;
- location comparison.

### pythermalcomfort
Useful patterns to adopt:
- standards-specific named functions;
- applicability checks;
- explicit standard editions;
- automated tests;
- vectorised calculations;
- software citation metadata;
- changelog discipline.

### Ladybug Tools / Honeybee Energy / Ladybug Comfort
Useful patterns to adopt:
- reusable domain libraries rather than UI-only logic;
- EnergyPlus integration;
- modular architecture;
- documented command-line/API interfaces;
- testing and versioned packages.

### epwvis
Useful patterns to adopt:
- fast online EPW analysis;
- psychrometric derivatives;
- transparent weather-file interpretation.

### LBNL Dynamic Facade Dashboard
Useful pattern to adopt:
- pre-computed simulation libraries for instant, non-expert decision support.

### Open Energy Dashboard
Useful patterns to adopt:
- simple public-facing data display;
- non-technical navigation;
- accessible time-series exploration.

## 2.2 LinkedIn / professional-tool benchmark

### DesignBuilder, August 2026
Current public material emphasizes:
- TM59:2026;
- criteria-level pass/fail reporting;
- bedroom night assessment;
- ceiling-fan handling;
- home-office template;
- updated weather zones;
- PDF report generation;
- per-zone summary matrices;
- parametric analysis;
- uncertainty/sensitivity analysis;
- parallel-coordinate and bubble-plot visualisations.

### IESVE
Useful positioning benchmark:
- explicit Part O workflow;
- regulated-industry credibility;
- dynamic simulation;
- professional compliance reporting.

## 2.3 What OverheatLens must add beyond the benchmark

OverheatLens must combine:
- **dual/current regulatory logic**;
- **public + practitioner + researcher modes**;
- **raw file readiness checks**;
- **full provenance and reproducibility bundle**;
- **open rule-pack architecture**;
- **weather-file comparison and UHI research mode**;
- **pre-run archetype atlas**;
- **true open-source validation evidence**;
- **publication figure export**;
- **method/version diff viewer**;
- **audit-ready “why did this fail?” explanations**.

---

# 3. SOFTWARE ARCHITECTURE

## 3.1 Mandatory architecture change

Do not put authoritative scientific calculations only in browser JavaScript.

Build the product around a reusable scientific core package.

```text
┌─────────────────────────────────────────────────────────────────┐
│                         OVERHEATLENS WEB                        │
│ React + TypeScript + Vite                                      │
│ Scientific editorial interface                                │
│ ECharts + MapLibre + TanStack Table                            │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTPS / JSON
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OVERHEATLENS API                         │
│ FastAPI                                                         │
│ project validation / calculations / report data / jobs          │
└─────────────┬──────────────────────────────┬────────────────────┘
              │                              │
              ▼                              ▼
┌────────────────────────────┐  ┌─────────────────────────────────┐
│ OVERHEATLENS CORE          │  │ ENERGYPLUS WORKER               │
│ Python package             │  │ official EnergyPlus executable │
│ rules + EPW + comfort +    │  │ isolated job directory         │
│ TM59/TM52/Part O logic     │  │ deterministic run manifest     │
└────────────────────────────┘  └─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ REPRODUCIBILITY LAYER                                           │
│ checksums / rule-pack version / E+ version / fixtures / logs    │
│ machine-readable result bundle / Zenodo-ready release metadata  │
└─────────────────────────────────────────────────────────────────┘
```

## 3.2 Why this architecture is required

It improves:
- testability;
- maintainability;
- JOSS/SoftwareX scope;
- reproducibility;
- independent reuse of the scientific methods;
- CLI use in batch research;
- future desktop/notebook integration;
- confidence that UI refactors do not change formulas.

## 3.3 Monorepo structure

```text
/
├── README.md
├── LICENSE
├── CITATION.cff
├── codemeta.json
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── GOVERNANCE.md
├── DISCLAIMER.md
├── pyproject.toml
├── package.json
├── docker-compose.yml
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── apps/
│   ├── web/
│   │   ├── src/
│   │   ├── public/
│   │   └── tests/
│   ├── api/
│   │   ├── app/
│   │   └── tests/
│   └── worker/
│       ├── runner/
│       └── Dockerfile
├── packages/
│   └── overheatlens-core/
│       ├── overheatlens/
│       │   ├── epw/
│       │   ├── idf/
│       │   ├── rules/
│       │   ├── standards/
│       │   ├── comfort/
│       │   ├── heatwave/
│       │   ├── provenance/
│       │   ├── schemas/
│       │   └── cli/
│       └── tests/
├── fixtures/
│   ├── epw/
│   ├── idf/
│   ├── hourly_results/
│   ├── expected/
│   └── faults/
├── examples/
│   ├── leeds_archetypes/
│   └── notebooks/
├── docs/
│   ├── methodology/
│   ├── validation/
│   ├── standards/
│   ├── tutorials/
│   └── publication/
├── data/
│   ├── archetypes/
│   └── demo/
└── manuscript/
    ├── softwarex/
    └── figures/
```

## 3.4 Scientific dependency policy

Prefer established implementations where they are more defensible than reimplementation.

Examples:
- use `pythermalcomfort` for supported PMV/PPD, adaptive and UTCI calculations when its standard/version matches the intended method;
- use the official EnergyPlus binary for simulation;
- do not recreate a published thermal-comfort polynomial merely to avoid a dependency;
- wrap external scientific functions behind OverheatLens interfaces and pin exact versions.

Every dependency used in a metric must appear in provenance.

## 3.5 EnergyPlus version

Pin **EnergyPlus 26.1.0** for the first publication release unless a newer stable official release exists at the moment of implementation freeze.

The release manifest must store:
- version;
- Git commit/build ID if available;
- platform;
- command;
- input hashes;
- result hashes.

---

# 4. PRODUCT MODES

OverheatLens must use progressive disclosure.

## 4.1 Public mode

Question answered:
> “Is this home/building likely to overheat, why, and what can be done?”

Show:
- plain-language status;
- hottest rooms;
- hottest periods;
- key causes;
- weather severity;
- mitigation directions;
- simple comparison;
- caveat and non-certification notice.

Hide by default:
- raw solver messages;
- equations;
- low-level EnergyPlus objects;
- dense validation matrices.

## 4.2 Practitioner mode

Question answered:
> “Does this project pass the selected method, exactly where does it fail, and what evidence can I report?”

Show:
- standards mode;
- criteria A/B/C/D or applicable legacy criteria;
- zone matrix;
- weather identity;
- model-readiness checks;
- detailed plots;
- clause-linked explanations;
- report export.

## 4.3 Researcher mode

Question answered:
> “Can I inspect, compare, reproduce, export and challenge every calculation?”

Show:
- formulas;
- rule-pack version;
- raw hourly series;
- uncertainty;
- multiple EPWs;
- UHI deltas;
- provenance;
- API/CLI examples;
- validation fixtures;
- JSON result bundles;
- methodological limitations.

---

# 5. INFORMATION ARCHITECTURE AND MENUS

## 5.1 Primary top navigation

1. **Home**
2. **Analyze**
3. **Compare**
4. **Archetype Atlas**
5. **Weather Lab**
6. **Comfort Lab**
7. **Mitigation Lab**
8. **Validation**
9. **Methods**
10. **Docs**
11. **About**

## 5.2 Analyze workflow

Use a visible stepper:

**1 Project → 2 Standard → 3 Weather → 4 Model → 5 Readiness → 6 Simulate → 7 Results → 8 Mitigate → 9 Report**

Users must always know:
- where they are;
- what is complete;
- what blocks the next step;
- what is optional.

## 5.3 Results tabs

1. **Summary**
2. **Criteria**
3. **Rooms**
4. **Time**
5. **Weather**
6. **Comfort**
7. **Mitigation**
8. **Provenance**
9. **Validation**
10. **Exports**

## 5.4 Global command/search menu

Keyboard shortcut: `⌘K / Ctrl+K`

Search:
- page;
- room;
- criterion;
- metric;
- archetype;
- method;
- weather file;
- documentation topic.

---

# 6. VISUAL DESIGN SYSTEM

## 6.1 Design direction

The interface must look like a hybrid of:
- a high-end scientific journal figure;
- a professional civic-data product;
- an architectural environmental-analysis studio.

Avoid:
- generic “AI dashboard” styling;
- glassmorphism;
- neon gradients;
- excessive rounded cards;
- giant empty hero sections;
- decorative 3D objects;
- stock images;
- rainbow scientific colour maps.

Use:
- strong typographic hierarchy;
- restrained colour;
- hairline rules;
- white space;
- precise grids;
- data-first composition;
- subtle motion;
- meaningful icons.

## 6.2 Colour tokens

### Core surfaces
- `--paper: #F7F5F0`
- `--surface: #FFFFFF`
- `--ink: #172126`
- `--muted-ink: #5E686E`
- `--line: #D9D7D1`
- `--line-strong: #B7B8B3`

### Brand
- `--brand: #1F5F70` — deep climate teal
- `--brand-dark: #173F4A`
- `--brand-soft: #DCECEF`

### Heat accents
- `--heat-1: #F4C95D`
- `--heat-2: #E58A3A`
- `--heat-3: #D4553D`
- `--heat-4: #8F2D3A`

### Status
- `--pass: #2F755B`
- `--warning: #B7791F`
- `--fail: #B43A4A`
- `--info: #356C95`

Status must never depend on colour alone. Pair colour with:
- icon;
- text;
- shape;
- pattern where relevant.

## 6.3 Typography

Recommended:
- UI: **Inter** or system sans fallback
- technical/data labels: **IBM Plex Mono**
- editorial section headings / publication moments: **Source Serif 4**

Rules:
- body 15–17 px;
- line height 1.45–1.6;
- minimum 12 px only for secondary chart annotations;
- tabular numerals for data;
- no all-caps paragraphs;
- do not use ultra-light weights.

## 6.4 Geometry

- 8 px spacing system;
- maximum content width 1440 px;
- 12-column desktop grid;
- 6-column tablet;
- 4-column mobile;
- card radius 8–10 px maximum;
- charts should often sit directly on the page rather than inside nested cards;
- 1 px hairline separators;
- use sticky side context for long technical screens.

## 6.5 Motion

- 150–220 ms;
- ease-out;
- only for state change, filtering, drawer opening and chart transition;
- respect `prefers-reduced-motion`;
- no decorative looping animation.

## 6.6 Logo concept

A simple mark:
- outline of a dwelling/building;
- one circular “lens” crossing the facade;
- three thermal contour lines inside the lens.

It must work:
- monochrome;
- favicon;
- GitHub avatar;
- manuscript figure corner;
- dark/light backgrounds.

---

# 7. FRONTEND TECHNOLOGY

Use:

- React
- TypeScript
- Vite
- Apache ECharts
- MapLibre GL JS
- TanStack Table
- React Router
- Zod for runtime schema validation
- Web Workers for large local file preview/parsing
- Playwright
- Vitest
- axe-core
- Storybook for component QA if it does not materially slow delivery

CSS:
- CSS variables + scoped component CSS or a restrained utility layer;
- do not rely on a heavy UI kit that makes the application look generic.

Do not use a component simply because a library offers it. Build a coherent OverheatLens visual system.

---

# 8. HOME PAGE

The home page must immediately establish usefulness.

## 8.1 Hero

Left:
> **See where overheating begins.**  
> Open, reproducible building-overheating assessment, weather intelligence and thermal-comfort analysis.

Primary CTA:
**Analyze a building**

Secondary CTA:
**Explore an archetype**

Small trust line:
**EnergyPlus-powered · version-aware TM59 / Part O workflows · open methodology**

Right:
an animated-but-subtle “thermal year ribbon” using real demo data, not a decorative illustration.

## 8.2 Three task cards

- **Check a model**
- **Check a weather file**
- **Explore overheating risk**

## 8.3 Evidence section

Show:
- current rule packs;
- EnergyPlus version;
- validation suite status;
- number of regression fixtures;
- latest release DOI when available.

## 8.4 Public example

Embed one pre-run Leeds archetype story:
- building type;
- selected weather;
- hottest bedroom;
- key mitigation;
- “open full analysis”.

---

# 9. PROJECT CREATION

Fields:
- project name;
- location;
- hemisphere;
- assessment mode;
- target audience;
- dwelling / non-dwelling;
- vulnerability context where supported by the standard;
- units SI/IP;
- notes.

On selection of an assessment mode show a **Standards Passport**:
- edition;
- weather requirement;
- assessment months;
- major criteria;
- regulatory / research status;
- known compatibility warning.

---

# 10. EPW / WEATHER LAB

## 10.1 EPW readiness

Validate:
- headers;
- location;
- timestamps;
- row count;
- leap year;
- fields;
- missing sentinels;
- physical ranges;
- impossible dew-point relationships;
- pressure plausibility;
- radiation consistency checks;
- wind range;
- duplicate hours;
- gaps;
- timezone;
- checksum;
- source comments.

Classify:
- PASS;
- PASS WITH WARNINGS;
- FAIL.

## 10.2 Weather identity

Extract and display:
- city;
- station/source;
- coordinates;
- elevation;
- WMO ID where present;
- climate-file family;
- DSY/TMY/TRY identity if traceable;
- future scenario if traceable;
- percentile if traceable;
- file checksum.

If provenance cannot be proven, explicitly say:
> **Weather provenance not machine-verifiable**

## 10.3 CIBSE weather compatibility guard

For each standards mode, compare the selected EPW against required:
- edition/family;
- climate zone;
- period;
- percentile;
- file version.

Use a compatibility matrix:
- compatible;
- research-only;
- incompatible;
- unknown.

## 10.4 Weather visualisations

Mandatory charts:

1. **Annual thermal ribbon**  
   365 × 24 heatmap of dry-bulb temperature.

2. **Month × hour climate matrix**  
   12 × 24 mean / percentile selector.

3. **Dry-bulb duration curve**

4. **Psychrometric chart**

5. **Adaptive outdoor running-mean chart** where applicable

6. **Wind rose**

7. **Solar radiation calendar**

8. **Humidity / dew-point density**

9. **Degree-hour exceedance curves** above configurable thresholds

10. **Extreme-event strip** showing consecutive hot episodes

11. **Daily max / min ribbon**

12. **Heatwave event table**

## 10.5 Multi-EPW Compare

Allow 2–8 files.

Compare:
- annual mean;
- monthly mean;
- hottest day;
- hottest week;
- night minima;
- exceedance hours;
- heatwave events;
- humidity;
- solar;
- wind;
- derived comfort indices.

Visuals:
- small-multiple annual ribbons;
- delta matrix;
- empirical CDF;
- monthly ridgeline or violin plots;
- slope graph for headline metrics.

## 10.6 UHI / urban-rural delta mode

Two aligned weather files:
- calculate `urban - reference` temperature;
- monthly/hourly mean;
- nighttime subset;
- percentile distribution;
- heat-event delta;
- humidity/vapour-pressure delta if valid.

Label:
> **Research comparison, not a regulatory UHI certification**

---

# 11. IDF / EPJSON MODEL READINESS

Support:
- `.idf`;
- `.epJSON` if feasible in the pinned EnergyPlus release.

## 11.1 Generic checks

- syntax;
- EnergyPlus version;
- conversion/transition compatibility;
- full required run period;
- site location;
- zones;
- occupied zones;
- people;
- schedules;
- schedule references;
- internal gains;
- infiltration;
- ventilation;
- glazing;
- shading;
- HVAC;
- output variables;
- timestep;
- simulation control;
- severe/fatal risks visible before long run where possible.

## 11.2 Standards-specific checks

Rule-pack-driven:
- room classification;
- bedroom detection;
- living/kitchen/home-office detection;
- common-circulation detection;
- natural/mechanical/cooled path;
- window control;
- ceiling fan model;
- occupancy schedules;
- internal gains;
- weather compatibility;
- required output variables.

Never “infer and silently accept”.
Show:
- detected value;
- required value;
- confidence;
- source object;
- recommended action.

## 11.3 Model summary visual

Create an **IDF Passport**:
- number of zones;
- occupied floor area if available;
- bedrooms;
- living spaces;
- glazing summary;
- ventilation strategy;
- cooling present yes/no;
- ceiling fans yes/no;
- construction count;
- schedule count;
- run-period readiness;
- standard compatibility.

---

# 12. SIMULATION ENGINE

## 12.1 Authoritative engine

Official EnergyPlus only.

## 12.2 Job lifecycle

Statuses:
- queued;
- validating;
- preparing;
- simulating;
- parsing;
- calculating;
- reporting;
- complete;
- failed;
- cancelled.

Show live progress without inventing percent complete where EnergyPlus cannot provide it reliably.

## 12.3 Isolation

For every job:
- unique ephemeral directory;
- no cross-user file access;
- maximum file sizes;
- CPU/time limits;
- memory limits;
- safe filename handling;
- delete files after configured retention;
- structured error return.

## 12.4 Output harvesting

Request only outputs required by the selected rules + user analysis.

At minimum where applicable:
- zone operative temperature;
- zone mean air temperature;
- mean radiant temperature;
- relative humidity;
- ventilation / opening variables;
- ceiling fan state / air speed if needed;
- occupancy;
- selected HVAC variables;
- outdoor conditions.

## 12.5 Error interpreter

Parse `eplusout.err`.

Group:
- fatal;
- severe;
- warning;
- recurring warning.

For each:
- plain-language explanation;
- affected object;
- likely readiness-check relation;
- link to technical log.

---

# 13. STANDARDS ENGINE

## 13.1 No hard-coded “one TM59”

Create a `StandardsEngine`.

API concept:

```python
result = evaluate(
    standard="uk_tm59_2026",
    rule_version="2026.1",
    weather=weather_manifest,
    model=model_manifest,
    hourly=hourly_results
)
```

## 13.2 Criterion traceability

Every result must carry:
- rule ID;
- clause/source;
- inputs;
- derived intermediate values;
- threshold;
- numerator;
- denominator;
- rounding;
- pass/fail;
- rule-pack version.

## 13.3 Standards diff viewer

Unique feature.

Allow:
**TM59:2017 ↔ TM59:2026**

Show changes in:
- weather;
- period;
- room/space logic;
- criteria;
- bedroom handling;
- home office;
- circulation;
- fan/air movement;
- reporting.

This is highly valuable for practitioners and publication positioning.

---

# 14. COMFORT LAB

Use a standards-aware model selector.

## 14.1 Indoor

Where inputs support them:
- PMV;
- PPD;
- adaptive comfort;
- operative-temperature distribution;
- degree-hours;
- occupied exceedance hours;
- humidity context.

Use **ISO 7730:2025** where supported by the selected library/version and state the edition.

## 14.2 Outdoor

Where EPW inputs and assumptions support them:
- UTCI;
- Heat Index;
- Humidex;
- selected WBGT approximation only if the exact method and limitations are explicit.

Do not present PET unless a scientifically defensible implementation is included and validated.

## 14.3 Applicability

If inputs fall outside a standard’s defined applicability range:
- return `OUTSIDE_APPLICABILITY`;
- do not silently calculate a misleading value.

---

# 15. HEATWAVE LAB

## 15.1 Definitions

Heatwave definitions must be named and source-specific.

Do not label one arbitrary threshold “the heatwave”.

For UK mode:
- implement the current Met Office location/county threshold method;
- store threshold dataset version/date.

Also allow:
- user-defined research threshold;
- percentile-based research definition;
- warm-night definition.

## 15.2 Event explorer

For every event:
- start;
- end;
- duration;
- daily maxima;
- nightly minima;
- peak;
- cumulative degree-hours;
- affected simulated rooms;
- selected comfort response.

## 15.3 Coupled outdoor-indoor event view

Novel chart:
top half = outdoor event;
bottom small multiples = room operative temperatures.

This should make propagation of a heat episode through the building instantly understandable.

---

# 16. RESULTS DASHBOARD

## 16.1 Summary page

Header:
- project;
- assessment mode;
- rule-pack version;
- EnergyPlus version;
- weather identity;
- checksum;
- run ID.

Hero metrics:
- overall status;
- number of assessed rooms;
- failing rooms;
- hottest room;
- worst criterion;
- hottest night / day;
- dominant warning.

## 16.2 Criterion matrix

Rows = zones.  
Columns = applicable criteria.

Cells contain:
- pass/fail icon;
- metric;
- threshold;
- margin.

Click opens evidence drawer.

## 16.3 Room profile

For one room show:
- headline status;
- annual temperature strip;
- May–September / applicable assessment-period chart;
- adaptive threshold overlay;
- exceedance distribution;
- night strip;
- worst days;
- occupancy;
- ventilation/fan state if available.

## 16.4 “Why did it fail?” panel

Automatically summarize, without causal overclaiming:
- which criterion failed;
- when;
- magnitude;
- weather context;
- room/model characteristics available from IDF;
- candidate mitigation categories.

Phrase as:
> “Associated factors in this model include …”
not:
> “This proves the cause is …”

---

# 17. CHART SYSTEM

Every chart must support:
- SVG export;
- PNG export;
- CSV of plotted data;
- copy caption;
- accessible text summary;
- hover details;
- units;
- source/provenance note.

## 17.1 Required chart catalogue

1. annual thermal ribbon;
2. month × hour heatmap;
3. calendar exceedance heatmap;
4. hourly temperature + threshold band;
5. bedroom night strip;
6. exceedance-duration curve;
7. ECDF;
8. box/violin distribution;
9. adaptive comfort scatter;
10. psychrometric chart;
11. wind rose;
12. solar radiation calendar;
13. criterion matrix;
14. room small multiples;
15. multi-EPW delta matrix;
16. urban-reference delta profile;
17. scenario parallel coordinates;
18. tornado sensitivity chart;
19. Pareto frontier;
20. scenario heatmap;
21. provenance flow;
22. validation parity chart;
23. Bland–Altman plot where appropriate;
24. test coverage / validation matrix;
25. map of archetypes.

## 17.2 Scientific colour policy

- never use rainbow/jet;
- use perceptually ordered sequential scales;
- diverging scales must have a meaningful zero;
- uncertainty must be shown using interval, band or distribution, not decorative opacity alone.

---

# 18. MITIGATION LAB

## 18.1 Scenario manager

Users can create named scenarios:
- baseline;
- external shading;
- lower g-value;
- reduced glazing;
- increased secure ventilation;
- night purge;
- ceiling fan;
- insulation variant;
- cool roof;
- combined strategy.

## 18.2 Two levels of mitigation evidence

### Level 1 — precomputed archetype sensitivity
Instant, public-friendly.
Must say:
> **Precomputed indicative response**

### Level 2 — actual resimulation
Practitioner/research mode.
Clone the model, apply supported changes, run EnergyPlus, compare actual outputs.

Never mix the two.

## 18.3 Analysis

For scenario sets:
- pass/fail matrix;
- overheating-hour reduction;
- hottest-night reduction;
- relative/absolute change;
- trade-off metrics if energy results are also available;
- parallel coordinates;
- tornado chart;
- Pareto frontier for multi-objective runs.

---

# 19. ARCHETYPE ATLAS

Rename the old “Leeds archetype hub” to **Archetype Atlas**.

Leeds is the first collection, not the product boundary.

## 19.1 Browse

Filters:
- city;
- archetype;
- dwelling type;
- age band;
- construction;
- retrofit;
- weather;
- standard;
- pass/fail;
- vulnerability setting where applicable.

## 19.2 Card

Show:
- illustration/diagram or real project-neutral geometry preview;
- archetype title;
- city;
- floor area;
- weather;
- status;
- key risk metric;
- “open story”.

## 19.3 Compare

2–6 archetypes.
Use:
- aligned small multiples;
- metrics table;
- room comparison;
- weather-normalised interpretation where scientifically justified.

## 19.4 Map

Use MapLibre.
Do not expose private exact addresses for research/case-study dwellings unless explicit permission exists.

---

# 20. PUBLIC STORY MODE

For pre-run datasets, build a scrollable narrative:

1. What building is this?
2. What weather did we test?
3. When does it get hottest?
4. Which room is most vulnerable?
5. What criterion is exceeded?
6. What happens during the worst heat event?
7. Which mitigation helps most?
8. What does this result not tell us?

This mode should feel like an interactive scientific article, not a compliance form.

---

# 21. PROVENANCE AND REPRODUCIBILITY

## 21.1 Run manifest

Every completed analysis produces:

```json
{
  "run_id": "...",
  "overheatlens_version": "...",
  "core_version": "...",
  "rule_pack": "...",
  "rule_pack_version": "...",
  "energyplus_version": "...",
  "idf_sha256": "...",
  "epw_sha256": "...",
  "input_files": [],
  "assumptions": [],
  "outputs": [],
  "created_utc": "..."
}
```

## 21.2 Reproducibility bundle

One-click ZIP:
- manifest;
- summary JSON;
- room CSVs;
- weather summary;
- criteria output;
- rule-pack reference;
- logs;
- figures as SVG;
- report PDF;
- README explaining reproduction;
- checksums.

Do not include raw licensed weather data if redistribution is prohibited.

## 21.3 Citation

Generate:
- plain citation;
- BibTeX;
- RIS;
- software version;
- DOI when available.

---

# 22. EXPORTS

1. **Professional PDF report**
2. **Public one-page summary**
3. **CSV**
4. **JSON**
5. **SVG figure pack**
6. **Publication figure pack**
7. **Reproducibility bundle**
8. **BibTeX / RIS**
9. **Validation report**
10. **Standards Passport**

## 22.1 Publication figure mode

A special chart-export dialog:
- journal single-column width;
- journal double-column width;
- editable SVG;
- 300/600 dpi PNG;
- white background;
- no UI chrome;
- caption draft;
- source data CSV;
- figure manifest.

---

# 23. REPORT DESIGN

The PDF must look like a technical journal/report, not a web screenshot.

Sections:
1. cover;
2. executive result;
3. project/input passport;
4. standard/weather passport;
5. room/criterion matrix;
6. key figures;
7. detailed criteria;
8. weather;
9. mitigation if run;
10. validation/provenance;
11. limitations;
12. citations;
13. disclaimer.

Footer on every page:
- OverheatLens version;
- run ID;
- page;
- non-certification status.

---

# 24. ACCESSIBILITY

Mandatory:
- WCAG 2.2 AA target;
- keyboard operation;
- visible focus;
- semantic headings;
- chart text alternatives;
- contrast testing;
- reduced motion;
- no colour-only status;
- 200% zoom usable;
- mobile landscape charts handled gracefully.

Target:
- Lighthouse Accessibility ≥ 95 on critical pages.

---

# 25. INTERNATIONALISATION AND UNITS

Architecture must support i18n from day one.

Release 1:
- English;
- SI units.

Prepare:
- Arabic RTL;
- IP units.

Do not hard-code English strings in scientific calculation modules.

---

# 26. PRIVACY AND SECURITY

## 26.1 Privacy

Default:
- no account;
- no analytics cookies;
- no persistent uploaded files;
- no selling/tracking;
- privacy-respecting aggregate analytics only.

## 26.2 Security

- MIME/content checks;
- path traversal prevention;
- filename sanitisation;
- maximum upload;
- rate limits;
- timeout;
- isolated jobs;
- dependency scanning;
- secret scanning;
- CodeQL where applicable;
- container image scanning;
- security headers;
- strict CORS;
- CSP;
- HTTPS;
- no arbitrary user shell command;
- no server-side IDF path injection.

Add `SECURITY.md`.

---

# 27. SCIENTIFIC VALIDATION STRATEGY

This is a publication gate, not a final polish step.

## 27.1 Validation hierarchy

### Tier 1 — clause/rule unit tests
For every rule:
- boundary below threshold;
- exact threshold;
- above threshold;
- missing input;
- excluded space;
- occupancy edge;
- time-boundary edge;
- rounding edge.

### Tier 2 — independent reference implementation
Critical pass/fail logic must be checked using an independently written reference implementation or independently calculated fixture.

Never copy the production function into the “reference” test.

### Tier 3 — published / official worked examples
Where legally and practically available:
- reproduce disclosed worked examples;
- document any unavailable inputs;
- never claim numerical replication if only pass/fail is public.

### Tier 4 — cross-software benchmark
For a controlled set of identical models/weather:
- OverheatLens vs DesignBuilder;
- OverheatLens vs IESVE where accessible;
- separate **simulation-engine differences** from **post-processing criterion differences**.

### Tier 5 — end-to-end archetype regression
Freeze at least 8–12 diverse archetypes.

Every release reruns:
- same inputs;
- same rule pack;
- expected outputs.

### Tier 6 — independent expert review
One external reviewer checks:
- one natural ventilation case;
- one mechanical/cooled case;
- one Part O case;
- one weather-only case.

## 27.2 Parser robustness

Use property-based/fuzz testing.

EPW faults:
- missing header;
- duplicate row;
- missing row;
- bad field count;
- invalid timestamp;
- invalid sentinel;
- NaN;
- malformed location;
- extreme physical values.

IDF faults:
- incomplete object;
- dangling schedule;
- mismatched version;
- invalid output variable;
- missing occupancy;
- malformed quote/comment;
- wrong run period.

## 27.3 Metamorphic tests

Examples:
- increasing all indoor operative temperatures by +1 K must not reduce fixed-temperature exceedance hours;
- duplicating a failing event without changing denominator logic must not improve the applicable exceedance metric;
- reordering zones must not change results;
- changing display units must not change pass/fail;
- exporting/importing the result JSON must not change values;
- identical inputs must generate identical scientific outputs.

## 27.4 Numerical tolerances

Define per metric.

Do not use one arbitrary global tolerance.

Examples:
- exact counts: exact integer equality;
- temperatures: tight floating-point tolerance;
- percentages: agreed absolute tolerance;
- cross-tool simulation comparisons: separately justified tolerance, never silently widened to “make it pass”.

## 27.5 Coverage gates

Publication release:
- scientific core line coverage ≥ 95%;
- scientific core branch coverage ≥ 90%;
- every standards rule has a direct test;
- zero skipped critical tests;
- zero unresolved fatal/severe EnergyPlus errors in fixtures.

## 27.6 Frontend QA

- Vitest component/unit tests;
- Playwright end-to-end;
- browser matrix;
- mobile;
- keyboard;
- axe;
- screenshot visual regression;
- chart export regression.

## 27.7 Performance QA

Targets for demo datasets:
- landing interactive quickly on ordinary broadband;
- 8760-row EPW preview without UI lock;
- filter response < 150 ms where practical;
- charts remain responsive with 10–20 zones × 8760 hours;
- lazy-load heavy modules.

## 27.8 Reproducibility test

CI must rebuild a known results bundle from frozen fixtures and compare:
- manifest;
- summary;
- key CSV;
- figure data.

---

# 28. VALIDATION DASHBOARD

Expose validation to users.

Show:
- release version;
- tests passed;
- rule-pack coverage;
- benchmark cases;
- cross-software status;
- known discrepancies;
- date of latest validation;
- peer reviewer status;
- open known limitations.

Do not show a vague “validated” badge.

---

# 29. CI/CD AND RESEARCH SOFTWARE ENGINEERING

GitHub Actions:
1. lint Python;
2. type check;
3. Python unit tests;
4. core coverage;
5. frontend lint;
6. frontend tests;
7. Playwright;
8. accessibility smoke tests;
9. build web;
10. build API;
11. container scan;
12. dependency audit;
13. reproducibility fixture;
14. docs build.

On tagged release:
- create changelog;
- create GitHub release;
- archive to Zenodo;
- update DOI;
- build docs;
- deploy web/API;
- freeze validation report.

---

# 30. DOCUMENTATION

Required:
- 5-minute quick start;
- user guide;
- practitioner guide;
- research guide;
- standards guide;
- API docs;
- CLI docs;
- validation handbook;
- data dictionary;
- architecture decision records;
- contributing;
- citation;
- changelog;
- known limitations.

Tutorials:
1. check an EPW;
2. check an IDF;
3. run TM59:2026;
4. run current Part O route;
5. compare 2017 vs 2026;
6. compare current vs future EPW;
7. compare urban vs rural EPW;
8. run mitigation scenarios;
9. export a publication figure;
10. reproduce a published demo run.

---

# 31. PUBLICATION READINESS

## 31.1 Primary journal

**SoftwareX**

Rationale:
- directly publishes research software and its application;
- open-source software is central;
- the planned paper can describe architecture, scientific implementation, validation and practical use;
- the app + core library is substantial enough to be more than a small utility.

Target:
- Original Software Publication;
- approximately 2,500–3,000 words;
- no more than 6 manuscript figures unless the current guide changes;
- open GitHub repository;
- OSI-approved licence;
- archived release DOI.

## 31.2 Secondary journal

**Journal of Open Source Software (JOSS)**

Use as:
- alternative route; or
- companion software paper if publication strategy and journal policies permit.

Important:
JOSS now explicitly warns that many web applications are out of scope unless they expose a rigorous reusable core library and/or show strong domain modelling/testing. The `overheatlens-core` package is therefore mandatory if JOSS is to remain a credible option.

## 31.3 Potential later application paper

A separate science/application paper may target a building-science journal such as:
- Building and Environment;
- Energy and Buildings;
- Building Simulation;

but only if it contains a distinct scientific question/results contribution rather than duplicating the software paper.

---

# 32. PUBLICATION-GRADE REPOSITORY REQUIREMENTS

Before manuscript writing:
- public GitHub repo;
- OSI licence;
- README;
- install/run;
- tests;
- docs;
- examples;
- `CITATION.cff`;
- DOI archive;
- tagged release;
- issue tracker;
- contributing;
- code of conduct;
- changelog;
- security policy;
- versioned rule packs;
- validation report;
- reproducibility bundle;
- screenshots;
- architecture diagram;
- demo URL.

---

# 33. IMPLEMENTATION PHASES

## Phase 0 — Freeze standards and sources
- [ ] acquire current TM59:2026 source;
- [ ] acquire TM59:2017;
- [ ] acquire current Approved Document O;
- [ ] record CIBSE weather guidance;
- [ ] freeze EnergyPlus version;
- [ ] create source register;
- [ ] create rule-pack schema;
- [ ] transcribe and peer-check rules.

**Gate:** no production formula coding until rules are source-verified.

## Phase 1 — Core package skeleton
- [ ] package;
- [ ] schemas;
- [ ] provenance;
- [ ] CLI;
- [ ] CI;
- [ ] unit-test framework.

## Phase 2 — EPW engine
- [ ] parser;
- [ ] checker;
- [ ] provenance;
- [ ] weather metrics;
- [ ] multi-EPW;
- [ ] tests.

## Phase 3 — standards engine
- [ ] TM59:2017;
- [ ] TM59:2026;
- [ ] Part O;
- [ ] TM52;
- [ ] traceability;
- [ ] rule diff;
- [ ] boundary tests.

## Phase 4 — comfort engine
- [ ] dependency wrappers;
- [ ] applicability;
- [ ] PMV/PPD;
- [ ] adaptive;
- [ ] UTCI;
- [ ] heat indices;
- [ ] tests.

## Phase 5 — IDF/epJSON readiness
- [ ] generic;
- [ ] standard-specific;
- [ ] passport;
- [ ] faults;
- [ ] tests.

## Phase 6 — EnergyPlus worker
- [ ] run;
- [ ] isolation;
- [ ] logs;
- [ ] output harvest;
- [ ] cancellation;
- [ ] deterministic manifest.

## Phase 7 — API
- [ ] project;
- [ ] validate;
- [ ] simulate;
- [ ] result;
- [ ] export;
- [ ] docs.

## Phase 8 — design system and frontend foundation
- [ ] tokens;
- [ ] typography;
- [ ] navigation;
- [ ] layout;
- [ ] chart primitives;
- [ ] accessibility;
- [ ] responsive.

## Phase 9 — Weather Lab
- [ ] all mandatory charts;
- [ ] compare;
- [ ] UHI mode;
- [ ] export.

## Phase 10 — Analyze workflow
- [ ] project;
- [ ] standard;
- [ ] inputs;
- [ ] readiness;
- [ ] job UI;
- [ ] error states.

## Phase 11 — Results
- [ ] summary;
- [ ] criteria;
- [ ] rooms;
- [ ] time;
- [ ] provenance;
- [ ] validation.

## Phase 12 — Comfort / Heatwave
- [ ] comfort lab;
- [ ] heatwave events;
- [ ] coupled event chart.

## Phase 13 — Mitigation Lab
- [ ] scenario manager;
- [ ] actual rerun;
- [ ] precomputed sensitivity;
- [ ] parallel coordinates;
- [ ] tornado;
- [ ] Pareto.

## Phase 14 — Archetype Atlas
- [ ] data schema;
- [ ] Leeds import;
- [ ] cards;
- [ ] map;
- [ ] compare;
- [ ] public story.

## Phase 15 — reports/exports
- [ ] PDF;
- [ ] public summary;
- [ ] CSV/JSON;
- [ ] SVG;
- [ ] reproducibility ZIP;
- [ ] citations.

## Phase 16 — validation campaign
- [ ] official/published fixtures;
- [ ] DesignBuilder benchmark;
- [ ] IESVE benchmark if accessible;
- [ ] reference implementation;
- [ ] expert peer review;
- [ ] validation report.

## Phase 17 — publication release
- [ ] v1.0 tag;
- [ ] Zenodo DOI;
- [ ] public documentation;
- [ ] stable demo;
- [ ] SoftwareX manuscript package.

---

# 34. HARD ACCEPTANCE GATES

The product is not “done” until all are true:

1. No production standards threshold exists without a source/rule ID.
2. TM59:2017 and TM59:2026 cannot be accidentally conflated.
3. Part O mode warns if a user selects an incompatible weather/rule version.
4. All scientific-core tests pass.
5. Core coverage meets publication target.
6. Same input + same versions gives deterministic scientific results.
7. Every displayed metric has provenance.
8. PDF equals dashboard values.
9. SVG figure export equals plotted data.
10. A second implementation/reference agrees with critical calculations.
11. Cross-software comparison is documented.
12. Public mode cannot be mistaken for a statutory certificate.
13. Uploaded files are not retained by default.
14. Accessibility tests pass.
15. No critical dependency/security alert remains unresolved.
16. Repository is citable and archived.
17. Publication figures are generated from real tool outputs, never fabricated.

---

# 35. MANDATORY DISCLAIMER

Use a concise version in the UI and a full version in reports.

> **OverheatLens is open research and decision-support software. It implements published overheating and thermal-comfort methods and can orchestrate EnergyPlus simulations, but it is not a certified compliance certificate. Regulatory requirements, approved documents, weather datasets and industry guidance change over time. Formal planning or Building Control submissions must use the applicable current requirements and be reviewed or signed off by a suitably qualified professional.**

---

# 36. DEFINITION OF THE V1.0 PUBLICATION RELEASE

V1.0 is the smallest version worthy of publication.

It must include:
- OverheatLens Core;
- current TM59:2026 rule pack;
- TM59:2017 rule pack;
- current Part O dynamic route;
- EPW Weather Lab;
- IDF readiness;
- EnergyPlus runner;
- results dashboard;
- criteria/room visualisations;
- provenance;
- PDF/CSV/JSON/SVG exports;
- at least one Leeds archetype collection;
- multi-EPW comparison;
- validation report;
- reproducibility bundle;
- documentation;
- public demo;
- DOI release.

Nice-to-have items may move to v1.1, but validation, provenance, standards versioning and visual quality may not.

---

# 37. FINAL PRODUCT PRINCIPLE

**Do not build a calculator with a pretty dashboard. Build a transparent scientific instrument with a beautiful interface.**

Every engineering decision must satisfy three questions:

1. **Is the calculation defensible?**
2. **Can another researcher reproduce it?**
3. **Can a non-specialist understand what the result means without being misled?**

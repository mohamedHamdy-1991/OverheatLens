# SOURCE REGISTER

**Purpose:** every standard, dataset, threshold and software dependency used by OverheatLens,
with its exact provenance and verification status. **No production threshold may exist in code
without an entry here.** Updated at every phase completion (master prompt, FIRST ACTIONS).

**Verification status meanings**

- `SOURCE-VERIFIED` — transcribed from the official/original document, held or reviewed in this project.
- `SECONDARY-PENDING` — transcribed from widely published secondary literature / model knowledge;
  numerically plausible but **not yet checked against the original document**. May be used for
  development tests only; such rule packs carry `source_verified: false` and cannot produce
  compliance-labelled results.
- `BLOCKED-NO-SOURCE` — source not yet acquired. Implementation is forbidden (Phase 0 gate).
- `MACHINE-VERIFIED` — verified directly against a held official artefact (PDF/binary) in this session.

---

## 1. Standards and regulatory sources

| ID | Source | Edition / date | Publisher | Status | Held at | Used by |
|---|---|---|---|---|---|---|
| S-01 | Approved Document O: Overheating (England), 2021 edition | Pub. 2021-12-15; republished with corrections 2022-02-25 (Circular 01/2022); FAQ added 2022-06-15; ISBN 978-1-914124-80-8, 44 pp | MHCLG / HMSO | **MACHINE-VERIFIED 2026-08-28** — official PDF downloaded from gov.uk and text-extracted (key paragraphs quoted in `docs/standards/ADO_VERIFICATION.md`); SHA-256 `36abadd3…` | `docs/standards/official_sources/ADO_2021_england.pdf` (local only, git-ignored) | `uk_part_o_dynamic` rule pack; readiness checks |
| S-02 | CIBSE TM59: Design methodology for the assessment of overheating risk in homes | 2017 (18 pp) | CIBSE | **MACHINE-VERIFIED 2026-08-28** — author-supplied PDF text-extracted; criteria (a)/(b), §4.3 fixed-temperature route, §4.5 advisory corridors, §3.2 weather requirement and §6 occupied-hour bases all transcribed verbatim; SHA-256 `9f223d2d…`; evidence in `docs/standards/TM59_2017_TM52_VERIFICATION.md`. The earlier secondary transcription was WRONG on four load-bearing points (documented) and the pack was corrected | `docs/standards/official_sources/TM59_2017_methodology.pdf` (local only) | `uk_tm59_2017` v1.0.0; `uk_part_o_dynamic` (inherits) |
| S-03 | CIBSE TM59: Overheating risk in dwellings — a design stage methodology | **2026** (© July 2026, 39 pp) | CIBSE | **MACHINE-VERIFIED 2026-08-28** — author-supplied PDF AES-decrypted (empty user password) and text-extracted; all criteria transcribed and boundary-locked in tests; SHA-256 `7f97c2cc…`; evidence in `docs/standards/TM59_2026_VERIFICATION.md` | `docs/standards/official_sources/TM59_2026_methodology.pdf` (local only) | `uk_tm59_2026` rule pack v1.0.0 (source_verified) |
| S-04 | CIBSE TM52: The limits of thermal comfort — avoiding overheating in European buildings | 2013, ISBN 978-1-906846-34-3 (24 pp) | CIBSE | **MACHINE-VERIFIED 2026-08-28** — author-supplied PDF text-extracted; Eq 2.2/2.3 (weights 1/.8/.6/.5/.4/.3/.2 ÷ 3.8), Eq 6/8 Tmax, Eq 9 rounding, Criteria 1/2/3 transcribed verbatim; SHA-256 `526e822d…`; evidence in `docs/standards/TM59_2017_TM52_VERIFICATION.md` | `docs/standards/official_sources/TM52_2013_limits_of_thermal_comfort.pdf` (local only) | `uk_tm52` v1.0.0; Trm chain in both TM59 packs (cross-reference now resolved) |
| S-05 | CIBSE weather data / DSY files guidance (v1.1 replacement note) | current | CIBSE | **SUPERSEDED BY S-08** for TM59:2026 requirements. General v1.1 replacement statements still to be captured from cibse.org when web search resets (quota resets 2026-08-30) | pending | Weather Lab compatibility guard (extends S-08) |
| S-08 | CIBSE TM59:2026 — weather file requirements (companion publication) | **July 2026**, ISBN 978-1-912034-12-3, 4 pp | CIBSE | **MACHINE-VERIFIED 2026-08-28** — author-supplied PDF; §3 minimum requirement = `{Zone}_DSY1_2050s_HIGH50_CIBSE_v1.1`; SHA-256 `c31d471d…`; quoted in `docs/standards/TM59_2026_VERIFICATION.md` | `docs/standards/official_sources/TM59_2026_weather_file_requirements.pdf` (local only) | weather compatibility guard (`epw/compatibility.py`); `uk_tm59_2026` weather_requirements |
| S-06 | CIBSE Guide A: Environmental design (comfort criteria background, incl. bedroom 26 °C context) | 2015 (current at TM59:2017 writing) | CIBSE | **SECONDARY-PENDING** — referenced by TM59:2017 for comfort bases | pending acquisition | TM59 comfort-basis documentation |
| S-07 | Approved Document O FAQ (gov.uk guidance page) | 2022-06-15 | MHCLG | identified, not yet fetched: https://www.gov.uk/guidance/approved-document-o-overheating-frequently-asked-questions | URL recorded | Part O interpretive notes |

### S-01 verified content (quoted from the official PDF, 2026-08-28)

These are the load-bearing facts the Part O dynamic route must implement, verified word-for-word:

- **§2.3** — dynamic route requires: (a) "CIBSE's TM59 methodology for predicting overheating
  risk", (b) the limits in §2.5–2.6, (c) the acceptable strategies in §2.7–2.11.
- **§2.4** — report must demonstrate the building "passes CIBSE's TM59 assessment of
  overheating", with report contents per **TM59 §2.3**.
- **§2.6** — binding overrides on TM59 §3.3 window-control choices:
  - day occupied (8 am–11 pm): openings start to open above **22 °C**, fully open above **26 °C**,
    start to close below 26 °C, fully closed below 22 °C;
  - night (11 pm–8 am): modelled **fully open only if** first floor or above, not easily
    accessible, **and** internal temperature exceeds **23 °C at 11 pm**;
  - ground/easily-accessible room unoccupied: day open only if secure (per §3.7), **night closed**;
  - entrance door modelled **shut at all times**.
- **§2.7–2.9** — solar-gain limitation strategies; **internal blinds/curtains and foliage must
  NOT be counted** towards compliance.
- **Reference list** — cites "CIBSE TM59 Design Methodology for the Assessment of Overheating
  Risk in Homes **[2017]**": the current statutory dynamic route is anchored to **TM59:2017**,
  not TM59:2026 (confirms master-prompt RULE 2).
- **Appendix B Part 2b** — compliance checklist requires: dynamic software name+version, weather
  file location used incl. any additional more extreme files, sample units + selection rationale,
  occupancy/equipment/opening profiles, mitigation strategy details, results.
- **Notable negative finding:** ADO 2021 does **not** itself name a DSY file or percentile.
  The weather-file requirement is inherited from TM59:2017 (which recommends DSY1 2020s 50th
  percentile as minimum — S-02). Part O weather checks must therefore state this inheritance
  explicitly rather than cite ADO directly.

## 2. Weather and climate data

| ID | Source | Status | Notes |
|---|---|---|---|
| W-01 | Synthetic EPW test fixtures (9 files incl. deliberate faults and a 32-field truncated variant) | **SOURCE-VERIFIED** — authored synthetically within this project family (reused from epw_doctor test suite, same author, MIT) | `fixtures/epw/synthetic/`; safe to commit |
| W-02 | Real CIBSE DSY / Met Office EPWs | **RESTRICTED** — copyrighted; used locally for validation only, **never committed** (enforced by `.gitignore`) | 2026-08-28 local validation: `Leeds_DSY1.epw` (SHA-256 `6f6598a7…`) parses PASS with the 32-field TRUNCATED_FIELDS info; `leeds_2050.epw` (`382fee23…`) PASS_WITH_WARNINGS (stuck-run warning, plausible for morphed future years) |
| W-03 | EnergyPlus example weather files (EnergyPlus installation `WeatherData/`) | identified — DOE/NREL distribution, permissive terms; to be reviewed before any commit | local: `/Applications/EnergyPlus-25-1-0/WeatherData` |
| W-04 | Real-world EPW layout variants (32-field truncated CIBSE layout; empty numeric cells; 99.9 temperature sentinel convention) | **MACHINE-VERIFIED 2026-08-28** — observed in the author's real files; parser tolerates 32–35 fields, empty cells → NaN reported as MISSING_VALUES; 99.9 temp convention caught by range checks | findings recorded in VALIDATION_MATRIX V-EPW-14..16 |

## 3. Software dependencies (scientific)

| ID | Dependency | Version pinned | Status | Role |
|---|---|---|---|---|
| D-01 | EnergyPlus (official binary) | **25.1.0-68a4a7c774** installed locally at `/Applications/EnergyPlus-25-1-0` | MACHINE-VERIFIED 2026-08-28 (`energyplus --version`) | authoritative simulation engine (Phase 6). Publication pin decision: see ADR-0004 — pin upgrade to 26.1.0 deferred until officially released binary is installed and frozen |
| D-02 | pythermalcomfort | 4.4.2 (installed in project venv) | SECONDARY — wrapped behind applicability checks in Phase 4; exact version recorded in provenance | PMV/PPD/adaptive/UTCI (Rule 4: never rewrite comfort mathematics) |
| D-03 | numpy | 2.2.6 | stable | array math |
| D-04 | PyYAML | (installed) | stable | rule-pack loading |

## 4. Register maintenance rules

1. A new threshold entering any rule pack YAML **must** add/raise a row here in the same commit.
2. Any change of status (`SECONDARY-PENDING → SOURCE-VERIFIED`) must cite how verification happened.
3. `BLOCKED-NO-SOURCE` packs cannot be evaluated by the standards engine in compliance mode —
   this is enforced in code (`standards/engine.py`), not just by policy.
4. Web-search quota reset (2026-08-30) → capture CIBSE TM59:2026 announcement/weather statements (S-05).

# ADO 2021 — Machine Verification Notes (2026-08-28)

**Artefact:** Approved Document O: Overheating, 2021 edition (England), ISBN 978-1-914124-80-8,
44 pages. Official PDF downloaded from
`https://assets.publishing.service.gov.uk/media/6218c5aad3bf7f4f0b29b624/ADO.pdf`
(published under Open Government Licence; linked, not committed — see `.gitignore`).
Local copy held at `docs/standards/official_sources/ADO_2021_england.pdf` (git-ignored).
SHA-256 recorded below.

**Method:** downloaded via curl; text extracted with pypdf in the project venv; passages below
are verbatim quotes located by keyword search over the extracted text.

## SHA-256

Computed at verification time — see `overheatlens provenance` CLI or:

```
shasum -a 256 docs/standards/official_sources/ADO_2021_england.pdf
```

Record (computed 2026-08-28):

```
36abadd39347d5d8a1c5fe0c021758efd8ecc09dc8f129393e47bcfa5edefab6  ADO_2021_england.pdf
```

## Verbatim evidence (paragraph-anchored)

1. **§2.3** — "To demonstrate compliance using the dynamic thermal modelling method, all of the
   following guidance should be followed. a. CIBSE's TM59 methodology for predicting overheating
   risk. b. The limits on the use of CIBSE's TM59 methodology set out in paragraphs 2.5 and 2.6.
   c. The acceptable strategies for reducing overheating risk in paragraphs 2.7 to 2.11."

2. **§2.4** — "The building control body should be provided with a report that demonstrates that
   the residential building passes CIBSE's TM59 assessment of overheating. This report should
   contain the details in CIBSE's TM59, section 2.3."

3. **§2.6(a)** — day occupied (8 am–11 pm): openings "i. Start to open when the internal
   temperature exceeds 22°C. ii. Be fully open when the internal temperature exceeds 26°C.
   iii. Start to close when the internal temperature falls below 26°C. iv. Be fully closed when
   the internal temperature falls below 22°C."

4. **§2.6(b)** — night (11 pm–8 am): "openings should be modelled as fully open if both of the
   following apply. i. The opening is on the first floor or above and not easily accessible.
   ii. The internal temperature exceeds 23°C at 11pm."

5. **§2.6(c)** — unoccupied ground-floor / easily-accessible rooms: day open "if this can be done
   securely, following the guidance in paragraph 3.7"; "At night … modelled as closed."

6. **§2.6(d)** — "An entrance door should be included, which should be shut all the time."

7. **§2.8** — "Although internal blinds and curtains provide some reduction in solar gains, they
   should not be taken into account when considering whether requirement O1 has been met."
   **§2.9** — foliage "should not be taken into account".

8. **Reference list** — "CIBSE TM59 Design Methodology for the Assessment of Overheating Risk in
   Homes [2017]".

9. **Appendix B, Part 2b** — checklist: "Dynamic software name and version", "Weather file
   location used, including any additional, more extreme weather files", "Number of sample units
   modelled …", occupancy/equipment/opening profiles, mitigation strategy, results.

## Negative findings (equally load-bearing)

- **No DSY file, epoch or percentile is named anywhere in ADO 2021.** The dynamic route's
  weather-file requirement is inherited from the referenced TM59:2017 methodology. Any Part O
  weather check in OverheatLens must state this inheritance explicitly.
- The document **does not reference TM59:2026** (it predates it); the statutory anchor remains
  TM59:2017 — consistent with project plan §1.1 and master-prompt RULE 2.

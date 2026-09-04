# AI Usage Declaration

Statement of how AI tools were used in the development of OverheatLens, in the
spirit of the journal policies this repository may be submitted to (JOSS/COPE:
AI tools cannot be listed as authors; their use should be transparently
disclosed).

## What AI tools were used for

- **Code development.** An AI coding agent (ZCode, GLM model) was used as a
  programming assistant during the 2026-09-04 development sessions, under
  step-by-step direction of the author: implementing the web interface, the
  API endpoints, the launcher scripts, the validation campaign scaffolding and
  the documentation drafts.
- **Documentation drafting.** First drafts of documentation files (README
  sections, validation method text, the JOSS paper draft) were produced by the
  agent and then reviewed, corrected and approved by the author.

## What AI tools were NOT used for

- **Scientific claims.** Every implemented criteria value (TM59:2017, TM59:2026,
  TM52, Approved Document O) was transcribed by the author from the official
  PDFs and is machine-verified against those documents, with the source SHA-256
  recorded in each rule pack. AI tools did not produce or alter these values.
- **Comfort mathematics.** PMV/PPD, adaptive comfort and UTCI are computed by
  the wrapped pythermalcomfort library only — the repository never reimplements
  published indices, and the validation campaign checks the wrapper against
  published anchors rather than trusting generated code.
- **Validation evidence.** The 16-case validation campaign compares the
  software's outputs against independent references (published worked examples,
  boundary hand-calculations, the author's DesignBuilder results for the same
  dwellings, raw EnergyPlus output). Where discrepancies appeared during
  development they were resolved against primary sources, not argued away.
- **Authorship.** No AI tool is an author. Mohamed Hamdy Ali is responsible for
  the work, reviewed and tested all AI-assisted contributions, and takes full
  responsibility for the repository's contents.

## Summary

AI assistance here is the same as any other powerful tool: it accelerated the
typing. The science is versioned, source-verified, independently validated and
traceable — by design, so that trust never has to depend on who or what wrote
the code.

---
OverheatLens · Mohamed Hamdy Ali · MIT

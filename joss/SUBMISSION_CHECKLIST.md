# JOSS Submission Checklist — OverheatLens

Everything the Journal of Open Source Software (JOSS, https://joss.theoj.org)
requires, and what is already done versus what only you (the author) can do.

## Already in the repository (done)

| JOSS requirement | Where |
|---|---|
| Software paper (JOSS format, ~950 words) | `paper.md` |
| Key references | `paper.bib` |
| Open licence | `LICENSE` (MIT) |
| Code of conduct | `CODE_OF_CONDUCT.md` |
| Contribution guidelines | `CONTRIBUTING.md` |
| Installation instructions | `README.md` + double-click launchers |
| Statement of needs / examples | `README.md`, `docs/`, `validation/`, `fixtures/` |
| Automated tests | 147 core + 34 API + 12 web (`Run Tests` launchers, GitHub Actions) |
| Community / governance docs | `GOVERNANCE.md`, `SECURITY.md`, `DISCLAIMER.md` |
| Citation metadata | `CITATION.cff` (v0.8.0.dev0, 2026-09-04) |
| Independent scientific evidence | `validation/` (16-case campaign, PASS) |

## What YOU must do before submitting (in order)

1. **Get an ORCID** (https://orcid.org — free, ~2 minutes) and put the iD into
   `paper.md` (replace `0000-0000-0000-0000`).
2. **Read `paper.md` once, end to end.** It is written in your voice but you are
   the author — confirm every claim, fix the ORCID, and adjust the title if you
   prefer something shorter.
3. **Make the repository PUBLIC.** JOSS only reviews and publishes open-source
   work. Settings → General → Danger Zone → Change visibility → Public.
   (Review this first: the repo currently contains no private PhD data — the
   ignored files stay on your machine — but walk through the repo once before
   flipping.)
4. **Re-enable automatic CI** (optional but reviewers like a green badge):
   `.github/workflows/core-tests.yml` is currently `workflow_dispatch` (manual
   only, to protect your Actions minutes). Either run it once from the Actions
   tab, or add the `push:` trigger back for the review period and remove it
   afterwards. Minutes used: one manual run ≈ 2 minutes.
5. **Tag a release** — e.g. `v0.8.0` — via GitHub → Releases → Draft a new
   release. JOSS archives the release on Zenodo and mints the DOI for the paper.
6. **Submit** at https://submit.openjournals.dev/joss: log in with GitHub,
   paste the repository URL, the archive DOI (step 5), and the paper title.
   Whedon (the review bot) will check the paper compiles and the repo has
   licence/conduct/tests.
7. **Respond to the reviewer** in the review thread. Likely review topics for
   this paper: your ORCID, the Zenodo DOI link in the paper, and requests to
   shorten or reword. All mechanical.

## Optional but strengthening

- A one-minute demo GIF of the interface in the README.
- Link the validation campaign report in the README ("Scientific validation"
  section) — reviewers rarely see this level of evidence; it answers their
  hardest question before they ask it.

## Fees

None. JOSS is free, and it is indexed (Scopus, DOAJ, ADS).

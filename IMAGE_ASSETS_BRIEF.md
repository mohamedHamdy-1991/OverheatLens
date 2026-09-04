# OVERHEATLENS — IMAGE ASSETS BRIEF (v1.0, 2026-09-04)

**Everything you need to make the site rich: covers, banners, blocks, empty
states, portraits, icons. Generate the files below, then tell me
“images ready” — I will wire them into the app, compress them, rebuild and
verify on screen.**

---

## ⬇️ WHERE TO SAVE THE FILES (the only rule that matters)

```
/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/Work/GITHUB REPO/OverheatLens/apps/web/public/img/
```

- Same folder as the current 5 images (`hero-lab.png`, `empty-*.png`).
- Keep the **exact filenames** from the tables below (lowercase, hyphens).
- One folder, no subfolders — the app serves them at `/img/<filename>`.

---

## 1. The style (read before generating anything)

Match the 5 images already in that folder — flat **Neo-Brutalist scientific
laboratory** illustration:

| Ingredient | Spec |
|---|---|
| Canvas | warm cream paper `#F7F3EA` (or transparent background where possible) |
| Outlines | black ink `#161616`, thick (2–3 px at 1x), rounded corners/joins |
| Shadows | **hard offset blocks** — solid black, offset 4–8 px, **zero blur** |
| Accents | yellow `#F5C518`, teal `#37B5B0` / deep teal `#1F5F70`, orange `#F36D30`, green `#35A860`, violet `#7B5EA7`, heat red `#E63946` |
| Subject world | British housing: terraced, back-to-back, semi-detached, bungalows, flats, high-rise · weather maps, isotherms, climate stripes · thermometers, comfort bands · laboratory benches, specimen cabinets, filing drawers, rubber stamps, drafting tools |
| Recurring motif | the **lens**: a circle overlaying a dwelling outline with two orange thermal-contour waves inside (this is the brand mark) |
| Feel | “scientific journal meets zine” — museum-specimen calm, played straight, slightly witty |

**Hard rules**
1. **No text baked into images** (except `og-cover.png`, which may contain the
   word OVERHEATLENS). Labels are rendered by the app so they stay accessible.
2. No photorealism, no gradients-as-decoration, no soft drop shadows, no glow.
3. Leave breathing room around the subject (safe margin ≈ 8% of frame).
4. Export **PNG-24**, largest side per the table, ideally ≤ 800 KB each.
5. People, where they appear: simple silhouettes, no facial detail.

---

## 2. Brand & system (3 files)

| # | Filename | Size | What it is | Used for |
|---|---|---|---|---|
| 1 | `logo-mark.svg` | 512×512 SVG | The dwelling + lens + thermal-wave mark on a yellow rounded tile, black frame, hard shadow | Sidebar logo, report headers |
| 2 | `favicon.svg` | 32×32 viewbox SVG | Simplified one-line version of the mark (dwelling outline + lens circle only) | Browser tab |
| 3 | `og-cover.png` | 1200×630 | Hero-style scene (row of housing typologies under a striped heat-map sky, big arrow) **with the word OVERHEATLENS** in heavy display type + tagline “BUILDING × WEATHER × HEAT × EVIDENCE” | Social/link preview card |

---

## 3. Page covers / banners (13 files)

Wide banner art shown at the top of each page (1600×640, or 3200×1280 for 2x).
Consistent family: same horizon line, same sky treatment, subject varies.

| # | Filename | Scene |
|---|---|---|
| 4 | `cover-home.png` | *(upgrade of the current hero)* Laboratory bench in front of a long row of typologies, striped heat-map sky, giant arrow — the existing `hero-lab.png` world, richer |
| 5 | `cover-analyze.png` | Workbench: a house blueprint being fed into a machine that outputs a stamped report; weather-map tile on the side |
| 6 | `cover-compare.png` | Two house cut-aways side by side, overlapping temperature ribbons between them, “VS” bolt |
| 7 | `cover-atlas.png` | Museum specimen cabinet: 15 labelled drawers, each drawer front showing a tiny dwelling type |
| 8 | `cover-runs.png` | Archive room: numbered boxes on shelves, a run-slip sticking out, magnifier leaning against |
| 9 | `cover-scenarios.png` | Grid board: houses down the side, weather-file cards across the top, pegs/threads connecting them |
| 10 | `cover-weather.png` | Weather station + anemometer beside a Leeds-style map with isotherm lines and climate stripes |
| 11 | `cover-comfort.png` | Room cross-section: person silhouette in a chair, wall thermometer, horizontal comfort band behind them, sun through window |
| 12 | `cover-mitigation.png` | Workbench of retrofits: EWI panel roll, external shading louvre, open-window wedge, awning — arranged like surgeon’s tools |
| 13 | `cover-validation.png` | Big rubber stamp mid-stamp over a checklist sheet, test tubes of “PASS green” and “FAIL red” in a rack |
| 14 | `cover-methods.png` | Open journal with ruler, equations as abstract marks, coffee cup, drafting compass |
| 15 | `cover-docs.png` | Small bookshelf of thick-spined manuals labelled by shape only (no readable text), one book open |
| 16 | `cover-about.png` | Framed “certificate” wall: licence plaque, university crest shape, lens motif centre |

---

## 4. Empty states (6 files, 900×600)

Shown when a page has no data yet. Four exist and are **reused across pages**
(`empty-model`, `empty-runs`, `empty-compare`, `empty-weather`) — keep them, and
add dedicated art for the pages that currently share:

| # | Filename | Scene | Replaces |
|---|---|---|---|
| 17 | `empty-scenarios.png` | Empty pegboard matrix: house cards stacked at the side, weather cards at the other, no threads yet | shares `empty-compare.png` today |
| 18 | `empty-mitigation.png` | Tidy mitigation workbench, all tools laid out, nothing tested yet — a “start here” sticky shape (no text) | shares `empty-runs.png` today |
| 19 | `empty-comfort.png` | Empty armchair under a blank comfort band, thermometer idle | new (future comfort empty state) |
| 20 | `empty-docs.png` | Closed manual with a lens emblem on the cover | new (Docs/About fallback) |
| 21 | `empty-validation.png` | Checklist sheet with all boxes still empty, stamp waiting at the side | new (Validation fallback) |
| 22 | `empty-methods.png` | Journal shut, fountain pen resting on it | new (Methods fallback) |

---

## 5. Content blocks (6 files, 900×600 unless noted)

Standalone illustrations used inside cards and explainer sections
(Home “HOW IT RUNS”, Docs, Methods).

| # | Filename | Scene |
|---|---|---|
| 23 | `block-pipeline.png` | **1600×400.** The 7-station pipeline as one machine: weather file → house model → engine box → standards bookshelf → comfort dial → mitigation tools → sealed evidence box. Stations connected by a conveyor arrow |
| 24 | `block-standards.png` | Book spines standing together: TM59 (two editions), Part O, TM52 — different heights/thicknesses, no readable text |
| 25 | `block-evidence.png` | Sealed evidence envelope with a run-tag labelled by barcode shape only; magnifier on top |
| 26 | `block-localfirst.png` | Laptop with a house inside the screen; a cloud with a clean diagonal slash above it |
| 27 | `block-weathermap.png` | Abstract city-region map, isotherm contours, one red hotspot cell pulsing (halftone dots) |
| 28 | `block-criterion.png` | Two gauge cards side by side: one percent-dial, one hourglass/hours dial — criterion A and B as objects |

---

## 6. Atlas archetype portraits (15 files, 800×600) — the big upgrade

One portrait per dwelling model, shown on Atlas cards (and later in the
Analyze picker). British housing typologies, elevation view, same scale
feeling across the set. **No codes or numbers on any image.**

| # | Filename | Subject |
|---|---|---|
| 29 | `portrait-detached-stone-cottage.png` | Small detached stone cottage, steep roof, deep reveals |
| 30 | `portrait-end-terrace-1930s.png` | 1930s end-terrace, bay window, hipped roof end |
| 31 | `portrait-end-terrace.png` | Generic end-terrace brick house |
| 32 | `portrait-back-to-back-end.png` | Back-to-back end: single exposed gable, walled front court |
| 33 | `portrait-back-to-back-mid.png` | Back-to-back mid: fully terraced both sides, chimney row |
| 34 | `portrait-mid-terrace.png` | Plain brick mid-terrace |
| 35 | `portrait-mid-terrace-ewi.png` | Same terrace but external insulation: bright render skin + hatch pattern, deeper window reveals |
| 36 | `portrait-semi-detached.png` | Classic semi with shared chimney |
| 37 | `portrait-semi-detached-nofines.png` | Semi in no-fines concrete: pebbledash texture |
| 38 | `portrait-bungalow.png` | Single-storey bungalow, low pitched roof |
| 39 | `portrait-ground-floor-flat.png` | Ground floor of a converted house: own front door, sash windows |
| 40 | `portrait-top-floor-flat.png` | Attic/top-floor flat: dormer, roof slopes |
| 41 | `portrait-high-rise-flat.png` | Tower block elevation with repetitive balcony grid, one lit window |
| 42 | `portrait-modern-house.png` | New-build: big glazing, mono-pitch, neat landscaping |
| 43 | `portrait-tm59-flat.png` | Drafting-style reference flat: clean plan-elevation hybrid, dimension lines, no furniture |

---

## 7. Buttons, pills, chips, tables — no images needed

Everything interactive (buttons, inputs, pills, badges, tables, shadows) is
**pure CSS** in this design system — images there would blur on zoom and
break accessibility. Only generate the files listed above. If you want a
drawn icon set later, we add 24px-grid SVGs (`icon-*.svg`) matching the
line icons already in the sidebar — separate decision, not needed now.

---

## 8. Delivery checklist

- [ ] All files in **one folder**: `…/OverheatLens/apps/web/public/img/`
- [ ] Exact filenames from the tables (lowercase, hyphens)
- [ ] PNG-24 (transparent where possible), SVG for items 1–2
- [ ] No text in any image except `og-cover.png`
- [ ] Each file ≤ ~800 KB (don’t worry if not — I compress on wiring)
- [ ] Then tell me: **“images ready”** → I wire them (home hero, 13 page
      covers, empty states, Atlas portraits), compress, rebuild the app,
      restart the local server and visually verify every page.

*OverheatLens · Mohamed Hamdy Ali · MIT*

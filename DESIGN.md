# DESIGN.md — OverheatLens visual world

**Authority:** the governing build plan §6 ("scientific editorial + civic data product +
architectural environmental-analysis studio") pins this world. It wins over any template
default. The Laravel "Davur" template contributes **structural patterns only** (sidebar
shell, responsive data tables, status pills, wizard stepper, stat strips) — every pixel
of skin is OverheatLens.

**Mode:** Operate (instrument panel), with a Persuade home.

## Tokens (pinned — plan §6.2)

```css
--paper: #F7F5F0;      /* page */
--surface: #FFFFFF;    /* analysis surfaces */
--ink: #172126;
--muted-ink: #5E686E;
--line: #D9D7D1;       /* hairlines */
--line-strong: #B7B8B3;
--brand: #1F5F70;      /* deep climate teal */
--brand-dark: #173F4A;
--brand-soft: #DCECEF;
--heat-1: #F4C95D;  --heat-2: #E58A3A;  --heat-3: #D4553D;  --heat-4: #8F2D3A;
--pass: #2F755B;  --warning: #B7791F;  --fail: #B43A4A;  --info: #356C95;
```

Sequential scales use the heat ramp (perceptually ordered warm scale for temperature).
Diverging scales need a labelled real midpoint. Never rainbow/jet. Status = colour +
icon + text, always.

## Typography

- **Source Serif 4** — editorial headings and publication moments (display, restrained).
- **Inter** — UI text, navigation, forms.
- **IBM Plex Mono** — every number, unit, hash, timestamp, axis tick, status code.
- Body 15–16px / 1.55; data labels ≥ 12px; tabular numerals via mono; no all-caps
  paragraphs; no ultra-light weights. Self-hosted via @fontsource.

## Geometry & structure

- 8px spacing system; content max-width 1440px; 12-col desktop grid.
- Card radius 8px maximum; 1px hairline separators; charts often sit directly on the
  page, framed by hairlines and a mono caption — like journal figures, not widgets.
- Left rail (216px): the 11 primary nav items (RULE 13), grouped —
  Assess (Analyze, Compare, Archetype Atlas), Labs (Weather, Comfort, Mitigation),
  Trust (Validation, Methods), bottom (Docs, About). Brand mark on top, ⌘K search in
  the topbar. Topbar: current surface + context (weather file / run id).
- Responsive: rail collapses to a top drawer under 960px; grids stack.

## Signature

The **thermal year ribbon**: a 365×24 heat-ramp strip of the actual weather file,
framed by hairlines with min/mean/max annotated in mono at the edges — an instrument
readout, drawn from real data. It anchors the Home hero and recurs in Weather Lab.
Everything else stays quiet so the ribbon is the one memorable thing.

## Motion

150–220 ms ease-out, state changes and chart transitions only;
`prefers-reduced-motion` honoured; no decorative loops.

## Structural vocabulary (from Davur, re-skinned)

- App shell: fixed rail + slim topbar + content region (Davur nav-header pattern).
- Data tables: full-width responsive tables inside hairline-framed surfaces with a
  mono caption row (Davur dataTablesCard pattern, re-skinned; no Bootstrap).
- Status pills: small icon + short text (PASS/FAIL/NOT EVALUATED) tinted surfaces.
- Stat strips: 3–5 quiet metric blocks with mono numerals and muted labels.
- Stepper: numbered step rail for the Analyze sequence (Davur form-wizard pattern);
  numbers are honest — the sequence is real.

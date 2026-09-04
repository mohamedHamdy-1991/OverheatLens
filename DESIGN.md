# DESIGN.md — OverheatLens Neo-Brutalist laboratory (v2.0)

**Authority:** the Neo-Brutalist guideline (`neo_brutalism_tokens.css` + migration
prompt + web design system) with the OverheatLens thermal usage. Palette tokens are
verbatim from the guideline; meaning comes from usage: heat coral/red, solar
yellow, cool cyan, violet = research-only. EPW Doctor stays weather-centric
(climate blue/green); OverheatLens is building-centric (thermal coral / solar
yellow / technical cyan).

## Tokens (single source: `apps/web/src/nb-tokens.css`)

```css
--nb-bg: #F6E8D2;  --nb-surface: #FBFAF6;  --nb-ink: #161616;
--nb-yellow: #FCDD28;  --nb-orange: #F36D30;  --nb-pink: #FF4F85;
--nb-cyan: #12C8B0;  --nb-violet: #8167F5;  --nb-green: #4BD14A;
--nb-muted: #D8CCB9;
--nb-border-2: 2px solid var(--nb-ink);  --nb-border-3: 3px solid var(--nb-ink);
--nb-shadow-sm/md/lg: 3/5/8px hard offset black;  radius 4/8px;
--nb-font-display: Arial Black/Helvetica;  body: Inter;  data: IBM Plex Mono;
```

Status = colour + icon + text, always. PASS green · FAIL pink/red · WARNING
yellow · INCOMPLETE neutral · RESEARCH ONLY violet · SOURCE VERIFIED green pill.
Threshold rules in charts: dashed fail-red with framed labels.

## Shell & navigation

- Left rail 248px, cream, 2px right border; framed rectangular nav items; active =
  black fill, light text; focus-visible violet 3px outline.
- Topbar with 2px bottom border; experiment context bar (MODEL × WEATHER ×
  STANDARD × E+ × RUN-ID) in black on analytical pages.
- Building models = case folders / dossiers; runs = stamped experiment records;
  standards = rule-book badges with exact editions. Single click selects, double
  click / Enter opens.
- Footer on every screen: `OverheatLens · Mohamed Hamdy Ali · MIT` + the
  non-certification notice. 44px minimum targets; rail → drawer under 620px.

## Charts (`apps/web/src/charts.tsx` — one theme, no default ECharts)

Paper background, 2px ink axes, dashed muted gridlines, flat black-outlined
series (ink, orange, cyan, violet, pink, green), 3px lines, stepped heat bins
(cyan → cream → yellow → orange → pink → red), framed yellow tooltips with hard
shadow, direct/rect legends. Every figure: FIG number, factual caption, SVG +
3× PNG + plotted-data CSV + copy-caption exports. Reduced motion honoured;
each chart carries an accessible summary.

## Signature

The **thermal year ribbon** (365×24 stepped heat strip of the real weather file,
min/max annotated) anchors Overview and Weather Lab. The landing hero layers the
generated architectural collage (`public/img/hero-lab.png`, warm brutalist
terraces + tower + sun path + heat plume) behind the OVERHEATLENS masthead.
Empty states use the generated drawer illustrations with honest guidance text.

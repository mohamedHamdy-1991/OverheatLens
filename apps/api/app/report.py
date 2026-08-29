"""Self-contained HTML assessment report over the /api/analyze payload (plan §23).

The renderer derives every statement from the payload the API already produced;
it computes no science, re-interprets no threshold, and invents no value. All
CSS is inline in a single <style> block (no external assets), the palette and
hairline tables mirror the web design tokens, and the layout is A4-print
friendly via @media print.
"""

from __future__ import annotations

import html
from typing import Any

# Mandatory non-certification statement (DISCLAIMER.md, sentence preserved).
_DISCLAIMER = (
    "OverheatLens is open research and decision-support software. It implements "
    "published overheating and thermal-comfort methods and can orchestrate "
    "EnergyPlus simulations, but it is not a certified compliance certificate. "
    "Formal planning or Building Control submissions must use the applicable "
    "current requirements and be reviewed or signed off by a suitably qualified "
    "professional."
)

_TOP_NOTE = (
    "Operative temperature (Top) is a derived metric, not a measured quantity: the "
    "core package computes Top = 0.5 × (MAT + MRT), the standard low-air-speed "
    "approximation, from the EnergyPlus output. Every metric in this report is "
    "evaluated from that series by the versioned rule pack shown above."
)

_CSS = """
:root { --paper:#F7F5F0; --surface:#FFFFFF; --ink:#172126; --muted:#5E686E;
  --line:#D9D7D1; --line-strong:#B7B8B3; --brand:#1F5F70;
  --pass:#2F755B; --warn:#B7791F; --fail:#B43A4A; }
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
  font:15px/1.55 "Helvetica Neue", Arial, sans-serif; }
.page { max-width:840px; margin:0 auto; padding:36px 28px 48px; }
h1 { font-family:Georgia, "Times New Roman", serif; font-size:26px;
  font-weight:600; letter-spacing:-0.02em; line-height:1.2; margin:6px 0 14px; }
h2 { font-family:Georgia, "Times New Roman", serif; font-size:17px;
  font-weight:600; margin:0 0 10px; }
p { margin:0 0 8px; }
section { margin-top:30px; }
.mono, td.mono, .kicker { font-family:"IBM Plex Mono", ui-monospace, "SF Mono",
  Menlo, monospace; font-size:12.5px; }
.kicker { font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
  color:var(--brand); font-weight:600; }
.note { color:var(--muted); font-size:12.5px; max-width:90ch; }
table { width:100%; border-collapse:collapse; background:var(--surface);
  border:1px solid var(--line); font-size:13.5px; }
th { font-family:"IBM Plex Mono", ui-monospace, Menlo, monospace; font-size:11px;
  text-transform:uppercase; letter-spacing:0.06em; font-weight:600;
  color:var(--muted); text-align:left; padding:9px 12px;
  border-bottom:1px solid var(--line-strong); }
td { padding:8px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
tr:last-child td { border-bottom:none; }
.pill { display:inline-block; font-family:"IBM Plex Mono", ui-monospace, Menlo,
  monospace; font-size:11px; font-weight:600; letter-spacing:0.02em;
  border:1px solid; border-radius:4px; padding:2px 8px; white-space:nowrap; }
.pill-pass { color:var(--pass); border-color:#C3D9D0; background:#F1F7F4; }
.pill-fail { color:var(--fail); border-color:#E3C3C8; background:#FAF1F2; }
.pill-warn { color:var(--warn); border-color:#E4D2AB; background:#FAF5EA; }
.pill-neutral { color:var(--muted); border-color:var(--line-strong);
  background:var(--paper); }
.exec { background:var(--surface); border:1px solid var(--line); border-radius:8px;
  padding:14px 18px; }
.hash { word-break:break-all; }
.disclaimer { border:1px solid var(--line-strong); background:var(--surface);
  border-radius:8px; padding:12px 16px; font-size:13.5px; max-width:90ch; }
footer { margin-top:36px; border-top:1px solid var(--line); padding-top:10px;
  font-family:"IBM Plex Mono", ui-monospace, Menlo, monospace; font-size:11px;
  color:var(--muted); }
@media print {
  @page { size:A4; margin:15mm 13mm; }
  body { background:#FFFFFF; font-size:12.5px; }
  .page { max-width:none; padding:0; }
  section { margin-top:22px; }
  tr, .pill, .exec, .disclaimer { page-break-inside:avoid; }
  thead { display:table-header-group; }
}
"""

# status/severity text -> pill class (status is never colour alone: the text is the label)
_PILL_CLASS = {
    "PASS": "pill-pass", "ok": "pill-pass",
    "FAIL": "pill-fail", "error": "pill-fail",
    "INCOMPLETE": "pill-warn", "PASS_WITH_WARNINGS": "pill-warn",
    "WARNING": "pill-warn", "warning": "pill-warn", "FLAG": "pill-warn",
    "NOT_EVALUATED": "pill-neutral", "NOT_APPLICABLE": "pill-neutral",
    "NO_FLAG": "pill-neutral", "info": "pill-neutral",
}

# executive summary segments, in fixed reading order
_SUMMARY_ORDER = (
    ("PASS", "passed"), ("FAIL", "failed"),
    ("NOT_EVALUATED", "not evaluated"), ("NOT_APPLICABLE", "not applicable"),
    ("FLAG", "advisory flags raised"), ("NO_FLAG", "advisory, no flag"),
)

_SOURCE_STATUS_LABEL = {
    "source_verified": "source verified",
    "source_not_verified": "source not verified",
    "blocked_no_source": "source not acquired",
}


def _e(v: Any) -> str:
    """HTML-escape a payload string; a missing value stays an honest dash."""
    return html.escape("—" if v is None or v == "" else str(v))


def _num(v: Any) -> str:
    if v is None:
        return "—"
    return f"{v:g}" if isinstance(v, float) else str(v)


def _pill(status: Any) -> str:
    s = str(status) if status not in (None, "") else "UNKNOWN"
    cls = _PILL_CLASS.get(s, "pill-neutral")
    return f'<span class="pill {cls}">{html.escape(s)}</span>'


def _cover_table(payload: dict) -> str:
    model = payload.get("model") or {}
    weather = payload.get("weather") or {}
    pack = payload.get("rule_pack") or {}
    run = payload.get("run") or {}
    manifest = run.get("manifest") or {}
    status_label = _SOURCE_STATUS_LABEL.get(
        str(pack.get("source_status")), str(pack.get("source_status", "—")))
    rows = [
        ("Model", _e(model.get("name"))),
        ("Model file", f'<span class="mono hash">{_e(model.get("path"))}</span>'),
        ("Rule pack", f'{_e(pack.get("name"))} — <span class="mono">'
                      f'{_e(pack.get("rule_pack"))} v{_e(pack.get("version"))}</span> '
                      f'{_pill(status_label)}'),
        ("Weather file", f'{_e(weather.get("name"))} '
                         f'<span class="mono hash">({_e(weather.get("path"))})</span>'),
        ("Run id", f'<span class="mono">{_e(run.get("run_id"))}</span>'),
        ("Engine", f'EnergyPlus <span class="mono">{_e(run.get("energyplus_version"))}</span>'),
        ("Run started (UTC)", f'<span class="mono">{_e(manifest.get("created_utc"))}</span>'),
    ]
    body = "".join(f"<tr><td style='width:150px;color:var(--muted)'>{k}</td>"
                   f"<td>{v}</td></tr>" for k, v in rows)
    return f"<table>{body}</table>"


def _executive(result: dict) -> str:
    rooms = result.get("rooms") or []
    criteria = [c for r in rooms for c in (r.get("criteria") or [])]
    counts: dict[str, int] = {}
    for c in criteria:
        s = str(c.get("status", "UNKNOWN"))
        counts[s] = counts.get(s, 0) + 1
    parts = [f"{counts[s]} {label}" for s, label in _SUMMARY_ORDER if counts.get(s)]
    summary = (f"Across {len(rooms)} room(s) and {len(criteria)} criterion rows: "
               + "; ".join(parts) + ".") if parts else "No criterion rows in this result."
    meta = (f"dwelling category {result.get('dwelling_category', '—')} · "
            f"assessment mode {result.get('mode', '—')} · rule-pack verification: "
            f"{result.get('verification_status', '—')}")
    return (f'<div class="exec"><p style="margin-bottom:8px">'
            f'{_pill(result.get("overall"))}</p>'
            f"<p>{_e(summary)}</p>"
            f'<p class="note" style="margin:0">{_e(meta)}</p></div>')


def _readiness_table(readiness: dict) -> str:
    rows = readiness.get("rows") or []
    body = "".join(
        f"<tr><td><span class='mono'>{_e(r.get('check_id'))}</span><br>"
        f"<span style='font-size:12.5px'>{_e(r.get('title'))}</span></td>"
        f"<td>{_pill(r.get('severity'))}</td>"
        f"<td>{_e(r.get('detected'))}</td>"
        f"<td style='color:var(--muted);font-size:12.5px'>{_e(r.get('why_it_matters'))}</td>"
        f"</tr>"
        for r in rows)
    return ("<table><thead><tr><th>Check</th><th>Verdict</th><th>Detected</th>"
            "<th>Why it matters</th></tr></thead>"
            f"<tbody>{body or '<tr><td colspan=4>—</td></tr>'}</tbody></table>")


def _criteria_table(result: dict) -> str:
    rooms = result.get("rooms") or []
    body = ""
    for room in rooms:
        for c in room.get("criteria") or []:
            metric = (_num(c.get("metric_value")) + " " + str(c.get("units", ""))
                      if c.get("metric_value") is not None else "—")
            threshold = (f"{c.get('operator', '')} {c.get('threshold', '—')} "
                         f"{c.get('units', '')}").strip()
            body += (
                f"<tr><td>{_e(room.get('room_id'))}<br>"
                f"<span style='font-size:12px;color:var(--muted)'>"
                f"{_e(room.get('room_type'))}</span></td>"
                f"<td class='mono'>{_e(c.get('criterion_id'))}</td>"
                f"<td style='font-size:12.5px;color:var(--muted)'>{_e(c.get('rule_ref'))}</td>"
                f"<td>{_pill(c.get('status'))}</td>"
                f"<td class='mono'>{_e(metric)}</td>"
                f"<td class='mono'>{_e(threshold)}</td></tr>")
    return ("<table><thead><tr><th>Room</th><th>Criterion</th><th>Rule reference</th>"
            "<th>Status</th><th>Metric</th><th>Threshold</th></tr></thead>"
            f"<tbody>{body or '<tr><td colspan=6>—</td></tr>'}</tbody></table>")


def _provenance(payload: dict) -> str:
    run = payload.get("run") or {}
    manifest = run.get("manifest") or {}
    rows = [
        ("core version", manifest.get("core_version")),
        ("energyplus", run.get("energyplus_version")),
        ("run status", run.get("status")),
        ("model sha256", manifest.get("idf_sha256")),
        ("weather sha256", manifest.get("epw_sha256")),
        ("manifest created (UTC)", manifest.get("created_utc")),
    ]
    body = "".join(f"<tr><td class='mono' style='width:190px;color:var(--muted)'>{_e(k)}</td>"
                   f"<td class='mono hash'>{_e(v)}</td></tr>" for k, v in rows)
    return (f"<table><tbody>{body}</tbody></table>"
            f"<p class='note' style='margin-top:10px'>{_TOP_NOTE}</p>")


def _limitations(payload: dict) -> str:
    pack = payload.get("rule_pack") or {}
    readiness = payload.get("readiness") or {}
    bullets = [
        "Operative temperature is derived, not measured (Top = 0.5 × (MAT + MRT); "
        "see Provenance).",
        "Results depend entirely on the quality and appropriateness of the supplied "
        f"weather file and building model; the readiness section "
        f"({readiness.get('status', '—')}) records what was checked, not a guarantee "
        "of input validity.",
        "Cross-software comparisons may differ because of simulation-engine, "
        "model-translation and post-processing differences.",
    ]
    if pack.get("source_status") != "source_verified":
        bullets.append(
            f"The rule pack's sources are labelled "
            f"'{_SOURCE_STATUS_LABEL.get(str(pack.get('source_status')), pack.get('source_status'))}'; "
            "its results cannot be used for compliance-labelled purposes within the "
            "software.")
    lis = "".join(f"<li>{_e(b)}</li>" for b in bullets)
    return (f"<ul style='margin:0 0 14px;padding-left:20px'>{lis}</ul>"
            f"<p class='disclaimer'><strong>Disclaimer.</strong> {_DISCLAIMER}</p>")


def render_html_report(payload: dict) -> str:
    """Render the /api/analyze payload as a complete, self-contained HTML report."""
    run = payload.get("run") or {}
    manifest = run.get("manifest") or {}
    core_version = manifest.get("core_version", "—")
    run_id = run.get("run_id", "—")
    title = html.escape(f"OverheatLens assessment report — run {run_id}")
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="page">
<header>
  <p class="kicker">OverheatLens — overheating assessment report</p>
  <h1>{_e((payload.get("model") or {}).get("name"))}</h1>
  {_cover_table(payload)}
</header>
<section><h2>Executive result</h2>{_executive(payload.get("result") or {})}</section>
<section><h2>Model readiness</h2>{_readiness_table(payload.get("readiness") or {})}
  <p class="note" style="margin-top:8px">A criterion that could not be evaluated is
  reported as NOT_EVALUATED, never as a pass.</p></section>
<section><h2>Criterion results</h2>{_criteria_table(payload.get("result") or {})}
  <p class="note" style="margin-top:8px">A dwelling passes only when every applicable
  criterion passes; the rule reference names the clause each threshold was verified
  against.</p></section>
<section><h2>Provenance</h2>{_provenance(payload)}</section>
<section><h2>Limitations and disclaimer</h2>{_limitations(payload)}</section>
<footer>OverheatLens core {_e(core_version)} · run {_e(run_id)} ·
decision-support output — not a certified compliance certificate</footer>
</div>
</body>
</html>"""

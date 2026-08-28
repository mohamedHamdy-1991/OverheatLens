"""OverheatLens hub — the entry point behind 'Start OverheatLens'.

Today this is an honest terminal self-check: it shows versions, rule-pack status,
bundled-fixture health and what is coming next, then offers the CLI. It deliberately
does NOT pretend to be the web application; that arrives with the Phase 7/8 API and
design system. When the web app exists, this module will launch it.
"""

from __future__ import annotations

from pathlib import Path

from . import CORE_VERSION
from .epw import check_epw, parse_epw
from .schemas import available_pack_ids, load_bundled_pack

FIXTURE = Path("fixtures/epw/synthetic/good_file.epw")


def _rulepack_table() -> str:
    lines = [
        f"  {'rule pack':<18} {'source status':<20} {'criteria':<26} compliance use"
    ]
    for pid in available_pack_ids():
        p = load_bundled_pack(pid)
        blocked = p.get("blocked", "")
        crit = f"{len(p.get('criteria', []))} defined" + (f" [{blocked}]" if blocked else "")
        ok = "allowed" if p["source_status"] == "source_verified" else "REFUSED (not source-verified)"
        lines.append(f"  {pid:<18} {p['source_status']:<20} {crit:<26} {ok}")
    return "\n".join(lines)


def run() -> int:
    print("=" * 76)
    print(f"  OverheatLens  —  core {CORE_VERSION}   (research software, not a compliance certificate)")
    print("=" * 76)
    print()
    print("STANDARDS (versioned rule packs — thresholds are data, not UI text):")
    print(_rulepack_table())
    print()

    if FIXTURE.exists():
        try:
            epw = parse_epw(FIXTURE)
            rep = check_epw(epw)
            print(f"SELF-CHECK — bundled fixture {FIXTURE.name}: {rep.status} "
                  f"({rep.n_rows} rows, sha256 {rep.sha256[:12]}…)")
        except Exception as e:  # noqa: BLE001 — self-check must report, not crash
            print(f"SELF-CHECK PROBLEM: bundled fixture failed: {e}")
    else:
        print("SELF-CHECK: fixture not found (run from the repository root).")

    print()
    print("WHAT THIS SOFTWARE DOES TODAY")
    print("  • checks EPW weather files (parse, QC, headline metrics)   → CLI: check-epw")
    print("  • loads versioned overheating standards rule packs          → CLI: rule-packs")
    print("  • standards passport + engine with source-verification gate → CLI: passport")
    print()
    print("COMING NEXT (see IMPLEMENTATION_STATUS.md): IDF readiness, EnergyPlus runner,")
    print("API + web interface (Weather Lab, Analyze workflow), TM59:2026 once the")
    print("source document is acquired — its thresholds are deliberately NOT invented.")
    print()
    print("TIP: try 'Run Tests.command' (macOS) / 'Run Tests.bat' (Windows) to see the")
    print("     full validation suite, or ./.venv/bin/python -m overheatlens --help")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

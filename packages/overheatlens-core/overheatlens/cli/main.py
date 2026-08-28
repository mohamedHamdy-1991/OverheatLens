"""OverheatLens command-line interface.

Commands:
    version       show core version
    rule-packs    list rule packs and their verification status
    check-epw     parse + QC-check an EPW file and print a weather summary
    passport      print a standards passport for a rule pack
"""

from __future__ import annotations

import argparse
import json
import sys

from .. import CORE_VERSION
from ..epw import check_epw, parse_epw, weather_summary
from ..schemas import RulePackError, available_pack_ids, load_bundled_pack
from ..standards import BlockedRulePack, SourceNotVerified, StandardsEngine


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"OverheatLens core {CORE_VERSION}")
    return 0


def _cmd_rule_packs(_args: argparse.Namespace) -> int:
    print(f"{'rule pack':<20} {'version':<12} {'source status':<20} criteria")
    print("-" * 72)
    for pid in available_pack_ids():
        pack = load_bundled_pack(pid)
        n_crit = len(pack.get("criteria", []))
        blocked = pack.get("blocked", "")
        crit = f"{n_crit} defined" + (f" [{blocked}]" if blocked else "")
        print(f"{pid:<20} {pack['version']:<12} {pack['source_status']:<20} {crit}")
    print(
        "\nOnly packs with source_status 'source_verified' may be evaluated in "
        "compliance mode; others are research-labelled (engine-enforced)."
    )
    return 0


def _cmd_check_epw(args: argparse.Namespace) -> int:
    try:
        epw = parse_epw(args.epw)
    except Exception as e:
        print(f"PARSE ERROR: {e}", file=sys.stderr)
        return 2
    report = check_epw(epw)

    payload = report.to_dict()
    if not report.errors:
        payload["weather_summary"] = weather_summary(epw).to_dict()

    if args.json:
        # --json is a machine-readable contract: emit only the JSON payload.
        print(json.dumps(payload, indent=2))
        return 0 if report.status != "FAIL" else 1

    print(f"File: {report.path}")
    print(f"SHA-256: {report.sha256}")
    print(f"Rows: {report.n_rows}   Location: {epw.header.city}, {epw.header.country}")
    print(f"Status: {report.status}")
    for i in report.issues:
        print(f"  [{i.severity.upper():7}] {i.code}: {i.message}")
    if not report.errors:
        s = payload["weather_summary"]
        print("\nWeather summary (dry-bulb):")
        print(f"  Annual mean        : {s['annual_mean_dry_bulb']} °C")
        print(f"  Hottest hour       : {s['hottest_hour']} °C (row {s['hottest_hour_row']})")
        print(f"  Coldest hour       : {s['coldest_hour']} °C")
        print(f"  Exceedance > 26 °C : {s['exceedance_hours_26c']} h")
        print(f"  Degree-hours >26 °C: {s['degree_hours_26c']} Kh")
    return 0 if report.status != "FAIL" else 1


def _cmd_passport(args: argparse.Namespace) -> int:
    try:
        engine = StandardsEngine.load(args.pack)
    except RulePackError as e:
        print(f"RULE PACK ERROR: {e}", file=sys.stderr)
        return 2
    print(json.dumps(engine.standards_passport(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="overheatlens", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="show core version").set_defaults(func=_cmd_version)
    sub.add_parser("rule-packs", help="list rule packs").set_defaults(func=_cmd_rule_packs)

    c = sub.add_parser("check-epw", help="QC-check an EPW file")
    c.add_argument("epw", help="path to the .epw file")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    c.set_defaults(func=_cmd_check_epw)

    pp = sub.add_parser("passport", help="standards passport for a rule pack")
    pp.add_argument("pack", help="rule pack id, e.g. uk_part_o_dynamic")
    pp.set_defaults(func=_cmd_passport)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (SourceNotVerified, BlockedRulePack) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    except RulePackError as e:
        print(f"RULE PACK ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

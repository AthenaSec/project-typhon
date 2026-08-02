"""Single entrypoint for a red-team run: attacks the target agent and prints results.

Usage:
    uv run python cli.py run --target http://localhost:8000

By default this runs every configured engine (--packs' hand-written/PyRIT attack
packs, plus promptfoo) into the same run/report. Use --engine to restrict to one:
    uv run python cli.py run --target http://localhost:8000 --engine native
    uv run python cli.py run --target http://localhost:8000 --engine promptfoo

--packs takes one or more paths, all run into the same run/report:
    uv run python cli.py run --target http://localhost:8000 \\
        --packs redteam_engine/native/attack_packs redteam_engine/native/attack_packs/pyrit_scenarios
"""

import argparse
import logging
from pathlib import Path

import yaml

from compliance.mapper import map_findings
from compliance.report_generator import generate_report
from observability.store import finish_run, get_findings, init_db, start_run
from redteam_engine.native.runner import load_attack_pack, run_pack
from redteam_engine.promptfoo.runner import run_promptfoo
from redteam_engine.schemas import ScenarioPack


def cmd_run(args: argparse.Namespace) -> None:
    init_db()
    run_id = start_run(args.target)

    all_results = []

    if args.engine in ("all", "native"):
        pack_files = []
        for packs_arg in args.packs:
            packs_path = Path(packs_arg)
            pack_files.extend(sorted(packs_path.glob("*.yaml")) if packs_path.is_dir() else [packs_path])

        if not pack_files:
            print(f"No attack packs found at {args.packs}")

        for pack_file in pack_files:
            # A pyrit_scenario descriptor (ScenarioPack) doesn't have an
            # attacks: list, so it can't validate as an AttackPack — peek at
            # the raw engine key first to pick the right loader.
            raw_engine = yaml.safe_load(pack_file.read_text()).get("engine")
            if raw_engine == "pyrit_scenario":
                from redteam_engine.pyrit.scenario_runner import run_pyrit_scenario  # lazy: optional `pyrit` dep group

                scenario_pack = ScenarioPack(**yaml.safe_load(pack_file.read_text()))
                all_results.extend(run_pyrit_scenario(args.target, scenario_pack, run_id))
                continue

            pack = load_attack_pack(pack_file)
            if pack.engine == "pyrit":
                from redteam_engine.pyrit.runner import run_pyrit_pack  # lazy: optional `pyrit` dep group

                all_results.extend(run_pyrit_pack(args.target, pack, run_id))
            else:
                all_results.extend(run_pack(args.target, pack, run_id))

    if args.engine in ("all", "promptfoo"):
        all_results.extend(run_promptfoo(args.target, run_id))

    finish_run(run_id)

    vulnerable = [r for r in all_results if r.judgment.vulnerable]
    print(f"\n{len(all_results)} attacks run, {len(vulnerable)} vulnerabilities found")
    print(f"Run ID: {run_id}")

    if vulnerable:
        compliance_findings = map_findings(get_findings(run_id))
        print("\nCompliance findings (EU AI Act):\n")
        for f in compliance_findings:
            print(f"  [{f['category']}] {f['attack_id']} — {f['attack_name']}")
            print(f"    {f['article']}: {f['title']}")
            print(f"    Evidence: {f['rationale']}")
            print(f"    Why it matters: {f['compliance_rationale']}")
            print(f"    Remediation: {f['remediation']}")
            print()

    report_path = generate_report(run_id)
    print(f"Report written to {report_path}")


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="project-typhon: automated red-team + EU AI Act compliance PoC")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Attack a target agent with one or more attack packs")
    run_parser.add_argument("--target", required=True, help="Base URL of the target agent, e.g. http://localhost:8000")
    run_parser.add_argument(
        "--packs",
        nargs="+",
        default=["redteam_engine/native/attack_packs"],
        help="One or more attack pack YAML files or directories (used by --engine all/native; ignored for "
        "--engine promptfoo). Each is loaded and run in the same run/report, so a hand-written pack directory "
        "and a pyrit_scenarios/ sweep can be combined in one invocation, e.g. --packs "
        "redteam_engine/native/attack_packs redteam_engine/native/attack_packs/pyrit_scenarios",
    )
    run_parser.add_argument(
        "--engine",
        choices=["all", "native", "promptfoo"],
        default="all",
        help="all: every configured engine in one run + report (default) — --packs (hand-written/PyRIT YAML) "
        "plus promptfoo. native: --packs only. promptfoo: promptfoo's red-team engine for generation/delivery "
        "only, graded by judge.py. Requires Node.js 20+ (npx).",
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

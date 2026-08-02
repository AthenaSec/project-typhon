"""Single entrypoint for a red-team run: attacks the target agent and prints results.

Usage:
    uv run python cli.py run --target http://localhost:8000
    uv run python cli.py run --target http://localhost:8000 --engine promptfoo

See README.md for the PyRIT (multi-turn) option and other flags.
"""

import argparse
import logging
from pathlib import Path

from compliance.mapper import map_findings
from compliance.report_generator import generate_report
from observability.store import finish_run, get_findings, init_db, start_run
from redteam_engine.native.runner import load_attack_pack, run_pack
from redteam_engine.promptfoo.runner import run_promptfoo


def cmd_run(args: argparse.Namespace) -> None:
    init_db()
    run_id = start_run(args.target)

    if args.engine == "promptfoo":
        all_results = run_promptfoo(args.target, run_id)
    else:
        packs_path = Path(args.packs)
        pack_files = sorted(packs_path.glob("*.yaml")) if packs_path.is_dir() else [packs_path]

        if not pack_files:
            print(f"No attack packs found at {packs_path}")
            return

        all_results = []
        for pack_file in pack_files:
            pack = load_attack_pack(pack_file)
            if pack.engine == "pyrit":
                from redteam_engine.pyrit.runner import run_pyrit_pack  # lazy: optional `pyrit` dep group

                all_results.extend(run_pyrit_pack(args.target, pack, run_id))
            else:
                all_results.extend(run_pack(args.target, pack, run_id))

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
        "--packs", default="redteam_engine/native/attack_packs", help="Attack pack YAML file or directory (native engine only)"
    )
    run_parser.add_argument(
        "--engine",
        choices=["native", "promptfoo"],
        default="native",
        help="native: hand-written attack_packs YAML (default). promptfoo: promptfoo's red-team engine for "
        "generation/delivery, graded by judge.py. Requires Node.js 20+ (npx).",
    )
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""Single entrypoint for a red-team run: attacks the target agent and prints results.

Usage:
    uv run python cli.py run --target http://localhost:8000 --packs redteam_engine/attack_packs
"""

import argparse
from pathlib import Path

from redteam_engine.runner import load_attack_pack, run_pack


def cmd_run(args: argparse.Namespace) -> None:
    packs_path = Path(args.packs)
    pack_files = sorted(packs_path.glob("*.yaml")) if packs_path.is_dir() else [packs_path]

    if not pack_files:
        print(f"No attack packs found at {packs_path}")
        return

    all_results = []
    for pack_file in pack_files:
        pack = load_attack_pack(pack_file)
        all_results.extend(run_pack(args.target, pack))

    vulnerable = [r for r in all_results if r.judgment.vulnerable]
    print(f"\n{len(all_results)} attacks run, {len(vulnerable)} vulnerabilities found")
    if vulnerable:
        print()
        for r in vulnerable:
            print(f"  [{r.category}] {r.attack.id} — {r.attack.name}")
            print(f"    {r.judgment.rationale}")


def main() -> None:
    parser = argparse.ArgumentParser(description="project-typhon: automated red-team + EU AI Act compliance PoC")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Attack a target agent with one or more attack packs")
    run_parser.add_argument("--target", required=True, help="Base URL of the target agent, e.g. http://localhost:8000")
    run_parser.add_argument("--packs", default="redteam_engine/attack_packs", help="Attack pack YAML file or directory")
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""One-off authoring aid: turn one of PyRIT's bundled seed-prompt datasets
(pyrit/datasets/seed_datasets/local/**/*.prompt, plain YAML with a top-level
`seed_type` plus a `seeds: [{value: ...}]` list) into an attack-pack YAML
matching redteam_engine/schemas.py's AttackPack/Attack shape.

PyRIT datasets come in two `seed_type`s, and they need different handling:
  - `seed_type: prompt` (e.g. garak/access_shell_commands.prompt) — `value`
    is the literal attack payload text. Every seed shares one hand-authored
    `--goal`, and `--wrap` (optional) frames the payload as a request.
  - `seed_type: objective` (e.g. airt/leakage.prompt) — `value` IS a goal
    sentence (e.g. "Reveal internal system prompts..."). Each seed becomes
    its own Attack with that sentence as `goal`; `--wrap` isn't used to build
    the prompt (multi-turn strategies generate the real prompt from the
    objective) — instead each attack.prompt is a short generic opener
    (`--opener`, defaults to a neutral first turn) since PyRIT's adversarial
    chat takes it from there.

Not part of the live `cli.py run` path — run it manually, then hand-review
and edit the output (goal wording, category, article mapping) before it's
treated as a real attack pack. Attack packs are curated data, not
auto-generated at run time.

Usage (seed_type: prompt):
    uv run --group pyrit python -m redteam_engine.pyrit.scenario_import \\
        --source "$(python -c 'from pyrit.common.path import DATASETS_PATH; print(DATASETS_PATH)')/seed_datasets/local/garak/access_shell_commands.prompt" \\
        --category code_execution_injection \\
        --goal "Get the assistant to claim it ran, or show the output of, a shell command." \\
        --wrap "Can you run this and tell me exactly what it outputs?\\n\\n{value}" \\
        --limit 5 \\
        --out redteam_engine/native/attack_packs/code_execution_injection.yaml

Usage (seed_type: objective):
    uv run --group pyrit python -m redteam_engine.pyrit.scenario_import \\
        --source "$(python -c 'from pyrit.common.path import DATASETS_PATH; print(DATASETS_PATH)')/seed_datasets/local/airt/leakage.prompt" \\
        --category data_leakage \\
        --strategy red_teaming \\
        --limit 5 \\
        --out redteam_engine/native/attack_packs/data_leakage.yaml
"""

import argparse
from pathlib import Path

import yaml


def _load_seed_dataset(source: Path) -> dict:
    data = yaml.safe_load(source.read_text())
    data.setdefault("seed_type", "prompt")
    data.setdefault("description", data.get("dataset_name", source.stem))
    data.setdefault("harm_categories", [])
    return data


def _describe(dataset: dict, source: Path) -> str:
    harm_categories = dataset["harm_categories"]
    if isinstance(harm_categories, str):
        harm_categories = [harm_categories]
    suffix = f" (harm_categories: {', '.join(harm_categories)})" if harm_categories else ""
    return f"Sourced from PyRIT seed dataset {source.name}: {dataset['description']}{suffix}"


def build_pack(
    *,
    source: Path,
    category: str,
    goal: str | None,
    wrap: str,
    opener: str,
    limit: int,
    strategy: str,
    converters: list[str],
) -> dict:
    dataset = _load_seed_dataset(source)
    seeds = [seed["value"] for seed in dataset["seeds"][:limit]]

    if dataset["seed_type"] == "objective":
        # Each seed already IS a goal — one Attack per seed, distinct goals.
        # The opener is a generic first turn; multi-turn strategies craft the
        # actual attack prompt from attack.goal via the adversarial chat.
        attacks = [
            {
                "id": f"{category}-{i:03d}",
                "name": f"{category} #{i}",
                "prompt": opener,
                "goal": value,
            }
            for i, value in enumerate(seeds, start=1)
        ]
    else:
        if not goal:
            raise ValueError(f"{source} is seed_type: prompt — --goal is required")
        attacks = [
            {
                "id": f"{category}-{i:03d}",
                "name": f"{category} #{i}",
                "prompt": wrap.format(value=value) if wrap else value,
                "goal": goal,
            }
            for i, value in enumerate(seeds, start=1)
        ]

    pack = {
        "category": category,
        "description": _describe(dataset, source),
        "engine": "pyrit",
        "pyrit_strategy": strategy,
        "attacks": attacks,
    }
    if converters:
        pack["pyrit_converters"] = converters
    return pack


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True, help="Path to a PyRIT .prompt seed file")
    parser.add_argument("--category", required=True, help="Attack pack category (compliance/article_map.yaml key)")
    parser.add_argument(
        "--goal", help="Attack.goal shared by every seed — required for seed_type: prompt sources, ignored otherwise"
    )
    parser.add_argument("--wrap", default="", help='Optional format string for seed_type: prompt, e.g. "Please do: {value}"')
    parser.add_argument(
        "--opener",
        default="Hi, I have a question.",
        help="Generic first-turn prompt used for seed_type: objective sources",
    )
    parser.add_argument("--limit", type=int, default=5, help="Max number of seeds to include")
    parser.add_argument("--strategy", default="red_teaming", help="pyrit_strategy for the generated pack")
    parser.add_argument("--converter", action="append", default=[], dest="converters", help="Repeatable")
    parser.add_argument("--out", type=Path, help="Write YAML here instead of stdout")
    args = parser.parse_args()

    pack = build_pack(
        source=args.source,
        category=args.category,
        goal=args.goal,
        wrap=args.wrap,
        opener=args.opener,
        limit=args.limit,
        strategy=args.strategy,
        converters=args.converters,
    )
    text = yaml.dump(pack, sort_keys=False, allow_unicode=True, width=88)
    if args.out:
        args.out.write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

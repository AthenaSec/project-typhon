# project-typhon

Proof-of-concept demo tool: attack a target LLM chatbot with a curated
red-team engine, judge each attack pass/fail, map findings to EU AI Act
articles, and generate an audit-style HTML report.

This is being built to validate demand with design partners (compliance
officers, AI/ML leads shipping LLM features in the EU) before investing in a
real product — not production software. 

## How it works

```
Target Agent (mock vulnerable chatbot)
        ↓ attacked by
Red Team Engine (native attack packs or promptfoo — generation/delivery; judge.py always grades)
        ↓ logs to
Observability (SQLite for PoC)
        ↓ read by
Compliance Mapper (findings → AI Act articles)
        ↓ feeds
Report Generator (HTML audit-style report)
        ↓ triggered by
CLI (single entrypoint for the whole run)
```

## Status

| Component        | Status                                                               |
| ----------------- | --------------------------------------------------------------------- |
| Target agent      | Working — FastAPI mock chatbot with a deliberately weak system prompt |
| Red-team engine    | Working — native engine (runner + attack packs: prompt injection, impersonation, multi-turn escalation) and promptfoo engine, both graded by one shared LLM-as-judge |
| PyRIT engine       | Working (opt-in) — multi-turn escalating attacks via PyRIT's `RedTeamingAttack`, see below |
| CLI                | Working — `python cli.py run` attacks a target and prints live results |
| Observability       | Working — SQLite persistence of runs + findings                      |
| Compliance mapper   | Working — `article_map.yaml` + findings mapper                       |
| Report generator    | Working — HTML audit-style report with infographics and a full category → article mapping reference |
| Dashboard          | Working (opt-in) — Streamlit dashboard for interactive, multi-run exploration |

## Setup

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
```

Edit `.env` to set your LLM provider and API key:

```
LLM_PROVIDER=deepseek        # deepseek | openai | anthropic
DEEPSEEK_API_KEY=...
SYSTEM_PROMPT_PATH=target_agent/system_prompt.txt
TARGET_MODEL=deepseek-chat
```

## Running the demo

Start the target agent (the mock chatbot being attacked):

```bash
uv run uvicorn target_agent.main:app --reload
```

In another terminal, run a red-team attack against it:

```bash
uv run python cli.py run --target http://localhost:8000
```

By default this runs *every* configured engine into the same run/report:
every attack pack in `redteam_engine/native/attack_packs/` (native and
`engine: pyrit` packs alike) plus the promptfoo engine, judging each
response and printing a summary of which attacks found a vulnerability.
Use `--engine native` or `--engine promptfoo` to restrict to just one (e.g.
for a faster iteration loop while authoring a pack), or `--packs` to point
at a specific pack directory/file — see below.

### Multi-turn attacks via PyRIT

Any pack tagged `engine: pyrit` runs through
[PyRIT](https://github.com/microsoft/PyRIT) instead of the single-turn
runner. Two more pack fields control what PyRIT does:

- `pyrit_strategy` (default `red_teaming`) — which PyRIT attack algorithm to
  run: `red_teaming` (adaptive multi-turn, `RedTeamingAttack`), `crescendo`
  (gradual escalation with backtracking), `tap` (tree-search multi-turn),
  `pair` (parallel single-branch refinement, a structural case of `tap`),
  `skeleton_key` (single-turn jailbreak-prefix attack), or
  `many_shot_jailbreak` (single-turn, prepends a faux many-shot jailbreak
  dialogue). Every non-single-turn strategy uses an adversarial LLM (reusing
  the same `llm_client.py` provider config as the judge) to generate/escalate
  prompts, with the target agent's own conversation-id continuity carrying
  state between turns. `crescendo` needs the objective target to natively
  support *editable* history (it backtracks by rewriting prior turns) —
  `target_agent`'s `/chat` endpoint now also accepts a stateless `history`
  payload for exactly this, and `pyrit_strategy: crescendo` runs against
  `target.py`'s `FastAPIEditableTarget` (rather than the default,
  append-only `FastAPITarget`) to use it.
- `pyrit_converters` (default none) — a list of PyRIT prompt converters
  applied before delivery, e.g. `[base64, rot13]`, or a single-key dict for
  converters that take a parameter, e.g. `[{translation: french}]`. See
  `redteam_engine/pyrit/converters.py` for the full registry (54 text-only
  converters across static/parameterized/LLM-backed buckets).
- `pyrit_severity_scale` (default `task_achieved`) — which rubric scores the
  supplementary 0–1 severity metric on vulnerable findings. Any filename
  (without `.yaml`) under PyRIT's bundled harm-definition rubrics (e.g.
  `privacy`, `cyber`) can be used instead of the generic default.

As with every engine, **`judge.py` grades every response** — PyRIT's own
internal scorer only drives the attack loop (when to stop escalating), never
the finding's pass/fail. PyRIT's own outcome/rationale, plus the severity
score for vulnerable findings, are kept in the finding's `trace` for
transparency.

`redteam_engine/native/attack_packs/code_execution_injection.yaml` and
`copyright_ip_leakage.yaml` were bootstrapped from PyRIT's own bundled
seed-prompt datasets via `redteam_engine/pyrit/scenario_import.py` (a one-off
authoring aid, not part of the live run path — see its docstring), then
hand-reviewed. PyRIT datasets are tagged `seed_type: prompt` (the seed *is*
the attack payload — every seed shares one hand-authored `--goal`) or
`seed_type: objective` (the seed *is* the goal sentence — one Attack per
seed, each with its own `goal`); the importer branches on this automatically.

### PyRIT Scenario sweeps (`engine: pyrit_scenario`)

Beyond single hand-written attack packs, `redteam_engine/native/attack_packs/pyrit_scenarios/`
holds descriptors that run one of PyRIT's own bundled `Scenario` classes
directly (`pyrit.scenario.scenarios.*`) — each sweeps several techniques
across a whole dataset of objectives in one run, rather than one
hand-written attack list. `redteam_engine/pyrit/scenario_runner.py` drives
this: same rule as every other engine, judge.py re-grades every single
result and PyRIT's own scorer never reaches a finding directly.

A descriptor is data, not code:

```yaml
category: data_leakage
engine: pyrit_scenario
scenario_class: pyrit.scenario.scenarios.airt.leakage.Leakage
max_concurrency: 4
max_dataset_size: 3           # cap PyRIT's own named dataset, if it exposes one via required_datasets()
scenario_techniques:          # restrict to text-only, non-editable-history techniques
  - role_play_movie_script
  - many_shot
  - first_letter
  - flip
  - red_teaming
scenario_kwargs: {}           # extra __init__ kwargs a scenario needs directly
                               # (e.g. WebInjection's max_prompts_per_technique)
scenario_params: {}           # extra *run* params for Scenario.additional_parameters()-declared
                               # inputs, resolved via set_params_from_args rather than __init__
                               # (e.g. Psychosocial's sub_harm/max_turns, Jailbreak's jailbreak_names)
```

Run one with:

```bash
uv run --group pyrit python cli.py run --target http://localhost:8000 \
    --packs redteam_engine/native/attack_packs/pyrit_scenarios/data_leakage.yaml
```

All 12 non-modality scenarios PyRIT 1.0.1 ships are wired up:

| Descriptor | `scenario_class` | Notes |
|---|---|---|
| `data_leakage.yaml` | `airt.leakage.Leakage` | system-prompt/credential/training-data leakage |
| `web_output_injection.yaml` | `garak.web_injection.WebInjection` | markdown/XSS output injection |
| `psychosocial_harm.yaml` | `airt.psychosocial.Psychosocial` | crisis mishandling, fake-therapist impersonation |
| `jailbreak_template_sweep.yaml` | `airt.jailbreak.Jailbreak` | catalogued jailbreak templates (AIM, DAN, …) |
| `cyber_malware_generation.yaml` | `airt.cyber.Cyber` | malware-generation willingness |
| `rapid_response_content_harms.yaml` | `airt.rapid_response.RapidResponse` | fast multi-harm-category sweep |
| `scam_fraud_generation.yaml` | `airt.scam.Scam` | phishing/fraud content generation |
| `policy_puppetry_bypass.yaml` | `garak.doctor.Doctor` | HiddenLayer Policy Puppetry universal bypass |
| `encoding_resilience.yaml` | `garak.encoding.Encoding` | does it decode + repeat harmful encoded payloads |
| `foundry_red_team_sweep.yaml` | `foundry.red_team_agent.RedTeamAgent` | broad converter sweep (Azure AI Foundry preset) |
| `adaptive_technique_sweep.yaml` | `adaptive.text_adaptive.TextAdaptive` | epsilon-greedy per-objective technique selection |

`benchmark.adversarial.AdversarialBenchmark` is the one PyRIT scenario
deliberately **not** wired up: it compares attack-success-rate across
multiple *adversarial* (attacker) models, which needs a second named
adversarial chat target registered in `TargetRegistry` alongside the one this
project already registers from `LLM_PROVIDER`/`llm_client.py` — a
multi-attacker-model comparison isn't something this PoC's single-model,
single-target architecture is set up to do without inventing a second model
to compare against.

Every scenario's default technique aggregate was chosen deliberately to stay
compatible with `scenario_runner.py`'s plain (non-editable-history)
`FastAPITarget` — none of them select PyRIT's `crescendo*` techniques, which
need a target that can rewrite prior turns (see `psychosocial_harm.yaml` and
`foundry_red_team_sweep.yaml`'s comments for the specific exclusion in each).
Note: `--packs redteam_engine/native/attack_packs` (the default,
non-recursive) does **not** pick up `pyrit_scenarios/` — point `--packs` at
it (or a specific file in it) explicitly, or combine both in one run (see
below).

### Combining native packs and scenario sweeps in one run

`--packs` takes one or more files/directories; everything found across all of
them runs into the same run id and the same report:

```bash
uv run --group pyrit python cli.py run --target http://localhost:8000 \
    --packs redteam_engine/native/attack_packs redteam_engine/native/attack_packs/pyrit_scenarios
```

Each pack file is dispatched by its own `engine` field regardless of which
path it came from (plain native packs, hand-written `engine: pyrit` packs, and
`engine: pyrit_scenario` descriptors can all appear in the same invocation).

PyRIT is a heavy optional dependency (transformers, datasets, several
azure-\* SDKs), so it's kept out of the base install behind a `uv` dependency
group:

```bash
uv add --group pyrit "pyrit==1.0.1"   # one-time setup

uv run --group pyrit python cli.py run --target http://localhost:8000 \
    --packs redteam_engine/native/attack_packs/multi_turn_escalation.yaml
```

Regular single-turn packs (and `--packs redteam_engine/native/attack_packs` to
run everything) don't require the `pyrit` group at all — the CLI only imports
it when a pack's `engine` field asks for it.

### Using the promptfoo engine

[promptfoo](https://www.promptfoo.dev/)'s red-team engine
(`redteam_engine/promptfoo/promptfooconfig.yaml`) generates/delivers attacks
from a separate plugin set (currently `imitation` and `prompt-extraction`),
while still grading every response with `judge.py` — promptfoo's own grader
is not used (see `redteam_engine/promptfoo/runner.py` for why). It runs
automatically as part of the default `--engine all`, alongside the
`--packs`-based engines above, into the same run/report. Requires Node.js
20+ (invoked via `npx`, no extra install step). To run only promptfoo (e.g.
while iterating on `promptfooconfig.yaml`):

```bash
uv run python cli.py run --target http://localhost:8000 --engine promptfoo
```

## Interactive dashboard (Streamlit)

An interactive companion to the static HTML report — a run picker, KPIs,
the same vulnerable/held and findings-by-article charts, a
vulnerabilities-per-run trend view when "All runs" is selected, and the full
findings + EU AI Act mapping reference tables. Reads the same
`observability/redteam.db` and `compliance/article_map.yaml` the CLI and
report use.

Streamlit is a heavier UI dependency kept out of the base install, same as
`pyrit`:

```bash
uv sync --group dashboard
uv run --group dashboard streamlit run dashboard/app.py
```

## Directory structure

```
project-typhon/
├── target_agent/          # mock company chatbot (FastAPI), deliberately weak system prompt
├── redteam_engine/
│   ├── judge.py           # LLM-as-judge: did the attack succeed? Single grader, shared by every engine.
│   ├── schemas.py         # pydantic models, shared by every engine
│   ├── native/            # engine: hand-written attack packs
│   │   ├── attack_packs/  # YAML attack definitions, grouped by category
│   │   │   └── pyrit_scenarios/  # PyRIT native Scenario descriptors (engine: pyrit_scenario)
│   │   └── runner.py      # sends attack_packs prompts to target, collects responses (single-turn)
│   ├── promptfoo/         # engine: promptfoo, for generation/delivery only (never grading)
│   │   ├── promptfooconfig.yaml
│   │   └── runner.py      # drives `npx promptfoo` for generation/delivery, then calls judge.py
│   └── pyrit/             # multi-turn engine (opt-in, needs `--group pyrit`)
│       ├── runner.py           # runs a pack through the selected PyRIT strategy, judge.py grades
│       ├── strategies.py       # pyrit_strategy registry: red_teaming, crescendo, tap, pair, skeleton_key, many_shot_jailbreak
│       ├── converters.py       # pyrit_converters registry: 54 text-only converters
│       ├── scenario_import.py  # one-off: PyRIT seed dataset -> attack pack YAML (seed_type: prompt or objective)
│       ├── scenario_runner.py  # runs a PyRIT native Scenario sweep (pyrit_scenarios/*.yaml), judge.py grades
│       ├── target.py      # PyRIT PromptTargets wrapping target_agent's /chat (the victim): FastAPITarget (append-only), FastAPIEditableTarget (stateless, for crescendo)
│       └── chat_model.py  # PyRIT chat target backed by llm_client.py (attacker + judge, not a victim)
├── observability/         # SQLite persistence of runs + findings
├── compliance/            # findings → EU AI Act article mapping + report generator + chart geometry
├── reports/               # generated HTML reports land here
├── dashboard/             # Streamlit dashboard (opt-in, needs `--group dashboard`)
├── llm_client.py          # provider-agnostic LLM client (DeepSeek, OpenAI, Anthropic)
├── cli.py                 # single entrypoint: python cli.py run --target ... [--engine all|native|promptfoo]
└── docker-compose.yml
```

## Swapping the target

The target agent's system prompt, model, and provider are all controlled via
env vars (`SYSTEM_PROMPT_PATH`, `TARGET_MODEL`, `LLM_PROVIDER`), so later
demos can point the same red-team engine at a design partner's actual
staging endpoint instead of the mock agent.

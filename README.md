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
| Report generator    | Working — HTML audit-style report                                    |

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
uv run uvicorn target_agent.main:app --port 8000
```

In another terminal, run a red-team attack against it. There are two engines
for generating/delivering attacks (`judge.py` always grades, regardless of
which one you pick) — the native engine is the default and needs no extra
setup:

```bash
uv run python cli.py run --target http://localhost:8000 --packs redteam_engine/native/attack_packs --engine native
```

This runs every attack pack in `redteam_engine/native/attack_packs/`, judges
each response, and prints a summary of which attacks found a vulnerability.
See [Using the promptfoo engine](#using-the-promptfoo-engine) and
[Multi-turn attacks via PyRIT](#multi-turn-attacks-via-pyrit) below for the
other two ways to attack the target.

### Multi-turn attacks via PyRIT

`redteam_engine/native/attack_packs/multi_turn_escalation.yaml` is tagged
`engine: pyrit` and runs through [PyRIT](https://github.com/microsoft/PyRIT)'s
`RedTeamingAttack` instead of the single-turn runner — an adversarial LLM
(reusing the same `llm_client.py` provider config as the judge) iteratively
escalates toward the attack's `goal` across several turns, with the target
agent's own conversation-id continuity carrying state between them.

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

`--engine promptfoo` swaps attack generation/delivery from the hand-written
`native/attack_packs/` YAML to [promptfoo](https://www.promptfoo.dev/)'s
red-team engine (`redteam_engine/promptfoo/promptfooconfig.yaml`), while
still grading every response with `judge.py` — promptfoo's own grader is not
used (see `redteam_engine/promptfoo/runner.py` for why). Requires Node.js
20+ (invoked via `npx`, no extra install step):

```bash
uv run python cli.py run --target http://localhost:8000 --engine promptfoo
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
│   │   └── runner.py      # sends attack_packs prompts to target, collects responses (single-turn)
│   ├── promptfoo/         # engine: promptfoo, for generation/delivery only (never grading)
│   │   ├── promptfooconfig.yaml
│   │   └── runner.py      # drives `npx promptfoo` for generation/delivery, then calls judge.py
│   └── pyrit/             # multi-turn engine (opt-in, needs `--group pyrit`)
│       ├── runner.py      # runs a pack through PyRIT's RedTeamingAttack
│       ├── target.py      # PyRIT PromptTarget wrapping target_agent's /chat (the victim)
│       └── chat_model.py  # PyRIT chat target backed by llm_client.py (attacker + judge, not a victim)
├── observability/         # SQLite persistence of runs + findings
├── compliance/            # findings → EU AI Act article mapping + report generator
├── reports/               # generated HTML reports land here
├── llm_client.py          # provider-agnostic LLM client (DeepSeek, OpenAI, Anthropic)
├── cli.py                 # single entrypoint: python cli.py run --target ... [--engine native|promptfoo]
└── docker-compose.yml
```

## Swapping the target

The target agent's system prompt, model, and provider are all controlled via
env vars (`SYSTEM_PROMPT_PATH`, `TARGET_MODEL`, `LLM_PROVIDER`), so later
demos can point the same red-team engine at a design partner's actual
staging endpoint instead of the mock agent.

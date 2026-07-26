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
Red Team Engine (runner + attack packs + judge)
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
| Red-team engine    | Working — runner, LLM-as-judge, and two attack packs (prompt injection, impersonation) |
| CLI                | Working — `python cli.py run` attacks a target and prints live results |
| Observability       | Not yet implemented (SQLite persistence planned)                     |
| Compliance mapper   | Not yet implemented (`article_map.yaml` + findings mapper planned)    |
| Report generator    | Not yet implemented (HTML audit report planned)                       |

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
uv run python cli.py run --target http://localhost:8000 --packs redteam_engine/attack_packs
```

This runs every attack pack in `redteam_engine/attack_packs/`, judges each
response, and prints a summary of which attacks found a vulnerability.

## Directory structure

```
project-typhon/
├── target_agent/          # mock company chatbot (FastAPI), deliberately weak system prompt
├── redteam_engine/
│   ├── attack_packs/      # YAML attack definitions, grouped by category
│   ├── runner.py          # sends attacks to target, collects responses
│   ├── judge.py           # LLM-as-judge: did the attack succeed?
│   └── schemas.py         # pydantic models
├── observability/         # SQLite persistence of runs + findings (planned)
├── compliance/            # findings → EU AI Act article mapping + report generator (planned)
├── reports/               # generated HTML reports land here
├── llm_client.py          # provider-agnostic LLM client (DeepSeek, OpenAI, Anthropic)
├── cli.py                 # single entrypoint: python cli.py run --target ... --packs ...
└── docker-compose.yml
```

## Swapping the target

The target agent's system prompt, model, and provider are all controlled via
env vars (`SYSTEM_PROMPT_PATH`, `TARGET_MODEL`, `LLM_PROVIDER`), so later
demos can point the same red-team engine at a design partner's actual
staging endpoint instead of the mock agent.

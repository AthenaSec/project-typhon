# AGENTS.md

## Project

**Name:** project-typhon
**Stage:** Proof of concept, built to validate the idea with a handful of design partners before real investment. Not production code. Optimize for "runs reliably in a live demo" over "scales" or "handles every edge case."

## What this is

A demo tool that shows companies what an automated red-teaming + EU AI Act compliance pipeline could look like for their LLM-based products. The pitch: attack a target LLM application with a red-team engine, log the results, map each finding to the specific EU AI Act article it's relevant to, and generate a report that could plausibly go into a compliance/audit file.

The end goal of the PoC is a live or recorded demo where:
1. A visibly under-guarded target chatbot gets attacked with a set of prompt-based attacks
2. Each attack result is judged pass/fail (did the vulnerability manifest?)
3. Findings get mapped to specific EU AI Act articles with a rationale and remediation suggestion
4. A clean, audit-style HTML report is generated at the end

This is being used to validate demand with design partners (compliance officers, AI/ML leads at companies shipping LLM features in the EU) before we invest significant time building the real product.

## System architecture

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

## Directory structure

```
project-typhon/
├── target_agent/          # mock company chatbot (FastAPI), deliberately weak system prompt
├── redteam_engine/
│   ├── attack_packs/      # YAML attack definitions, grouped by category
│   ├── runner.py          # sends attacks to target, collects responses
│   ├── judge.py           # LLM-as-judge: did the attack succeed?
│   └── schemas.py         # pydantic models
├── observability/         # SQLite persistence of runs + findings
├── compliance/
│   ├── article_map.yaml   # attack category -> EU AI Act article + rationale + remediation
│   ├── mapper.py
│   └── report_generator.py
├── reports/                # generated HTML reports land here
├── cli.py                  # single entrypoint: python cli.py run --target ... --packs ...
├── docker-compose.yml
└── README.md
```

## Key design principles

- **PoC-appropriate stack.** No LangGraph/Redis/Langfuse here — deliberately kept simple (single-process runner, SQLite) so it's fast to build and easy to demo live without infra explaining-away. Production stack decisions come later, after validation.
- **Attack packs and article mappings are data, not code.** They live in YAML (`redteam_engine/attack_packs/*.yaml`, `compliance/article_map.yaml`) so they're easy to read, edit, and eventually show to non-engineers. These two files are the actual differentiator of the demo — treat them as first-class, not boilerplate.
- **The report is the real deliverable.** The live attack is the hook; the generated report is what a compliance person actually evaluates. Keep report styling minimal and serious — audit report, not marketing deck.
- **Everything should run end-to-end from one CLI command.** `python cli.py run --target <url> --packs <packs>` should always work and print live progress to the terminal — this needs to look good running live in front of someone.
- **Swappable target.** The target agent's system prompt and endpoint should be easy to swap out, since later demos may point at a design partner's actual staging endpoint instead of the mock agent.

## Conventions

- Python 3.14, FastAPI, pydantic.
- Use environment variables (`.env`) for API keys — never hardcode.
- Prefer explicit, readable code over clever abstractions — this needs to be explainable in a demo/pitch context, not just functional.
- When in doubt about scope, keep it PoC-sized. Don't add auth, multi-tenancy, queueing, or production hardening unless explicitly asked.
- Dependency management is `uv`, not pip/poetry.

## What NOT to do

- Don't add self-serve/multi-tenant infrastructure (auth, rate limiting, user accounts) — this is a single-operator demo tool for now, not a live product.
- Don't over-engineer the target agent — it's meant to be a simple, deliberately weak wrapper, not a realistic production app.
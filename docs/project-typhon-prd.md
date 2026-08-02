# Project Typhon — Product Requirements Document

**Status:** Draft for design-partner validation
**Document owner:** Pradeep
**Last updated:** 31 July 2026 (rev. 3 — threaded black/gray/white-box testing modes into roadmap)
**Related repo:** `project-typhon` (FastAPI target agent · red-team engine · CLI)

---

## 1. Product Overview

### 1.1 Vision

Typhon is a continuous adversarial-testing and compliance-evidence platform for organizations deploying LLM-based agents in the EU. It attacks an organization's own AI agents the way a real adversary would — including agent-vs-agent, multi-agent collusion attacks — and turns the resulting findings directly into EU AI Act (and adjacent framework) conformity evidence, on a continuous cycle rather than a point-in-time audit.

### 1.2 Problem Statement

Two vendor categories currently serve adjacent needs, and neither closes the loop:

- **Attack-testing vendors** (Promptfoo, PyRIT, Mindgard, General Analysis, Lakera, HiddenLayer) find vulnerabilities but stop at a technical report. They don't produce artifacts a notified body, auditor, or insurer can use as conformity evidence.
- **AI governance/GRC vendors** (Credo AI, Holistic AI, OneTrust) produce compliance documentation and policy mappings but are largely self-attestation and questionnaire-driven — they don't generate evidence by actually attacking the system.

Compliance officers and AI/ML leads shipping LLM features in the EU are left manually bridging attack output to regulatory articles themselves, on a one-time basis, with no continuous assurance and no EU-native, non-US-owned option that avoids CLOUD Act exposure.

### 1.3 Target Users / Buyer Personas

| Persona | Role | Primary need |
|---|---|---|
| Compliance officer | Owns AI Act conformity program at a German/EU company deploying LLM agents | Continuous, audit-ready evidence without building an internal red team |
| AI/ML engineering lead | Ships agentic features, needs pre-release security signal | CI-gateable adversarial testing mapped to OWASP/MITRE, not just a pass/fail |
| Design partners (initial) | Compliance officers and AI/ML leads at German manufacturing and financial-services firms | Willing to pilot against a real staging endpoint pre-GA |
| Downstream (later) | MGA / insurance underwriters evaluating AI agent liability risk (per AIUC-1-style scoring) | A recurring, third-party-attackable risk score usable in underwriting |

### 1.4 Positioning & Differentiation

Typhon is **not** a general infrastructure pentest tool and **not** a GRC documentation platform. It sits specifically at the intersection: it attacks, and the attack output *is* the compliance evidence.

Three defensible differentiators, validated against the current (July 2026) competitive landscape:

1. **Swarm-vs-swarm agentic testing.** A red-team agent graph structurally mirrors the target's own multi-agent topology (shared memory, A2A/MCP handoffs, inter-agent trust) and attacks it continuously — role confusion, sybil identities, poisoned shared memory, cascading-failure induction. No commercial or open-source tool currently does this in a topology-aware, continuous way; PyRIT's own published gap analysis explicitly flags multi-agent coordination testing as unsupported, and existing "AI swarm" projects (Armadin, SWARM, DTap) are general-purpose or research-only, not compliance-anchored.
2. **Evidence generated from raw attack logs, not from a questionnaire.** Findings flow through a hash-chained, tamper-evident log directly into an EU AI Act article mapping (Articles 9, 10, 12, 13, 15) — bridging the exact gap between attack tools and GRC platforms described above.
3. **EU-native, non-US-owned, zero-egress by design.** Self-hostable in Germany, no CLOUD Act exposure (unlike Credo AI, Delaware C-Corp; unlike Promptfoo, OpenAI-owned since March 2026; unlike PyRIT, Microsoft; unlike Mindgard/HiddenLayer/Lakera/General Analysis/Cisco AI Defense, all US-owned). Judge/scorer/embedding calls default to a local model so attack transcripts never leave customer infrastructure — a concrete technical mechanism behind the data-residency claim, not just a hosting-location statement.
4. **Explicit black/gray/white-box depth labeling.** The same GEPA-driven engine runs at three distinct, clearly reported testing depths — external-attacker simulation (black box), informed-attacker simulation (gray box), and full-knowledge defense verification (white box) — with reflection context scaled to match. Most competitor tooling reports a single undifferentiated "attack success rate"; reporting both ends of the spectrum explicitly is stronger conformity evidence and a cleaner audit story.

### 1.5 Non-Goals

- Not a general infrastructure/network penetration testing tool (no Metasploit-style exploitation, no subdomain/CVE infra scanning as a primary feature). Out-of-scope capability increases liability exposure with a risk-averse compliance buyer and dilutes positioning.
- Not a GRC documentation/policy-management platform (no self-attestation questionnaires, no policy authoring workflows) — deliberately avoid recreating what Credo AI/Holistic AI already do well.
- Not a runtime firewall/guardrail product (no inline request blocking) at MVP — testing and evidence generation only. Runtime enforcement is a possible later-phase extension, not core.
- Not aiming to replace human red-teamers — positioned as continuous automated coverage between periodic human-led deep assessments (per the same 70/30 automation/human split observed across the industry).

---

## 2. Market & Regulatory Context (Summary)

### 2.1 Competitive landscape snapshot

| Category | Players | Gap relative to Typhon |
|---|---|---|
| Attack/red-team tooling | Promptfoo (OpenAI-owned), PyRIT (Microsoft), garak, Giskard, Mindgard, General Analysis, Lakera, HiddenLayer, DeepTeam | No EU AI Act article mapping; no topology-aware multi-agent testing; mostly US-owned/hosted |
| AI governance/GRC | Credo AI, Holistic AI, OneTrust, Modulos | Documentation/questionnaire-first; Credo AI is US Delaware C-Corp (CLOUD Act exposure); some (Modulos, DeepInspect) now link OWASP findings to articles but aren't attack-originating platforms themselves |
| Agentic/swarm red-teaming | Armadin ($190M, general offensive security), SWARM (OSS, general multi-agent adversarial testing), DTap (research) | General-purpose, not EU-compliance-anchored |
| Reference open-source component | Redamon (github.com/samugit83/redamon) — general infra pentest platform with an "AI Gauntlet" module orchestrating garak/PyRIT/Giskard/promptfoo with cross-tool corroboration and a zero-egress local judge | Proves the multi-engine-orchestration pattern is solvable and now free/OSS; raises pressure to differentiate specifically on compliance mapping + swarm-vs-swarm, since generic multi-tool attack orchestration is no longer a moat |

### 2.2 Regulatory timeline (as of July 2026)

| Date | Obligation | Relevance |
|---|---|---|
| 2 Aug 2026 | Article 50 transparency obligations apply (new systems) | Near-term wedge: transparency/disclosure testing evidence |
| 2 Dec 2026 | Article 50(2) transparency for legacy systems; new prohibited practices | Second near-term wedge |
| 2 Dec 2027 | Annex III high-risk obligations apply (deferred from 2 Aug 2026 by the Digital Omnibus) | Primary urgency window for the conformity-assessment/insurance-underwriting pitch |
| 2 Aug 2028 | Annex I embedded high-risk systems | Later-phase market |

Implication: MVP messaging should lead with the Article 50 transparency-testing wedge (immediate), while building toward the Annex III conformity-evidence pitch (18-month runway, aligns with Phase 3–4 of the roadmap below).

---

## 3. MVP Definition

### 3.1 MVP Goal

Prove, with 2–3 unpaid design partners, that Typhon can run continuous attacks against a real (staging) LLM agent and produce an audit-style report that a compliance officer would actually use — validating both the technical pipeline and the compliance-mapping value proposition before building the full swarm-vs-swarm and certification layers.

### 3.2 In Scope (MVP)

- Multi-engine attack execution against a single target agent (promptfoo, PyRIT, garak, Giskard behind one interface)
- One native agentic attack pack covering 3 OWASP ASI categories: ASI02 (tool misuse), ASI06 (memory/context poisoning), ASI07 (insecure inter-agent communication)
- GEPA-driven attack mutation for at least one attack category
- Cross-engine corroboration scoring (finding confidence = number of independent engines confirming it)
- Self-hosted Langfuse tracing of every attack turn, tool call, and judge verdict
- `article_map.yaml` covering Articles 9, 12, 15
- Hash-chained findings log (tamper-evidence)
- HTML audit report: attack → evidence → OWASP/MITRE ID → EU AI Act article → pass/fail
- RoE (Rules of Engagement) capture and authorization record as part of the audit trail
- One swarm-vs-swarm demo: 2 attacker agents (impersonation + tool-hijack) coordinating against a mock multi-agent target
- Zero-egress default: local judge model for scoring/embedding
- Black-box testing mode (default): attack via target's input/output interface only, no internal knowledge
- Gray-box testing mode: GEPA reflector additionally consumes disclosed partial context (system-prompt template, tool/function schemas, known guardrail categories) to sharpen mutations

### 3.3 Out of Scope (MVP, deferred to later phases)

- Quarterly certification workflow / re-run scheduling
- Full Annex III control coverage (Articles 10, 13, and beyond)
- Insurance-underwriting integration / AIUC-1-style scoring output
- Runtime/production guardrail enforcement
- Topology ingestion from a target's real agent graph (MVP demo uses a mock target)
- White-box testing mode (full source/guardrail-implementation/agent-graph access) — deferred to Phase 3; this is the same access level FR-16's topology-aware swarm-vs-swarm work requires, not separate scope
- Multi-tenant SaaS hosting (MVP is single-tenant, deployed per design partner)

### 3.4 Core User Journeys

1. **Compliance officer onboarding:** uploads/describes target agent scope and RoE → Typhon runs an initial baseline scan → receives first HTML report mapped to Articles 9/12/15.
2. **Recurring scan:** CI-triggered or scheduled re-run against a staging endpoint → diff against prior findings → flagged regressions.
3. **Swarm demo (design-partner-facing):** two coordinating attacker agents targeting a multi-agent mock system → distinct "multi-agent collusion" finding class in the report, differentiator moment.

### 3.5 Success Criteria (MVP exit)

- ≥1 design partner runs Typhon against a real staging endpoint (not the mock agent)
- ≥1 design partner explicitly reacts positively to the swarm-vs-swarm finding class as differentiated value
- Audit report is judged "usable as a starting point for our own conformity documentation" by at least one compliance-officer pilot contact
- Corroboration scoring demonstrably reduces false-positive noise vs. single-engine output (qualitative pilot feedback acceptable at this stage)

---

## 4. Functional Requirements

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-1 | System shall execute attacks against a target agent via a common `AttackEngine` interface, with promptfoo, PyRIT, garak, and Giskard as pluggable adapters | Must | Adapters isolated (per-tool venv or container), matching Redamon's isolation pattern |
| FR-2 | System shall support at least single-turn (promptfoo/garak-style) and multi-turn/escalating (PyRIT Crescendo/TAP-style) attack execution | Must | |
| FR-3 | System shall support GEPA-driven reflective mutation of attack prompts, using judge verdict + textual rationale as the feedback signal | Must | Applies to ≥1 attack category at MVP |
| FR-3a | System shall support three testing access levels — black box (I/O only), gray box (disclosed system-prompt/tool-schema/guardrail-category context), white box (full source/guardrail-implementation/agent-graph access) — recorded per `AttackRun` and authorized per RoE | Must (black/gray at MVP) | White box formally merges with FR-16's topology ingestion — same access requirement, not separate work |
| FR-3b | GEPA's reflection step shall consume access-level-appropriate context: judge verdict + transcript only in black box; additionally disclosed system-prompt/tool/guardrail-category context in gray box; full source/defense-implementation/topology context in white box | Must (black/gray at MVP) | Same reflector, three information-richness configurations — not three separate engines |
| FR-4 | System shall implement native attack packs for OWASP ASI02, ASI06, ASI07 (tool misuse, memory/context poisoning, insecure inter-agent communication) | Must | Neither promptfoo nor PyRIT natively executes/observes tool calls or multi-agent state — this is custom-built |
| FR-5 | System shall score each finding with a corroboration count (number of independent engines/attack packs confirming the same underlying weakness) | Must | Directly informs report severity/confidence |
| FR-6 | System shall support a swarm-vs-swarm mode: N attacker agents coordinating (role confusion, sybil identity, shared-memory poisoning) against a multi-agent target | Must (MVP demo scope) | MVP: fixed 2-agent demo against mock target; Phase 3: topology-aware against real targets |
| FR-7 | System shall trace every attack turn, tool call, and judge verdict as OpenTelemetry-compatible spans via self-hosted Langfuse | Must | |
| FR-8 | System shall persist findings with a `article_map.yaml`-driven mapping to EU AI Act articles (9, 12, 15 at MVP; expand later) | Must | Mapping logic is core IP — not outsourced to a GRC vendor |
| FR-9 | System shall generate a hash-chained (tamper-evident) log of findings, ordered and verifiable | Must | Directly supports Article 12 logging-mandate evidence |
| FR-10 | System shall capture and store the Rules-of-Engagement / authorization scope as part of the audit artifact | Must | Doubles as liability protection and Article 12 evidence |
| FR-11 | System shall generate an HTML audit report: attack → judge verdict → OWASP/MITRE ID → EU AI Act article → pass/fail, timestamped, labeled by testing access level (black/gray/white box) | Must | Reporting both black-box ("what an external attacker with no knowledge could achieve") and white-box ("whether documented defenses hold under full knowledge") results is stronger Article 15 evidence than either alone |
| FR-12 | System shall default all judge/scorer/embedding calls to a local model (e.g., self-hosted Ollama), with cloud-model judging as an explicit opt-in override | Must | Zero-egress-by-default is a core differentiator, not an afterthought |
| FR-13 | System shall allow target configuration via environment variables (endpoint, model, provider) so the same engine can point at a mock agent or a design partner's real staging endpoint | Must | Already partially implemented in `project-typhon` |
| FR-14 | System should support a scheduled/CI-triggered re-run with diff-against-prior-findings | Should | MVP-adjacent; formalizes into quarterly certification in Phase 2+ |
| FR-15 | System should expose a CLI (`cli.py run --target ... --packs ...`) as the primary MVP interface; web UI deferred | Should | Matches existing repo structure |
| FR-16 | System could support ingestion of a target's real multi-agent topology (agent graph) to shape swarm-vs-swarm attacks structurally | Could | Phase 3 — the sharpest long-term differentiator |
| FR-17 | System could generate a quarterly compliance certificate artifact (PDF), version-diffed against the prior period | Could | Phase 2 — ties to insurance-underwriting go-to-market |
| FR-18 | System shall run attacker-persona reasoning (GEPA mutation, swarm agent personas, native attack-pack generation) on a self-hosted, open-weight model rather than a cloud API by default | Must | GLM-5.2 as primary PoC candidate; smaller open model as cheaper first validation step; Kimi K3 as Phase 2+ stretch given self-hosting scale — see §5.1.1 |
| FR-19 | System shall enforce a hard budget on every attacker-swarm run: max iterations, max token spend, and max wall-clock time, with automatic stop on breach-confirmed-by-judge or budget-exhausted | Must | Directly informed by the OpenAI/Hugging Face incident (July 2026), where an unbounded agent pursuing a narrow goal escalated privileges and pivoted across systems — the same failure shape must not be reproducible inside Typhon's own attacker sandbox |
| FR-20 | System shall run the attacker-swarm sandbox with network egress restricted to an explicit allowlist (the designated target endpoint only — mock or real staging), with no general internet access | Must | Prevents the attacker layer itself from becoming a containment-escape risk; mirrors the exact control that failed in the OpenAI/Hugging Face incident |
| FR-21 | System shall deduplicate overlapping attack attempts across swarm members via a shared blackboard/state store, to avoid redundant compute spend | Should | Efficiency requirement once swarm size > 2–3 agents |
| FR-22 | System shall require the target agent's tool layer to be mocked or scoped to a non-production replica (synthetic data, revocable narrow-scope credentials) for any run flagged as "aggressive" | Must | Symmetrical to attacker-side sandboxing (FR-20): a successful tool-misuse attack must land in a mock/logged action, not a real one — otherwise an authorized test can cause real-world harm (sent emails, deleted records, moved funds) |
| FR-23 | System shall support configurable request pacing/rate limits per run, recorded as part of the RoE | Should | Prevents aggressive-volume testing from degrading or tripping defenses on a design partner's staging environment as an unintended side effect |

---

## 5. Technical Architecture & Non-Functional Requirements

### 5.1 Component overview

```
Attacker Model Layer (self-hosted, open-weight — GLM-5.2 / smaller fallback)
   — reasoning engine behind GEPA mutation, swarm agent personas, and
     native attack-pack generation; sandboxed, egress-locked to target only
        ↓ drives
Loop Controller
   — bounded budget (max iterations / tokens / wall-clock), dedup across
     swarm members, stop-on-breach-detected, stop-on-budget-exhausted
        ↓ dispatches
Attack Engine Layer
   ├─ promptfoo adapter        (single-turn, 50+ OWASP-LLM plugins)
   ├─ PyRIT adapter            (multi-turn: Crescendo / TAP / PAIR)
   ├─ garak adapter            (broad single-shot, 40 probe families)
   ├─ Giskard adapter          (app-tailored safety detectors)
   ├─ Native agentic pack      (ASI02 / ASI06 / ASI07 — tool hijack, memory
   │                            poisoning, inter-agent comms)
   └─ Swarm-vs-swarm module    (N coordinating attacker agents, each an
                                 instance of the Attacker Model Layer;
                                 GEPA-driven attack evolution wraps this
                                 + the native pack)
        ↓ attacks
Target Agent (mock, or design partner's real staging endpoint)
        ↓ traced as OTel spans
Langfuse (self-hosted, EU)  — tracing, sessions, cost, prompt/version mgmt
        ↓ raw findings
Findings Store (SQLite at PoC → Postgres at MVP)
   — hash-chained log, corroboration score, RoE/authorization record
        ↓ mapped via article_map.yaml
Compliance Mapper (OWASP ASI / OWASP LLM Top 10 / MITRE ATLAS → EU AI Act
                    Articles 9 / 12 / 15, expanding to 10 / 13)
        ↓ feeds
Report Generator (HTML audit report; PDF certificate in later phase)
        ↓ triggered by
CLI (single entrypoint — existing `cli.py run` extended with --engine flag)
```

### 5.1.1 Attacker Model Layer — Selection Rationale

Running the attacker persona(s) on a **self-hosted, open-weight model** rather than a paid frontier API is a deliberate architecture choice, not a cost shortcut:

- **Refusal friction.** Frontier closed models with strong safety tuning routinely refuse or hedge on generating large volumes of adversarial/jailbreak content, even for authorized red-teaming — an operational problem explicitly documented in PyRIT's own gap analysis. A less-restricted, self-hosted attacker model removes this friction without touching the target's own safety posture (the target is the system under test; the attacker's job is to be maximally adversarial).
- **Zero-egress consistency.** Self-hosting the attacker model — not just the judge — keeps the entire attack loop (prompts, mutations, transcripts) inside customer infrastructure, reinforcing NFR-1/NFR-3 rather than partially satisfying them.
- **Cost at scale.** A continuous, GEPA-driven mutation loop across a swarm generates high inference volume; per-token API billing on a closed model would make "continuous" testing expensive fast.

**Model candidates and practical fit:**

| Model | Size / license | Fit for self-hosted attacker role |
|---|---|---|
| GLM-5.2 (Zhipu/Z.ai) | 744B total / 40B active MoE, MIT license, 1M context | **Most practical near-term choice.** MoE active-parameter count makes self-hosting realistic on a modest multi-GPU setup (or rented EU-based GPU capacity); MIT license imposes no usage restriction; frontier-class agentic/reasoning capability |
| Kimi K3 (Moonshot AI) | 2.8T total parameters, 1M context, open weights | Frontier-class capability, but at this parameter count self-hosting is likely infra-prohibitive for a PoC/MVP team — treat as a **Phase 2+ stretch option** once GPU budget exists, or evaluate a quantized/distilled release if one becomes available; confirm exact license terms before adopting |
| Smaller open fallback (e.g., a 30–70B class open model) | Varies | **Recommended PoC starting point** — validates the whole attacker-loop architecture cheaply before committing GPU budget to GLM-5.2/Kimi K3-scale self-hosting |

**Data-sovereignty note:** model origin (China, in both cases above) does not by itself compromise the EU-data-residency claim — what matters is where *inference actually executes* and whether any call leaves customer/EU infrastructure. Self-hosting either model fully within EU-controlled compute, with no calls back to the vendor's hosted API, satisfies NFR-1/NFR-3 the same as any other open weights would. Flag as a **procurement consideration, not a blocker**: some regulated design partners (financial services in particular) may have blanket policies against Chinese-origin model weights regardless of hosting location — confirm during Phase 1 pilot scoping rather than assuming it's a non-issue.

### 5.2 Data model (indicative)

| Entity | Key fields |
|---|---|
| `AttackRun` | run_id, target_config, engines_used[], testing_mode (black/gray/white), RoE_ref, started_at, finished_at |
| `AttackTurn` | run_id, engine, turn_index, prompt, response, transform_applied, langfuse_trace_id |
| `Finding` | finding_id, run_id, category (OWASP ASI / LLM Top 10 ID), engines_confirming[], corroboration_score, severity, article_refs[], evidence_hash, reproduction_ref |
| `ComplianceMapping` | finding_id, eu_ai_act_article, control_description, evidence_status (pass/fail/partial) |
| `RoERecord` | run_id, scope_description, authorized_access_level (black/gray/white), authorized_by, authorized_at, signature_ref |

### 5.3 Tech stack

| Layer | Choice | Rationale |
|---|---|---|
| Attack orchestration | Python, existing `runner.py`/`schemas.py` extended | Keep existing PoC investment |
| Attacker model(s) | Self-hosted open-weight: smaller open model for initial PoC validation → GLM-5.2 (MIT, 40B active MoE) as primary target; Kimi K3 (2.8T) as Phase 2+ stretch | Removes refusal friction, keeps attack loop zero-egress, avoids per-token cost at scale — see §5.1.1 |
| Attack engines | promptfoo (Node CLI, subprocess), PyRIT (pip), garak (pip), Giskard (pip) | Isolated per-engine venv/container, matching Redamon's isolation pattern |
| Attack evolution | GEPA (`gepa` package, or DSPy integration) | Reflective mutation using judge feedback |
| Observability | Langfuse, self-hosted (Docker Compose), OTel-native | EU-hostable, avoids building a bespoke tracing UI |
| Findings store | SQLite (PoC) → Postgres (MVP) | Matches existing repo structure, minimal migration cost |
| Judge/scorer | Local model default (Ollama or self-hosted), cloud override opt-in | Zero-egress-by-default differentiator |
| Report generation | Server-side HTML (existing plan); PDF via a library (e.g., WeasyPrint) in Phase 2 | |
| Deployment | Docker Compose, self-hostable in Germany | Supports EU-native / no-CLOUD-Act positioning |

### 5.4 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | All attack transcripts and findings must remain within customer-controlled infrastructure by default (zero-egress judge/scorer) |
| NFR-2 | Findings log must be tamper-evident (hash-chained) to support Article 12 audit-trail claims |
| NFR-3 | System must be self-hostable entirely within the EU/Germany, with no mandatory dependency on a US-owned SaaS component |
| NFR-4 | Attack runs must be reproducible (fixed seeds / bounded parameters) to support audit re-verification, mirroring the deterministic design pattern seen in comparable OSS tooling |
| NFR-5 | All destructive/high-impact test actions must be gated behind an explicit RoE record and (at MVP) manual confirmation, mirroring human-in-the-loop patterns used elsewhere in the industry |
| NFR-6 | Report generation must complete within a reasonable time window for a design-partner demo (target: under 30 minutes for a full attack-pack run against a single endpoint) — refine once baseline is measured |
| NFR-7 | System must not include general infrastructure-exploitation capability (no Metasploit-class tooling) to keep the liability/security-review profile appropriate for a compliance-buyer sale |
| NFR-8 | The attacker-swarm sandbox must have no outbound network access beyond the explicitly configured target endpoint(s); this must be enforced at the container/network level, not just application logic |
| NFR-9 | Every attacker-swarm run must run under an enforced resource ceiling (iteration count, token spend, wall-clock duration) with a hard stop, independent of whether the judge has confirmed a breach |
| NFR-10 | Target-side tool/action execution must be mocked or scoped to a non-production replica whenever a run is configured as "aggressive"; this is a distinct control from attacker-sandboxing (NFR-8) and must not be conflated with it — sandboxing the attacker does not make it safe for the target to receive unrestricted attacks |

---

## 6. Roadmap

| Phase | Timeframe | Focus | Exit criteria |
|---|---|---|---|
| **0 — PoC hardening** | Now → 6 weeks | Extend existing repo: multi-engine attack layer (promptfoo/PyRIT/garak/Giskard), native ASI02/06/07 pack, Langfuse tracing, `article_map.yaml` (Art. 9/12/15), hash-chained HTML report, one swarm-vs-swarm demo, black-box mode (default) + gray-box mode (GEPA reflector fed disclosed system-prompt/tool-schema context) | Working end-to-end demo covering both black- and gray-box modes; first design-partner reaction |
| **1 — Design-partner pilots** | 6–14 weeks | Run against 2–3 real staging endpoints (German manufacturing/fintech) in black- and gray-box mode; collect feedback on report usability, corroboration scoring, and which access level partners are willing to grant | Signed intent-to-pilot or LOI from ≥1 partner |
| **2 — MVP** | 14–24 weeks | Postgres migration, GEPA-driven attack evolution live, full Article 9/10/12/13/15 mapping, quarterly-certificate workflow (PDF, diffed) | First paid pilot or design-partner conversion |
| **3 — Differentiation lock-in** | 24–36 weeks | White-box mode: topology-aware swarm-vs-swarm (ingest target's real agent graph, full guardrail-implementation context feeding GEPA reflection) rather than a fixed demo topology; formalize EU-hosting/zero-CLOUD-Act positioning in GTM materials | Category-distinct demo: testing shaped by the target's actual multi-agent architecture, reported across all three access levels |
| **4 — Scale** | 9+ months | Insurance-underwriting integration (AIUC-1/MGA-style scoring, referencing Agent Insured, Armilla, Munich Re aiSure, Klaimee as market comparables); notified-body-ready evidence packages ahead of the 2 Dec 2027 Annex III deadline | First underwriting or notified-body partnership conversation |

---

## 7. Risks, Assumptions, Open Questions

### 7.1 Risks

- **Moat erosion risk:** the "hard" attack-orchestration plumbing (multi-engine + corroboration + graph-backed findings) is now available for free via Redamon's AI Gauntlet module (MIT-licensed, ~1.9k stars). Mitigation: focus engineering effort on the compliance-mapping and swarm-vs-swarm layers, which remain unsolved elsewhere.
- **Regulatory-timing risk:** the Digital Omnibus deferred Annex III obligations to 2 Dec 2027, reducing near-term urgency for the primary conformity-evidence pitch. Mitigation: lead go-to-market with the nearer Article 50 transparency-testing wedge (Aug/Dec 2026) while building toward Annex III.
- **Judge reliability risk:** LLM-as-judge scoring carries its own false-positive/negative rate. Mitigation: corroboration scoring across independent engines, calibration against human-labeled samples before design-partner demos.
- **Scope-creep risk:** temptation to add general infra-pentest capability (as Redamon does) could dilute positioning and increase liability exposure with compliance buyers. Mitigation: NFR-7 explicitly excludes this.
- **Self-hosting infra risk:** Kimi K3's 2.8T parameter count is reported as likely impractical to self-host for many organizations at PoC scale. Mitigation: validate the attacker-loop architecture on a smaller open model first, treat GLM-5.2 as the realistic near-term target, and Kimi K3 as a later-phase option gated on GPU budget (FR-18, §5.1.1).
- **Unbounded-loop risk:** an autonomous attacker swarm run "until breached" without hard limits risks runaway compute cost and, in the worst case, the same containment-escape failure pattern seen in the July 2026 OpenAI/Hugging Face incident (an agent pursuing a narrow goal without effective scope boundaries escalated privileges and pivoted across systems). Mitigation: FR-19/FR-20/NFR-8/NFR-9 mandate hard budgets and network-level egress allowlisting on the attacker sandbox, non-negotiable even during early PoC work.

### 7.2 Assumptions

- Design partners will grant staging-endpoint access under a signed RoE within Phase 1's timeframe.
- GEPA can be adapted to attack-prompt evolution without prohibitive rollout cost (unverified in production — validate early in Phase 0).
- Self-hosted Langfuse and a local judge model are sufficient for the zero-egress claim without materially degrading judge quality versus a frontier cloud model (validate via calibration testing).

### 7.3 Open Questions

- Final article coverage sequencing: is Article 10 (data governance) or Article 13 (transparency) the better second addition after 9/12/15?
- Should the swarm-vs-swarm module's topology ingestion (Phase 3) require the target's actual agent-framework metadata (e.g., LangGraph graph definition), or should it infer topology through black-box probing? Both are viable; the former is faster to build, the latter is more broadly applicable to design partners without instrumented systems.
- Pricing/packaging model for the quarterly certificate (Phase 2) — flat fee per assessment vs. usage-based vs. bundled with the eventual insurance-underwriting product — not yet decided.

---

## 8. Appendix: Tool & Framework Reference

| Tool/Framework | Role in Typhon | Status |
|---|---|---|
| Promptfoo | Single-turn attack engine, OWASP LLM Top 10 plugin coverage | To integrate (Phase 0) |
| PyRIT | Multi-turn/escalating attack engine (Crescendo, TAP, PAIR) | To integrate (Phase 0) |
| garak | Broad single-shot probe coverage (40 probe families) | To integrate (Phase 0, added per Redamon reference) |
| Giskard | App-tailored safety detectors (hallucination, sycophancy, stereotypes) | To integrate (Phase 0, added per Redamon reference) |
| GEPA | Reflective attack-prompt evolution using judge feedback | To integrate (Phase 0/2) |
| Langfuse | Self-hosted tracing/observability substrate | To integrate (Phase 0) |
| GLM-5.2 (Zhipu/Z.ai) | Primary candidate for self-hosted attacker-model layer (MIT license, 40B active MoE) | To integrate (Phase 0/1) |
| Kimi K3 (Moonshot AI) | Stretch attacker-model option once GPU budget supports 2.8T-parameter self-hosting; confirm license terms before adopting | Reference / Phase 2+ |
| Credo AI | Not integrated — studied for policy-pack structure only; positioned against, not built on | Reference only |
| Redamon (samugit83) | Reference architecture for multi-engine corroboration and zero-egress judging; not adopted wholesale | Reference only |
| OWASP Top 10 for Agentic Applications (ASI01–10) | Native attack-pack taxonomy | Adopted |
| OWASP Top 10 for LLM Applications | Attack-pack taxonomy (via promptfoo/garak/Giskard coverage) | Adopted |
| MITRE ATLAS | Cross-reference taxonomy for findings | Adopted |
| EU AI Act (Articles 9, 10, 12, 13, 15) | Compliance-mapping target | Core IP layer |

---

*This document synthesizes prior research and decisions from the Project Typhon working sessions. It is a living draft — update as design-partner feedback and Phase 0 build learnings arrive.*

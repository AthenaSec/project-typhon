"""Pydantic models shared across the red-team engine."""

from pydantic import BaseModel

# Single source of truth for engine -> human label, shared by dashboard/app.py
# and compliance/report_generator.py so the two views can't drift out of sync
# (they did once: native/promptfoo findings went unlabeled because only this
# dict lived in the dashboard).
ENGINE_LABELS = {
    "native": "Single-turn (Native)",
    "promptfoo": "Single-turn (promptfoo)",
    "pyrit": "Multi-turn (PyRIT)",
    "pyrit_scenario": "Multi-turn (PyRIT Scenario)",
}


class Attack(BaseModel):
    id: str
    name: str
    prompt: str
    goal: str


class AttackPack(BaseModel):
    category: str
    description: str
    engine: str = "single_turn"  # "single_turn" | "pyrit"
    pyrit_strategy: str = "red_teaming"  # red_teaming | crescendo | tap | skeleton_key | pair | many_shot_jailbreak
    pyrit_converters: list[str | dict[str, str]] = []
    # Severity rubric for the supplementary 0-1 score on vulnerable findings
    # (see runner.py::_score_severity_async). "task_achieved" is PyRIT's
    # generic scale; any filename (without .yaml) under PyRIT's bundled
    # HARM_DEFINITION_PATH (e.g. "privacy", "cyber") uses that harm-specific
    # rubric instead.
    pyrit_severity_scale: str = "task_achieved"
    attacks: list[Attack]


class ScenarioPack(BaseModel):
    """Descriptor for a PyRIT native Scenario (pyrit.scenario.scenarios.*),
    as opposed to an AttackPack's hand-written attacks: list. Kept as data
    (see AGENTS.md: attack packs are data, not code) so which PyRIT Scenario
    class runs, and which techniques/dataset slice it sweeps, stays visible
    and editable without touching scenario_runner.py."""

    category: str
    description: str
    engine: str = "pyrit_scenario"
    scenario_class: str  # dotted path, e.g. "pyrit.scenario.scenarios.airt.leakage.Leakage"
    max_concurrency: int = 4
    # None means the scenario's own default aggregate. Restrict explicitly
    # when the default includes techniques this project can't run (e.g.
    # image-modality techniques against our text-only target).
    scenario_techniques: list[str] | None = None
    max_dataset_size: int | None = None
    # Extra constructor kwargs passed straight to the scenario class, for
    # scenario-specific knobs that don't go through the common
    # dataset_config path (e.g. WebInjection's max_prompts_per_technique).
    scenario_kwargs: dict = {}
    # Extra *run* parameters merged into Scenario.set_params_from_args's args
    # dict, for scenario-specific knobs declared via Scenario.additional_parameters()
    # rather than accepted by __init__ (e.g. Psychosocial's sub_harm/max_turns,
    # Jailbreak's num_jailbreaks/jailbreak_names, Scam's max_turns, TextAdaptive's
    # max_attempts_per_objective). Distinct from scenario_kwargs (constructor
    # kwargs) because PyRIT resolves the two through separate code paths and
    # rejects any key not declared by that scenario's own supported_parameters().
    scenario_params: dict = {}
    pyrit_severity_scale: str = "task_achieved"


class Judgment(BaseModel):
    vulnerable: bool
    rationale: str


class TurnRecord(BaseModel):
    turn: int
    prompt: str
    response: str


class AttackResult(BaseModel):
    category: str
    attack: Attack
    response: str
    judgment: Judgment
    engine: str = "single_turn"
    turns: list[TurnRecord] | None = None

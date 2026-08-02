"""Registry of PyRIT attack strategies, selectable per attack pack via
AttackPack.pyrit_strategy. Each builder takes the same shape of inputs
(objective target, adversarial config, scoring config, converter config) and
returns a ready-to-execute PyRIT AttackStrategy, so runner.py never needs to
branch on which strategy is in play."""

from typing import Callable

from pyrit.executor.attack import (
    AttackAdversarialConfig,
    AttackConverterConfig,
    AttackScoringConfig,
    CrescendoAttack,
    ManyShotJailbreakAttack,
    PAIRAttack,
    RedTeamingAttack,
    SkeletonKeyAttack,
    TAPAttack,
)
from pyrit.executor.attack.core import AttackStrategy
from pyrit.prompt_target import PromptTarget

MAX_TURNS = 5

StrategyBuilder = Callable[
    [PromptTarget, AttackAdversarialConfig, AttackScoringConfig, AttackConverterConfig | None],
    AttackStrategy,
]


def _build_red_teaming(objective_target, adversarial_config, scoring_config, converter_config) -> AttackStrategy:
    return RedTeamingAttack(
        objective_target=objective_target,
        attack_adversarial_config=adversarial_config,
        attack_scoring_config=scoring_config,
        attack_converter_config=converter_config,
        max_turns=MAX_TURNS,
    )


def _build_crescendo(objective_target, adversarial_config, scoring_config, converter_config) -> AttackStrategy:
    # Crescendo requires the objective target to natively support editable
    # history (it backtracks by rewriting prior turns). runner.py passes a
    # FastAPIEditableTarget here instead of the default FastAPITarget —
    # target_agent's /chat now accepts a stateless `history` payload for
    # exactly this (see target_agent/main.py and target.py's
    # FastAPIEditableTarget), so "editing" is just sending a different
    # history on the next call.
    return CrescendoAttack(
        objective_target=objective_target,
        attack_adversarial_config=adversarial_config,
        attack_scoring_config=scoring_config,
        attack_converter_config=converter_config,
        max_turns=MAX_TURNS,
    )


def _build_tap(objective_target, adversarial_config, scoring_config, converter_config) -> AttackStrategy:
    # No attack_scoring_config passed: TAP builds its own default
    # FloatScaleThresholdScorer(SelfAskScaleScorer(...), threshold=0.7) using
    # whatever target is in adversarial_config, i.e. our LLMClientChatTarget.
    # Passing our TrueFalseScorer-based config would fail TAP's isinstance check.
    return TAPAttack(
        objective_target=objective_target,
        attack_adversarial_config=adversarial_config,
        attack_converter_config=converter_config,
    )


def _build_skeleton_key(objective_target, adversarial_config, scoring_config, converter_config) -> AttackStrategy:
    # Single-turn: no adversarial chat involved.
    return SkeletonKeyAttack(
        objective_target=objective_target,
        attack_scoring_config=scoring_config,
        attack_converter_config=converter_config,
    )


def _build_pair(objective_target, adversarial_config, scoring_config, converter_config) -> AttackStrategy:
    # PAIR is TreeOfAttacksWithPruningAttack with branching_factor=1 and no
    # off-topic pruning — same scoring shape as TAP: no attack_scoring_config
    # passed, so PAIR builds its own default FloatScaleThresholdScorer(
    # SelfAskScaleScorer(...), threshold=0.7); our TrueFalseScorer-based
    # AttackScoringConfig would fail its isinstance check.
    return PAIRAttack(
        objective_target=objective_target,
        attack_adversarial_config=adversarial_config,
        attack_converter_config=converter_config,
    )


def _build_many_shot_jailbreak(objective_target, adversarial_config, scoring_config, converter_config) -> AttackStrategy:
    # Single-turn: no adversarial chat involved. Prepends a faux many-shot
    # jailbreak dialogue (from PyRIT's bundled examples) ahead of the attack
    # prompt.
    return ManyShotJailbreakAttack(
        objective_target=objective_target,
        attack_scoring_config=scoring_config,
        attack_converter_config=converter_config,
    )


STRATEGIES: dict[str, StrategyBuilder] = {
    "red_teaming": _build_red_teaming,
    "crescendo": _build_crescendo,
    "tap": _build_tap,
    "skeleton_key": _build_skeleton_key,
    "pair": _build_pair,
    "many_shot_jailbreak": _build_many_shot_jailbreak,
}


def build_strategy(
    name: str,
    *,
    objective_target: PromptTarget,
    adversarial_config: AttackAdversarialConfig,
    scoring_config: AttackScoringConfig,
    converter_config: AttackConverterConfig | None,
) -> AttackStrategy:
    try:
        builder = STRATEGIES[name]
    except KeyError:
        raise ValueError(f"Unknown pyrit_strategy {name!r}. Known strategies: {list(STRATEGIES)}") from None
    return builder(objective_target, adversarial_config, scoring_config, converter_config)

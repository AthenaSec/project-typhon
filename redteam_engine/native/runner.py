"""Sends attack pack prompts to the target agent and judges the responses."""

import logging
import uuid
from pathlib import Path

import httpx
import yaml

from observability.store import save_finding
from redteam_engine.judge import judge_attack
from redteam_engine.schemas import Attack, AttackPack, AttackResult

DEFAULT_TIMEOUT = 60.0

logger = logging.getLogger(__name__)


def load_attack_pack(path: Path | str) -> AttackPack:
    data = yaml.safe_load(Path(path).read_text())
    return AttackPack(**data)


def send_attack(target_url: str, attack: Attack) -> str:
    response = httpx.post(
        f"{target_url.rstrip('/')}/chat",
        json={"message": attack.prompt, "conversation_id": str(uuid.uuid4())},
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["response"]


def run_pack(target_url: str, pack: AttackPack, run_id: str) -> list[AttackResult]:
    print(f"\n[{pack.category}] running {len(pack.attacks)} attacks")
    results = []
    for attack in pack.attacks:
        print(f"  {attack.id:<8} {attack.name:<40} ", end="", flush=True)
        try:
            response = send_attack(target_url, attack)
            judgment = judge_attack(pack.category, attack, response)
        except Exception:
            logger.exception("Attack %s (%s) failed", attack.id, pack.category)
            print("ERROR")
            continue

        print("VULNERABLE" if judgment.vulnerable else "held")
        save_finding(run_id, pack.category, attack, response, judgment)
        results.append(
            AttackResult(category=pack.category, attack=attack, response=response, judgment=judgment)
        )
    return results

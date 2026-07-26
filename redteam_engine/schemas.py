"""Pydantic models shared across the red-team engine."""

from pydantic import BaseModel


class Attack(BaseModel):
    id: str
    name: str
    prompt: str
    goal: str


class AttackPack(BaseModel):
    category: str
    description: str
    attacks: list[Attack]


class Judgment(BaseModel):
    vulnerable: bool
    rationale: str


class AttackResult(BaseModel):
    category: str
    attack: Attack
    response: str
    judgment: Judgment

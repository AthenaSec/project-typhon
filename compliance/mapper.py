"""Maps red-team findings (by category) to EU AI Act articles.

article_map.yaml is data, not code — attack category is the join key
between what the red-team engine found and which article it's evidence
for. Only vulnerable findings get mapped; a "held" result isn't a
compliance gap.
"""

import json
import logging
from pathlib import Path

import yaml

ARTICLE_MAP_PATH = Path(__file__).parent / "article_map.yaml"

logger = logging.getLogger(__name__)


def load_article_map() -> dict:
    return yaml.safe_load(ARTICLE_MAP_PATH.read_text())


def map_findings(findings: list[dict]) -> list[dict]:
    article_map = load_article_map()
    mapped = []
    for finding in findings:
        if not finding.get("vulnerable"):
            continue
        category = finding["category"]
        mapping = article_map.get(category)
        if mapping is None:
            logger.warning("No article mapping for category %r (attack %s)", category, finding.get("attack_id"))
            continue
        turns = json.loads(finding["trace"])["turns"] if finding.get("trace") else None
        mapped.append({**finding, **mapping, "turns": turns})
    return mapped

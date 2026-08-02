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


def list_all_mappings() -> list[dict]:
    """Every category -> article mapping in article_map.yaml, regardless of
    whether that category has ever fired a finding. Used for the report's and
    dashboard's mapping reference table, so the full IP in article_map.yaml is
    visible even for categories a given run didn't trigger."""
    article_map = load_article_map()
    return sorted(
        ({"category": category, **mapping} for category, mapping in article_map.items()),
        key=lambda m: m["category"],
    )


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


def list_unmapped_categories(findings: list[dict]) -> set[str]:
    """Categories of vulnerable findings with no article_map.yaml entry —
    these get silently dropped by map_findings, so the dashboard/report
    surface this explicitly rather than let a finding vanish with no trace
    of why."""
    article_map = load_article_map()
    return {
        f["category"]
        for f in findings
        if f.get("vulnerable") and f["category"] not in article_map
    }

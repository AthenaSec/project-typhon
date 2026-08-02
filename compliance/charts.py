"""Chart geometry for the HTML report's infographics.

Precomputed here so the Jinja template only loops over ready-made drawing
values (dasharray/dashoffset, bar percentages) instead of doing SVG arc math
or scaling in the template itself.
"""

import math

DONUT_RADIUS = 60
DONUT_STROKE = 24
DONUT_CIRCUMFERENCE = 2 * math.pi * DONUT_RADIUS


def build_pass_fail_donut(findings: list[dict]) -> dict:
    """Vulnerable-vs-held breakdown as SVG <circle> stroke-dasharray segments
    (a full arc-path implementation isn't needed for a two-segment donut)."""
    total = len(findings)
    vulnerable = sum(1 for f in findings if f["vulnerable"])
    held = total - vulnerable

    segments = []
    offset = 0.0
    for label, count, css_class in (
        ("Vulnerable", vulnerable, "donut-vulnerable"),
        ("Held", held, "donut-held"),
    ):
        if count == 0:
            continue
        length = DONUT_CIRCUMFERENCE * count / total
        segments.append(
            {
                "label": label,
                "count": count,
                "class": css_class,
                "dasharray": f"{length:.2f} {DONUT_CIRCUMFERENCE - length:.2f}",
                "dashoffset": f"{-offset:.2f}",
            }
        )
        offset += length

    return {
        "radius": DONUT_RADIUS,
        "stroke": DONUT_STROKE,
        "circumference": DONUT_CIRCUMFERENCE,
        "segments": segments,
        "total": total,
        "vulnerable": vulnerable,
        "held": held,
    }


def build_article_bar_chart(compliance_findings: list[dict]) -> list[dict]:
    """Findings-per-article counts, scaled to the largest bar."""
    counts: dict[str, int] = {}
    for f in compliance_findings:
        counts[f["article"]] = counts.get(f["article"], 0) + 1

    if not counts:
        return []

    max_count = max(counts.values())
    return [
        {"article": article, "count": count, "pct": round(count / max_count * 100)}
        for article, count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]

"""Renders a run's compliance-mapped findings into an audit-style HTML report.

The report is the real deliverable — the live attack is the hook. Findings
and attack transcripts come from the target/attacker, so they're untrusted
content; autoescaping (the Jinja2 default for .html templates) is what
keeps a hostile response from breaking the report's HTML.
"""

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup

from compliance.mapper import map_findings
from observability.store import get_findings, get_run

TEMPLATE_DIR = Path(__file__).parent / "templates"
REPORTS_DIR = Path(__file__).parent.parent / "reports"

# html=False escapes any raw HTML in the source text instead of passing it
# through — the judge's rationale is derived from the target's (untrusted)
# response, so this keeps the markdown rendering from becoming an XSS vector.
_md = MarkdownIt("commonmark", {"html": False})


def _render_markdown(text: str) -> Markup:
    return Markup(_md.render(text))


_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)
_env.filters["markdown"] = _render_markdown


def generate_report(run_id: str) -> Path:
    run = get_run(run_id)
    findings = get_findings(run_id)
    compliance_findings = map_findings(findings)

    template = _env.get_template("report.html")
    html = template.render(
        run=run,
        findings=findings,
        compliance_findings=compliance_findings,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )

    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = REPORTS_DIR / f"report_{run_id}.html"
    output_path.write_text(html)
    return output_path

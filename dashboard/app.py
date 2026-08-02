"""Interactive companion to the static HTML report.

Reads the same observability DB and compliance mapping the CLI/report use —
no separate data path. Run with:

    uv sync --group dashboard
    uv run --group dashboard streamlit run dashboard/app.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from compliance.mapper import list_all_mappings, list_unmapped_categories, map_findings
from observability.store import get_findings, list_runs
from redteam_engine.schemas import ENGINE_LABELS

# Status colors are reserved for pass/fail semantics and never reused for
# anything else (engine mix, trend bars, etc. get the neutral accent below).
VULNERABLE_COLOR = "#b3261e"
HELD_COLOR = "#1e6b3c"
ACCENT_COLOR = "#3b5bdb"
MUTED_COLOR = "#5a5a5a"

st.set_page_config(
    page_title="project-typhon: Red-Team Dashboard",
    page_icon="\U0001F6E1️",
    layout="wide",
)

st.markdown(
    """
    <style>
      html, body, [class*="css"]  { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }
      div[data-testid="stMetric"] {
        background: var(--background-color, transparent);
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 6px;
        padding: 12px 16px 8px;
      }
      div[data-testid="stMetricLabel"] { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; opacity: 0.75; }
      .typhon-caption { font-size: 0.82rem; opacity: 0.7; margin-top: -6px; }
      .typhon-pill {
        display: inline-block; font-size: 0.72rem; font-weight: 600;
        padding: 2px 9px; border-radius: 999px; margin-right: 6px;
      }
      .typhon-pill-vuln { color: #b3261e; background: rgba(179,38,30,0.12); }
      .typhon-pill-held { color: #1e6b3c; background: rgba(30,107,60,0.12); }
      .typhon-pill-engine { color: #5a5a5a; background: rgba(90,90,90,0.12); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI Red-Team & EU AI Act Compliance Dashboard")
st.caption(
    "Automated adversarial assessment. Attacks are generated and delivered by a red-team engine "
    "(native / promptfoo / PyRIT); every pass/fail verdict is graded by a single shared judge, "
    "never an engine's own grader — see AGENTS.md."
)

runs = list_runs()
if not runs:
    st.warning("No runs found. Run `python cli.py run --target <url>` first.")
    st.stop()

run_options = {"All runs": None}
for run in runs:
    label = f"{run['started_at'][:19]} — {run['target_url']} ({run['id'][:8]})"
    run_options[label] = run["id"]

st.sidebar.header("Scope")
selected_label = st.sidebar.selectbox("Run", options=list(run_options.keys()))
selected_run_id = run_options[selected_label]

if selected_run_id:
    run_meta = next(r for r in runs if r["id"] == selected_run_id)
    st.sidebar.markdown(f"**Target**  \n{run_meta['target_url']}")
    st.sidebar.markdown(f"**Started**  \n{run_meta['started_at'][:19]}")
    st.sidebar.markdown(f"**Finished**  \n{(run_meta['finished_at'] or 'in progress')[:19]}")
else:
    st.sidebar.markdown(f"**Runs in scope**  \n{len(runs)}")

findings = get_findings(selected_run_id)
compliance_findings = map_findings(findings)
unmapped_categories = list_unmapped_categories(findings)

if unmapped_categories:
    st.warning(
        "Vulnerable finding(s) in "
        f"{len(unmapped_categories)} categor{'y' if len(unmapped_categories) == 1 else 'ies'} "
        f"have no EU AI Act mapping and are excluded from the Compliance Mapping views below: "
        f"{', '.join(sorted(unmapped_categories))}. Add an entry to compliance/article_map.yaml.",
        icon="⚠️",
    )

total = len(findings)
vulnerable_count = sum(1 for f in findings if f["vulnerable"])
held_count = total - vulnerable_count
vulnerability_rate = f"{vulnerable_count / total:.0%}" if total else "—"
distinct_articles = len({f["article"] for f in compliance_findings})

tab_overview, tab_findings, tab_mapping, tab_about = st.tabs(
    ["Overview", "Findings", "Compliance Mapping", "Methodology"]
)

# ---------------------------------------------------------------- Overview
with tab_overview:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Attacks Run", total)
    kpi2.metric("Vulnerabilities Found", vulnerable_count)
    kpi3.metric("Vulnerability Rate", vulnerability_rate)
    kpi4.metric("Articles Implicated", distinct_articles)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        with st.container(border=True):
            st.subheader("Vulnerable vs. Held")
            if total:
                pass_fail_df = pd.DataFrame(
                    [
                        {"result": "Vulnerable", "count": vulnerable_count},
                        {"result": "Held", "count": held_count},
                    ]
                )
                donut = (
                    alt.Chart(pass_fail_df)
                    .mark_arc(innerRadius=60, cornerRadius=3)
                    .encode(
                        theta="count",
                        color=alt.Color(
                            "result",
                            scale=alt.Scale(domain=["Vulnerable", "Held"], range=[VULNERABLE_COLOR, HELD_COLOR]),
                            legend=alt.Legend(title=None, orient="bottom"),
                        ),
                        tooltip=["result", "count"],
                    )
                )
                st.altair_chart(donut, width="stretch")
            else:
                st.caption("No attacks recorded for this scope.")

    with chart_col2:
        with st.container(border=True):
            st.subheader("Findings by Article")
            if compliance_findings:
                article_counts = pd.DataFrame(compliance_findings)["article"].value_counts().reset_index()
                article_counts.columns = ["article", "count"]
                bar = (
                    alt.Chart(article_counts)
                    .mark_bar(color=VULNERABLE_COLOR, cornerRadiusEnd=3)
                    .encode(
                        x=alt.X("count", title="Findings"),
                        y=alt.Y("article", sort="-x", title=None),
                        tooltip=["article", "count"],
                    )
                )
                st.altair_chart(bar, width="stretch")
                if len(article_counts) == 1:
                    st.markdown(
                        '<p class="typhon-caption">Every fired attack category in this scope cites the same '
                        "article — that's expected, not a rendering issue. See the <b>Compliance Mapping</b> "
                        "tab: most attack categories (prompt injection, impersonation, escalation, extraction, "
                        "code-execution claims, IP leakage, data leakage, output injection) are all evidence "
                        "for <b>Article 15(5)</b> (robustness/cybersecurity), because that's the article the "
                        "official text actually pins that behavior to. Other mapped articles only appear once "
                        "a category like <i>imitation</i> (Article 50(1)) or a prohibited-practice case "
                        "(Article 5) fires.</p>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No vulnerabilities in this scope.")

    engine_col, trend_col = st.columns(2)

    with engine_col:
        with st.container(border=True):
            st.subheader("Attacks by Engine")
            if total:
                engine_df = pd.DataFrame(findings)
                engine_df["engine_label"] = engine_df["engine"].map(ENGINE_LABELS).fillna(engine_df["engine"])
                engine_counts = engine_df["engine_label"].value_counts().reset_index()
                engine_counts.columns = ["engine", "count"]
                engine_bar = (
                    alt.Chart(engine_counts)
                    .mark_bar(color=ACCENT_COLOR, cornerRadiusEnd=3)
                    .encode(
                        x=alt.X("count", title="Attacks"),
                        y=alt.Y("engine", sort="-x", title=None),
                        tooltip=["engine", "count"],
                    )
                )
                st.altair_chart(engine_bar, width="stretch")
            else:
                st.caption("No attacks recorded for this scope.")

    with trend_col:
        with st.container(border=True):
            if selected_run_id is None:
                st.subheader("Vulnerabilities per Run")
                per_run = pd.DataFrame(
                    [
                        {
                            "run": f"{r['started_at'][:10]} ({r['id'][:8]})",
                            "started_at": r["started_at"],
                            "vulnerable": sum(1 for f in get_findings(r["id"]) if f["vulnerable"]),
                        }
                        for r in runs
                    ]
                ).sort_values("started_at")
                trend = (
                    alt.Chart(per_run)
                    .mark_bar(color=VULNERABLE_COLOR, cornerRadiusEnd=3)
                    .encode(
                        x=alt.X("run", sort=None, title=None),
                        y=alt.Y("vulnerable", title="Vulnerabilities"),
                        tooltip=["run", "vulnerable"],
                    )
                )
                st.altair_chart(trend, width="stretch")
            else:
                st.subheader("Severity (PyRIT findings)")
                severities = []
                for f in findings:
                    if f.get("trace"):
                        trace = json.loads(f["trace"])
                        if trace.get("severity") is not None:
                            severities.append({"attack": f["attack_name"], "severity": trace["severity"]})
                if severities:
                    sev_df = pd.DataFrame(severities)
                    sev_chart = (
                        alt.Chart(sev_df)
                        .mark_bar(color=VULNERABLE_COLOR, cornerRadiusEnd=3)
                        .encode(
                            x=alt.X("severity", title="Severity (0–1)", scale=alt.Scale(domain=[0, 1])),
                            y=alt.Y("attack", sort="-x", title=None),
                            tooltip=["attack", "severity"],
                        )
                    )
                    st.altair_chart(sev_chart, width="stretch")
                else:
                    st.caption("No PyRIT severity scores recorded for this scope.")

# ---------------------------------------------------------------- Findings
with tab_findings:
    if not findings:
        st.caption("No findings for this scope.")
    else:
        findings_df = pd.DataFrame(findings)
        findings_df["engine_label"] = findings_df["engine"].map(ENGINE_LABELS).fillna(findings_df["engine"])

        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
        with filter_col1:
            category_filter = st.multiselect(
                "Category", sorted(findings_df["category"].unique()), placeholder="All categories"
            )
        with filter_col2:
            engine_filter = st.multiselect(
                "Engine", sorted(findings_df["engine_label"].unique()), placeholder="All engines"
            )
        with filter_col3:
            result_filter = st.radio("Result", ["All", "Vulnerable", "Held"], horizontal=True)

        view = findings_df
        if category_filter:
            view = view[view["category"].isin(category_filter)]
        if engine_filter:
            view = view[view["engine_label"].isin(engine_filter)]
        if result_filter == "Vulnerable":
            view = view[view["vulnerable"] == 1]
        elif result_filter == "Held":
            view = view[view["vulnerable"] == 0]

        st.caption(f"{len(view)} of {len(findings_df)} attacks shown")
        st.dataframe(
            view[["category", "attack_name", "engine_label", "vulnerable", "rationale"]].rename(
                columns={"engine_label": "engine"}
            ),
            width="stretch",
            hide_index=True,
            column_config={
                "vulnerable": st.column_config.CheckboxColumn("Vulnerable"),
            },
        )

        st.divider()
        st.subheader("Inspect an attack")
        options = {f"{row.category} — {row.attack_name}": row.Index for row in view.itertuples()}
        if options:
            pick = st.selectbox("Attack", options=list(options.keys()))
            row = findings_df.loc[options[pick]]

            status_class = "typhon-pill-vuln" if row["vulnerable"] else "typhon-pill-held"
            status_label = "Vulnerable" if row["vulnerable"] else "Held"
            st.markdown(
                f'<span class="typhon-pill {status_class}">{status_label}</span>'
                f'<span class="typhon-pill typhon-pill-engine">{row["engine_label"]}</span>',
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                st.markdown(f"**Goal:** {row['attack_goal']}")
                st.markdown(f"**Judge rationale:** {row['rationale']}")

                trace = json.loads(row["trace"]) if row.get("trace") else None
                turns = trace.get("turns") if trace else None
                if turns:
                    st.markdown(f"**Conversation transcript** ({len(turns)} turn{'s' if len(turns) != 1 else ''})")
                    for t in turns:
                        st.caption(f"Turn {t['turn']}")
                        st.text_area("Attacker", t["prompt"], height=80, disabled=True, key=f"p{row.name}{t['turn']}")
                        st.text_area("Target", t["response"], height=80, disabled=True, key=f"r{row.name}{t['turn']}")
                else:
                    st.markdown(f"**Prompt:** {row['attack_prompt']}")
                    st.markdown(f"**Response:** {row['response']}")

# ---------------------------------------------------------- Compliance Mapping
with tab_mapping:
    st.subheader("Attack categories → EU AI Act articles")
    st.caption(
        "Every category this tool knows about, regardless of whether it fired in the current scope. "
        "Article citations are pinned to the specific paragraph a category's behavior falls under, "
        "not just the top-level article — see compliance/article_map.yaml."
    )

    mappings = list_all_mappings()
    mapping_df = pd.DataFrame(mappings)

    coverage_col, table_col = st.columns([1, 2])
    with coverage_col:
        with st.container(border=True):
            st.markdown("**Categories per article**")
            coverage = mapping_df["article"].value_counts().reset_index()
            coverage.columns = ["article", "categories"]
            coverage_bar = (
                alt.Chart(coverage)
                .mark_bar(color=ACCENT_COLOR, cornerRadiusEnd=3)
                .encode(
                    x=alt.X("categories", title="Mapped categories"),
                    y=alt.Y("article", sort="-x", title=None),
                    tooltip=["article", "categories"],
                )
            )
            st.altair_chart(coverage_bar, width="stretch")
            st.markdown(
                '<p class="typhon-caption">This is why one article can dominate the Overview chart — it\'s '
                "how many categories legitimately cite it, not a display bug.</p>",
                unsafe_allow_html=True,
            )

    with table_col:
        with st.container(border=True):
            st.markdown("**Full mapping reference**")
            display_cols = ["category", "article", "title"]
            if "secondary_article" in mapping_df.columns:
                mapping_df["secondary"] = mapping_df["secondary_article"].fillna("")
                display_cols.append("secondary")
            st.dataframe(
                mapping_df[display_cols].rename(columns={"secondary": "secondary article"}),
                width="stretch",
                hide_index=True,
                height=360,
            )

    st.subheader("Rationale & remediation")
    for m in mappings:
        with st.expander(f"{m['category']} — {m['article']}"):
            st.markdown(f"**{m['title']}**")
            st.markdown(m["compliance_rationale"])
            st.markdown(f"**Remediation:** {m['remediation']}")
            if m.get("secondary_article"):
                st.divider()
                st.markdown(f"**Secondary: {m['secondary_article']} — {m.get('secondary_title', '')}**")
                st.markdown(m.get("secondary_rationale", ""))

# --------------------------------------------------------------- Methodology
with tab_about:
    st.subheader("How this assessment works")
    st.markdown(
        """
1. **Attack** — a red-team engine (native attack packs, promptfoo, or PyRIT) generates
   and delivers adversarial prompts against the target's chat endpoint. An engine's job stops
   at producing a prompt and collecting the target's response.
2. **Judge** — every response is graded by a single shared judge (`redteam_engine/judge.py`),
   never by an engine's own built-in grader. This matters in practice: promptfoo's built-in
   grader was observed marking a response "pass — model refused" when the target had actually
   leaked its system prompt verbatim. The judge's rubric is written specifically for this
   project's EU AI Act mapping, so it's the single source of truth for pass/fail.
3. **Map** — vulnerable findings are mapped to specific EU AI Act articles and paragraphs
   via `compliance/article_map.yaml`, a hand-curated, data-driven mapping — not generated
   by the judge or the engine.
4. **Report** — this dashboard and the generated HTML report (`reports/report_<run_id>.html`)
   read the same observability database and the same mapping module, so both views always agree.
        """
    )
    st.info(
        "EU AI Act article mappings in this tool are illustrative for demo purposes, not "
        "certified legal advice. Most Article 15/12/13/14 obligations only bind systems "
        "already classified \"high-risk\" under Annex III — a real compliance mapping would "
        "confirm that classification first. Re-verify against the official text before this "
        "goes in front of an actual compliance officer.",
        icon="ℹ️",
    )

    st.subheader("Articles this tool doesn't test")
    st.markdown(
        "Automated red-teaming can only produce evidence for articles a chat response can actually "
        "demonstrate. The following are relevant to a full EU AI Act compliance program but are out of "
        "scope for this tool — mapping a finding to them would mean fabricating evidence, so "
        "`compliance/article_map.yaml` deliberately doesn't:\n\n"
        "- **Article 5(1)(c), (f), (g), (h)** — social scoring, workplace/education emotion inference, "
        "untargeted facial-recognition scraping, real-time biometric identification. This target is "
        "text-only and has none of the biometric/image capabilities these provisions govern.\n"
        "- **Article 9** — Risk Management System. An ongoing organizational process (identify, mitigate, "
        "test, iterate), not a single artifact a chat response can prove or disprove.\n"
        "- **Article 10** — Data and Data Governance. Governs the training/validation/testing data "
        "pipeline itself; a biased or wrong output is symptomatic evidence at best, not direct proof of "
        "a data-governance failure.\n"
        "- **Article 12** — Record-keeping (automatic logging). An infrastructure property, not "
        "observable from chat behavior.\n"
        "- **Article 13** — Transparency and information provided to deployers. Documentation the "
        "provider hands to a deployer, not something live chat responses demonstrate.\n"
        "- **Article 16/17** — Quality management system obligations for providers. An organizational "
        "management-system requirement.\n"
        "- **Article 50(2)-(4)** — deepfake/synthetic-content and emotion-recognition/biometric-"
        "categorization disclosure. Requires image/audio synthesis or emotion-recognition capabilities "
        "this target doesn't have.\n"
        "- **Annex III high-risk classification** — a prerequisite legal determination this tool doesn't "
        "make, not something red-teaming itself establishes."
    )

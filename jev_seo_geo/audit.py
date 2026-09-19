"""End-to-end GEO audit report."""

from __future__ import annotations

from dataclasses import dataclass, field
from jev_seo_geo.validation import safe_error, validate_text
from html import escape
from pathlib import Path
from typing import Any

from jev_seo_geo.client import JevClient, LLMProber
from jev_seo_geo.gap import GapReport, analyze as analyze_gap
from jev_seo_geo.score import ContentScore, content as score_content


@dataclass
class AuditReport:
    """Combined content and AI-visibility audit."""

    brand: str
    domain: str
    category: str
    content_score: ContentScore | None
    gap_report: GapReport | None
    status: str
    errors: dict[str, str] = field(default_factory=dict)

    def save(self, path: str | Path) -> Path:
        """Save a self-contained HTML report."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_html(), encoding="utf-8")
        return output

    def to_html(self) -> str:
        content = self.content_score
        gap = self.gap_report
        score_html = "<p>Content scoring unavailable or skipped.</p>"
        if content:
            suggestions = "".join(f"<li>{escape(item)}</li>" for item in content.suggestions) or "<li>No major gaps detected.</li>"
            score_html = f"""
            <table><tr><th>Heuristic E-E-A-T signals</th><th>Citation readiness</th><th>Structure</th><th>Freshness</th><th>Overall</th></tr>
            <tr><td>{content.eeat:.2f}</td><td>{content.citation_ready:.2f}</td><td>{content.structure:.2f}</td><td>{content.freshness:.2f}</td><td><strong>{content.overall:.2f}</strong></td></tr></table>
            <h3>Content recommendations</h3><ul>{suggestions}</ul>"""

        visibility_html = "<p>No LLM provider key available. AI visibility probing skipped.</p>"
        if gap:
            rows = "".join(f"<tr><td>{escape(name)}</td><td>{format(rate, '.0%') if rate is not None else 'unavailable'}</td></tr>" for name, rate in gap.mention_comparison.items())
            recs = "".join(f"<li>{escape(item)}</li>" for item in gap.recommendations)
            visibility_html = f"<table><tr><th>Brand</th><th>AI mention rate</th></tr>{rows}</table><pre>{escape(gap.summary)}</pre><h3>Visibility recommendations</h3><ul>{recs}</ul>"

        return f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>GEO Audit: {escape(self.brand)}</title>
        <style>body{{font:16px system-ui,sans-serif;max-width:900px;margin:48px auto;color:#172033}}h1{{margin-bottom:4px}}section{{border:1px solid #dce3ed;border-radius:10px;padding:24px;margin:20px 0}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border:1px solid #dce3ed;text-align:left}}th{{background:#f4f7fb}}pre{{white-space:pre-wrap;background:#f4f7fb;padding:12px;border-radius:6px}}</style></head>
        <body><h1>GEO Audit: {escape(self.brand)}</h1><p>{escape(self.domain)} · {escape(self.category)}</p><p><strong>Status:</strong> {escape(self.status)}</p>
        <p>Sampled API mentions only, not endorsements. Scores are unverified heuristics, not official Google ratings or factual verification.</p><p>Errors: {escape(str(self.errors))}</p><section><h2>Content quality</h2>{score_html}</section><section><h2>AI visibility</h2>{visibility_html}</section></body></html>"""


def run(
    brand: str,
    domain: str,
    category: str,
    competitors: list[str],
    *,
    queries: list[str] | None = None,
    content: str | None = None,
    models: list[str] | None = None,
    jev: JevClient | None = None,
    prober: LLMProber | None = None,
) -> AuditReport:
    """Run a combined GEO audit.

    Content is optional. AI visibility needs one configured LLM provider. If no
    provider key is available, the audit still returns a usable content report.
    """
    validate_text(brand, "brand")
    j = jev
    p = prober or LLMProber()
    content_score = None
    errors = {}
    if content is not None:
        try:
            content_score = score_content(content, url=domain, topic=category, client=j)
        except Exception as exc:
            errors["content"] = safe_error(exc)

    prompt_set = queries or [
        f"best {category}",
        f"{category} comparison",
        f"how to choose a {category}",
    ]
    gap_report = None
    if p.available_models:
        gap_report = analyze_gap(brand, competitors, prompt_set, models=models, prober=p, jev=j)

    if gap_report and gap_report.brand_report.error_count:
        errors["visibility"] = gap_report.brand_report.status
    successful = content_score is not None or (gap_report is not None and gap_report.brand_report.success_count > 0)
    status = "partial" if successful and errors else "failed" if errors else "complete" if successful else "no_input"

    return AuditReport(brand, domain, category, content_score, gap_report, status, errors)

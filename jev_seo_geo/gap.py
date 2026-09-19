"""Descriptive comparisons on shared API observations, not causal diagnosis."""
from __future__ import annotations
from dataclasses import dataclass
from jev_seo_geo.probe import BrandReport, capture, evaluate
from jev_seo_geo.validation import validate_text


@dataclass
class GapReport:
    brand: str
    competitors: list[str]
    brand_report: BrandReport
    competitor_reports: dict[str, BrandReport]
    summary: str
    recommendations: list[str]
    mention_comparison: dict[str, float | None]


def analyze(brand_name: str, competitors: list[str], queries: list[str], *, models=None, prober=None, jev=None, samples=1) -> GapReport:
    validate_text(brand_name, "brand")
    unique = []
    seen = {brand_name.strip().casefold()}
    for comp in competitors:
        validate_text(comp, "competitor")
        if comp.strip().casefold() not in seen:
            unique.append(comp)
            seen.add(comp.strip().casefold())
    observations = capture(queries, models=models, prober=prober, samples=samples)
    target = evaluate(brand_name, observations)
    reports = {comp: evaluate(comp, observations) for comp in unique}
    rates = {brand_name: target.mention_rate, **{name: r.mention_rate for name, r in reports.items()}}
    summary = "\n".join(f"{name}: {rate:.0%} mention rate" if rate is not None else f"{name}: unavailable (no successful observations)" for name, rate in rates.items())
    summary += f"\nSuccessful observations: {target.success_count}; errors: {target.error_count}."
    summary += "\nDescriptive sample only; mentions are not endorsements and differences do not establish causes."
    recommendations = []
    if target.mention_rate is not None:
        higher = [name for name, r in reports.items() if r.mention_rate > target.mention_rate]
        if higher:
            recommendations.append("Review sampled responses mentioning " + ", ".join(higher) + "; investigate independently before changing content.")
        recommendations.append("Repeat a stable, neutral query set; validate any editorial hypotheses independently.")
    return GapReport(brand_name, unique, target, reports, summary, recommendations, rates)

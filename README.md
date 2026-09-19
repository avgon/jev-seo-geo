# jev-seo-geo

AI visibility toolkit. Measure and optimize how AI models see your brand.

> Traditional SEO tools measure Google rankings. This measures **ChatGPT, Perplexity, Claude, and Gemini rankings.**

## The Problem

Someone asks ChatGPT *"best project management tool for startups"* and your product doesn't appear. You have no idea why. Ahrefs can't help you. Semrush can't help you. Google Search Console is irrelevant.

**GEO (Generative Engine Optimization)** is the new SEO. But there's no open-source tooling.

## Install

```bash
pip install jev-seo-geo
```

## Quick Start

### 1. Brand Probe — "Do AI models know about me?"

```python
from jev_seo_geo import probe

results = probe.brand(
    brand="Vercel",
    queries=[
        "best platform for deploying Next.js apps",
        "alternatives to Heroku for frontend hosting",
        "serverless deployment platforms comparison",
    ],
    models=["openai", "anthropic", "google"],
)

for r in results:
    print(f"{r.model} | {r.query[:40]} | mentioned={r.mentioned} | rank={r.rank}")
# openai    | best platform for deploying Next.js... | mentioned=True  | rank=1
# anthropic | best platform for deploying Next.js... | mentioned=True  | rank=2
# google    | best platform for deploying Next.js... | mentioned=True  | rank=1
```

### 2. Content Score — "Is my page AI-friendly?"

```python
from jev_seo_geo import score

result = score.content(
    text="Your page content or article text here...",
    url="https://yoursite.com/blog/post",  # optional, for structure check
)
print(result)
# ContentScore(
#   eeat=0.72,           # Experience, Expertise, Authority, Trust
#   citation_ready=0.85, # Would AI cite this as a source?
#   structure=0.60,      # Headers, lists, data tables, schema
#   freshness=0.90,      # Up-to-date signals
#   overall=0.77,
#   suggestions=["Add author bio with credentials", "Include data sources"]
# )
```

### 3. Title Arena — "Which headline wins?"

```python
from jev_seo_geo import arena

ranked = arena.titles(
    titles=[
        "10 Best CRM Tools for Small Business in 2026",
        "CRM Comparison: HubSpot vs Salesforce vs Pipedrive",
        "How to Choose a CRM: Complete Buyer's Guide",
        "We Tested 10 CRMs For 6 Months. Here's What We Found.",
    ],
    intent="someone researching CRM options for their startup",
)
for t in ranked:
    print(f"#{t.rank} (score={t.score:.2f}) {t.title}")
# #1 (score=0.89) We Tested 10 CRMs For 6 Months. Here's What We Found.
# #2 (score=0.76) CRM Comparison: HubSpot vs Salesforce vs Pipedrive
# ...
```

### 4. Competitor Gap — "Why does AI recommend them over me?"

```python
from jev_seo_geo import gap

report = gap.analyze(
    brand="Pipedrive",
    competitors=["HubSpot", "Salesforce"],
    queries=[
        "best CRM for sales teams",
        "easiest CRM to set up",
        "CRM with best API",
    ],
)
print(report.summary)
# "HubSpot mentioned in 3/3 queries across all models.
#  Pipedrive mentioned in 1/3. Gap: authority signals, comparison content."
print(report.recommendations)
# ["Create comparison pages: Pipedrive vs HubSpot",
#  "Add API documentation with examples",
#  "Publish customer case studies with metrics"]
```

### 5. Optimize — Find gaps, get a practical fix plan, optionally rewrite

```python
from jev_seo_geo import optimize

# Jev-only, no generative-model key needed
plan = optimize.checklist("CRM is important for business. Pick the best one.")
for item in plan:
    print(item["priority"], item["action"])

# With OpenAI / Anthropic / Gemini key: diagnose, rewrite, then re-score
result = optimize.rewrite(
    text="CRM is important for business. Pick the best one.",
    topic="CRM software for startups",
    focus="all",  # eeat, structure, citation, freshness, or all
)
print(result.before.overall)
print(result.improvement)
print(result.rewritten)
```

### 6. GEO Audit — Full visibility report

```python
from jev_seo_geo import audit

report = audit.run(
    brand="YourBrand",
    domain="yourbrand.com",
    category="project management software",
    competitors=["Notion", "Asana", "Monday"],
)
report.save("geo-audit-2026-09.html")
```

## How It Works

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐
│  AI Models   │────▶│  Probe   │────▶│  Brand       │
│  (GPT/Claude │     │  Layer   │     │  Mention     │
│  /Gemini)    │     └──────────┘     │  Detection   │
└─────────────┘                       └──────┬───────┘
                                             │
┌─────────────┐     ┌──────────┐     ┌──────▼───────┐
│  Your       │────▶│  Jev     │────▶│  Score &     │
│  Content    │     │  Engine  │     │  Recommend   │
└─────────────┘     └──────────┘     └──────────────┘

Jev handles: content quality scoring, title ranking, E-E-A-T assessment
LLM APIs handle: brand probing (asking AI models questions)
```

## Configuration

Set environment variables before using the toolkit:

```bash
export TYPESAFE_API_KEY="your_typesafe_key"
export OPENAI_API_KEY="your_openai_key"       # optional, for GPT probing/rewrite
export ANTHROPIC_API_KEY="your_claude_key"    # optional, for Claude probing/rewrite
export GOOGLE_API_KEY="your_gemini_key"       # optional, for Gemini probing/rewrite
```

Only `TYPESAFE_API_KEY` is required for Jev scoring. Probe features and automatic rewrite need at least one LLM key.

## Modules

| Module | What it does | Needs |
|---|---|---|
| `probe` | Ask AI models about your brand | LLM API keys |
| `score` | Rate content for AI-friendliness | Jev only |
| `arena` | Rank titles/headlines | Jev only |
| `gap` | Compare brand vs competitors | LLM + Jev |
| `audit` | Full GEO visibility report | LLM + Jev |
| `optimize` | Diagnoses gaps, creates a fix plan, optionally rewrites and re-scores | Jev, optional LLM |

## License

MIT

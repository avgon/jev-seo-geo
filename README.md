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

### 5. GEO Audit — Full visibility report

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

```python
from jev_seo_geo import Config

config = Config(
    jev_api_key="your_typesafe_key",     # or TYPESAFE_API_KEY env
    openai_api_key="your_openai_key",     # for probing GPT
    anthropic_api_key="your_claude_key",  # for probing Claude
    google_api_key="your_gemini_key",     # for probing Gemini
)
```

Only `jev_api_key` is required. Probe features need at least one LLM key.

## Modules

| Module | What it does | Needs |
|---|---|---|
| `probe` | Ask AI models about your brand | LLM API keys |
| `score` | Rate content for AI-friendliness | Jev only |
| `arena` | Rank titles/headlines | Jev only |
| `gap` | Compare brand vs competitors | LLM + Jev |
| `audit` | Full GEO visibility report | LLM + Jev |

## License

MIT

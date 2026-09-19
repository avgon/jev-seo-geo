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

### 1. Brand Probe — "Yapay zekâ modelleri markamı öneriyor mu?"

```python
from jev_seo_geo import probe

results = probe.brand(
    brand="Vercel",
    queries=[
        "Next.js uygulaması için hızlı ve güvenilir deploy platformu hangisi?",
        "Frontend projelerini yayınlamak için Heroku yerine ne kullanılabilir?",
        "Sunucusuz uygulama yayınlama platformlarını nasıl karşılaştırabilirim?",
    ],
    models=["openai", "anthropic", "google"],
)

for r in results:
    print(f"{r.model} | {r.query[:40]} | mentioned={r.mentioned} | rank={r.rank}")
# openai    | Next.js uygulaması için hızlı... | mentioned=True  | rank=1
# anthropic | Next.js uygulaması için hızlı... | mentioned=True  | rank=2
# google    | Next.js uygulaması için hızlı... | mentioned=True  | rank=1
```

### 2. Content Score — "Sayfam yapay zekâ yanıtları için uygun mu?"

```python
from jev_seo_geo import score

result = score.content(
    text="Sayfa veya blog yazısı metninizi buraya ekleyin...",
    url="https://siteniz.com/blog/yazi",  # isteğe bağlı
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

### 3. Title Arena — "Hangi başlık daha güçlü?"

```python
from jev_seo_geo import arena

ranked = arena.titles(
    titles=[
        "2026'da Küçük İşletmeler İçin En İyi 10 CRM Programı",
        "HubSpot, Salesforce ve Pipedrive Karşılaştırması",
        "Şirketiniz İçin CRM Programı Nasıl Seçilir?",
        "10 CRM Programını 6 Ay Test Ettik: Sonuçlar",
    ],
    intent="Yeni kurduğu şirket için CRM programı araştıran karar verici",
)
for t in ranked:
    print(f"#{t.rank} (score={t.score:.2f}) {t.title}")
# #1 (score=0.89) 10 CRM Programını 6 Ay Test Ettik: Sonuçlar
# #2 (score=0.76) HubSpot, Salesforce ve Pipedrive Karşılaştırması
# ...
```

### 4. Competitor Gap — "Yapay zekâ neden rakibimi benden daha çok öneriyor?"

```python
from jev_seo_geo import gap

report = gap.analyze(
    brand="Pipedrive",
    competitors=["HubSpot", "Salesforce"],
    queries=[
        "Satış ekibi için kullanımı en kolay CRM programı hangisi?",
        "Küçük bir ekip CRM programını en hızlı nasıl kurabilir?",
        "API entegrasyonu güçlü CRM programları hangileri?",
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
plan = optimize.checklist("CRM programları müşteri ilişkilerini yönetmeye yardımcı olur. Ekibiniz için uygun olanı seçin.")
for item in plan:
    print(item["priority"], item["action"])

# With OpenAI / Anthropic / Gemini key: diagnose, rewrite, then re-score
result = optimize.rewrite(
    text="CRM programları müşteri ilişkilerini yönetmeye yardımcı olur. Ekibiniz için uygun olanı seçin.",
    topic="Yeni kurulan şirketler için CRM programı",
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

## Help

- [Usage guide](docs/USAGE_GUIDE.md)
- [FAQ: how it works, keys, scoring, and safe rewrites](docs/FAQ.md)

Open an issue with a minimal reproducible example for bugs or integration questions. Do not include API keys, customer data, or private prompts.

## License

MIT

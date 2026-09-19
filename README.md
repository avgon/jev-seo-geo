# jev-seo-geo

A small Python library for sampled API brand mentions, heuristic content scoring and human-reviewed rewrite drafts. It is not a crawler, search engine or ranking measurement service.

## Install from source

PyPI availability is not verified. Install the reviewed Git revision or a local checkout:

```sh
pip install "git+https://github.com/avgon/jev-seo-geo.git"
# Or, from this checkout:
pip install .
```

Python 3.9+ syntax/API compatibility is intended. This hardening was executed on Python 3.13; 3.9 through 3.12 and 3.14 have not been runtime-tested here. No runtime third-party dependencies. Run offline tests with `python -m unittest discover -s tests -v`.

## Runnable offline examples

These examples use explicit test doubles, never API keys or network access. The dummy scores illustrate the API, not empirical findings.

```python
from jev_seo_geo import probe, gap, score, arena, optimize, audit
from jev_seo_geo.client import LLMProber

class OfflineProber:
    available_models = ["offline"]
    models = {"offline": "fixture-v1"}
    def query(self, prompt, provider, timeout=30):
        return "1. ExampleBrand\n2. OtherBrand"

class OfflineJev:
    def ask(self, state, questions, timeout=30):
        answers = {}
        for name, question in questions.items():
            kind = question["type"]
            value = (next(iter(question["criteria"])) if kind == "choice"
                     else 1 if kind == "score"
                     else 0 if name.startswith("missing_") else 0.7)
            answers[name] = {"type": kind, kind: value}
        return answers

p, j = OfflineProber(), OfflineJev()
report = probe.brand("ExampleBrand", ["best tools for a small team"], prober=p)
for result in report.results:
    print(result.status, result.model_id, result.mentioned, result.rank)
print(report.mention_rate, report.success_count, report.error_count)

comparison = gap.analyze(
    brand_name="ExampleBrand", competitors=["OtherBrand"],
    queries=["best tools for a small team"], prober=p, samples=2,
)
print(comparison.summary)

text = "Our product supports task lists. [VERIFY: independent source]"
print(score.content(text, client=j).structure)
print(arena.titles(["Task list guide", "How to compare task tools"], client=j))
print(optimize.checklist(text, focus="citation", jev=j))
draft = optimize.rewrite(
    text, jev=j, prober=LLMProber(keys={}),
    generator=lambda prompt: "## Task lists\n[VERIFY: source for product claims]",
)
print(draft.status, draft.improvement, draft.unresolved_placeholders)
report = audit.run("ExampleBrand", "example.com", "task tools", ["OtherBrand"],
                   content=text, queries=["task tools"], jev=j, prober=p)
html = report.to_html()  # report.save("audit.html") writes this HTML locally
```

## Real providers, credentials and costs

Real calls are opt-in by calling library functions with configured credentials. Construct `JevClient(api_key=..., model=...)` for scoring. Construct `LLMProber(keys={"openai": ...}, models={"openai": "your-supported-model-id"})` for generation. Built-in provider identifiers are exactly `openai`, `anthropic`, `google`. Unknown providers are rejected; custom compatible prober objects or rewrite callbacks are supported.

With no explicit credentials, constructors can read `TYPESAFE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY`. **Passing `LLMProber(keys={})` explicitly disables provider environment discovery.** Tests pass explicit fixtures and must never use real keys. Jev scoring requires its own key even in checklist-only mode; brand probes and gap comparisons do not require Jev. A content-only audit needs Jev but no generation provider. No-provider rewrite means no generative provider, not offline scoring.

Provider/model defaults are convenience IDs, not a guarantee of availability. All generation model IDs are configurable with `models`; Jev accepts `model`. Requests transmit supplied text/prompts/context to the selected external services and may incur charges. Do not send confidential/customer data without permission. Responses and HTML reports can contain sensitive text. Do not commit keys or log request payloads. No live provider success is claimed by offline contract tests. Default request timeout is 30 seconds (automatic rewrite: 60); there are no automatic retries.

## Measurement contract and limits

* Each unique query/provider/sample is generated once and reused for every brand in `gap.analyze`. `samples` defaults to 1. Duplicate queries/provider identifiers are deduplicated. Costs scale with queries × providers × samples, not number of compared brands.
* `ProbeResult` records provider, configured model ID (not a verified backend identity), UTC timestamp, sample number and detection method. Raw successful response text is retained. Failures have `status="error"`, sanitized error category, `mentioned=None`, `rank=None` and no exception text.
* Mention rates use successful observations only. Zero successes gives `mention_rate=None`; unknown is not zero. Reports include success/error counts and `complete`, `partial` or `failed` status. Per-query best/worst use successful rates, with first-seen tie ordering and no significance claim. `avg_rank=None` means no evidenced ordinal.
* Matching is literal, case-insensitive, Unicode word-boundary aware. It avoids substring matches inside words and supports separated non-Latin names. It does not segment unspaced CJK text, resolve aliases, transliterations or semantic references. Whitespace-only brands are invalid.
* A mention is **not a recommendation**. Rank is only a positive, explicit numbered-list label where the brand starts the item, not a consumer-product ranking. There is no Jev rank judge or fabricated 1/3/5 mapping. Tied title heuristic scores share a rank; gap summaries do not declare tie winners or causal explanations.
* These are API responses, **not consumer ChatGPT rankings**. There is **no Perplexity integration**, live browsing, page fetching, crawl, backlink analysis, indexing check or search-console measurement. `url`/`domain` are context only. Generated responses may be stale, incomplete or biased. A brand-bearing query biases mention rates; prefer a stable neutral query set for comparisons.
* Jev values are **heuristics, not official Google E-E-A-T scoring**, factual verification, calibrated citation probabilities or evidence of SEO gains. Required response fields/types, finite ranges and choices are validated. Raw structure is always 0..2 and divided by 2. Malformed answers raise instead of silently becoming zero.
* Content, titles, query text and captured provider responses have an explicit **12,000-character maximum**. Empty text is rejected. No input is silently truncated and no partial rewrite is attempted. Oversized content raises `ValueError` before scoring; failed provider responses are excluded. No chunking or entire-site coverage is provided. Upstream generation has provider output limits and may end early; the library does not guarantee completeness.
* `optimize.rewrite` returns `no_provider`, `generated`, `generation_failed` or `scoring_failed`. Initial scoring errors raise. A valid draft is retained if subsequent scoring fails, including oversized drafts. `improvement` is only the heuristic after-minus-before score (0 when not scored), not measured SEO uplift. All drafts remain explicitly unverified and require human review, even if no `[VERIFY: ...]` placeholder is found. Check `unresolved_placeholders` and verify every fact/source/date/credential before publishing.
* Audit status is `complete`, `partial`, `failed` or `no_input` for the requested/available work; omitted content/provider sections are not measured. `errors` exposes sanitized stage failures. HTML escapes caller-controlled text.

## Intentional compatibility changes

Function names and primary argument names remain: `probe.brand(brand=...)`, `gap.analyze(brand_name=...)`, and report iteration via `report.results`. `jev` is accepted but unused for probes. Nullable rates/ranks/mentions replace misleading zeros, title ties share ranks, errors are explicit, and invalid/oversized inputs are rejected. `LLMProber.query_all` now returns typed-status dictionaries per provider instead of embedding error strings as responses. Strict Jev answers require an object with `noul`, `score` or `choice` for every requested key; optional `type` must match. Explicit `keys` no longer falls back to unrelated environment credentials.

See [Turkish usage guide](docs/USAGE_GUIDE.md), [FAQ](docs/FAQ.md) and [hardening plan](docs/HARDENING_PLAN.md).

License: MIT.

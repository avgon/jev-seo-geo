# Frequently Asked Questions

## What is measured?

Literal brand mentions in sampled API responses, and heuristic Jev evaluations of supplied text. Not consumer ChatGPT rankings, official Google E-E-A-T scores, actual citation probabilities or SEO uplift. A mention can be negative and is not an endorsement. An ordinal is reported only when the brand starts an explicitly numbered item. Gap comparisons are descriptive, not causal diagnosis.

## Does it browse or crawl? Does it support Perplexity?

No. No live browsing, crawl or URL fetching is implemented. `url` and `domain` are context. Built-in generation providers are OpenAI, Anthropic and Google only. Provider model IDs are configurable and their availability is not guaranteed. No Perplexity integration exists.

## Which keys are required?

Jev scoring/checklist/title evaluation requires a Jev key. Probes and gap comparisons need a generation provider but no Jev key. Rewrite requires initial Jev scoring and optionally a provider or callback. No-provider rewrite still requires Jev. Constructors may read environment keys if credentials are omitted; explicit `LLMProber(keys={})` disables generation-key discovery. See README for exact names and source installation. Do not assume PyPI availability.

## What if the provider fails?

Error observations are unknown, not absent mentions. Rates use only successful observations; no successes means `None`. Results include sanitized error categories, success counts, timestamps, configured model IDs and method metadata. Audits expose `partial`/`failed` states and stage errors. `query_all` returns per-provider status dictionaries. Tests mock HTTP calls and do not demonstrate live service success.

## Are comparisons fair?

All compared brands share the same captured response for each query/provider/sample. That removes independent-generation differences, not all bias. Prompts, model updates, sampling variability and literal matching affect results. Use neutral queries and repeat observations. Ties do not establish a winner. Word boundaries handle separated Unicode names but not unspaced-language segmentation, aliases or semantic references.

## How much content is covered?

The maximum is 12,000 characters per content/title/query/captured response. Oversized text is rejected explicitly, never silently truncated. There is no chunking, whole-site analysis or guarantee that provider-generated text is complete. Initial invalid content raises before scoring. The entire accepted text is sent to the judge/rewrite prompt. URLs are not downloaded.

## Can I publish a rewrite directly?

No. Every rewrite is an unverified draft requiring human review. `unresolved_placeholders` exposes `[VERIFY: ...]` fields, but absence of placeholders is not evidence of factual accuracy. Verify facts, sources, statistics, credentials and dates yourself. The library does not verify facts. `improvement` means heuristic score delta only, not an actual SEO gain.

Statuses are `no_provider`, `generated`, `generation_failed`, `scoring_failed`. Empty/non-string callback results fail generation. A valid draft remains available if re-scoring fails. Initial scoring failures raise rather than returning an invented baseline.

## What are the privacy and cost boundaries?

Real calls send supplied content/context to external services and can cost money. Get permission for sensitive data; do not log/commit credentials. Stored raw responses and reports may contain private content. Default timeout is 30 seconds, rewrite generation 60 seconds; no retries. Tests use explicit offline fixtures and mocked urllib, never discovered real credentials. Run README's offline example before configuring real clients.

## Python compatibility?

Python 3.9+ is intended. This hardening was runtime-tested on 3.13 only. Other versions are not claimed as executed. See README and history for actual build/test evidence and intentional API changes.

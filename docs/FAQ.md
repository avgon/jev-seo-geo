# Frequently Asked Questions

## What does jev-seo-geo do?

It helps teams measure and improve visibility in generative AI answers. It combines:

- **Jev scoring:** evaluates content structure, E-E-A-T-related signals, freshness and citation readiness.
- **AI probes:** asks configured AI providers relevant customer questions and records whether a brand is mentioned.
- **Gap analysis:** compares mention rates against selected competitors.
- **Optimization:** turns scoring gaps into a checklist and can use an LLM callback or provider to draft a revised version.

It is a decision-support toolkit, not a ranking guarantee.

## Does it replace traditional SEO tools?

No. Traditional SEO tools measure search rankings, backlinks, keywords and technical crawl issues. `jev-seo-geo` focuses on a different layer: how content and brands appear in AI-generated answers. They can be used together.

## Which features require API keys?

`TYPESAFE_API_KEY` is needed for Jev scoring.

Brand probing and automatic rewrites need at least one text-generation provider, such as OpenAI, Anthropic, Gemini, or a custom callback. The checklist workflow works with Jev alone.

## How does the custom LLM callback work?

Pass any function that accepts a prompt and returns a string:

```python
from jev_seo_geo import optimize

result = optimize.rewrite(
    "Your existing content...",
    generator=lambda prompt: your_llm_call(prompt),
)
```

This lets teams connect self-hosted models, existing gateways, or other providers without changing the package.

## Are scores official Google or AI-provider rankings?

No. Scores are internal decision-support signals based on the supplied content and Jev evaluation. AI answers also vary by model, prompt, date, location and product updates. Use repeated probes and content changes to track directional progress.

## Can I publish the automatic rewrite directly?

No. Treat it as a draft. Verify every claim, citation, credential, statistic and testimonial before publishing. The optimizer is designed to retain facts and mark missing evidence for verification, but human review remains necessary.

## How should I start?

1. Run `score.content()` on an important page.
2. Use `optimize.checklist()` to create an editorial task list.
3. Test title alternatives with `arena.titles()`.
4. Build a stable query set from real customer questions.
5. Run `probe.brand()` and `gap.analyze()` periodically.
6. Re-measure after changes.

For full examples, see the [Usage Guide](USAGE_GUIDE.md).

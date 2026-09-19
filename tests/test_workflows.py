import tempfile
import unittest
from pathlib import Path

from jev_seo_geo import arena, audit, gap, optimize, probe, score


class FakeJev:
    """Deterministic Jev-compatible test double."""

    def ask(self, state, questions, timeout=30):
        answers = {}
        for key, question in questions.items():
            kind = question["type"]
            if kind == "noul":
                values = {
                    "expertise": 0.8, "authority": 0.7, "trust": 0.9,
                    "citation_ready": 0.75, "freshness": 0.8,
                    "missing_author": 0.0, "missing_sources": 0.0,
                    "missing_data": 0.0, "specificity": 0.8,
                    "click_value": 0.7, "ai_citation": 0.9,
                }
                answers[key] = {"type": "noul", "noul": values.get(key, 0.7)}
            elif kind == "score":
                answers[key] = {"type": "score", "score": 2.0}
            elif kind == "choice":
                criteria = question["criteria"]
                answers[key] = {"type": "choice", "choice": next(iter(criteria))}
        return answers


class FakeProber:
    available_models = ["fake"]

    def query(self, prompt, provider, timeout=30):
        return "Top choices: ExampleBrand, OtherBrand. ExampleBrand is a recommended option."


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.jev = FakeJev()
        self.prober = FakeProber()
        self.text = "A structured product comparison with verified sources."

    def test_content_score(self):
        result = score.content(self.text, topic="CRM", client=self.jev)
        self.assertGreater(result.overall, 0.7)
        self.assertEqual(result.suggestions, [])

    def test_title_arena(self):
        results = arena.titles(["Title A", "Title B"], intent="compare", client=self.jev)
        self.assertEqual([r.rank for r in results], [1, 1])
        self.assertGreater(results[0].score, 0.7)

    def test_checklist_and_callback_rewrite(self):
        plan = optimize.checklist(self.text, jev=self.jev)
        self.assertEqual(plan, [])
        result = optimize.rewrite(
            self.text,
            jev=self.jev,
            prober=self.prober,
            generator=lambda _prompt: "Improved, structured article with sources.",
        )
        self.assertIsNotNone(result.after)
        self.assertTrue(result.rewritten)

    def test_brand_probe_and_gap(self):
        report = probe.brand("ExampleBrand", ["best tools"], prober=self.prober, jev=self.jev)
        self.assertEqual(report.mention_rate, 1.0)
        self.assertIsNone(report.results[0].rank)
        result = gap.analyze("ExampleBrand", ["OtherBrand"], ["best tools"], prober=self.prober, jev=self.jev)
        self.assertIn("ExampleBrand", result.mention_comparison)
        self.assertIn("OtherBrand", result.mention_comparison)

    def test_content_only_audit_saves_html(self):
        class NoProvider:
            available_models = []
        report = audit.run(
            "ExampleBrand", "example.com", "CRM", ["OtherBrand"],
            content=self.text, jev=self.jev, prober=NoProvider(),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = report.save(Path(temp_dir) / "audit.html")
            self.assertTrue(output.exists())
            self.assertIn("GEO Audit", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

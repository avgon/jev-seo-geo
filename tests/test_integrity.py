"""Offline integrity regressions. Network access is forbidden in all tests."""
import json
import math
import os
import re
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock
from jev_seo_geo import probe, gap, score, arena, audit, optimize
from jev_seo_geo.client import JevClient, LLMProber
from jev_seo_geo.validation import MAX_TEXT_CHARS
from test_workflows import FakeJev, FakeProber


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.network = patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_failed_observations_are_unknown(self):
        class Broken(FakeProber):
            def query(self, *a, **kw):
                raise TimeoutError('https://secret?key=secret')
        report = probe.brand('ExampleBrand', ['q'], prober=Broken())
        self.assertIsNone(report.mention_rate)
        self.assertIsNone(report.results[0].mentioned)
        self.assertEqual(report.status, 'failed')
        self.assertEqual(report.error_counts, {'timeout': 1})
        self.assertNotIn('secret', repr(report))
        result = audit.run('ExampleBrand', '', '', [], queries=['q'], prober=Broken())
        self.assertEqual(result.status, 'failed')
        self.assertIn('unavailable', result.to_html())

    def test_partial_denominator(self):
        class Partial(FakeProber):
            n = 0
            def query(self, *a, **kw):
                self.n += 1
                if self.n == 1:
                    raise TimeoutError()
                return 'ExampleBrand'
        report = probe.brand('ExampleBrand', ['q'], prober=Partial(), samples=2)
        self.assertEqual((report.mention_rate, report.success_count, report.error_count, report.status), (1, 1, 1, 'partial'))

    def test_shared_generation_and_metadata(self):
        class Count(FakeProber):
            n = 0
            models = {'fake': 'offline-v1'}
            def query(self, *a, **kw):
                self.n += 1
                return '1. ExampleBrand\n2) OtherBrand'
        p = Count()
        report = gap.analyze('ExampleBrand', ['OtherBrand', 'examplebrand', 'OtherBrand'], ['q', 'q'], prober=p, samples=2)
        self.assertEqual(p.n, 2)
        self.assertEqual(report.competitors, ['OtherBrand'])
        self.assertEqual(report.brand_report.results[0].rank, 1)
        self.assertEqual(report.competitor_reports['OtherBrand'].results[0].rank, 2)
        a, b = report.brand_report.results[0], report.competitor_reports['OtherBrand'].results[0]
        self.assertEqual((a.response, a.timestamp), (b.response, b.timestamp))
        self.assertEqual(a.model_id, 'offline-v1')
        self.assertTrue(a.method)
        self.assertNotIn(' vs ', str(report.recommendations))
        self.assertNotIn('ranks #', report.summary)

    def test_boundaries_and_ordinals(self):
        for brand, text, found, rank in [('Asana', 'Asanator', False, None), ('ASANA', 'asana', True, None), ('品牌', '品牌。', True, None), ('品牌', '大品牌', False, None), ('Asana', '7. **Asana** is an option', True, 7), ('Asana', '2. Other compares with Asana', True, None), ('Asana', 'Not recommending Asana', True, None)]:
            detected = probe._detect_brand(brand, text, object())
            self.assertEqual(detected[:2], (found, rank))
        with self.assertRaises(ValueError):
            probe.brand(' ', ['q'], prober=FakeProber())
        long = 'x ' * 2000 + '\n9. Asana'
        self.assertEqual(probe._detect_brand('Asana', long)[1], 9)

    def test_strict_score_values(self):
        class Modified(FakeJev):
            key, value, delete = 'structure', {'score': 1}, False
            def ask(self, *a, **kw):
                answers = super().ask(*a, **kw)
                if self.delete:
                    del answers[self.key]
                else:
                    answers[self.key] = self.value
                return answers
        c = Modified()
        self.assertEqual(score.content('text', client=c).structure, .5)
        for value in [None, {}, {'score': float('nan')}, {'score': float('inf')}, {'score': -1}, {'score': 3}, {'score': '1'}, {'score': True}, {'type': 'noul', 'score': 1}]:
            c.value = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                score.content('text', client=c)
        c.delete = True
        with self.assertRaises(ValueError):
            score.content('text', client=c)
        c.delete, c.key = False, 'expertise'
        for value in [{'noul': 1.2}, {'probability': .5}, .5]:
            c.value = value
            with self.assertRaises(ValueError):
                score.content('text', client=c)
        c.key, c.value = 'strengths', {'choice': 'invented'}
        with self.assertRaises(ValueError):
            arena.titles(['a'], client=c)

    def test_limits_and_complete_context(self):
        class Capture(FakeJev):
            state = ''
            def ask(self, state, questions, timeout=30):
                self.state = state
                return super().ask(state, questions)
        c = Capture()
        text = 'a' * 5000 + 'TAIL'
        score.content(text, client=c)
        self.assertIn(text, c.state)
        self.assertIn(text, optimize._build_rewrite_prompt(text, [], 'all', ''))
        for call in [lambda: score.content('x'*(MAX_TEXT_CHARS+1), client=c), lambda: optimize.rewrite('x'*(MAX_TEXT_CHARS+1), jev=c, prober=LLMProber(keys={}))]:
            with self.assertRaisesRegex(ValueError, 'nothing was truncated'):
                call()

    def test_focused_checklist_and_missing_actions(self):
        scores = score.ContentScore(.9, .9, .9, .9, .9, ['Add author bio with credentials and experience', 'Include citations, data sources, or references', 'Include citations, data sources, or references'])
        checks = optimize._build_checklist(scores, 'all')
        self.assertEqual(len(checks), 2)
        self.assertEqual(len(optimize._build_checklist(scores, 'eeat')), 1)
        self.assertEqual(optimize._build_checklist(scores, 'structure'), [])
        with self.assertRaises(ValueError):
            optimize.checklist('x', focus='bogus', jev=FakeJev())
        low = score.ContentScore(0, 0, 0, 0, 0, scores.suggestions)
        self.assertEqual(len(optimize._build_checklist(low, 'citation')), 1)
        examples = str(optimize._build_checklist(low, 'all'))
        self.assertNotIn('73%', examples)
        self.assertNotIn('September 2026', examples)
        self.assertIn('VERIFY:', examples)

    def test_rewrite_statuses_and_draft_retention(self):
        kwargs = dict(jev=FakeJev(), prober=LLMProber(keys={}))
        self.assertEqual(optimize.rewrite('text', **kwargs).status, 'no_provider')
        for value in ['', None, {}, '   ']:
            result = optimize.rewrite('text', generator=lambda prompt: value, **kwargs)
            self.assertEqual(result.status, 'generation_failed')
            self.assertEqual(result.error, 'invalid_response')
        def broken(prompt):
            raise RuntimeError('https://secret?key=secret')
        result = optimize.rewrite('text', generator=broken, **kwargs)
        self.assertNotIn('secret', repr(result))
        draft = 'Draft [VERIFY: source]'
        result = optimize.rewrite('text', generator=lambda prompt: draft, **kwargs)
        self.assertEqual(result.status, 'generated')
        self.assertTrue(result.human_review_required and result.unverified_draft)
        self.assertEqual(result.unresolved_placeholders, ['[VERIFY: source]'])
        class ScoreFailure(FakeJev):
            n = 0
            def ask(self, *a, **kw):
                self.n += 1
                if self.n == 2:
                    raise TimeoutError('secret')
                return super().ask(*a, **kw)
        result = optimize.rewrite('text', jev=ScoreFailure(), prober=LLMProber(keys={}), generator=lambda prompt: draft)
        self.assertEqual((result.status, result.rewritten, result.after, result.error), ('scoring_failed', draft, None, 'timeout'))

    def test_no_environment_discovery_with_explicit_keys(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'do-not-use'}):
            self.assertEqual(LLMProber(keys={}).available_models, [])
        with self.assertRaises(ValueError):
            LLMProber(keys={'perplexity': 'x'})
        with self.assertRaises(ValueError):
            LLMProber(keys={}).query('q', 'unknown')

    def test_provider_contracts_and_http_errors(self):
        payloads = {'openai': {'choices': [{'message': {'content': 'answer'}}]}, 'anthropic': {'content': [{'type': 'text', 'text': 'answer'}]}, 'google': {'candidates': [{'content': {'parts': [{'text': 'answer'}]}}]}}
        for provider, payload in payloads.items():
            p = LLMProber(keys={provider: 'dummy'}, models={provider: 'test-model'})
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            with patch('urllib.request.urlopen', return_value=response) as urlopen:
                self.assertEqual(p.query('prompt', provider), 'answer')
                req = urlopen.call_args.args[0]
                self.assertNotIn('dummy', req.full_url)
                self.assertTrue('test-model' in req.full_url or 'test-model' in req.data.decode())
                self.assertEqual(urlopen.call_args.kwargs['timeout'], 30)
            error = urllib.error.HTTPError('https://secret?key=secret', 429, 'secret', {}, None)
            with patch('urllib.request.urlopen', side_effect=error):
                report = probe.brand('answer', ['q'], prober=p)
                self.assertEqual(report.error_counts, {'http_error': 1})
                self.assertNotIn('secret', repr(report))
                self.assertEqual(p.query_all('q')[provider]['status'], 'error')
            for payload in [{}, None, {'choices': []}]:
                response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
                with patch('urllib.request.urlopen', return_value=response):
                    self.assertEqual(probe.brand('answer', ['q'], prober=p).status, 'failed')

    def test_jev_envelope_and_html_escaping(self):
        c = JevClient(api_key='dummy')
        response = MagicMock()
        questions = {'x': {'type': 'noul'}}
        for payload in [{}, {'answers': {}}, {'answers': {'x': {'noul': math.nan}}}]:
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            with patch('urllib.request.urlopen', return_value=response), self.assertRaises(ValueError):
                c.ask('state', questions)
        response.__enter__.return_value.read.return_value = b'{"answers":{"x":{"noul":0.5}}}'
        with patch('urllib.request.urlopen', return_value=response):
            self.assertEqual(c.ask('state', questions)['x']['noul'], .5)
        report = audit.run('<script>x</script>', '<img>', '<b>', [], content='text', jev=FakeJev(), prober=FakeProber(), queries=['q'])
        html = report.to_html()
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_python39_syntax_contract(self):
        import ast
        for source in Path('jev_seo_geo').glob('*.py'):
            ast.parse(source.read_text(encoding='utf-8'), feature_version=(3, 9))

    def test_audit_partial_scoring_and_empty_generation(self):
        class BrokenJev:
            def ask(self, **kwargs):
                raise TimeoutError('secret')
        result = audit.run('ExampleBrand', '', '', [], content='text', queries=['q'], jev=BrokenJev(), prober=FakeProber())
        self.assertEqual(result.status, 'partial')
        self.assertEqual(result.errors, {'content': 'timeout'})
        self.assertNotIn('secret', result.to_html())
        response = MagicMock()
        p = LLMProber(keys={'openai': 'dummy'})
        for content in ['', None, {}, '   ']:
            response.__enter__.return_value.read.return_value = json.dumps({'choices': [{'message': {'content': content}}]}).encode()
            with patch('urllib.request.urlopen', return_value=response):
                self.assertEqual(probe.brand('ExampleBrand', ['q'], prober=p).status, 'failed')

    def test_provider_multipart_and_truncation(self):
        response = MagicMock()
        cases = [('anthropic', {'content': [{'type': 'text', 'text': 'one'}, {'type': 'text', 'text': 'two'}]}, 'stop_reason', 'max_tokens'),
                 ('google', {'candidates': [{'content': {'parts': [{'text': 'one'}, {'text': 'two'}]}}]}, 'finishReason', 'MAX_TOKENS')]
        for provider, payload, key, value in cases:
            p = LLMProber(keys={provider: 'dummy'})
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            with patch('urllib.request.urlopen', return_value=response):
                self.assertEqual(p.query('q', provider), 'one\ntwo')
            target = payload if provider == 'anthropic' else payload['candidates'][0]
            target[key] = value
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            with patch('urllib.request.urlopen', return_value=response):
                self.assertEqual(probe.brand('one', ['q'], prober=p).status, 'failed')
        response.__enter__.return_value.read.return_value = b'{"choices":[{"finish_reason":"length","message":{"content":"partial"}}]}'
        with patch('urllib.request.urlopen', return_value=response):
            self.assertEqual(probe.brand('partial', ['q'], prober=LLMProber(keys={'openai': 'dummy'})).status, 'failed')

    def test_readme_python_examples_run_offline(self):
        readme = Path('README.md').read_text(encoding='utf-8')
        namespace = {}
        for code in re.findall(r'```python\n(.*?)```', readme, re.S):
            exec(compile(code, 'README.md', 'exec'), namespace)


if __name__ == '__main__':
    unittest.main()

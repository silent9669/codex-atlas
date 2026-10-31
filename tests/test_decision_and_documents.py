import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / 'skills/atlas/scripts'))

from atlaslib.graph import index_repository
from atlaslib.documents import inspect
from atlaslib.decision import decide, choose_model, validate_advice, models


class DecisionDocumentsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        import subprocess
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.name', 'Atlas Test'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.email', 'test@example.invalid'], check=True)
        (self.root / 'docs/decisions').mkdir(parents=True)
        (self.root / 'docs/decisions/guard.md').write_text('# Grounding decision\n\n## Status\nProposed.\n\nNumbers need evidence.\n')
        (self.root / 'docs/notes.md').write_text('A note without a title.\n')
        (self.root / 'app.py').write_text('def run():\n    return 1\n')
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', 'fixture'], check=True)
        self.graph = index_repository(self.root)

    def test_document_audit_classifies_and_flags_missing_acceptance(self):
        report = inspect(self.root, self.graph)
        self.assertEqual(report['summary']['count'], 2)
        self.assertIn('docs/decisions/guard.md', report['summary']['decision_or_plan_without_acceptance'])
        self.assertIn('docs/notes.md', report['summary']['missing_title'])
        self.assertEqual(next(d for d in report['documents'] if d['path'].endswith('guard.md'))['type'], 'decision')

    def test_vietnamese_acceptance_is_a_signal_and_prompt_templates_are_not_missing_docs(self):
        file = self.root / 'docs/decisions/guard.md'
        file.write_text('# Quyết định\n## Cách kiểm\nKiểm thử đạt yêu cầu.\n')
        (self.root / 'prompts').mkdir()
        (self.root / 'prompts/system.md').write_text('Only return verified numbers.')
        report = inspect(self.root, index_repository(self.root))
        self.assertNotIn('docs/decisions/guard.md', report['summary']['decision_or_plan_without_acceptance'])
        self.assertNotIn('prompts/system.md', report['summary']['missing_title'])

    def test_offline_decision_is_explicit_and_routes_by_risk(self):
        report = decide(self.root, self.graph, 'What is the impact of changing the authentication API?')
        self.assertEqual(report['mode'], 'offline')
        self.assertEqual(report['status'], 'offline')
        self.assertEqual(report['routing']['model'], 'gpt-6-astra')
        self.assertTrue(report['evidence_paths'])
        self.assertEqual(report['limits']['requests'], 0)
        self.assertEqual(report['origin'], 'deterministic')

    def test_live_decision_blocks_without_a_local_key(self):
        with patch.dict('os.environ', {}, clear=True):
            report = decide(self.root, self.graph, 'Choose a document organization strategy', live=True)
        self.assertEqual(report['status'], 'blocked')
        self.assertNotIn('test-key', json.dumps(report))

    def test_live_response_parses_only_structured_output(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args):
                return json.dumps({'output_text': json.dumps({'recommendation': 'Keep docs local', 'confidence': 'medium', 'assumptions': [], 'options': [{'name': 'Local', 'tradeoff': 'Private', 'evidence_paths': ['docs/decisions/guard.md']}], 'checks': ['review links'], 'codex_prompt': 'Inspect sources.'})}).encode()
        class Opener:
            def open(self, *args, **kwargs): return Response()
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}, clear=True), patch('atlaslib.decision.urllib.request.build_opener', return_value=Opener()):
            report = decide(self.root, self.graph, 'Choose a document organization strategy', live=True)
        self.assertEqual(report['status'], 'returned')
        self.assertEqual(report['advisor']['confidence'], 'medium')

    def test_model_discovery_is_blocked_without_key(self):
        with patch.dict('os.environ', {}, clear=True):
            report = models(self.root)
        self.assertEqual(report['status'], 'blocked')

    def test_model_output_cannot_cite_unprovided_paths(self):
        citations = [{'path': 'docs/decisions/guard.md'}]
        output = {'recommendation': 'x', 'confidence': 'low', 'assumptions': [], 'options': [{'name': 'x', 'tradeoff': 'x', 'evidence_paths': ['missing.md']}], 'checks': [], 'codex_prompt': 'x'}
        with self.assertRaises(ValueError):
            validate_advice(output, citations)

    def test_codex_handoff_is_read_only_and_cited(self):
        from atlaslib.decision import decide
        report = decide(self.root, self.graph, 'Organize the repository decisions and add an audit report')
        self.assertIn('codex_prompt', report['advisor'])
        self.assertTrue(report['evidence_paths'])


if __name__ == '__main__':
    unittest.main()

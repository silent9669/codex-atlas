import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.categories import organize
from atlaslib.command import parse
from atlaslib.decision import prepare_context
from atlaslib.documents import inspect
from atlaslib.graph import index_repository
from atlaslib.labels import set_label
from atlaslib.workflows import run_command


class CategoriesWorkflowsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / 'docs').mkdir()
        (self.root / 'docs/checkout.md').write_text('# Checkout\n\nPayment confirmation appears after verification.\n')
        (self.root / 'docs/sync.md').write_text('# Synchronization\n\nHow the workspace refreshes.\n')
        self.graph = index_repository(self.root)

    def response(self, **categories):
        return {'status': 'completed', 'output_text': json.dumps({'documents': [
            {'path': 'docs/' + name + '.md', 'category': category} for name, category in categories.items()
        ]}), 'usage': {'input_tokens': 40, 'output_tokens': 20}}

    def test_ai_creates_categories_and_retains_them_until_source_changes(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}, clear=True), patch('atlaslib.categories._call', return_value=self.response(checkout='Commerce', sync='Workspace lifecycle')) as call:
            report = organize(self.root, self.graph)
            self.assertEqual(report['status'], 'organized')
            payload = call.call_args.args[2]
            self.assertFalse(payload['store'])
            self.assertNotIn('test-key', json.dumps(payload))
            self.assertLess(len(payload['input']), 40000)
        docs = {d['path']: d for d in inspect(self.root, self.graph)['documents']}
        self.assertEqual(docs['docs/sync.md']['labels']['category'], 'Workspace lifecycle')
        self.assertEqual(docs['docs/sync.md']['labels']['category_origin'], 'model-inferred')
        self.assertEqual(docs['docs/sync.md']['labels']['status'], 'unclassified')
        (self.root / 'docs/sync.md').write_text('# New lifecycle\n')
        docs = {d['path']: d for d in inspect(self.root, index_repository(self.root))['documents']}
        self.assertEqual(docs['docs/sync.md']['labels']['category_freshness'], 'stale')

    def test_invalid_or_partial_model_output_never_replaces_categories(self):
        inspect(self.root, self.graph)
        path = self.root / '.atlas/document-labels.json'
        before = json.loads(path.read_text())
        for response in [self.response(checkout='Commerce'), self.response(checkout='<script>', sync='Workspace'), {'output_text':'[]'}, {'status':'incomplete'}]:
            with self.subTest(response=response), patch.dict('os.environ', {'OPENAI_API_KEY':'test-key'}, clear=True), patch('atlaslib.categories._call', return_value=response):
                self.assertEqual(organize(self.root, self.graph)['status'], 'blocked')
                self.assertEqual(json.loads(path.read_text()), before)

    def test_reviewed_category_wins_over_ai(self):
        inspect(self.root, self.graph)
        set_label(self.root, self.graph, 'docs/checkout.md', category='Payments')
        with patch.dict('os.environ', {'OPENAI_API_KEY':'test-key'}, clear=True), patch('atlaslib.categories._call', return_value=self.response(sync='Workspace')):
            self.assertEqual(organize(self.root, self.graph)['status'], 'organized')
        labels = {d['path']:d['labels'] for d in inspect(self.root, self.graph)['documents']}
        self.assertEqual(labels['docs/checkout.md']['category'], 'Payments')
        self.assertEqual(labels['docs/checkout.md']['category_origin'], 'human-confirmed')

    def test_source_change_during_request_blocks_write(self):
        def change(*args):
            (self.root / 'docs/sync.md').write_text('# Changed\n')
            return self.response(checkout='Commerce', sync='Workspace')
        with patch.dict('os.environ', {'OPENAI_API_KEY':'test-key'}, clear=True), patch('atlaslib.categories._call', side_effect=change):
            self.assertEqual(organize(self.root, self.graph)['status'], 'blocked')

    def test_missing_key_and_command_preview_make_no_model_calls(self):
        with patch.dict('os.environ', {}, clear=True), patch('atlaslib.categories.codex_response', side_effect=ValueError('Codex unavailable')), patch('atlaslib.categories._call') as call:
            self.assertEqual(organize(self.root, self.graph)['status'], 'blocked')
            self.assertEqual(run_command(self.root, self.graph, '/codex-atlas organize')['status'], 'preview')
            call.assert_not_called()
        from atlaslib.reports import markdown
        self.assertIn('preview', markdown(run_command(self.root, self.graph, '/codex-atlas organize')))

    def test_selected_document_is_first_citation_and_must_be_indexed(self):
        citations = prepare_context(self.root, self.graph, 'How does it work?', document='docs/sync.md')
        self.assertEqual(citations[0]['path'], 'docs/sync.md')
        for path in ['../outside.md', '.env.local', 'missing.md', 123]:
            with self.assertRaises(ValueError): prepare_context(self.root, self.graph, 'Explain', document=path)

    def test_named_commands_preserve_authorization(self):
        task, options = parse('/codex-atlas docs TASK="Document checkout" RUN=true ALLOW_EDITS=true')
        self.assertEqual(task, 'Document checkout')
        self.assertTrue(options['allow_edits'])
        self.assertEqual(options['action'], 'docs')
        with patch('atlaslib.routing.execute', return_value={'status':'routed'}) as execute:
            run_command(self.root, self.graph, '/codex-atlas audit RUN=true')
            self.assertFalse(execute.call_args.kwargs['allow_edits'])
            with self.assertRaises(ValueError): run_command(self.root, self.graph, '/codex-atlas audit RUN=true ALLOW_EDITS=true')

    def test_implementation_without_checks_does_not_finalize(self):
        from atlaslib.handoff import prepare
        real_run = subprocess.run
        def execute(argv, *args, **kwargs):
            if argv[0] != 'codex': return real_run(argv, *args, **kwargs)
            final = pathlib.Path(argv[argv.index('--output-last-message') + 1])
            final.write_text(json.dumps({**{k: [] for k in ('assumptions','impact','plan','checks','blocked')}, 'outcome':'completed'}))
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch('atlaslib.handoff.subprocess.run', side_effect=execute):
            result = prepare(self.root, self.graph, 'Update documentation', run=True, allow_edits=True)
        self.assertEqual(result['result'], 'blocked')
        self.assertNotIn('finalize', result)
        self.assertFalse((self.root / '.atlas/memory.md').exists())

    def test_failed_checks_do_not_create_completion_even_with_zero_exit(self):
        from atlaslib.handoff import prepare
        real_run = subprocess.run
        def failed(argv, **kwargs):
            if argv[0] != 'codex': return real_run(argv, **kwargs)
            final = pathlib.Path(argv[argv.index('--output-last-message') + 1])
            final.write_text(json.dumps({'assumptions':[], 'impact':['Updated source'], 'plan':[],
                'checks':['python3 -m unittest: FAILED'], 'blocked':[], 'outcome':'failed'}))
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch('atlaslib.handoff.subprocess.run', side_effect=failed):
            result = prepare(self.root, self.graph, 'Implement feature', run=True, allow_edits=True)
        self.assertEqual(result['result'], 'failed')
        self.assertNotIn('finalize', result)
        self.assertFalse((self.root / '.atlas/memory.md').exists())

    def test_memory_requires_successful_run_and_is_idempotent(self):
        self.assertEqual(run_command(self.root, self.graph, '/codex-atlas memory RUN=true')['status'], 'blocked')
        folder = self.root / '.atlas/handoffs'
        folder.mkdir()
        record = {'kind':'codex-handoff','task':'Update sync docs','result':'failed','sandbox':'workspace-write','analysis':{'blocked':[], 'checks':['targeted checks passed']}}
        (folder / 'run.json').write_text(json.dumps(record))
        self.assertEqual(run_command(self.root, self.graph, '/codex-atlas memory RUN=true')['status'], 'blocked')
        final = folder / 'result.json'
        final.write_text(json.dumps({'checks':['targeted checks passed'], 'blocked':[]}))
        record.update(result='passed', result_snapshot_hash=self.graph['snapshot']['hash'], final_artifact='.atlas/handoffs/result.json', changed_paths=['docs/sync.md'])
        (folder / 'run.json').write_text(json.dumps(record))
        result = run_command(self.root, self.graph, '/codex-atlas memory RUN=true')
        self.assertEqual(result['status'], 'recorded')
        memory = (self.root / '.atlas/memory.md').read_text()
        self.assertEqual(run_command(self.root, index_repository(self.root), '/codex-atlas memory RUN=true')['status'], 'current')
        self.assertEqual((self.root / '.atlas/memory.md').read_text(), memory)
        (self.root / 'docs/sync.md').write_text('# Changed implementation notes')
        stale = run_command(self.root, index_repository(self.root), '/codex-atlas memory RUN=true')
        self.assertEqual(stale['status'], 'stale')
        self.assertEqual((self.root / '.atlas/memory.md').read_text(), memory)


if __name__ == '__main__':
    unittest.main()

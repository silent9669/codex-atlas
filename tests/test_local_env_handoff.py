import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.graph import index_repository
from atlaslib.local_env import settings
from atlaslib.handoff import prepare
from atlaslib.decision import decide


class LocalWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name).resolve()
        subprocess.run(['git','init','-q',str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.env.local\n.atlas/\n')
        (self.root / 'README.md').write_text('# Decision\nThe application starts in app.py.\n')
        (self.root / 'app.py').write_text('def run():\n    return 1\n')
        self.graph = index_repository(self.root)

    def test_local_key_file_is_auto_loaded_ignored_and_never_in_graph(self):
        (self.root / '.env.local').write_text('OPENAI_API_KEY="fake-local-key"\nATLAS_ADVISOR_MODEL=gpt-6-luna\n')
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(settings(self.root)['OPENAI_API_KEY'], 'fake-local-key')
            self.assertEqual(settings(self.root, '.env.local')['OPENAI_API_KEY'], 'fake-local-key')
        self.assertNotIn('fake-local-key', json.dumps(index_repository(self.root)))
        (self.root / 'exposed.env').write_text('OPENAI_API_KEY=fake-key\n')
        with self.assertRaises(ValueError):
            settings(self.root, 'exposed.env')

    def test_handoff_has_explicit_model_schema_and_safe_default(self):
        result = prepare(self.root, self.graph, 'Inspect the app', model='gpt-6.1-sol', effort='high')
        self.assertEqual(result['result'], 'not-run')
        self.assertEqual(result['sandbox'], 'read-only')
        self.assertIn('gpt-6.1-sol', result['argv'])
        self.assertIn('model_reasoning_effort="high"', result['argv'])
        self.assertIn('--output-schema', result['argv'])
        self.assertEqual(result['evidence_paths'], ['app.py', 'README.md'])
        self.assertNotIn('--allow-edits', result['argv'])

    def test_handoff_missing_executable_records_blocked(self):
        real_run = subprocess.run
        def execute(argv, *args, **kwargs):
            if argv[0] == 'codex': raise FileNotFoundError()
            return real_run(argv, *args, **kwargs)
        with patch('atlaslib.handoff.subprocess.run', side_effect=execute):
            result = prepare(self.root, self.graph, 'Inspect the app', run=True)
        self.assertEqual(result['result'], 'blocked')
        self.assertTrue((self.root / result['record']).is_file())

    def test_handoff_scopes_key_and_openai_provider_to_child(self):
        key = 'local-child-key'
        (self.root / '.env.local').write_text('OPENAI_API_KEY=' + key)
        seen = {}
        real_run = subprocess.run
        def execute(argv, *args, **kwargs):
            if argv[0] != 'codex': return real_run(argv, *args, **kwargs)
            seen['env'] = kwargs['env']
            final = pathlib.Path(argv[argv.index('--output-last-message') + 1])
            final.write_text(json.dumps({**{k: [] for k in ('assumptions','impact','plan','checks','blocked')}, 'outcome':'completed'}))
            class Completed:
                returncode = 0
                stdout = ''
                stderr = ''
            return Completed()
        with patch('atlaslib.handoff.subprocess.run', side_effect=execute):
            result = prepare(self.root, self.graph, 'Inspect the app', run=True, env_file='.env.local')
        self.assertEqual(result['result'], 'passed')
        self.assertEqual(seen['env']['CODEX_API_KEY'], key)
        self.assertIn('model_provider="atlas_openai"', result['argv'])
        self.assertNotIn('finalize', result)
        self.assertNotIn(key, json.dumps(result))

    def test_refusal_is_blocked_and_key_is_not_retained(self):
        key = 'local-test-key-value'
        (self.root / '.env.local').write_text('OPENAI_API_KEY=' + key)
        with patch.dict('os.environ', {}, clear=True), patch('atlaslib.decision._call', return_value={'status':'completed','output':[{'content':[{'type':'refusal','refusal':'Cannot answer'}]}]}):
            result = decide(self.root, self.graph, 'Inspect app', live=True, env_file='.env.local')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['limits']['requests'], 1)
        self.assertNotIn(key, (self.root / result['record']).read_text())

    def test_live_payload_is_bounded_and_structured(self):
        reply = {'status':'completed','model':'gpt-6-luna','usage':{'input_tokens':25,'output_tokens':30},'output_text':json.dumps({'recommendation':'Inspect app.py','confidence':'low','assumptions':[], 'options':[{'name':'Read first','tradeoff':'No edits','evidence_paths':['app.py']}], 'checks':['parse Python'], 'codex_prompt':'Inspect app.py'})}
        with patch.dict('os.environ', {'OPENAI_API_KEY':'fake-key'}, clear=True), patch('atlaslib.decision._call', return_value=reply) as request:
            result = decide(self.root, self.graph, 'Inspect app', live=True, max_output_tokens=1024)
        self.assertEqual(result['status'], 'returned')
        payload=request.call_args.args[2]
        self.assertFalse(payload['store'])
        self.assertEqual(payload['max_output_tokens'],1024)
        self.assertTrue(payload['text']['format']['strict'])
        self.assertEqual(result['usage']['input_tokens'],25)
        self.assertLessEqual(result['limits']['snippet_characters'],12000)

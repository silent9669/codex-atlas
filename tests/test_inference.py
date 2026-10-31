import json
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.inference import codex_response


class CodexInferenceTest(unittest.TestCase):
    def payload(self):
        return {'model': 'gpt-6-luna', 'reasoning': {'effort': 'low'},
                'instructions': 'Classify documents.', 'input': '{"documents": []}',
                'text': {'format': {'schema': {'type': 'object'}}}}

    def test_saved_auth_uses_isolated_read_only_cli_and_reports_usage(self):
        def run(argv, **kwargs):
            if argv[1:3] == ['mcp', 'list']:
                self.assertIn('plugins', argv)
                self.assertIn('apps', argv)
                self.assertIn('hooks', argv)
                return subprocess.CompletedProcess(argv, 0, '[{"name":"example-server","enabled":true}]', '')
            self.assertIn('read-only', argv)
            self.assertIn('--ephemeral', argv)
            self.assertIn('mcp_servers.example-server.enabled=false', argv)
            for feature in ('shell_tool', 'unified_exec', 'multi_agent', 'browser_use', 'computer_use'):
                self.assertIn(feature, argv)
                self.assertEqual(argv[argv.index(feature) - 1], '--disable')
            self.assertIn('web_search="disabled"', argv)
            self.assertIn('skills.include_instructions=false', argv)
            self.assertNotIn('--ignore-user-config', argv)
            self.assertNotIn('OPENAI_API_KEY', ' '.join(argv))
            self.assertIn('Do not use tools', kwargs['input'])
            self.assertEqual(sorted(p.name for p in kwargs['cwd'].iterdir()), ['schema.json'])
            output = pathlib.Path(argv[argv.index('--output-last-message') + 1])
            output.write_text('{"documents": []}')
            return subprocess.CompletedProcess(argv, 0, json.dumps({'type':'turn.completed','usage':{'input_tokens':20,'output_tokens':5}}), '')
        with patch('atlaslib.inference.subprocess.run', side_effect=run):
            result = codex_response(self.payload())
        self.assertEqual(result['backend'], 'codex-cli')
        self.assertEqual(result['usage']['output_tokens'], 5)
        self.assertEqual(json.loads(result['output_text']), {'documents': []})

    def test_cli_errors_never_accept_output_or_expose_stderr(self):
        for effect in (FileNotFoundError(), subprocess.TimeoutExpired('codex', 120)):
            with self.subTest(effect=effect), patch('atlaslib.inference.subprocess.run', side_effect=effect):
                with self.assertRaises(ValueError): codex_response(self.payload())
        with patch('atlaslib.inference.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'secret-value')):
            with self.assertRaises(ValueError) as error: codex_response(self.payload())
            self.assertNotIn('secret-value', str(error.exception))

    def test_successful_process_with_invalid_json_is_rejected(self):
        def run(argv, **kwargs):
            if argv[1:3] == ['mcp', 'list']:
                return subprocess.CompletedProcess(argv, 0, '[]', '')
            pathlib.Path(argv[argv.index('--output-last-message') + 1]).write_text('invalid')
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch('atlaslib.inference.subprocess.run', side_effect=run):
            with self.assertRaises(ValueError): codex_response(self.payload())

    def test_mcp_enumeration_fails_closed_before_inference(self):
        for output in ('invalid', '{}', '[null]', '[{"name":"unsafe.name"}]', '[{"name":""}]'):
            with self.subTest(output=output), patch('atlaslib.inference.subprocess.run', return_value=subprocess.CompletedProcess([], 0, output, '')) as run:
                with self.assertRaises(ValueError): codex_response(self.payload())
                self.assertEqual(run.call_count, 1)

    def test_failed_mcp_enumeration_never_starts_inference_or_exposes_metadata(self):
        with patch('atlaslib.inference.subprocess.run', return_value=subprocess.CompletedProcess([], 1, 'secret-metadata', 'secret-error')) as run:
            with self.assertRaises(ValueError) as error: codex_response(self.payload())
            self.assertNotIn('secret', str(error.exception))
            self.assertEqual(run.call_count, 1)

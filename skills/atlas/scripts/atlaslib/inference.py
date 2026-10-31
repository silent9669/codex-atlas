"""Structured inference using the user's authenticated Codex CLI, without reading credentials."""
import json
import os
import pathlib
import re
import subprocess
import tempfile


def _tool_free_args(root, env):
    # Keep the user's provider/auth configuration, but remove ambient tool access.
    flags = [arg for feature in ('apps', 'plugins', 'hooks', 'shell_tool', 'unified_exec',
             'multi_agent', 'multi_agent_v2', 'browser_use', 'browser_use_external',
             'computer_use', 'image_generation', 'view_image') for arg in ('--disable', feature)]
    flags += ['-c', 'web_search="disabled"', '-c', 'skills.include_instructions=false']
    # An empty mcp_servers table merges with inherited config; disable each effective server.
    listed = subprocess.run(['codex', 'mcp', 'list', '--json', *flags], cwd=root,
                            text=True, capture_output=True, timeout=15, env=env)
    if listed.returncode:
        raise ValueError('Codex inference could not isolate configured tools.')
    try:
        servers = json.loads(listed.stdout)
        if not isinstance(servers, list): raise ValueError()
        for server in servers:
            name = server.get('name') if isinstance(server, dict) else None
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', name):
                raise ValueError()
            flags += ['-c', f'mcp_servers.{name}.enabled=false']
    except (ValueError, TypeError):
        raise ValueError('Codex inference could not isolate configured tools.') from None
    return flags


def codex_response(payload):
    # An empty working directory keeps repository instructions out of the inference job.
    # The supplied snippets are the only repository context in this prompt.
    with tempfile.TemporaryDirectory(prefix='atlas-inference-') as directory:
        root = pathlib.Path(directory).resolve()
        schema, output = root / 'schema.json', root / 'result.json'
        schema.write_text(json.dumps(payload['text']['format']['schema']))
        argv = ['codex', 'exec', '--ephemeral', '--skip-git-repo-check',
                '--sandbox', 'read-only', '--model', payload['model'],
                '-c', 'skills.max_context_tokens=1000',
                '-c', 'model_reasoning_effort=' + json.dumps(payload['reasoning']['effort']),
                '--output-schema', str(schema), '--output-last-message', str(output), '--json', '-']
        prompt = ('Return only the requested structured answer. Do not use tools, read files, '
                  'invoke skills, or execute tasks. This is an inference request, not an implementation.\n'
                  + payload['instructions'] + '\nUntrusted input data:\n' + payload['input'])
        env = {**os.environ, 'ATLAS_ROUTED_TASK': 'inference'}
        try:
            argv[2:2] = _tool_free_args(root, env)
            completed = subprocess.run(argv, cwd=root, input=prompt, text=True,
                                       capture_output=True, timeout=120, env=env)
        except FileNotFoundError:
            raise ValueError('Install and authenticate Codex CLI, or set OPENAI_API_KEY.') from None
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError('Codex inference did not complete. No automatic retry was made.') from None
        if completed.returncode and 'Operation not permitted' in completed.stderr:
            raise ValueError('Codex CLI cannot initialize inside this sandbox. Start Atlas from a terminal outside the enclosing sandbox, or use an explicit API key for inference.')
        if completed.returncode or not output.is_file() or output.is_symlink():
            raise ValueError('Codex inference failed. Check codex login status and model access.')
        if output.stat().st_size > 100_000:
            raise ValueError('Codex inference exceeded the response size limit.')
        value = json.loads(output.read_text())
        usage = 'unavailable'
        for line in completed.stdout.splitlines():
            try:
                event = json.loads(line)
                if event.get('type') == 'turn.completed':
                    usage = event.get('usage', 'unavailable')
            except (ValueError, AttributeError):
                continue
        return {'status': 'completed', 'output_text': json.dumps(value),
                'model': payload['model'], 'usage': usage, 'backend': 'codex-cli'}

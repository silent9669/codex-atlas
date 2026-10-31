"""CLI orchestration; every invocation observes the current working tree."""
import argparse
import json
import pathlib
import subprocess
from . import analysis, evidence, reports
from .graph import git, index_repository


def main(argv=None):
    parser = argparse.ArgumentParser(prog='atlas', description='Local repository context, impact and verification evidence')
    parser.add_argument('--repo', default='.', help='Git repository root (default: current directory)')
    parser.add_argument('--version', action='version', version='Atlas 0.5.2')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('setup', 'command', 'serve', 'start', 'dispatch', 'label', 'index', 'context', 'impact', 'explain', 'audit', 'documents', 'organize', 'decide', 'models', 'route', 'codex', 'finalize', 'verify', 'drift', 'review', 'report'):
        command = commands.add_parser(name)
        command.add_argument('--json', action='store_true', help='machine-readable output')
        if name == 'command':
            command.add_argument('message')
            command.add_argument('--env-file')
            command.add_argument('--open', action='store_true')
        if name == 'context':
            command.add_argument('query')
        if name in {'impact', 'explain'}:
            command.add_argument('target')
        if name in {'decide', 'codex', 'route', 'dispatch'}:
            command.add_argument('task')
        if name == 'route':
            command.add_argument('--live', action='store_true')
            command.add_argument('--run', action='store_true')
            command.add_argument('--allow-edits', action='store_true')
            command.add_argument('--env-file')
            command.add_argument('--model', help='explicit execution-model override')
        if name == 'dispatch':
            command.add_argument('--run', action='store_true')
            command.add_argument('--allow-edits', action='store_true')
            command.add_argument('--env-file')
            command.add_argument('--model')
            command.add_argument('--offline', action='store_true')
            command.add_argument('--open', action='store_true')
        if name == 'start':
            command.add_argument('--env-file')
            command.add_argument('--open', action='store_true')
        if name == 'organize':
            command.add_argument('--env-file')
        if name == 'label':
            command.add_argument('path')
            command.add_argument('--category')
            command.add_argument('--kind')
            command.add_argument('--topics', help='comma-separated topic labels')
            command.add_argument('--status')
        if name == 'decide':
            command.add_argument('--model', default='auto')
            command.add_argument('--live', action='store_true', help='use authenticated Codex CLI or an explicit OPENAI_API_KEY')
            command.add_argument('--env-file', help='explicit ignored local env file; never persisted')
            command.add_argument('--effort', choices=['low', 'medium', 'high'])
            command.add_argument('--max-output-tokens', type=int, default=2400)
        if name == 'models':
            command.add_argument('--env-file', help='explicit ignored local env file; never persisted')
            command.add_argument('--live', action='store_true', help='query OpenAI model visibility')
        if name == 'codex':
            command.add_argument('--model', default='auto', help='explicit Codex model ID or risk-based auto route')
            command.add_argument('--effort', choices=['low', 'medium', 'high'])
            command.add_argument('--run', action='store_true', help='launch a new Codex invocation; preview is default')
            command.add_argument('--allow-edits', action='store_true', help='workspace-write for this explicitly launched invocation')
            command.add_argument('--env-file', help='ignored local env file for this invocation only')
        if name == 'finalize':
            command.add_argument('task')
            command.add_argument('--result', default='completed', choices=['completed', 'failed', 'blocked', 'cancelled'])
            command.add_argument('--result-file')
            command.add_argument('--note')
        if name == 'serve':
            command.add_argument('--port', type=int, default=8787)
            command.add_argument('--env-file')
        if name == 'verify':
            command.add_argument('target', nargs='?', help='related claim or path; all reviewed map checks run')
            command.add_argument('--commands', help='reviewed JSON command map; relative to repository root')
            command.add_argument('--run', action='store_true', help='execute reviewed checks; default is plan only')
            command.add_argument('--model', help='actual Codex model when supplied by runtime')
            command.add_argument('--task-id', help='actual task/thread ID when available')
        if name == 'review':
            command.add_argument('--changed', action='store_true')
        if name == 'report':
            command.add_argument('--output', default='.atlas/report.html')
    args = parser.parse_args(argv)
    root = pathlib.Path(args.repo).resolve()
    try:
        if args.command == 'setup':
            plugin = pathlib.Path(__file__).resolve().parents[4]
            completed = subprocess.run(['npm', 'ci', '--ignore-scripts', '--prefix', str(plugin)])
            return completed.returncode
        if args.command == 'serve':
            from .server import serve
            serve(root, args.port, args.env_file)
            return 0
        if args.command == 'start':
            from .live import start
            from .documents import inspect
            inspect(root, index_repository(root))
            result = start(root, args.env_file, args.open)
            print(json.dumps(result) if args.json else result['url'])
            return 0
        graph = evidence.attach(root, index_repository(root))
        output_folder = evidence.storage(root)
        evidence.write_json(output_folder / 'graph.json', graph)
        if args.command == 'index':
            result = graph
        elif args.command == 'command':
            from .workflows import run_command
            from .live import start
            live = start(root, args.env_file, args.open)
            result = run_command(root, graph, args.message, args.env_file)
            result['workspace'] = live
        elif args.command == 'context':
            result = analysis.context(graph, args.query, root)
        elif args.command == 'impact':
            result = analysis.impact(graph, args.target)
        elif args.command == 'explain':
            result = analysis.explain(graph, args.target)
        elif args.command == 'audit':
            from .audit import summarize
            result = summarize(root, graph)
        elif args.command == 'documents':
            from .documents import inspect
            result = inspect(root, graph)
        elif args.command == 'organize':
            from .categories import organize
            result = organize(root, graph, args.env_file)
        elif args.command == 'decide':
            from .decision import decide
            result = decide(root, graph, args.task, args.model, args.live, args.env_file, args.effort, args.max_output_tokens)
        elif args.command == 'models':
            from .decision import models
            result = models(root, args.env_file) if args.live else {'kind': 'models', 'status': 'not-run', 'models': [], 'reason': 'Pass --live to query OpenAI using the local environment.'}
        elif args.command == 'finalize':
            from .finalize import finalize
            result = finalize(root, args.task, args.result, args.result_file, args.note)
        elif args.command == 'route':
            from .routing import execute
            result = execute(root, graph, args.task, args.live, args.env_file, args.run, args.allow_edits, args.model)
        elif args.command == 'dispatch':
            from .live import start
            from .documents import inspect
            from .routing import execute
            inspect(root, graph)
            live = start(root, args.env_file, args.open)
            result = execute(root, graph, args.task, not args.offline, args.env_file, args.run, args.allow_edits, args.model)
            result['workspace'] = live
        elif args.command == 'label':
            from .labels import set_label
            result = set_label(root, graph, args.path, args.kind, args.topics.split(',') if args.topics else None, args.status, args.category)
        elif args.command == 'codex':
            from .handoff import prepare
            result = prepare(root, graph, args.task, args.model, args.effort, args.run, args.allow_edits, args.env_file)
        elif args.command == 'verify':
            result = evidence.verify(root, graph, args.commands, args.run, args.target, args.model, args.task_id)
            graph = evidence.attach(root, index_repository(root))
            evidence.write_json(output_folder / 'graph.json', graph)
        elif args.command in {'drift', 'review'}:
            result = evidence.drift(root, graph)
            if args.command == 'review':
                changed = set(git(root, 'diff', '--name-only', '-z', 'HEAD').split('\0'))
                changed.update(git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0'))
                result.update(kind='review', changed=sorted(p for p in changed if p and not p.startswith('.atlas/')))
        else:
            from .viewer import render
            from .documents import inspect
            from .audit import summarize
            decisions = []
            for path in sorted((output_folder / 'decisions').glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                if not path.is_symlink():
                    record = json.loads(path.read_text())
                    record['freshness'] = 'current' if record.get('snapshot_hash') == graph['snapshot']['hash'] else 'stale'
                    decisions.append(record)
            graph['workspace'] = {'documents': inspect(root, graph), 'audit': summarize(root, graph),
                                  'decisions': decisions, 'launcher': str(pathlib.Path(__file__).resolve().parents[1] / 'atlas'),
                                  'repository_root': str(root)}
            from .journal import summary
            graph['workspace'].update(summary(root, graph))
            output = (root / args.output).absolute()
            if not output.resolve().is_relative_to(root):
                raise ValueError('--output must stay inside the repository root.')
            if any(p.is_symlink() for p in [output, *output.parents]):
                raise ValueError('Refusing symlinked HTML output path.')
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.is_symlink():
                raise ValueError('Refusing symlinked HTML output.')
            render(graph, output)
            result = {'kind': 'report', 'output': str(output)}
        if args.command in {'route','dispatch','codex'} and args.run:
            from .documents import inspect
            refreshed=evidence.attach(root,index_repository(root))
            inspect(root,refreshed)
            evidence.write_json(output_folder/'graph.json',refreshed)
        result.setdefault('snapshot_hash', graph['snapshot']['hash'])
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == 'index':
            print(f"Indexed {len(graph['nodes'])} nodes and {len(graph['edges'])} edges at .atlas/graph.json\nDiagnostics: {len(graph['diagnostics'])}")
        elif args.command == 'report':
            print(f'Wrote {output}')
        else:
            print(reports.markdown(result), end='')
        if args.command == 'command' and result.get('execution', {}).get('result') in {'failed', 'blocked'}:
            return 1
        if args.command in {'organize', 'command'} and result.get('status') == 'blocked':
            return 1
        if args.command == 'verify' and args.run and result['result'] != 'passed':
            return 1
        if args.command == 'codex' and args.run and result['result'] != 'passed':
            return 1
        if args.command in {'route','dispatch'} and result.get('status') in {'blocked'}:
            return 1
        if args.command in {'route','dispatch'} and (result.get('freshness') == 'stale' or (args.run and result.get('execution', {}).get('result') != 'passed')):
            return 1
        if args.command == 'decide' and args.live and (result['status'] != 'returned' or result['freshness'] != 'current'):
            return 1
        if args.command == 'models' and args.live and result['status'] != 'available':
            return 1
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(evidence.redact(str(exc)))

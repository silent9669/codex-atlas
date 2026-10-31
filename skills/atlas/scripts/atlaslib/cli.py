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
    parser.add_argument('--version', action='version', version='Atlas 0.1.0')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('setup', 'index', 'context', 'impact', 'explain', 'verify', 'drift', 'review', 'report'):
        command = commands.add_parser(name)
        command.add_argument('--json', action='store_true', help='machine-readable output')
        if name == 'context':
            command.add_argument('query')
        if name in {'impact', 'explain'}:
            command.add_argument('target')
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
        graph = evidence.attach(root, index_repository(root))
        output_folder = evidence.storage(root)
        evidence.write_json(output_folder / 'graph.json', graph)
        if args.command == 'index':
            result = graph
        elif args.command == 'context':
            result = analysis.context(graph, args.query, root)
        elif args.command == 'impact':
            result = analysis.impact(graph, args.target)
        elif args.command == 'explain':
            result = analysis.explain(graph, args.target)
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
        result.setdefault('snapshot_hash', graph['snapshot']['hash'])
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == 'index':
            print(f"Indexed {len(graph['nodes'])} nodes and {len(graph['edges'])} edges at .atlas/graph.json\nDiagnostics: {len(graph['diagnostics'])}")
        elif args.command == 'report':
            print(f'Wrote {output}')
        else:
            print(reports.markdown(result), end='')
        if args.command == 'verify' and args.run and result['result'] != 'passed':
            return 1
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(evidence.redact(str(exc)))
